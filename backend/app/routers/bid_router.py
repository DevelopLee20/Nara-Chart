from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.services.bid_service import BidService
from app.schemas.bid_schemas import (
    BidCreate,
    BidUpdate,
    BidResponse,
    BidListResponse,
    BidOperationResponse
)
from app.utils.bid_utils import BidDataUploader
import tempfile
import os

router = APIRouter(
    prefix="/api/bids",
    tags=["입찰 데이터 관리"]
)


def _get_service(db: Session = Depends(get_db)) -> BidService:
    """BidService 의존성 주입 헬퍼"""
    return BidService(db=db)


@router.get("/", response_model=BidListResponse)
def get_bids(
    skip: int = Query(0, ge=0, description="건너뛸 레코드 수"),
    limit: int = Query(100, ge=1, le=1000, description="최대 반환 레코드 수"),
    service: BidService = Depends(_get_service)
):
    """
    입찰 데이터 목록 조회 (페이지네이션)
    """
    bids, total = service.get_bids(skip=skip, limit=limit)
    return BidListResponse(
        total=total,
        items=bids  # type: ignore
    )


@router.get("/search", response_model=BidListResponse)
def search_bids(
    keyword: str | None = Query(None, description="제목 검색 키워드"),
    organization: str | None = Query(None, description="발주기관"),
    industry: str | None = Query(None, description="업종"),
    region: str | None = Query(None, description="지역"),
    skip: int = Query(0, ge=0, description="건너뛸 레코드 수"),
    limit: int = Query(100, ge=1, le=1000, description="최대 반환 레코드 수"),
    service: BidService = Depends(_get_service)
):
    """
    입찰 데이터 검색

    검색 조건:
    - keyword: 공고명으로 검색 (부분 일치)
    - organization: 발주기관 (정확히 일치)
    - industry: 업종 (정확히 일치)
    - region: 지역 (정확히 일치)
    """
    bids, total = service.search_bids(
        keyword=keyword,
        organization=organization,
        industry=industry,
        region=region,
        skip=skip,
        limit=limit
    )
    return BidListResponse(
        total=total,
        items=bids
    )


@router.get("/statistics")
def get_statistics(
    service: BidService = Depends(_get_service)
):
    """
    입찰 데이터 통계 조회

    - 전체 입찰 수
    - 평균 추정가격
    - 평균 기초금액
    - 평균 낙찰금액
    - 평균 기초/낙찰률
    - 평균 추정/낙찰률
    """
    return service.get_statistics()


@router.get("/filters/organizations", response_model=List[str])
def get_organizations(
    service: BidService = Depends(_get_service)
):
    """
    모든 발주기관 목록 조회 (필터용)
    """
    return service.get_organizations()


@router.get("/filters/industries", response_model=List[str])
def get_industries(
    service: BidService = Depends(_get_service)
):
    """
    모든 업종 목록 조회 (필터용)
    """
    return service.get_industries()


@router.get("/filters/regions", response_model=List[str])
def get_regions(
    service: BidService = Depends(_get_service)
):
    """
    모든 지역 목록 조회 (필터용)
    """
    return service.get_regions()


@router.get("/{bid_id}", response_model=BidResponse)
def get_bid(
    bid_id: int,
    service: BidService = Depends(_get_service)
):
    """
    특정 입찰 데이터 조회 (ID)
    """
    bid = service.get_bid(bid_id)
    if not bid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"입찰 데이터 ID {bid_id}를 찾을 수 없습니다."
        )
    return bid


@router.get("/number/{bid_number}", response_model=BidResponse)
def get_bid_by_number(
    bid_number: str,
    service: BidService = Depends(_get_service)
):
    """
    특정 입찰 데이터 조회 (공고번호)
    """
    bid = service.get_bid_by_number(bid_number)
    if not bid:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"공고번호 '{bid_number}'를 찾을 수 없습니다."
        )
    return bid


@router.post("/", response_model=BidOperationResponse, status_code=status.HTTP_201_CREATED)
def create_bid(
    bid_data: BidCreate,
    service: BidService = Depends(_get_service)
):
    """
    새로운 입찰 데이터 생성
    """
    try:
        bid = service.create_bid(bid_data)
        return BidOperationResponse(
            success=True,
            message=f"입찰 데이터 '{bid.title}' 생성 완료",
            data=bid
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"입찰 데이터 생성 실패: {str(e)}"
        )


@router.put("/{bid_id}", response_model=BidOperationResponse)
def update_bid(
    bid_id: int,
    bid_data: BidUpdate,
    service: BidService = Depends(_get_service)
):
    """
    입찰 데이터 업데이트
    """
    try:
        bid = service.update_bid(bid_id, bid_data)
        if not bid:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"입찰 데이터 ID {bid_id}를 찾을 수 없습니다."
            )
        return BidOperationResponse(
            success=True,
            message=f"입찰 데이터 '{bid.title}' 업데이트 완료",
            data=bid
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"입찰 데이터 업데이트 실패: {str(e)}"
        )


@router.delete("/{bid_id}", response_model=BidOperationResponse)
def delete_bid(
    bid_id: int,
    service: BidService = Depends(_get_service)
):
    """
    입찰 데이터 삭제
    """
    success = service.delete_bid(bid_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"입찰 데이터 ID {bid_id}를 찾을 수 없습니다."
        )
    return BidOperationResponse(
        success=True,
        message=f"입찰 데이터 ID {bid_id} 삭제 완료"
    )


@router.post("/upload", response_model=BidOperationResponse)
async def upload_excel(
    file: UploadFile = File(...),
    service: BidService = Depends(_get_service)
):
    """
    엑셀 파일 업로드 - 모든 데이터 삭제 후 엑셀 데이터 일괄 등록

    - 기존의 모든 입찰 데이터를 삭제합니다
    - 업로드된 엑셀 파일의 데이터를 데이터베이스에 저장합니다
    - 지원 파일 형식: .xlsx, .xls
    """
    # 파일 확장자 검증
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="파일명이 없습니다."
        )

    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ['.xlsx', '.xls']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="엑셀 파일만 업로드 가능합니다. (.xlsx, .xls)"
        )

    # 임시 파일로 저장
    temp_file = None
    try:
        # 임시 파일 생성
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_ext) as temp:
            temp_file = temp.name
            content = await file.read()
            temp.write(content)

        # BidDataUploader를 사용하여 엑셀 데이터 파싱
        uploader = BidDataUploader()
        import pandas as pd
        df = pd.read_excel(temp_file)
        records = uploader._preprocess_data(df)

        # 모든 기존 데이터 삭제
        deleted_count = service.delete_all_bids()

        # 새 데이터 일괄 등록
        success_count, fail_count = service.bulk_create_bids(records)

        return BidOperationResponse(
            success=True,
            message=f"업로드 완료: 기존 {deleted_count}건 삭제, {success_count}건 추가 성공, {fail_count}건 실패"
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"엑셀 파일 처리 오류: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"파일 업로드 실패: {str(e)}"
        )
    finally:
        # 임시 파일 삭제
        if temp_file and os.path.exists(temp_file):
            os.unlink(temp_file)
