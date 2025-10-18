from pydantic import BaseModel, Field
from typing import Optional, Dict
from datetime import datetime


class EnvVarBase(BaseModel):
    """환경변수 기본 스키마"""
    key: str = Field(..., description="환경변수 키", min_length=1, max_length=255)
    value: str = Field(..., description="환경변수 값", min_length=0)


class EnvVarCreate(EnvVarBase):
    """환경변수 생성 스키마"""
    pass


class EnvVarUpdate(BaseModel):
    """환경변수 업데이트 스키마"""
    value: str = Field(..., description="환경변수 값", min_length=0)


class EnvVarResponse(EnvVarBase):
    """환경변수 응답 스키마"""
    updated_at: Optional[datetime] = Field(None, description="마지막 업데이트 시간")

    class Config:
        from_attributes = True


class EnvVarListResponse(BaseModel):
    """환경변수 목록 응답 스키마"""
    env_vars: Dict[str, str] = Field(..., description="환경변수 딕셔너리")
    count: int = Field(..., description="환경변수 개수")


class EnvVarStatsResponse(BaseModel):
    """환경변수 통계 응답 스키마"""
    redis_count: int = Field(..., description="Redis에 캐싱된 환경변수 개수")
    postgresql_count: int = Field(..., description="PostgreSQL에 저장된 환경변수 개수")


class EnvVarBulkCreate(BaseModel):
    """환경변수 일괄 생성 스키마"""
    env_vars: Dict[str, str] = Field(..., description="환경변수 딕셔너리")


class EnvVarOperationResponse(BaseModel):
    """환경변수 작업 응답 스키마"""
    success: bool = Field(..., description="작업 성공 여부")
    message: str = Field(..., description="작업 결과 메시지")
    count: Optional[int] = Field(None, description="처리된 환경변수 개수")
