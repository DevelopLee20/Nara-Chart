from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class BidBase(BaseModel):
    """
    입찰 데이터 기본 스키마
    """
    bid_number: str = Field(..., description="입찰 공고번호")
    title: str = Field(..., description="입찰 제목")
    organization: Optional[str] = Field(None, description="발주 기관")
    bid_type: Optional[str] = Field(None, description="입찰 유형")
    budget: Optional[float] = Field(None, description="예산 금액")
    start_date: Optional[datetime] = Field(None, description="입찰 시작일")
    end_date: Optional[datetime] = Field(None, description="입찰 마감일")
    status: Optional[str] = Field("진행중", description="입찰 상태")
    description: Optional[str] = Field(None, description="입찰 상세 설명")


class BidCreate(BidBase):
    """
    입찰 데이터 생성 스키마
    """
    pass


class BidUpdate(BaseModel):
    """
    입찰 데이터 수정 스키마 (모든 필드 선택적)
    """
    bid_number: Optional[str] = None
    title: Optional[str] = None
    organization: Optional[str] = None
    bid_type: Optional[str] = None
    budget: Optional[float] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: Optional[str] = None
    description: Optional[str] = None


class BidResponse(BidBase):
    """
    입찰 데이터 응답 스키마
    """
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True  # SQLAlchemy 모델과 호환


class BidListResponse(BaseModel):
    """
    입찰 목록 응답 스키마
    """
    total: int
    items: list[BidResponse]
