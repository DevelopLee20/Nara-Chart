from sqlalchemy.orm import Session
from typing import List, Optional
from app.models.bid_models import DataModel


class BidCRUD:
    """
    입찰 데이터 CRUD 작업 클래스
    """

    @staticmethod
    def get_bid(db: Session, bid_id: int) -> Optional[DataModel]:
        """
        ID로 입찰 데이터 조회
        """
        return db.query(DataModel).filter(DataModel.id == bid_id).first()

    @staticmethod
    def get_bid_by_number(db: Session, bid_number: str) -> Optional[DataModel]:
        """
        입찰 공고번호로 입찰 데이터 조회
        """
        return db.query(DataModel).filter(DataModel.bid_number == bid_number).first()

    @staticmethod
    def get_bids(db: Session, skip: int = 0, limit: int = 100) -> List[DataModel]:
        """
        입찰 데이터 목록 조회 (페이지네이션)
        """
        return db.query(DataModel).offset(skip).limit(limit).all()

    @staticmethod
    def create_bid(db: Session, bid_data: dict) -> DataModel:
        """
        새로운 입찰 데이터 생성

        Args:
            db: 데이터베이스 세션
            bid_data: 입찰 데이터 딕셔너리

        Returns:
            생성된 BidData 객체
        """
        db_bid = DataModel(**bid_data)
        db.add(db_bid)
        db.commit()
        db.refresh(db_bid)
        return db_bid

    @staticmethod
    def update_bid(db: Session, bid_id: int, bid_data: dict) -> Optional[DataModel]:
        """
        입찰 데이터 업데이트

        Args:
            db: 데이터베이스 세션
            bid_id: 입찰 ID
            bid_data: 업데이트할 데이터 딕셔너리

        Returns:
            업데이트된 BidData 객체 또는 None
        """
        db_bid = BidCRUD.get_bid(db, bid_id)
        if db_bid:
            for key, value in bid_data.items():
                setattr(db_bid, key, value)
            db.commit()
            db.refresh(db_bid)
        return db_bid

    @staticmethod
    def delete_bid(db: Session, bid_id: int) -> bool:
        """
        입찰 데이터 삭제

        Args:
            db: 데이터베이스 세션
            bid_id: 입찰 ID

        Returns:
            삭제 성공 여부
        """
        db_bid = BidCRUD.get_bid(db, bid_id)
        if db_bid:
            db.delete(db_bid)
            db.commit()
            return True
        return False

    @staticmethod
    def search_bids_by_title(db: Session, keyword: str, skip: int = 0, limit: int = 100) -> List[DataModel]:
        """
        제목으로 입찰 검색

        Args:
            db: 데이터베이스 세션
            keyword: 검색 키워드
            skip: 건너뛸 레코드 수
            limit: 최대 반환 레코드 수

        Returns:
            검색된 BidData 목록
        """
        return db.query(DataModel).filter(
            DataModel.title.ilike(f"%{keyword}%")
        ).offset(skip).limit(limit).all()

    @staticmethod
    def get_bids_by_organization(db: Session, organization: str, skip: int = 0, limit: int = 100) -> List[DataModel]:
        """
        발주 기관별 입찰 조회

        Args:
            db: 데이터베이스 세션
            organization: 발주 기관명
            skip: 건너뛸 레코드 수
            limit: 최대 반환 레코드 수

        Returns:
            해당 기관의 BidData 목록
        """
        return db.query(DataModel).filter(
            DataModel.organization == organization
        ).offset(skip).limit(limit).all()
