"""
파일 형식별 텍스트 추출 유틸리티
지원 형식: PDF, DOCX, XLSX, TXT
"""

import io
import logging
from pathlib import Path
from typing import Optional, Union, List, Dict, Any

import PyPDF2
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
