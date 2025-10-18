from sqlalchemy import Column, Integer, String, DateTime, Float, Date
from sqlalchemy.sql import func
from app.db.database import Base


class DataModel(Base):
    """
    입찰 데이터 모델
    """
    __tablename__ = "bid_data"

    # 기본 정보
    id = Column(Integer, primary_key=True, index=True, comment="번호")
    bid_type = Column(String(50), comment="타입")
    participation_deadline = Column(Date, comment="참가마감")
    bid_deadline = Column(Date, comment="투찰마감")
    bid_date = Column(Date, comment="입찰일")
    organization = Column(String(200), comment="발주기관")
    title = Column(String(500), nullable=False, comment="공고명")
    bid_number = Column(String(100), unique=True, index=True, comment="공고번호")
    industry = Column(String(100), comment="업종")
    region = Column(String(100), comment="지역")

    # 금액 정보
    estimated_price = Column(Float, comment="추정가격")
    base_price = Column(Float, comment="기초금액")
    winning_price = Column(Float, comment="낙찰금액")

    # 낙찰 정보
    first_rank_company = Column(String(200), comment="1순위업체명")
    base_winning_rate = Column(Float, comment="기초/낙찰률")
    estimated_winning_rate = Column(Float, comment="추정/낙찰률")

    # 메타데이터
    created_at = Column(DateTime, server_default=func.now(), comment="생성 일시")
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), comment="수정 일시")

    def __repr__(self):
        return f"<DataModel(id={self.id}, bid_number={self.bid_number}, title={self.title})>"
