from sqlalchemy import Column, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from datetime import datetime
from typing import cast

from app.db.database import Base


class EnvVar(Base):
    """
    환경변수 저장 테이블
    - key-value 형태로 환경변수를 영구 저장
    - Redis 캐싱의 백업 및 복원용 데이터 소스
    """
    __tablename__ = "env_vars"

    key: Mapped[str] = mapped_column(String, primary_key=True, index=True, comment="환경변수 키")
    value: Mapped[str] = mapped_column(String, nullable=False, comment="환경변수 값")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="마지막 업데이트 시간"
    )

    def __repr__(self):
        return f"<EnvVar(key='{self.key}', value='{self.value}', updated_at='{self.updated_at}')>"

    def to_dict(self):
        """모델을 딕셔너리로 변환"""
        updated = cast(datetime | None, self.updated_at)

        return {
            "key": self.key,
            "value": self.value,
            "updated_at": updated.isoformat() if updated else None
        }
