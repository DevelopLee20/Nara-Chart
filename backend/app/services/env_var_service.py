import redis
from sqlalchemy.orm import Session
from typing import Dict
from app.db.cruds.env_var_crud import EnvVarCRUD
from app.clients.redis_client import get_redis_client


class EnvVarService:
    """
    동적 환경변수 관리 서비스
    - Redis: 빠른 캐시 접근
    - PostgreSQL: 영구 저장 및 백업
    """

    ENV_PREFIX = "env:"  # Redis 키 접두사

    def __init__(self, db: Session, redis_client: redis.Redis):
        self.db = db
        self.redis = redis_client

    def _make_redis_key(self, key: str) -> str:
        """Redis 키 생성 (접두사 추가)"""
        return f"{self.ENV_PREFIX}{key}"

    # ✅ Redis key → str 변환 helper (bytes 대응)
    def _decode(self, value):
        if isinstance(value, bytes):
            return value.decode("utf-8")
        return value

    def load_from_db_to_redis(self) -> int:
        """
        PostgreSQL에서 모든 환경변수를 읽어 Redis에 로드
        앱 시작 시 호출
        """
        env_vars = EnvVarCRUD.get_all_as_dict(self.db)
        count = 0

        for key, value in env_vars.items():
            redis_key = self._make_redis_key(key)
            self.redis.set(redis_key, value)
            count += 1

        print(f"✓ PostgreSQL에서 Redis로 {count}개 환경변수 로드 완료")
        return count

    def get(self, key: str) -> str | None:
        """환경변수 조회 (Redis 우선)"""
        redis_key = self._make_redis_key(key)
        value = self.redis.get(redis_key)

        if value is not None:
            return self._decode(value)

        value = EnvVarCRUD.get_value_by_key(self.db, key)
        if value is not None:
            self.redis.set(redis_key, value)
            return value
        return None

    def get_all(self) -> Dict[str, str]:
        """Redis에서 모든 환경변수 조회"""
        pattern = f"{self.ENV_PREFIX}*"
        keys = self.redis.keys(pattern)
        env_vars = {}

        for redis_key in keys:
            redis_key_str = self._decode(redis_key)
            key = redis_key_str.replace(self.ENV_PREFIX, "", 1)
            value = self.redis.get(redis_key)
            if value is not None:
                env_vars[key] = self._decode(value)

        return env_vars

    def set(self, key: str, value: str) -> bool:
        """환경변수 설정 (Redis + PostgreSQL 동기화)"""
        try:
            EnvVarCRUD.upsert(self.db, key, value)
            redis_key = self._make_redis_key(key)
            self.redis.set(redis_key, value)
            return True
        except Exception as e:
            print(f"✗ 환경변수 설정 실패 [{key}]: {e}")
            return False

    def set_many(self, env_vars: Dict[str, str]) -> int:
        """여러 환경변수 일괄 설정"""
        count = 0
        for key, value in env_vars.items():
            if self.set(key, value):
                count += 1
        return count

    def delete(self, key: str) -> bool:
        """환경변수 삭제 (Redis + PostgreSQL)"""
        try:
            db_deleted = EnvVarCRUD.delete(self.db, key)
            redis_key = self._make_redis_key(key)
            redis_deleted = self.redis.delete(redis_key) > 0
            return bool(db_deleted or redis_deleted)
        except Exception as e:
            print(f"✗ 환경변수 삭제 실패 [{key}]: {e}")
            return False

    def sync_redis_to_db(self) -> int:
        """Redis → PostgreSQL 동기화"""
        env_vars = self.get_all()
        return EnvVarCRUD.bulk_upsert(self.db, env_vars)

    def sync_db_to_redis(self) -> int:
        """PostgreSQL → Redis 복원"""
        return self.load_from_db_to_redis()

    def clear_redis_cache(self) -> int:
        """Redis 캐시 전체 삭제 (환경변수만)"""
        pattern = f"{self.ENV_PREFIX}*"
        keys = self.redis.keys(pattern)
        if keys:
            deleted = self.redis.delete(*keys)
            print(f"✓ Redis에서 {deleted}개 환경변수 삭제 완료")
            return deleted
        return 0

    def get_stats(self) -> Dict[str, int]:
        """환경변수 통계 정보"""
        redis_count = len(self.redis.keys(f"{self.ENV_PREFIX}*"))
        db_count = len(EnvVarCRUD.get_all(self.db))
        return {"redis_count": redis_count, "postgresql_count": db_count}


def get_env_var_service(db: Session, redis_client: redis.Redis):
    """FastAPI 의존성 주입용 Service 인스턴스 생성"""
    return EnvVarService(db=db, redis_client=redis_client)
