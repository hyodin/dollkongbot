"""
파일 형식별 텍스트 추출 유틸리티
지원 형식: PDF, DOCX, XLSX, TXT
"""

import io
import logging
from pathlib import Path
from typing import Optional

import PyPDF2
from docx import Document
from openpyxl import load_workbook

logger = logging.getLogger(__name__)


class FileParser:
    """파일 형식별 텍스트 추출기"""
    
    SUPPORTED_EXTENSIONS = {'.pdf', '.docx', '.xlsx', '.txt'}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    @classmethod
    async def extract_text(cls, file_content: bytes, filename: str) -> str:
        """
        파일 내용에서 텍스트 추출
        
        Args:
            file_content: 파일 바이트 데이터
            filename: 파일명 (확장자 포함)
            
        Returns:
            추출된 텍스트
            
        Raises:
            ValueError: 지원하지 않는 파일 형식
            RuntimeError: 텍스트 추출 실패
        """
        if len(file_content) > cls.MAX_FILE_SIZE:
            raise ValueError(f"파일 크기가 {cls.MAX_FILE_SIZE / 1024 / 1024}MB를 초과합니다")
        
        file_ext = Path(filename).suffix.lower()
        
        if file_ext not in cls.SUPPORTED_EXTENSIONS:
            raise ValueError(f"지원하지 않는 파일 형식: {file_ext}")
        
        try:
            if file_ext == '.pdf':
                return await cls._extract_from_pdf(file_content)
            elif file_ext == '.docx':
                return await cls._extract_from_docx(file_content)
            elif file_ext == '.xlsx':
                return await cls._extract_from_xlsx(file_content)
            elif file_ext == '.txt':
                return await cls._extract_from_txt(file_content)
        except Exception as e:
            logger.error(f"텍스트 추출 실패 - 파일: {filename}, 오류: {str(e)}")
            raise RuntimeError(f"텍스트 추출 실패: {str(e)}")
    
    @staticmethod
    async def _extract_from_pdf(file_content: bytes) -> str:
        """PDF 파일에서 텍스트 추출"""
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
    async def _extract_from_docx(file_content: bytes) -> str:
        """DOCX 파일에서 텍스트 추출"""
        try:
            docx_file = io.BytesIO(file_content)
            doc = Document(docx_file)
            
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
            raise RuntimeError(f"DOCX 처리 오류: {str(e)}")
    
    @staticmethod
    async def _extract_from_xlsx(file_content: bytes) -> str:
        """XLSX 파일에서 텍스트 추출"""
        try:
            xlsx_file = io.BytesIO(file_content)
            workbook = load_workbook(xlsx_file, read_only=True, data_only=True)
            
            text_parts = []
            
            for sheet_name in workbook.sheetnames:
                sheet = workbook[sheet_name]
                sheet_text = []
                
                # 시트의 모든 셀에서 텍스트 추출
                for row in sheet.iter_rows(values_only=True):
                    row_text = []
                    for cell_value in row:
                        if cell_value is not None:
                            cell_str = str(cell_value).strip()
                            if cell_str:
                                row_text.append(cell_str)
                    
                    if row_text:
                        sheet_text.append(' | '.join(row_text))
                
                if sheet_text:
                    text_parts.append(f"[{sheet_name}]\n" + '\n'.join(sheet_text))
            
            workbook.close()
            
            if not text_parts:
                raise RuntimeError("XLSX에서 텍스트를 추출할 수 없습니다")
            
            return '\n\n'.join(text_parts)
            
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
