from pydantic import BaseModel, Field
from datetime import datetime, date


class BidBase(BaseModel):
    """
    입찰 데이터 기본 스키마
    """
    bid_type: str | None = Field(None, description="타입")
    participation_deadline: date | None = Field(None, description="참가마감")
    bid_deadline: date | None = Field(None, description="투찰마감")
    bid_date: date | None = Field(None, description="입찰일")
    organization: str | None = Field(None, description="발주기관")
    title: str = Field(..., description="공고명")
    bid_number: str = Field(..., description="공고번호")
    industry: str | None = Field(None, description="업종")
    region: str | None = Field(None, description="지역")
    estimated_price: float | None = Field(None, description="추정가격")
    base_price: float | None = Field(None, description="기초금액")
    winning_price: float | None = Field(None, description="낙찰금액")
    first_rank_company: str | None = Field(None, description="1순위업체명")
    base_winning_rate: float | None = Field(None, description="기초/낙찰률")
    estimated_winning_rate: float | None = Field(None, description="추정/낙찰률")


class BidCreate(BidBase):
    """
    입찰 데이터 생성 스키마
    """
    pass


class BidUpdate(BaseModel):
    """
    입찰 데이터 수정 스키마 (모든 필드 선택적)
    """
    bid_type: str | None = None
    participation_deadline: date | None = None
    bid_deadline: date | None = None
    bid_date: date | None = None
    organization: str | None = None
    title: str | None = None
    bid_number: str | None = None
    industry: str | None = None
    region: str | None = None
    estimated_price: float | None = None
    base_price: float | None = None
    winning_price: float | None = None
    first_rank_company: str | None = None
    base_winning_rate: float | None = None
    estimated_winning_rate: float | None = None


class BidResponse(BidBase):
    """
    입찰 데이터 응답 스키마
    """
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BidListResponse(BaseModel):
    """
    입찰 목록 응답 스키마
    """
    total: int
    items: list[BidResponse]


class BidSearchParams(BaseModel):
    """
    입찰 검색 파라미터
    """
    keyword: str | None = Field(None, description="제목 검색 키워드")
    organization: str | None = Field(None, description="발주기관")
    industry: str | None = Field(None, description="업종")
    region: str | None = Field(None, description="지역")
    skip: int = Field(0, ge=0, description="건너뛸 레코드 수")
    limit: int = Field(100, ge=1, le=1000, description="최대 반환 레코드 수")


class BidOperationResponse(BaseModel):
    """
    입찰 작업 응답 스키마
    """
    success: bool
    message: str
    data: BidResponse | None = None
