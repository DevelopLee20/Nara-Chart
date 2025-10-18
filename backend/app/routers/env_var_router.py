from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict
from app.db.database import get_db
from app.services.env_var_service import EnvVarService
from app.clients.redis_client import get_redis_client
from app.schemas.env_var_schemas import (
    EnvVarCreate,
    EnvVarUpdate,
    EnvVarResponse,
    EnvVarListResponse,
    EnvVarStatsResponse,
    EnvVarBulkCreate,
    EnvVarOperationResponse
)
import redis

router = APIRouter(
    prefix="/api/env-vars",
    tags=["환경변수 관리"]
)


def _get_service(
    db: Session = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis_client)
) -> EnvVarService:
    """EnvVarService 의존성 주입 헬퍼"""
    return EnvVarService(db=db, redis_client=redis_client)


@router.get("/", response_model=EnvVarListResponse)
def get_all_env_vars(
    service: EnvVarService = Depends(_get_service)
):
    """
    모든 환경변수 조회 (Redis 캐시에서)
    """
    env_vars = service.get_all()
    return EnvVarListResponse(
        env_vars=env_vars,
        count=len(env_vars)
    )


@router.get("/stats", response_model=EnvVarStatsResponse)
def get_env_var_stats(
    service: EnvVarService = Depends(_get_service)
):
    """
    환경변수 통계 조회 (Redis vs PostgreSQL)
    """
    stats = service.get_stats()
    return EnvVarStatsResponse(**stats)


@router.get("/{key}")
def get_env_var(
    key: str,
    service: EnvVarService = Depends(_get_service)
):
    """
    특정 환경변수 조회
    """
    value = service.get(key)
    if value is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"환경변수 '{key}'를 찾을 수 없습니다."
        )
    return {"key": key, "value": value}


@router.put("/{key}", response_model=EnvVarOperationResponse)
def set_env_var(
    key: str,
    data: EnvVarUpdate,
    service: EnvVarService = Depends(_get_service)
):
    """
    환경변수 설정/업데이트 (Redis + PostgreSQL)
    """
    success = service.set(key, data.value)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"환경변수 '{key}' 설정 실패"
        )
    return EnvVarOperationResponse(
        success=True,
        message=f"환경변수 '{key}' 설정 완료"
    )


@router.post("/", response_model=EnvVarOperationResponse)
def create_env_var(
    data: EnvVarCreate,
    service: EnvVarService = Depends(_get_service)
):
    """
    환경변수 생성 (Redis + PostgreSQL)
    """
    # 기존 환경변수 확인
    existing = service.get(data.key)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"환경변수 '{data.key}'가 이미 존재합니다."
        )

    success = service.set(data.key, data.value)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"환경변수 '{data.key}' 생성 실패"
        )
    return EnvVarOperationResponse(
        success=True,
        message=f"환경변수 '{data.key}' 생성 완료"
    )


@router.post("/bulk", response_model=EnvVarOperationResponse)
def bulk_set_env_vars(
    data: EnvVarBulkCreate,
    service: EnvVarService = Depends(_get_service)
):
    """
    여러 환경변수 일괄 설정/업데이트
    """
    count = service.set_many(data.env_vars)
    return EnvVarOperationResponse(
        success=True,
        message=f"{count}개 환경변수 설정 완료",
        count=count
    )


@router.delete("/{key}", response_model=EnvVarOperationResponse)
def delete_env_var(
    key: str,
    service: EnvVarService = Depends(_get_service)
):
    """
    환경변수 삭제 (Redis + PostgreSQL)
    """
    success = service.delete(key)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"환경변수 '{key}'를 찾을 수 없습니다."
        )
    return EnvVarOperationResponse(
        success=True,
        message=f"환경변수 '{key}' 삭제 완료"
    )


@router.post("/sync/db-to-redis", response_model=EnvVarOperationResponse)
def sync_db_to_redis(
    service: EnvVarService = Depends(_get_service)
):
    """
    PostgreSQL -> Redis 동기화 (복원)
    """
    count = service.sync_db_to_redis()
    return EnvVarOperationResponse(
        success=True,
        message=f"PostgreSQL에서 Redis로 {count}개 환경변수 동기화 완료",
        count=count
    )


@router.post("/sync/redis-to-db", response_model=EnvVarOperationResponse)
def sync_redis_to_db(
    service: EnvVarService = Depends(_get_service)
):
    """
    Redis -> PostgreSQL 동기화 (백업)
    """
    count = service.sync_redis_to_db()
    return EnvVarOperationResponse(
        success=True,
        message=f"Redis에서 PostgreSQL로 {count}개 환경변수 동기화 완료",
        count=count
    )


@router.delete("/cache/clear", response_model=EnvVarOperationResponse)
def clear_redis_cache(
    service: EnvVarService = Depends(_get_service)
):
    """
    Redis 캐시 전체 삭제 (환경변수만)
    """
    count = service.clear_redis_cache()
    return EnvVarOperationResponse(
        success=True,
        message=f"Redis 캐시 {count}개 환경변수 삭제 완료",
        count=count
    )
