"""
네이버웍스 게시판 연동 라우터

주요 기능:
- 게시판 첨부파일 수동 동기화
- 동기화 상태 조회
- 동기화 이력 조회
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from fastapi import APIRouter, HTTPException, Header, BackgroundTasks
from pydantic import BaseModel

from services.naverworks_board_service import get_board_service
from services.vector_db import get_vector_db
from utils.file_parser import FileParser
from services.safe_preprocessor import get_safe_preprocessor
from services.chunker import get_chunker
from services.embedder import get_embedder
from routers.auth import verify_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/board", tags=["board"])

# 동기화 이력 저장 (메모리 기반, 실제 프로덕션에서는 DB 사용 권장)
sync_history: List[Dict[str, Any]] = []


class BoardSyncRequest(BaseModel):
    """게시판 동기화 요청 모델"""
    board_id: str
    title_keyword: str
    

class BoardSyncResponse(BaseModel):
    """게시판 동기화 응답 모델"""
    success: bool
    message: str
    posts_found: int = 0
    files_downloaded: int = 0
    files_processed: int = 0
    errors: List[str] = []


class SyncStatus(BaseModel):
    """동기화 상태 모델"""
    is_running: bool
    last_sync_time: Optional[str] = None
    last_sync_status: Optional[str] = None
    files_synced: int = 0


# 현재 동기화 상태
current_sync_status = {
    "is_running": False,
    "last_sync_time": None,
    "last_sync_status": None,
    "files_synced": 0
}


@router.post("/sync-attachments", response_model=BoardSyncResponse)
async def sync_board_attachments(
    request: BoardSyncRequest,
    background_tasks: BackgroundTasks,
    authorization: Optional[str] = Header(None)
):
    """
    네이버웍스 게시판 첨부파일 수동 동기화 (관리자 전용)
    
    Args:
        request: 게시판 ID와 제목 키워드
        authorization: Bearer 토큰 (관리자 인증)
        
    Returns:
        동기화 결과
    """
    # 관리자 권한 확인
    await verify_admin(authorization)
    
    try:
        logger.info("=" * 70)
        logger.info("게시판 첨부파일 동기화 시작")
        logger.info("=" * 70)
        logger.info(f"게시판 ID: {request.board_id}")
        logger.info(f"제목 키워드: {request.title_keyword}")
        
        # 현재 동기화 중인지 확인
        if current_sync_status["is_running"]:
            raise HTTPException(
                status_code=409, 
                detail="이미 동기화가 진행 중입니다. 잠시 후 다시 시도해주세요."
            )
        
        # 액세스 토큰 추출
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="인증 토큰이 필요합니다")
        
        access_token = authorization.split(" ")[1]
        
        # 백그라운드에서 동기화 실행
        background_tasks.add_task(
            _sync_attachments_background,
            access_token,
            request.board_id,
            request.title_keyword
        )
        
        return BoardSyncResponse(
            success=True,
            message="동기화가 시작되었습니다. 백그라운드에서 처리 중입니다.",
            posts_found=0,
            files_downloaded=0,
            files_processed=0
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"동기화 시작 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"동기화 시작 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/sync-attachments-sync", response_model=BoardSyncResponse)
async def sync_board_attachments_sync(
    request: BoardSyncRequest,
    authorization: Optional[str] = Header(None)
):
    """
    네이버웍스 게시판 첨부파일 동기 동기화 (테스트용, 관리자 전용)
    
    Args:
        request: 게시판 ID와 제목 키워드
        authorization: Bearer 토큰 (관리자 인증)
        
    Returns:
        동기화 결과
    """
    # 관리자 권한 확인
    await verify_admin(authorization)
    
    try:
        # 액세스 토큰 추출
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="인증 토큰이 필요합니다")
        
        access_token = authorization.split(" ")[1]
        
        # 동기 실행
        result = await _sync_attachments(
            access_token,
            request.board_id,
            request.title_keyword
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"동기화 실패: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"동기화 중 오류가 발생했습니다: {str(e)}"
        )


async def _sync_attachments_background(
    access_token: str,
    board_id: str,
    title_keyword: str
):
    """백그라운드에서 첨부파일 동기화 실행"""
    try:
        result = await _sync_attachments(access_token, board_id, title_keyword)
        logger.info(f"백그라운드 동기화 완료: {result.files_processed}개 파일 처리됨")
    except Exception as e:
        logger.error(f"백그라운드 동기화 실패: {str(e)}")


async def _sync_attachments(
    access_token: str,
    board_id: str,
    title_keyword: str
) -> BoardSyncResponse:
    """
    첨부파일 동기화 메인 로직
    
    프로세스:
    1. 게시판 API로 게시물 검색
    2. 첨부파일 다운로드
    3. 파일 처리 파이프라인으로 벡터화
    4. Qdrant에 저장
    """
    global current_sync_status
    
    # 동기화 시작 상태 설정
    current_sync_status["is_running"] = True
    sync_start_time = datetime.utcnow()
    
    errors = []
    posts_found = 0
    files_downloaded = 0
    files_processed = 0
    
    try:
        logger.info("Step 1: 게시판 서비스 초기화")
        board_service = get_board_service(access_token)
        
        # Step 2: 게시물 검색
        logger.info("Step 2: 게시물 검색")
        posts = board_service.search_posts_by_title(board_id, title_keyword)
        posts_found = len(posts)
        
        if posts_found == 0:
            logger.warning(f"키워드 '{title_keyword}'에 매칭되는 게시물이 없습니다")
            current_sync_status.update({
                "is_running": False,
                "last_sync_time": sync_start_time.isoformat(),
                "last_sync_status": "no_posts_found",
                "files_synced": 0
            })
            
            # 이력 저장
            sync_history.append({
                "timestamp": sync_start_time.isoformat(),
                "board_id": board_id,
                "title_keyword": title_keyword,
                "posts_found": 0,
                "files_processed": 0,
                "status": "no_posts_found"
            })
            
            return BoardSyncResponse(
                success=True,
                message=f"'{title_keyword}' 키워드에 매칭되는 게시물이 없습니다",
                posts_found=0,
                files_downloaded=0,
                files_processed=0
            )
        
        logger.info(f"✓ {posts_found}개 게시물 발견")
        
        # Step 3: 첨부파일 다운로드
        logger.info("Step 3: 첨부파일 다운로드")
        attachments = board_service.get_all_attachments_from_posts(board_id, posts)
        files_downloaded = len(attachments)
        
        if files_downloaded == 0:
            logger.warning("다운로드할 첨부파일이 없습니다")
            current_sync_status.update({
                "is_running": False,
                "last_sync_time": sync_start_time.isoformat(),
                "last_sync_status": "no_attachments",
                "files_synced": 0
            })
            
            # 이력 저장
            sync_history.append({
                "timestamp": sync_start_time.isoformat(),
                "board_id": board_id,
                "title_keyword": title_keyword,
                "posts_found": posts_found,
                "files_processed": 0,
                "status": "no_attachments"
            })
            
            return BoardSyncResponse(
                success=True,
                message=f"{posts_found}개 게시물에 첨부파일이 없습니다",
                posts_found=posts_found,
                files_downloaded=0,
                files_processed=0
            )
        
        logger.info(f"✓ {files_downloaded}개 첨부파일 다운로드 완료")
        
        # Step 4: 파일 처리 및 벡터화
        logger.info("Step 4: 파일 처리 및 벡터화")
        
        for file_content, file_name in attachments:
            try:
                logger.info(f"파일 처리 시작: {file_name}")
                
                # 파일 처리 (기존 파이프라인 활용)
                await _process_and_store_file(file_content, file_name)
                
                files_processed += 1
                logger.info(f"✓ 파일 처리 완료: {file_name}")
                
            except Exception as e:
                error_msg = f"파일 처리 실패 ({file_name}): {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        # 동기화 완료 상태 설정
        current_sync_status.update({
            "is_running": False,
            "last_sync_time": sync_start_time.isoformat(),
            "last_sync_status": "success",
            "files_synced": files_processed
        })
        
        # 이력 저장
        sync_history.append({
            "timestamp": sync_start_time.isoformat(),
            "board_id": board_id,
            "title_keyword": title_keyword,
            "posts_found": posts_found,
            "files_downloaded": files_downloaded,
            "files_processed": files_processed,
            "errors": errors,
            "status": "success"
        })
        
        logger.info("=" * 70)
        logger.info("✅ 게시판 첨부파일 동기화 완료")
        logger.info(f"   - 게시물 수: {posts_found}")
        logger.info(f"   - 다운로드: {files_downloaded}개")
        logger.info(f"   - 처리 완료: {files_processed}개")
        logger.info(f"   - 오류: {len(errors)}개")
        logger.info("=" * 70)
        
        return BoardSyncResponse(
            success=True,
            message=f"동기화 완료: {files_processed}/{files_downloaded}개 파일 처리됨",
            posts_found=posts_found,
            files_downloaded=files_downloaded,
            files_processed=files_processed,
            errors=errors
        )
        
    except Exception as e:
        error_msg = f"동기화 중 오류 발생: {str(e)}"
        logger.error(error_msg)
        
        # 오류 상태 설정
        current_sync_status.update({
            "is_running": False,
            "last_sync_time": sync_start_time.isoformat(),
            "last_sync_status": "error",
            "files_synced": files_processed
        })
        
        # 이력 저장
        sync_history.append({
            "timestamp": sync_start_time.isoformat(),
            "board_id": board_id,
            "title_keyword": title_keyword,
            "posts_found": posts_found,
            "files_downloaded": files_downloaded,
            "files_processed": files_processed,
            "errors": [error_msg],
            "status": "error"
        })
        
        raise


async def _process_and_store_file(file_content: bytes, file_name: str):
    """
    파일 처리 및 벡터 DB 저장 (기존 upload.py 로직 재사용)
    
    Args:
        file_content: 파일 바이트 데이터
        file_name: 파일명
    """
    try:
        # 1. 중복 파일명 확인 및 삭제
        vector_db = get_vector_db()
        existing_files = vector_db.get_file_list()
        
        for existing_file in existing_files:
            if existing_file.get('file_name') == file_name:
                file_id_to_delete = existing_file.get('file_id')
                logger.info(f"기존 파일 발견: {file_name} (ID: {file_id_to_delete})")
                
                delete_success = vector_db.delete_document(file_id_to_delete)
                if delete_success:
                    logger.info(f"기존 파일 삭제 완료: {file_name}")
                break
        
        # 2. 파일 형식 확인
        file_ext = "." + file_name.lower().split('.')[-1]
        
        # 지원하지 않는 파일 형식 체크
        if file_ext not in FileParser.SUPPORTED_EXTENSIONS:
            raise ValueError(f"지원하지 않는 파일 형식: {file_ext}")
        
        # 3. 데이터 추출
        logger.info(f"데이터 추출 시작: {file_name}")
        extracted_data = await FileParser.extract_text(file_content, file_name)
        
        if file_ext in ['.xlsx', '.pdf', '.docx'] and isinstance(extracted_data, list):
            # 구조화된 데이터 처리
            if not extracted_data:
                raise ValueError(f"{file_ext.upper()} 파일에서 데이터를 추출할 수 없습니다")
            
            logger.info(f"{file_ext.upper()} 구조화 데이터: {len(extracted_data)} 개 항목")
            
            chunks = []
            cell_metadata = []
            preprocessor = get_safe_preprocessor()
            
            for cell_data in extracted_data:
                # 검색용 텍스트 생성
                header = cell_data.get('col_header', cell_data.get('header', ''))
                if header and header not in ['텍스트', ''] and not header.startswith('Column'):
                    search_text = f"{header}: {cell_data['value']}"
                else:
                    search_text = cell_data['value']
                
                # 계층형 정보 포함
                lvl_parts = []
                if cell_data.get('lvl1'):
                    lvl_parts.append(cell_data['lvl1'])
                if cell_data.get('lvl2'):
                    lvl_parts.append(cell_data['lvl2'])
                if cell_data.get('lvl3'):
                    lvl_parts.append(cell_data['lvl3'])
                
                if lvl_parts:
                    search_text = f"{' > '.join(lvl_parts)} | {search_text}"
                
                # LLM 컨텍스트용 텍스트
                context_parts = []
                if cell_data.get('lvl1') or cell_data.get('lvl2') or cell_data.get('lvl3'):
                    hierarchy_info = []
                    if cell_data.get('lvl1'):
                        hierarchy_info.append(f"대분류: {cell_data['lvl1']}")
                    if cell_data.get('lvl2'):
                        hierarchy_info.append(f"중분류: {cell_data['lvl2']}")
                    if cell_data.get('lvl3'):
                        hierarchy_info.append(f"소분류: {cell_data['lvl3']}")
                    context_parts.append(f"분류 체계: {' > '.join(hierarchy_info)}")
                
                if header:
                    context_parts.append(f"{header}: {cell_data['value']}")
                else:
                    context_parts.append(cell_data['value'])
                
                if cell_data.get('lvl4'):
                    context_parts.append(f"상세 내용: {cell_data['lvl4']}")
                
                if cell_data.get('row_context'):
                    context_parts.append(f"관련 정보: {cell_data['row_context']}")
                
                context_text = " | ".join(context_parts)
                
                # 메타데이터
                metadata = {
                    "search_text": search_text,
                    "context_text": context_text,
                    "sheet_name": cell_data.get('sheet', cell_data.get('page', '')),
                    "cell_address": cell_data.get('cell_address', f"Page{cell_data.get('page', 1)}_Row{cell_data.get('row', 1)}"),
                    "col_header": header,
                    "is_numeric": cell_data.get('is_numeric', False),
                    "row": cell_data.get('row', 1),
                    "col": cell_data.get('col', 1),
                    "lvl1": cell_data.get('lvl1', ''),
                    "lvl2": cell_data.get('lvl2', ''),
                    "lvl3": cell_data.get('lvl3', ''),
                    "lvl4": cell_data.get('lvl4', '')
                }
                
                preprocessed_search = preprocessor.preprocess_text(search_text)
                if preprocessed_search:
                    chunks.append(preprocessed_search)
                else:
                    chunks.append(search_text)
                
                cell_metadata.append(metadata)
            
            logger.info(f"청킹 완료: {len(chunks)} 개 청크")
            
        else:
            # 기타 파일: 텍스트 처리
            if not extracted_data or not isinstance(extracted_data, str) or len(extracted_data.strip()) < 10:
                raise ValueError("추출된 텍스트가 너무 짧습니다")
            
            text = extracted_data
            logger.info(f"텍스트 추출: {len(text)} 문자")
            
            preprocessor = get_safe_preprocessor()
            preprocessed_text = preprocessor.preprocess_text(text)
            
            if not preprocessed_text:
                preprocessed_text = text
            
            chunker = get_chunker()
            chunks = chunker.chunk_text(preprocessed_text)
            logger.info(f"청킹 완료: {len(chunks)} 개 청크")
            
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
            raise RuntimeError("임베딩 생성 실패")
        
        logger.info(f"임베딩 생성 완료: {len(embeddings)} 개")
        
        # 5. 벡터 DB 저장
        logger.info("벡터 DB 저장 시작")
        file_id = vector_db.insert_documents(chunks, embeddings, file_name, file_ext, cell_metadata)
        
        logger.info(f"벡터 DB 저장 완료: 파일 ID {file_id}")
        
    except Exception as e:
        logger.error(f"파일 처리 중 오류: {str(e)}")
        raise


@router.get("/sync-status", response_model=SyncStatus)
async def get_sync_status():
    """
    현재 동기화 상태 조회
    
    Returns:
        동기화 상태 정보
    """
    return SyncStatus(
        is_running=current_sync_status["is_running"],
        last_sync_time=current_sync_status["last_sync_time"],
        last_sync_status=current_sync_status["last_sync_status"],
        files_synced=current_sync_status["files_synced"]
    )


@router.get("/sync-history")
async def get_sync_history(
    limit: int = 10,
    authorization: Optional[str] = Header(None)
):
    """
    동기화 이력 조회 (관리자 전용)
    
    Args:
        limit: 조회할 이력 수
        authorization: Bearer 토큰
        
    Returns:
        동기화 이력 목록
    """
    # 관리자 권한 확인
    await verify_admin(authorization)
    
    # 최신 이력부터 반환
    return {
        "history": sync_history[-limit:] if len(sync_history) > limit else sync_history[::-1]
    }

