from sqlalchemy.orm import Session
from typing import List
from app.db.cruds.bid_crud import BidCRUD
from app.models.bid_models import DataModel
from app.schemas.bid_schemas import BidCreate, BidUpdate


class BidService:
    """
    입찰 데이터 비즈니스 로직 서비스
    """

    def __init__(self, db: Session):
        self.db = db

    def get_bid(self, bid_id: int) -> DataModel | None:
        """
        ID로 입찰 데이터 조회
        """
        return BidCRUD.get_bid(self.db, bid_id)

    def get_bid_by_number(self, bid_number: str) -> DataModel | None:
        """
        공고번호로 입찰 데이터 조회
        """
        return BidCRUD.get_bid_by_number(self.db, bid_number)

    def get_bids(self, skip: int = 0, limit: int = 100) -> tuple[List[DataModel], int]:
        """
        입찰 데이터 목록 조회 (페이지네이션)

        Returns:
            (입찰 목록, 전체 개수) 튜플
        """
        bids = BidCRUD.get_bids(self.db, skip, limit)
        total = self.db.query(DataModel).count()
        return bids, total

    def create_bid(self, bid_data: BidCreate) -> DataModel:
        """
        새로운 입찰 데이터 생성

        Args:
            bid_data: 입찰 생성 스키마

        Returns:
            생성된 입찰 데이터

        Raises:
            ValueError: 공고번호가 이미 존재하는 경우
        """
        # 중복 체크
        existing = self.get_bid_by_number(bid_data.bid_number)
        if existing:
            raise ValueError(f"공고번호 '{bid_data.bid_number}'가 이미 존재합니다.")

        bid_dict = bid_data.model_dump(exclude_unset=True)
        return BidCRUD.create_bid(self.db, bid_dict)

    def update_bid(self, bid_id: int, bid_data: BidUpdate) -> DataModel | None:
        """
        입찰 데이터 업데이트

        Args:
            bid_id: 입찰 ID
            bid_data: 업데이트할 데이터

        Returns:
            업데이트된 입찰 데이터 또는 None
        """
        # None이 아닌 필드만 업데이트
        update_dict = bid_data.model_dump(exclude_unset=True)

        # 공고번호가 변경되는 경우 중복 체크
        if "bid_number" in update_dict:
            existing = self.get_bid_by_number(update_dict["bid_number"])
            if existing and existing.id != bid_id: # type: ignore
                raise ValueError(f"공고번호 '{update_dict['bid_number']}'가 이미 존재합니다.")

        return BidCRUD.update_bid(self.db, bid_id, update_dict)

    def delete_bid(self, bid_id: int) -> bool:
        """
        입찰 데이터 삭제

        Args:
            bid_id: 입찰 ID

        Returns:
            삭제 성공 여부
        """
        return BidCRUD.delete_bid(self.db, bid_id)

    def search_bids(
        self,
        keyword: str | None = None,
        organization: str | None = None,
        industry: str | None = None,
        region: str | None = None,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[List[DataModel], int]:
        """
        입찰 데이터 검색

        Args:
            keyword: 제목 검색 키워드
            organization: 발주기관
            industry: 업종
            region: 지역
            skip: 건너뛸 레코드 수
            limit: 최대 반환 레코드 수

        Returns:
            (검색 결과 목록, 전체 개수) 튜플
        """
        query = self.db.query(DataModel)

        # 조건별 필터링
        if keyword:
            query = query.filter(DataModel.title.ilike(f"%{keyword}%"))
        if organization:
            query = query.filter(DataModel.organization == organization)
        if industry:
            query = query.filter(DataModel.industry == industry)
        if region:
            query = query.filter(DataModel.region == region)

        total = query.count()
        bids = query.offset(skip).limit(limit).all()

        return bids, total

    def get_organizations(self) -> List[str]:
        """
        모든 발주기관 목록 조회

        Returns:
            발주기관 목록 (중복 제거)
        """
        result = self.db.query(DataModel.organization).distinct().filter(
            DataModel.organization.isnot(None)
        ).all()
        return [org[0] for org in result]

    def get_industries(self) -> List[str]:
        """
        모든 업종 목록 조회

        Returns:
            업종 목록 (중복 제거)
        """
        result = self.db.query(DataModel.industry).distinct().filter(
            DataModel.industry.isnot(None)
        ).all()
        return [ind[0] for ind in result]

    def get_regions(self) -> List[str]:
        """
        모든 지역 목록 조회

        Returns:
            지역 목록 (중복 제거)
        """
        result = self.db.query(DataModel.region).distinct().filter(
            DataModel.region.isnot(None)
        ).all()
        return [reg[0] for reg in result]

    def get_statistics(self) -> dict:
        """
        입찰 데이터 통계 조회

        Returns:
            통계 정보 딕셔너리
        """
        from sqlalchemy import func

        total_count = self.db.query(DataModel).count()

        # 평균 금액
        avg_estimated = self.db.query(func.avg(DataModel.estimated_price)).filter(
            DataModel.estimated_price.isnot(None)
        ).scalar() or 0

        avg_base = self.db.query(func.avg(DataModel.base_price)).filter(
            DataModel.base_price.isnot(None)
        ).scalar() or 0

        avg_winning = self.db.query(func.avg(DataModel.winning_price)).filter(
            DataModel.winning_price.isnot(None)
        ).scalar() or 0

        # 평균 낙찰률
        avg_base_winning_rate = self.db.query(func.avg(DataModel.base_winning_rate)).filter(
            DataModel.base_winning_rate.isnot(None)
        ).scalar() or 0

        avg_estimated_winning_rate = self.db.query(func.avg(DataModel.estimated_winning_rate)).filter(
            DataModel.estimated_winning_rate.isnot(None)
        ).scalar() or 0

        return {
            "total_count": total_count,
            "average_estimated_price": float(avg_estimated),
            "average_base_price": float(avg_base),
            "average_winning_price": float(avg_winning),
            "average_base_winning_rate": float(avg_base_winning_rate),
            "average_estimated_winning_rate": float(avg_estimated_winning_rate)
        }
