import pytest
from app.services.env_var_service import EnvVarService
from app.db.cruds.env_var_crud import EnvVarCRUD


class TestEnvVarService:
    """환경변수 서비스 테스트"""

    def test_set_and_get(self, env_var_service: EnvVarService):
        """환경변수 설정 및 조회 테스트"""
        success = env_var_service.set("SERVICE_KEY", "SERVICE_VALUE")
        assert success is True

        value = env_var_service.get("SERVICE_KEY")
        assert value == "SERVICE_VALUE"

    def test_get_from_cache(self, env_var_service: EnvVarService):
        """Redis 캐시에서 조회 테스트"""
        env_var_service.set("CACHE_KEY", "CACHE_VALUE")

        # Redis에서 직접 확인
        redis_key = env_var_service._make_redis_key("CACHE_KEY")
        redis_value = env_var_service.redis.get(redis_key)
        assert redis_value == "CACHE_VALUE"

    def test_load_from_db_to_redis(self, env_var_service: EnvVarService):
        """PostgreSQL에서 Redis로 로드 테스트"""
        # DB에 직접 저장
        EnvVarCRUD.create(env_var_service.db, "DB_KEY", "DB_VALUE")

        # Redis로 로드
        count = env_var_service.load_from_db_to_redis()
        assert count == 1

        # Redis에서 조회
        value = env_var_service.get("DB_KEY")
        assert value == "DB_VALUE"

    def test_delete(self, env_var_service: EnvVarService):
        """환경변수 삭제 테스트"""
        env_var_service.set("DELETE_KEY", "DELETE_VALUE")
        deleted = env_var_service.delete("DELETE_KEY")
        assert deleted is True

        value = env_var_service.get("DELETE_KEY")
        assert value is None

    def test_get_all(self, env_var_service: EnvVarService):
        """모든 환경변수 조회 테스트"""
        env_var_service.set("KEY1", "VALUE1")
        env_var_service.set("KEY2", "VALUE2")

        all_vars = env_var_service.get_all()
        assert len(all_vars) == 2
        assert all_vars["KEY1"] == "VALUE1"
        assert all_vars["KEY2"] == "VALUE2"

    def test_set_many(self, env_var_service: EnvVarService):
        """여러 환경변수 일괄 설정 테스트"""
        env_vars = {
            "BULK_KEY1": "BULK_VALUE1",
            "BULK_KEY2": "BULK_VALUE2",
            "BULK_KEY3": "BULK_VALUE3"
        }
        count = env_var_service.set_many(env_vars)
        assert count == 3

        value1 = env_var_service.get("BULK_KEY1")
        assert value1 == "BULK_VALUE1"

    def test_stats(self, env_var_service: EnvVarService):
        """환경변수 통계 테스트"""
        env_var_service.set("STATS_KEY1", "VALUE1")
        env_var_service.set("STATS_KEY2", "VALUE2")

        stats = env_var_service.get_stats()
        assert stats["redis_count"] == 2
        assert stats["postgresql_count"] == 2

    def test_sync_redis_to_db(self, env_var_service: EnvVarService):
        """Redis -> PostgreSQL 동기화 테스트"""
        # Redis에 직접 저장
        redis_key = env_var_service._make_redis_key("REDIS_KEY")
        env_var_service.redis.set(redis_key, "REDIS_VALUE")

        # PostgreSQL로 동기화
        count = env_var_service.sync_redis_to_db()
        assert count >= 1

        # PostgreSQL에서 확인
        value = EnvVarCRUD.get_value_by_key(env_var_service.db, "REDIS_KEY")
        assert value == "REDIS_VALUE"

    def test_clear_redis_cache(self, env_var_service: EnvVarService):
        """Redis 캐시 삭제 테스트"""
        env_var_service.set("CLEAR_KEY1", "VALUE1")
        env_var_service.set("CLEAR_KEY2", "VALUE2")

        count = env_var_service.clear_redis_cache()
        assert count >= 2

        # Redis에서 확인
        all_vars = env_var_service.get_all()
        assert len(all_vars) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
