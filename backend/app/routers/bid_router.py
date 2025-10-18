from fastapi import APIRouter, Depends, HTTPException, status, Query
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
