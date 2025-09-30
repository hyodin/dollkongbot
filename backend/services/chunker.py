"""
문장 단위 텍스트 청킹 서비스
"""

import logging
import re
from typing import List

try:
    import kss
    KSS_AVAILABLE = True
except ImportError:
    KSS_AVAILABLE = False
    logging.warning("kss 라이브러리가 설치되지 않았습니다. 기본 문장 분리기를 사용합니다.")

logger = logging.getLogger(__name__)


class TextChunker:
    """텍스트 청킹 처리기"""
    
    def __init__(self, max_chunk_length: int = 500, overlap_length: int = 50):
        """
        초기화
        
        Args:
            max_chunk_length: 청크 최대 길이 (문자 기준)
            overlap_length: 청크 간 겹치는 길이
        """
        self.max_chunk_length = max_chunk_length
        self.overlap_length = overlap_length
        
        # 문장 종료 패턴 (한국어)
        self.sentence_endings = re.compile(r'[.!?。][\s]*')
        
        logger.info(f"TextChunker 초기화 완료 - 최대 길이: {max_chunk_length}, 겹침: {overlap_length}")
    
    def chunk_text(self, text: str) -> List[str]:
        """
        텍스트를 문장 단위로 청킹
        
        Args:
            text: 입력 텍스트
            
        Returns:
            청크 리스트
        """
        if not text or not text.strip():
            return []
        
        # 1. 문장 분리
        sentences = self._split_sentences(text)
        
        if not sentences:
            return []
        
        # 2. 청크로 그룹화
        chunks = self._create_chunks(sentences)
        
        # 3. 빈 청크 제거 및 정제
        cleaned_chunks = []
        for chunk in chunks:
            cleaned = chunk.strip()
            if cleaned and len(cleaned) > 10:  # 최소 길이 체크
                cleaned_chunks.append(cleaned)
        
        logger.info(f"텍스트 청킹 완료 - 입력 길이: {len(text)}, 청크 수: {len(cleaned_chunks)}")
        return cleaned_chunks
    
    def _split_sentences(self, text: str) -> List[str]:
        """문장 분리"""
        if KSS_AVAILABLE:
            try:
                # kss를 사용한 한국어 문장 분리
                sentences = kss.split_sentences(text)
                return [s.strip() for s in sentences if s.strip()]
            except Exception as e:
                logger.warning(f"kss 문장 분리 실패, 기본 방식 사용: {str(e)}")
        
        # 기본 문장 분리 (정규식 기반)
        return self._split_sentences_regex(text)
    
    def _split_sentences_regex(self, text: str) -> List[str]:
        """정규식 기반 문장 분리"""
        # 줄바꿈을 공백으로 변환
        text = re.sub(r'\n+', ' ', text)
        
        # 문장 종료 기호로 분리
        sentences = self.sentence_endings.split(text)
        
        result = []
        for i, sentence in enumerate(sentences):
            sentence = sentence.strip()
            if sentence:
                # 마지막 문장이 아니면서 문장 종료 기호가 없으면 추가
                if i < len(sentences) - 1:
                    # 원본에서 해당 위치의 종료 기호 찾아서 추가
                    original_ending = self._find_sentence_ending(text, sentence)
                    sentence += original_ending
                result.append(sentence)
        
        return result
    
    def _find_sentence_ending(self, original_text: str, sentence: str) -> str:
        """원본 텍스트에서 문장 종료 기호 찾기"""
        # 간단한 구현: 첫 번째로 발견되는 종료 기호 반환
        for ending in ['.', '!', '?', '。']:
            if ending in original_text:
                return ending
        return '.'
    
    def _create_chunks(self, sentences: List[str]) -> List[str]:
        """문장들을 청크로 그룹화"""
        if not sentences:
            return []
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            # 현재 청크에 문장을 추가했을 때의 길이 확인
            potential_chunk = current_chunk + (" " if current_chunk else "") + sentence
            
            if len(potential_chunk) <= self.max_chunk_length:
                # 최대 길이 이내이면 추가
                current_chunk = potential_chunk
            else:
                # 최대 길이 초과 시
                if current_chunk:
                    chunks.append(current_chunk)
                
                # 새 청크 시작
                if len(sentence) <= self.max_chunk_length:
                    current_chunk = sentence
                else:
                    # 문장이 너무 길면 분할
                    split_chunks = self._split_long_sentence(sentence)
                    chunks.extend(split_chunks[:-1])
                    current_chunk = split_chunks[-1] if split_chunks else ""
        
        # 마지막 청크 추가
        if current_chunk:
            chunks.append(current_chunk)
        
        # 겹치는 부분 추가 (더 나은 컨텍스트를 위해)
        if self.overlap_length > 0 and len(chunks) > 1:
            chunks = self._add_overlaps(chunks)
        
        return chunks
    
    def _split_long_sentence(self, sentence: str) -> List[str]:
        """긴 문장을 더 작은 청크로 분할"""
        if len(sentence) <= self.max_chunk_length:
            return [sentence]
        
        # 쉼표나 세미콜론으로 1차 분할 시도
        for delimiter in [', ', '; ', ' - ', ' – ']:
            if delimiter in sentence:
                parts = sentence.split(delimiter)
                chunks = []
                current = ""
                
                for part in parts:
                    potential = current + (delimiter if current else "") + part
                    if len(potential) <= self.max_chunk_length:
                        current = potential
                    else:
                        if current:
                            chunks.append(current)
                        current = part
                
                if current:
                    chunks.append(current)
                
                if len(chunks) > 1:
                    return chunks
        
        # 델리미터로 분할할 수 없으면 강제 분할
        chunks = []
        while len(sentence) > self.max_chunk_length:
            # 공백 기준으로 적절한 위치 찾기
            split_pos = sentence.rfind(' ', 0, self.max_chunk_length)
            if split_pos == -1:
                split_pos = self.max_chunk_length
            
            chunks.append(sentence[:split_pos])
            sentence = sentence[split_pos:].strip()
        
        if sentence:
            chunks.append(sentence)
        
        return chunks
    
    def _add_overlaps(self, chunks: List[str]) -> List[str]:
        """청크 간 겹치는 부분 추가"""
        if len(chunks) <= 1:
            return chunks
        
        overlapped_chunks = [chunks[0]]
        
        for i in range(1, len(chunks)):
            prev_chunk = chunks[i-1]
            current_chunk = chunks[i]
            
            # 이전 청크의 마지막 부분을 현재 청크 앞에 추가
            if len(prev_chunk) > self.overlap_length:
                # 단어 단위로 겹치는 부분 찾기
                prev_words = prev_chunk.split()
                overlap_words = []
                overlap_length = 0
                
                for word in reversed(prev_words):
                    if overlap_length + len(word) + 1 <= self.overlap_length:
                        overlap_words.insert(0, word)
                        overlap_length += len(word) + 1
                    else:
                        break
                
                if overlap_words:
                    overlap_text = ' '.join(overlap_words)
                    current_chunk = overlap_text + " " + current_chunk
            
            overlapped_chunks.append(current_chunk)
        
        return overlapped_chunks


# 싱글톤 인스턴스
_chunker_instance = None


def get_chunker() -> TextChunker:
    """전역 청킹 인스턴스 반환 (싱글톤 패턴)"""
    global _chunker_instance
    if _chunker_instance is None:
        _chunker_instance = TextChunker()
    return _chunker_instance
