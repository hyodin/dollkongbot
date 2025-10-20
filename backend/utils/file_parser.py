"""
파일 형식별 텍스트 추출 유틸리티
지원 형식: PDF, DOCX, XLSX, TXT
"""

import io
import logging
from pathlib import Path
from typing import Optional, Union, List, Dict, Any

import PyPDF2
import pdfplumber
from docx import Document
from openpyxl import load_workbook
from openpyxl.utils import get_column_letter

logger = logging.getLogger(__name__)


class FileParser:
    """파일 형식별 텍스트 추출기"""
    
    SUPPORTED_EXTENSIONS = {'.pdf', '.docx', '.xlsx', '.txt'}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    @classmethod
    async def extract_text(cls, file_content: bytes, filename: str) -> Union[str, List[Dict[str, Any]]]:
        """
        파일 내용에서 텍스트 추출
        
        Args:
            file_content: 파일 바이트 데이터
            filename: 파일명 (확장자 포함)
            
        Returns:
            XLSX: 구조화된 셀 데이터 리스트
            기타: 추출된 텍스트 문자열
            
        Raises:
            ValueError: 지원하지 않는 파일 형식
            RuntimeError: 텍스트 추출 실패
        """
        if len(file_content) > FileParser.MAX_FILE_SIZE:
            raise ValueError(f"파일 크기가 {FileParser.MAX_FILE_SIZE / 1024 / 1024}MB를 초과합니다")
        
        file_ext = Path(filename).suffix.lower()
        
        if file_ext not in FileParser.SUPPORTED_EXTENSIONS:
            raise ValueError(f"지원하지 않는 파일 형식: {file_ext}")
        
        try:
            if file_ext == '.pdf':
                return await FileParser._extract_from_pdf(file_content)
            elif file_ext == '.docx':
                return await FileParser._extract_from_docx(file_content)
            elif file_ext == '.xlsx':
                return await FileParser._extract_from_xlsx(file_content)
            elif file_ext == '.txt':
                return await FileParser._extract_from_txt(file_content)
        except Exception as e:
            logger.error(f"텍스트 추출 실패 - 파일: {filename}, 오류: {str(e)}")
            raise RuntimeError(f"텍스트 추출 실패: {str(e)}")
    
    @staticmethod
    async def _extract_from_pdf(file_content: bytes) -> Union[str, List[Dict[str, Any]]]:
        """PDF 파일에서 텍스트 및 표 추출"""
        try:
            pdf_file = io.BytesIO(file_content)
            
            # pdfplumber로 표 감지 및 추출 시도
            try:
                with pdfplumber.open(pdf_file) as pdf:
                    structured_data = []
                    has_tables = False
                    
                    for page_num, page in enumerate(pdf.pages):
                        logger.info(f"PDF 페이지 {page_num + 1} 처리 중...")
                        
                        # 표 추출 시도
                        tables = page.extract_tables()
                        if tables:
                            logger.info(f"페이지 {page_num + 1}에서 {len(tables)}개 표 발견")
                            has_tables = True
                            
                            for table_idx, table in enumerate(tables):
                                if table and len(table) > 1:  # 헤더 + 데이터 행이 있는 경우
                                    logger.info(f"표 {table_idx + 1} 처리 중... (행 수: {len(table)})")
                                    table_data = FileParser._process_pdf_table(table, page_num + 1, table_idx + 1)
                                    logger.info(f"표 {table_idx + 1}에서 {len(table_data)}개 항목 추출")
                                    structured_data.extend(table_data)
                                else:
                                    logger.warning(f"표 {table_idx + 1}이 비어있거나 데이터가 부족합니다")
                        
                        # 표가 없는 경우 일반 텍스트 추출
                        if not tables:
                            logger.info(f"페이지 {page_num + 1}에 표가 없음, 텍스트 추출 시도")
                            page_text = page.extract_text()
                            if page_text and page_text.strip():
                                logger.info(f"페이지 {page_num + 1}에서 텍스트 추출 성공 ({len(page_text)}자)")
                                # 텍스트를 구조화된 형태로 변환
                                text_data = FileParser._process_pdf_text(page_text, page_num + 1)
                                logger.info(f"텍스트에서 {len(text_data)}개 항목 추출")
                                structured_data.extend(text_data)
                            else:
                                logger.warning(f"페이지 {page_num + 1}에서 텍스트를 추출할 수 없습니다")
                    
                    if has_tables and structured_data:
                        logger.info(f"PDF 표 데이터 추출 완료: {len(structured_data)}개 항목")
                        return structured_data
                    elif structured_data:
                        logger.info(f"PDF 텍스트 데이터 추출 완료: {len(structured_data)}개 항목")
                        return structured_data
                    else:
                        # 기존 방식으로 폴백
                        return await FileParser._extract_from_pdf_fallback(file_content)
                        
            except Exception as e:
                logger.warning(f"pdfplumber 처리 실패, 기존 방식으로 폴백: {str(e)}")
                return await FileParser._extract_from_pdf_fallback(file_content)
                
        except Exception as e:
            raise RuntimeError(f"PDF 처리 오류: {str(e)}")
    
    @staticmethod
    async def _extract_from_pdf_fallback(file_content: bytes) -> str:
        """PDF 파일에서 텍스트 추출 (기존 방식)"""
        text_parts = []
        
        try:
            pdf_file = io.BytesIO(file_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text.strip():
                        text_parts.append(page_text)
                except Exception as e:
                    logger.warning(f"PDF 페이지 {page_num + 1} 텍스트 추출 실패: {str(e)}")
                    continue
            
            if not text_parts:
                raise RuntimeError("PDF에서 텍스트를 추출할 수 없습니다")
                
            return '\n\n'.join(text_parts)
            
        except Exception as e:
            raise RuntimeError(f"PDF 처리 오류: {str(e)}")
    
    @staticmethod
    def _process_pdf_table(table: List[List[str]], page_num: int, table_idx: int) -> List[Dict[str, Any]]:
        """PDF 표를 구조화된 데이터로 변환"""
        if not table or len(table) < 2:
            logger.warning(f"표가 비어있거나 데이터가 부족합니다 (행 수: {len(table) if table else 0})")
            return []
        
        logger.info(f"표 처리 시작 - 페이지: {page_num}, 표: {table_idx}, 행 수: {len(table)}")
        
        structured_data = []
        headers = table[0] if table else []
        
        # 헤더 정리
        clean_headers = []
        for header in headers:
            if header:
                clean_headers.append(str(header).strip())
            else:
                clean_headers.append("")
        
        logger.info(f"표 헤더: {clean_headers}")
        
        # 데이터 행 처리
        processed_rows = 0
        for row_idx, row in enumerate(table[1:], 1):
            if not row or all(not cell for cell in row):
                logger.debug(f"행 {row_idx} 건너뛰기 (빈 행)")
                continue
            
            # 행 데이터 정리
            clean_row = []
            for cell in row:
                if cell:
                    clean_row.append(str(cell).strip())
                else:
                    clean_row.append("")
            
            # 계층형 구조 추출 시도
            lvl1, lvl2, lvl3, lvl4 = FileParser._extract_hierarchical_structure(clean_headers, clean_row)
            
            if lvl1 or lvl2 or lvl3 or lvl4:
                logger.debug(f"행 {row_idx} 계층형 구조: lvl1={lvl1}, lvl2={lvl2}, lvl3={lvl3}, lvl4={lvl4}")
            
            # 각 셀별로 데이터 생성
            row_cells = 0
            for col_idx, (header, value) in enumerate(zip(clean_headers, clean_row)):
                if value:  # 값이 있는 셀만 처리
                    cell_data = {
                        "page": page_num,
                        "table": table_idx,
                        "row": row_idx,
                        "col": col_idx + 1,
                        "header": header,
                        "value": value,
                        "lvl1": lvl1,
                        "lvl2": lvl2,
                        "lvl3": lvl3,
                        "lvl4": lvl4,
                        "row_context": " | ".join([v for v in clean_row if v])
                    }
                    structured_data.append(cell_data)
                    row_cells += 1
            
            if row_cells > 0:
                processed_rows += 1
                logger.debug(f"행 {row_idx} 처리 완료: {row_cells}개 셀")
        
        logger.info(f"표 처리 완료: {processed_rows}개 행, {len(structured_data)}개 셀")
        return structured_data
    
    @staticmethod
    def _process_pdf_text(text: str, page_num: int) -> List[Dict[str, Any]]:
        """PDF 텍스트를 구조화된 데이터로 변환"""
        if not text or not text.strip():
            return []
        
        lines = text.strip().split('\n')
        structured_data = []
        
        for line_idx, line in enumerate(lines, 1):
            if line.strip():
                # 간단한 구조화 (실제로는 더 정교한 파싱이 필요할 수 있음)
                structured_data.append({
                    "page": page_num,
                    "table": 0,
                    "row": line_idx,
                    "col": 1,
                    "header": "텍스트",
                    "value": line.strip(),
                    "lvl1": "",
                    "lvl2": "",
                    "lvl3": "",
                    "lvl4": line.strip(),
                    "row_context": line.strip()
                })
        
        return structured_data
    
    @staticmethod
    def _extract_hierarchical_structure(headers: List[str], row: List[str]) -> tuple:
        """표 행에서 계층형 구조 추출"""
        lvl1 = lvl2 = lvl3 = lvl4 = ""
        
        # 일반적인 계층형 구조 패턴 감지
        if len(headers) >= 4 and len(row) >= 4:
            # 첫 번째 컬럼이 구분/카테고리인 경우
            if headers[0] and any(keyword in headers[0].lower() for keyword in ['구분', '분류', '카테고리', '구분1']):
                lvl1 = row[0] if row[0] else ""
            if len(headers) > 1 and headers[1] and any(keyword in headers[1].lower() for keyword in ['구분2', '세부', '하위']):
                lvl2 = row[1] if row[1] else ""
            if len(headers) > 2 and headers[2] and any(keyword in headers[2].lower() for keyword in ['구분3', '세부', '항목']):
                lvl3 = row[2] if row[2] else ""
            if len(headers) > 3 and headers[3] and any(keyword in headers[3].lower() for keyword in ['내용', '세부내용', '설명']):
                lvl4 = row[3] if row[3] else ""
        
        # 자동 감지가 실패한 경우 첫 4개 컬럼을 lvl1~lvl4로 매핑
        if not lvl1 and len(row) >= 1:
            lvl1 = row[0] if row[0] else ""
        if not lvl2 and len(row) >= 2:
            lvl2 = row[1] if row[1] else ""
        if not lvl3 and len(row) >= 3:
            lvl3 = row[2] if row[2] else ""
        if not lvl4 and len(row) >= 4:
            lvl4 = row[3] if row[3] else ""
        
        return lvl1, lvl2, lvl3, lvl4
    
    @staticmethod
    async def _extract_from_docx(file_content: bytes) -> Union[str, List[Dict[str, Any]]]:
        """DOCX 파일에서 텍스트 및 구조 추출"""
        try:
            docx_file = io.BytesIO(file_content)
            doc = Document(docx_file)
            
            logger.info("DOCX 파일 구조 분석 시작")
            
            # 구조화된 데이터 추출 시도
            structured_data = []
            
            # 1. 문단 구조 분석
            paragraph_data = FileParser._extract_docx_paragraphs(doc.paragraphs)
            if paragraph_data:
                structured_data.extend(paragraph_data)
                logger.info(f"문단에서 {len(paragraph_data)}개 항목 추출")
            
            # 2. 표 구조 분석
            table_data = FileParser._extract_docx_tables(doc.tables)
            if table_data:
                structured_data.extend(table_data)
                logger.info(f"표에서 {len(table_data)}개 항목 추출")
            
            if structured_data:
                logger.info(f"DOCX 구조화 데이터 추출 완료: {len(structured_data)}개 항목")
                return structured_data
            else:
                # 구조화 실패 시 기존 방식으로 폴백
                logger.warning("구조화 추출 실패, 기존 텍스트 방식으로 폴백")
                return await FileParser._extract_from_docx_fallback(doc)
                
        except Exception as e:
            logger.error(f"DOCX 처리 오류: {str(e)}")
            raise RuntimeError(f"DOCX 처리 오류: {str(e)}")
    
    @staticmethod
    async def _extract_from_docx_fallback(doc) -> str:
        """DOCX 파일에서 텍스트 추출 (기존 방식)"""
        try:
            text_parts = []
            
            # 문단 텍스트 추출
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_parts.append(paragraph.text)
            
            # 표 텍스트 추출
            for table in doc.tables:
                for row in table.rows:
                    row_text = []
                    for cell in row.cells:
                        if cell.text.strip():
                            row_text.append(cell.text.strip())
                    if row_text:
                        text_parts.append(' | '.join(row_text))
            
            if not text_parts:
                raise RuntimeError("DOCX에서 텍스트를 추출할 수 없습니다")
            
            return '\n'.join(text_parts)
            
        except Exception as e:
            raise RuntimeError(f"DOCX 폴백 처리 오류: {str(e)}")
    
    @staticmethod
    def _extract_docx_paragraphs(paragraphs) -> List[Dict[str, Any]]:
        """DOCX 문단에서 구조화된 데이터 추출"""
        structured_data = []
        current_lvl1 = ""
        current_lvl2 = ""
        current_lvl3 = ""
        
        logger.info(f"문단 처리 시작: {len(paragraphs)}개 문단")
        
        for para_idx, paragraph in enumerate(paragraphs):
            text = paragraph.text.strip()
            if not text:
                continue
            
            # 제목/조항 패턴 감지
            lvl1, lvl2, lvl3, lvl4 = FileParser._extract_docx_structure(text, paragraph)
            
            # 계층형 구조 업데이트 (forward fill)
            if lvl1:
                current_lvl1 = lvl1
                current_lvl2 = ""
                current_lvl3 = ""
                logger.info(f"조항 발견: {lvl1}")
            elif lvl2:
                current_lvl2 = lvl2
                current_lvl3 = ""
                logger.debug(f"소항목 발견: {lvl2}")
            elif lvl3:
                current_lvl3 = lvl3
                logger.debug(f"세부항목 발견: {lvl3}")
            
            # lvl4가 없으면 전체 텍스트를 lvl4로 사용
            if not lvl4:
                lvl4 = text
            
            # 구조화된 데이터 생성
            if text:  # 빈 텍스트가 아닌 경우만
                structured_data.append({
                    "page": 1,  # DOCX는 페이지 정보가 없으므로 1로 설정
                    "table": 0,
                    "row": para_idx + 1,
                    "col": 1,
                    "header": "문단",
                    "value": text,
                    "lvl1": current_lvl1,
                    "lvl2": current_lvl2,
                    "lvl3": current_lvl3,
                    "lvl4": lvl4,
                    "row_context": text,
                    "paragraph_style": paragraph.style.name if paragraph.style else "Normal"
                })
        
        logger.info(f"문단 처리 완료: {len(structured_data)}개 항목 추출")
        return structured_data
    
    @staticmethod
    def _extract_docx_tables(tables) -> List[Dict[str, Any]]:
        """DOCX 표에서 구조화된 데이터 추출"""
        structured_data = []
        
        logger.info(f"표 처리 시작: {len(tables)}개 표")
        
        for table_idx, table in enumerate(tables, 1):
            logger.info(f"표 {table_idx} 처리 중... (행 수: {len(table.rows)})")
            
            if not table.rows:
                logger.warning(f"표 {table_idx}이 비어있습니다")
                continue
            
            # 헤더 추출 (첫 번째 행)
            headers = []
            if table.rows:
                first_row = table.rows[0]
                for cell in first_row.cells:
                    headers.append(cell.text.strip())
            
            logger.info(f"표 {table_idx} 헤더: {headers}")
            
            # 데이터 행 처리
            processed_rows = 0
            for row_idx, row in enumerate(table.rows[1:], 1):
                if not row.cells:
                    continue
                
                # 행 데이터 추출
                row_data = []
                for cell in row.cells:
                    row_data.append(cell.text.strip())
                
                # 계층형 구조 추출
                lvl1, lvl2, lvl3, lvl4 = FileParser._extract_hierarchical_structure(headers, row_data)
                
                if lvl1 or lvl2 or lvl3 or lvl4:
                    logger.debug(f"표 {table_idx} 행 {row_idx} 계층형 구조: lvl1={lvl1}, lvl2={lvl2}, lvl3={lvl3}, lvl4={lvl4}")
                
                # 각 셀별로 데이터 생성
                row_cells = 0
                for col_idx, (header, value) in enumerate(zip(headers, row_data)):
                    if value:  # 값이 있는 셀만 처리
                        structured_data.append({
                            "page": 1,
                            "table": table_idx,
                            "row": row_idx,
                            "col": col_idx + 1,
                            "header": header,
                            "value": value,
                            "lvl1": lvl1,
                            "lvl2": lvl2,
                            "lvl3": lvl3,
                            "lvl4": lvl4,
                            "row_context": " | ".join([v for v in row_data if v])
                        })
                        row_cells += 1
                
                if row_cells > 0:
                    processed_rows += 1
                    logger.debug(f"표 {table_idx} 행 {row_idx} 처리 완료: {row_cells}개 셀")
            
            logger.info(f"표 {table_idx} 처리 완료: {processed_rows}개 행, {len([item for item in structured_data if item.get('table') == table_idx])}개 셀")
        
        logger.info(f"표 처리 완료: {len(structured_data)}개 항목 추출")
        return structured_data
    
    @staticmethod
    def _extract_docx_structure(text: str, paragraph) -> tuple:
        """DOCX 문단에서 계층형 구조 추출"""
        lvl1 = lvl2 = lvl3 = lvl4 = ""
        
        # 제목/조항 패턴 감지
        import re
        
        # 제1조, 제2조 등의 패턴 (lvl1)
        article_match = re.match(r'제(\d+)조\s*\(([^)]+)\)', text)
        if article_match:
            lvl1 = text
            return lvl1, lvl2, lvl3, lvl4
        
        # ①, ②, ③ 등의 패턴 (lvl2)
        if re.match(r'[①②③④⑤⑥⑦⑧⑨⑩]', text):
            lvl2 = text
            return lvl1, lvl2, lvl3, lvl4
        
        # 1), 2), 3) 등의 패턴 (lvl3)
        if re.match(r'\d+\)', text):
            lvl3 = text
            return lvl1, lvl2, lvl3, lvl4
        
        # 가), 나), 다) 등의 패턴 (lvl3)
        if re.match(r'[가-힣]\)', text):
            lvl3 = text
            return lvl1, lvl2, lvl3, lvl4
        
        # 일반 문단은 lvl4로 처리
        lvl4 = text
        return lvl1, lvl2, lvl3, lvl4
    
    @staticmethod
    async def _extract_from_xlsx(file_content: bytes) -> List[Dict[str, Any]]:
        """XLSX 파일에서 구조화된 셀 데이터 추출 (계층형 컬럼 지원)"""
        try:
            xlsx_file = io.BytesIO(file_content)
            workbook = load_workbook(xlsx_file, read_only=True, data_only=True)
            
            cell_data = []
            
            for sheet_name in workbook.sheetnames:
                sheet = workbook[sheet_name]
                
                # 시트가 비어있으면 건너뛰기
                if sheet.max_row == 0:
                    continue
                
                # 첫 번째 행을 헤더로 저장
                headers = {}
                first_row = list(sheet.iter_rows(min_row=1, max_row=1, values_only=True))[0]
                for col_idx, header_value in enumerate(first_row, 1):
                    if header_value is not None:
                        headers[col_idx] = str(header_value).strip()
                    else:
                        headers[col_idx] = f"Column{col_idx}"
                
                # 고정 매핑 규칙 (항상 동일한 컬럼 순서 사용)
                # 컬럼 순서: 구분1(1번째), 구분2(2번째), 구분3(3번째), 세부 내용(4번째), 비고(5번째)
                lvl1_col_idx = 2  # 구분1 - 항상 1번째 컬럼
                lvl2_col_idx = 3  # 구분2 - 항상 2번째 컬럼
                lvl3_col_idx = 4  # 구분3 - 항상 3번째 컬럼
                detail_col_idx = 5  # 세부 내용 - 항상 4번째 컬럼
                remarks_col_idx = 6  # 비고 - 항상 5번째 컬럼
                
                # 계층형 컬럼 추출을 위한 상태 관리
                lvl1_value = None
                lvl2_value = None
                lvl3_value = None
                
                # 2행부터 데이터 처리
                for row_idx in range(2, sheet.max_row + 1):
                    row_values = list(sheet.iter_rows(min_row=row_idx, max_row=row_idx, values_only=True))[0]
                    
                    # 행 컨텍스트 생성 (같은 행의 모든 값들)
                    row_context_parts = []
                    for val in row_values:
                        if val is not None:
                            val_str = str(val).strip()
                            if val_str:
                                row_context_parts.append(val_str)
                    row_context = " | ".join(row_context_parts) if row_context_parts else ""
                    
                    # 계층형 컬럼 값 업데이트 (forward fill 로직)
                    current_lvl1 = lvl1_value
                    current_lvl2 = lvl2_value
                    current_lvl3 = lvl3_value
                    
                    # 구분1 컬럼 확인
                    if lvl1_col_idx and len(row_values) >= lvl1_col_idx and row_values[lvl1_col_idx-1] is not None:
                        val_str = str(row_values[lvl1_col_idx-1]).strip()
                        if val_str:
                            current_lvl1 = val_str
                            lvl1_value = val_str  # 다음 행을 위해 저장
                    
                    # 구분2 컬럼 확인
                    if lvl2_col_idx and len(row_values) >= lvl2_col_idx and row_values[lvl2_col_idx-1] is not None:
                        val_str = str(row_values[lvl2_col_idx-1]).strip()
                        if val_str:
                            current_lvl2 = val_str
                            lvl2_value = val_str
                    
                    # 구분3 컬럼 확인
                    if lvl3_col_idx and len(row_values) >= lvl3_col_idx and row_values[lvl3_col_idx-1] is not None:
                        val_str = str(row_values[lvl3_col_idx-1]).strip()
                        if val_str:
                            current_lvl3 = val_str
                            lvl3_value = val_str
                    
                    # 세부 내용과 비고 컬럼 추출
                    detail_content = ""
                    remarks = ""
                    
                    if detail_col_idx and len(row_values) >= detail_col_idx and row_values[detail_col_idx-1] is not None:
                        detail_content = str(row_values[detail_col_idx-1]).strip()
                    
                    if remarks_col_idx and len(row_values) >= remarks_col_idx and row_values[remarks_col_idx-1] is not None:
                        remarks = str(row_values[remarks_col_idx-1]).strip()
                    
                    # lvl4 생성 (세부 내용 + 비고)
                    lvl4_parts = []
                    if detail_content:
                        lvl4_parts.append(detail_content)
                    if remarks:
                        lvl4_parts.append(remarks)
                    lvl4_value = " | ".join(lvl4_parts) if lvl4_parts else ""
                    
                    # 각 셀 처리 (기존 로직 유지)
                    for col_idx, cell_value in enumerate(row_values, 1):
                        if cell_value is not None:
                            cell_str = str(cell_value).strip()
                            if cell_str and len(cell_str) > 0:  # 빈 문자열이 아닌 경우
                                col_letter = get_column_letter(col_idx)
                                
                                # 숫자 여부 판단
                                is_numeric = False
                                try:
                                    float(cell_str)
                                    is_numeric = True
                                except ValueError:
                                    pass
                                
                                cell_info = {
                                    "sheet": sheet_name,
                                    "row": row_idx,
                                    "col": col_letter,
                                    "cell_address": f"{sheet_name}!{col_letter}{row_idx}",
                                    "value": cell_str,
                                    "row_context": row_context,
                                    "col_header": headers.get(col_idx, f"Column{col_idx}"),
                                    "is_numeric": is_numeric,
                                    # 계층형 컬럼 추가
                                    "lvl1": current_lvl1 or "",
                                    "lvl2": current_lvl2 or "",
                                    "lvl3": current_lvl3 or "",
                                    "lvl4": lvl4_value
                                }
                                cell_data.append(cell_info)
            
            workbook.close()
            
            if not cell_data:
                raise RuntimeError("XLSX에서 데이터를 추출할 수 없습니다")
            
            logger.info(f"XLSX 셀 데이터 추출 완료: {len(cell_data)}개 셀 (계층형 컬럼 포함)")
            return cell_data
            
        except Exception as e:
            raise RuntimeError(f"XLSX 처리 오류: {str(e)}")
    
    @staticmethod
    async def _extract_from_txt(file_content: bytes) -> str:
        """TXT 파일에서 텍스트 추출"""
        try:
            # UTF-8로 먼저 시도
            try:
                text = file_content.decode('utf-8')
            except UnicodeDecodeError:
                # UTF-8 실패 시 CP949 (EUC-KR) 시도
                try:
                    text = file_content.decode('cp949')
                except UnicodeDecodeError:
                    # 모든 인코딩 실패 시 무시하고 디코딩
                    text = file_content.decode('utf-8', errors='ignore')
            
            if not text.strip():
                raise RuntimeError("TXT 파일이 비어있습니다")
            
            return text
            
        except Exception as e:
            raise RuntimeError(f"TXT 처리 오류: {str(e)}")
