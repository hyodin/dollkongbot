"""
파일 업로드 API 라우터
지원 형식: PDF, TXT, DOCX, XLSX
"""

import logging
from io import BytesIO
from typing import Dict, Any, Optional

from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Header, Depends
from fastapi.responses import JSONResponse

from utils.file_parser import FileParser
from services.safe_preprocessor import get_safe_preprocessor
from services.chunker import get_chunker
from services.embedder import get_embedder
from services.vector_db import get_vector_db
from routers.auth import verify_admin

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/upload")
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    authorization: Optional[str] = Header(None)
) -> Dict[str, Any]:
    """
    파일 업로드 및 벡터화 처리 (관리자 전용)
    
    Args:
        file: 업로드할 파일 (PDF, DOCX, XLSX, TXT)
        authorization: Bearer 토큰 (관리자 인증)
        
    Returns:
        업로드 결과 정보
    """
    # 관리자 권한 확인
    await verify_admin(authorization)
    
    try:
        # 1. 파일 유효성 검사
        await _validate_file(file)
        
        # 2. 파일 내용 읽기
        file_content = await file.read()
        file_name = file.filename
        
        logger.info(f"파일 업로드 시작: {file_name} ({len(file_content)} bytes)")
        
        # 3. 백그라운드에서 처리
        background_tasks.add_task(
            _process_file_background,
            file_content,
            file_name
        )
        
        # 4. 즉시 응답 반환
        return {
            "status": "accepted",
            "message": "파일이 업로드되었습니다. 처리 중입니다.",
            "file_name": file_name,
            "file_size": len(file_content)
        }
        
    except ValueError as e:
        logger.warning(f"파일 검증 실패: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"파일 업로드 실패: {str(e)}")
        raise HTTPException(status_code=500, detail="파일 업로드 처리 중 오류가 발생했습니다")


@router.post("/upload-sync")
async def upload_file_sync(
    file: UploadFile = File(...),
    authorization: Optional[str] = Header(None)
) -> Dict[str, Any]:
    """
    파일 업로드 및 동기 처리 (테스트용, 관리자 전용)
    
    Args:
        file: 업로드할 파일
        authorization: Bearer 토큰 (관리자 인증)
        
    Returns:
        처리 결과
    """
    # 관리자 권한 확인
    await verify_admin(authorization)
    
    try:
        # 1. 파일 유효성 검사
        await _validate_file(file)
        
        # 2. 파일 내용 읽기
        file_content = await file.read()
        file_name = file.filename
        
        logger.info(f"동기 파일 처리 시작: {file_name}")
        
        # 3. 동기 처리
        result = await _process_file(file_content, file_name)
        
        return result
        
    except ValueError as e:
        logger.warning(f"파일 검증 실패: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"파일 처리 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"파일 처리 중 오류가 발생했습니다: {str(e)}")


async def _validate_file(file: UploadFile) -> None:
    """파일 유효성 검사"""
    if not file.filename:
        raise ValueError("파일명이 없습니다")
    
    # 파일 확장자 검사
    file_ext = file.filename.lower().split('.')[-1]
    if f".{file_ext}" not in FileParser.SUPPORTED_EXTENSIONS:
        supported = ", ".join(FileParser.SUPPORTED_EXTENSIONS)
        raise ValueError(f"지원하지 않는 파일 형식입니다. 지원 형식: {supported}")
    
    # 파일 크기 검사 (추정)
    if hasattr(file, 'size') and file.size > FileParser.MAX_FILE_SIZE:
        max_mb = FileParser.MAX_FILE_SIZE / 1024 / 1024
        raise ValueError(f"파일 크기가 {max_mb}MB를 초과합니다")


async def _process_file_background(file_content: bytes, file_name: str) -> None:
    """백그라운드에서 파일 처리"""
    try:
        result = await _process_file(file_content, file_name)
        logger.info(f"백그라운드 파일 처리 완료: {file_name} - 청크 수: {result['chunks_saved']}")
    except Exception as e:
        logger.error(f"백그라운드 파일 처리 실패: {file_name} - {str(e)}")


async def _process_file(file_content: bytes, file_name: str) -> Dict[str, Any]:
    """파일 처리 메인 로직"""
    try:
        # 1. 파일 형식 확인
        file_ext = "." + file_name.lower().split('.')[-1]
        
        # 2. 데이터 추출 (XLSX, PDF vs 기타)
        logger.info(f"데이터 추출 시작: {file_name}")
        extracted_data = await FileParser.extract_text(file_content, file_name)
        
        if file_ext in ['.xlsx', '.pdf', '.docx'] and isinstance(extracted_data, list):
            # XLSX, PDF, DOCX: 구조화된 데이터 처리
            if not extracted_data:
                raise ValueError(f"{file_ext.upper()} 파일에서 구조화된 데이터를 추출할 수 없습니다")
            
            logger.info(f"{file_ext.upper()} 구조화 데이터 추출 완료: {len(extracted_data)} 개 항목")
            
            # 파일별 구조 분석 로깅
            if file_ext == '.pdf':
                logger.info("PDF 표 구조 분석:")
                lvl1_count = sum(1 for item in extracted_data if item.get('lvl1'))
                lvl2_count = sum(1 for item in extracted_data if item.get('lvl2'))
                lvl3_count = sum(1 for item in extracted_data if item.get('lvl3'))
                lvl4_count = sum(1 for item in extracted_data if item.get('lvl4'))
                logger.info(f"  - lvl1 항목: {lvl1_count}개")
                logger.info(f"  - lvl2 항목: {lvl2_count}개")
                logger.info(f"  - lvl3 항목: {lvl3_count}개")
                logger.info(f"  - lvl4 항목: {lvl4_count}개")
            elif file_ext == '.docx':
                logger.info("DOCX 문서 구조 분석:")
                lvl1_count = sum(1 for item in extracted_data if item.get('lvl1'))
                lvl2_count = sum(1 for item in extracted_data if item.get('lvl2'))
                lvl3_count = sum(1 for item in extracted_data if item.get('lvl3'))
                lvl4_count = sum(1 for item in extracted_data if item.get('lvl4'))
                logger.info(f"  - lvl1 항목 (조항): {lvl1_count}개")
                logger.info(f"  - lvl2 항목 (소항목): {lvl2_count}개")
                logger.info(f"  - lvl3 항목 (세부항목): {lvl3_count}개")
                logger.info(f"  - lvl4 항목 (내용): {lvl4_count}개")
            
            # RAG 챗봇에 최적화된 텍스트 생성
            chunks = []
            cell_metadata = []
            preprocessor = get_safe_preprocessor()
            
            for cell_data in extracted_data:
                # 1. 검색(임베딩)용 텍스트 생성 - 핵심 정보만
                header = cell_data.get('col_header', cell_data.get('header', ''))
                if header and header not in ['텍스트', ''] and not header.startswith('Column'):
                    search_text = f"{header}: {cell_data['value']}"
                else:
                    search_text = cell_data['value']
                
                # 계층형 정보를 검색 텍스트에 포함
                lvl_parts = []
                if cell_data.get('lvl1'):
                    lvl_parts.append(cell_data['lvl1'])
                if cell_data.get('lvl2'):
                    lvl_parts.append(cell_data['lvl2'])
                if cell_data.get('lvl3'):
                    lvl_parts.append(cell_data['lvl3'])
                
                if lvl_parts:
                    search_text = f"{' > '.join(lvl_parts)} | {search_text}"
                
                # 2. LLM 컨텍스트용 텍스트 생성 - 풍부한 맥락 (계층형 정보 포함)
                context_parts = []
                
                # 계층형 구조 정보 추가
                if cell_data.get('lvl1') or cell_data.get('lvl2') or cell_data.get('lvl3'):
                    hierarchy_info = []
                    if cell_data.get('lvl1'):
                        hierarchy_info.append(f"대분류: {cell_data['lvl1']}")
                    if cell_data.get('lvl2'):
                        hierarchy_info.append(f"중분류: {cell_data['lvl2']}")
                    if cell_data.get('lvl3'):
                        hierarchy_info.append(f"소분류: {cell_data['lvl3']}")
                    context_parts.append(f"분류 체계: {' > '.join(hierarchy_info)}")
                
                # 셀/항목 정보 추가
                if header:
                    context_parts.append(f"{header}: {cell_data['value']}")
                else:
                    context_parts.append(cell_data['value'])
                
                # 상세 내용 추가 (lvl4)
                if cell_data.get('lvl4'):
                    context_parts.append(f"상세 내용: {cell_data['lvl4']}")
                
                # 행 컨텍스트 추가
                if cell_data.get('row_context'):
                    context_parts.append(f"관련 정보: {cell_data['row_context']}")
                
                context_text = " | ".join(context_parts)
                
                # 3. 메타데이터 저장 (계층형 컬럼 포함)
                metadata = {
                    "search_text": search_text,
                    "context_text": context_text,
                    "sheet_name": cell_data.get('sheet', cell_data.get('page', '')),
                    "cell_address": cell_data.get('cell_address', f"Page{cell_data.get('page', 1)}_Row{cell_data.get('row', 1)}"),
                    "col_header": header,
                    "is_numeric": cell_data.get('is_numeric', False),
                    "row": cell_data.get('row', 1),
                    "col": cell_data.get('col', 1),
                    # 계층형 컬럼 추가
                    "lvl1": cell_data.get('lvl1', ''),
                    "lvl2": cell_data.get('lvl2', ''),
                    "lvl3": cell_data.get('lvl3', ''),
                    "lvl4": cell_data.get('lvl4', '')
                }
                
                # 4. 검색용 텍스트를 전처리하여 임베딩용으로 사용
                preprocessed_search = preprocessor.preprocess_text(search_text)
                if preprocessed_search:
                    chunks.append(preprocessed_search)
                else:
                    chunks.append(search_text)
                
                cell_metadata.append(metadata)
            
            logger.info(f"XLSX 셀 청킹 완료: {len(chunks)} 개 청크")
            text = f"{len(extracted_data)} 개 셀 데이터"
            preprocessed_text = f"{len(chunks)} 개 전처리된 셀"
            
        else:
            # 기타 파일: 기존 텍스트 처리 방식
            if not extracted_data or not isinstance(extracted_data, str) or len(extracted_data.strip()) < 10:
                raise ValueError("추출된 텍스트가 너무 짧습니다")
            
            text = extracted_data
            logger.info(f"텍스트 추출 완료: {len(text)} 문자")
            
            # 텍스트 전처리
            logger.info("텍스트 전처리 시작")
            preprocessor = get_safe_preprocessor()
            preprocessed_text = preprocessor.preprocess_text(text)
            
            if not preprocessed_text:
                logger.warning("전처리 실패, 원본 텍스트 사용")
                preprocessed_text = text
            
            # 일반 청킹
            logger.info("텍스트 청킹 시작")
            chunker = get_chunker()
            chunks = chunker.chunk_text(preprocessed_text)
            logger.info(f"일반 청킹 완료: {len(chunks)} 개 청크")
            
            # 기타 파일용 메타데이터 생성
            cell_metadata = []
            for i, chunk in enumerate(chunks):
                metadata = {
                    "search_text": chunk,
                    "context_text": chunk,
                    "chunk_index": i
                }
                cell_metadata.append(metadata)
        
        if not chunks:
            raise ValueError("데이터를 청크로 분할할 수 없습니다")
        
        # 4. 임베딩 생성
        logger.info("임베딩 생성 시작")
        embedder = get_embedder()
        embeddings = embedder.encode_batch(chunks)
        
        if len(embeddings) != len(chunks):
            raise RuntimeError("임베딩 생성 실패: 청크 수와 임베딩 수 불일치")
        
        logger.info(f"임베딩 생성 완료: {len(embeddings)} 개")
        
        # 5. 벡터 DB 저장 (메타데이터와 함께)
        logger.info("벡터 DB 저장 시작")
        vector_db = get_vector_db()
        file_id = vector_db.insert_documents(chunks, embeddings, file_name, file_ext, cell_metadata)
        
        logger.info(f"벡터 DB 저장 완료: 파일 ID {file_id}")
        
        # 6. 결과 반환
        return {
            "status": "success",
            "message": "파일 처리가 완료되었습니다",
            "file_id": file_id,
            "file_name": file_name,
            "file_type": file_ext,
            "chunks_saved": len(chunks),
            "text_length": len(str(text)),
            "preprocessed_length": len(str(preprocessed_text))
        }
        
    except Exception as e:
        logger.error(f"파일 처리 중 오류: {str(e)}")
        raise


@router.get("/documents")
async def get_documents() -> Dict[str, Any]:
    """업로드된 문서 목록 조회"""
    try:
        vector_db = get_vector_db()
        
        # 파일 목록 조회
        files = vector_db.get_file_list()
        
        # 전체 통계
        stats = vector_db.get_document_stats()
        
        return {
            "status": "success",
            "files": files,
            "statistics": stats
        }
        
    except Exception as e:
        logger.error(f"문서 목록 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail="문서 목록 조회 중 오류가 발생했습니다")


@router.delete("/documents/{file_id}")
async def delete_document(
    file_id: str,
    authorization: Optional[str] = Header(None)
) -> Dict[str, Any]:
    """
    문서 삭제 (관리자 전용)
    
    Args:
        file_id: 삭제할 문서 ID
        authorization: Bearer 토큰 (관리자 인증)
    """
    # 관리자 권한 확인
    await verify_admin(authorization)
    
    try:
        vector_db = get_vector_db()
        
        success = vector_db.delete_document(file_id)
        
        if success:
            return {
                "status": "success",
                "message": "문서가 삭제되었습니다",
                "file_id": file_id
            }
        else:
            raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"문서 삭제 실패: {str(e)}")
        raise HTTPException(status_code=500, detail="문서 삭제 중 오류가 발생했습니다")
