import pytest
from sqlalchemy.orm import Session
from app.db.cruds.env_var_crud import EnvVarCRUD


class TestEnvVarCRUD:
    """환경변수 CRUD 테스트"""

    def test_create_env_var(self, db_session: Session):
        """환경변수 생성 테스트"""
        env_var = EnvVarCRUD.create(db_session, "TEST_KEY", "TEST_VALUE")
        assert env_var.key == "TEST_KEY"
        assert env_var.value == "TEST_VALUE"

    def test_get_by_key(self, db_session: Session):
        """환경변수 조회 테스트"""
        EnvVarCRUD.create(db_session, "TEST_KEY", "TEST_VALUE")
        env_var = EnvVarCRUD.get_by_key(db_session, "TEST_KEY")
        assert env_var is not None
        assert env_var.value == "TEST_VALUE"

    def test_update_env_var(self, db_session: Session):
        """환경변수 업데이트 테스트"""
        EnvVarCRUD.create(db_session, "TEST_KEY", "OLD_VALUE")
        updated = EnvVarCRUD.update(db_session, "TEST_KEY", "NEW_VALUE")
        assert updated is not None
        assert updated.value == "NEW_VALUE"

    def test_upsert_create(self, db_session: Session):
        """환경변수 업서트 테스트 - 생성"""
        env_var = EnvVarCRUD.upsert(db_session, "NEW_KEY", "NEW_VALUE")
        assert env_var.key == "NEW_KEY"
        assert env_var.value == "NEW_VALUE"

    def test_upsert_update(self, db_session: Session):
        """환경변수 업서트 테스트 - 업데이트"""
        EnvVarCRUD.create(db_session, "EXISTING_KEY", "OLD_VALUE")
        env_var = EnvVarCRUD.upsert(db_session, "EXISTING_KEY", "UPDATED_VALUE")
        assert env_var.value == "UPDATED_VALUE"

    def test_delete_env_var(self, db_session: Session):
        """환경변수 삭제 테스트"""
        EnvVarCRUD.create(db_session, "DELETE_ME", "VALUE")
        deleted = EnvVarCRUD.delete(db_session, "DELETE_ME")
        assert deleted is True
        env_var = EnvVarCRUD.get_by_key(db_session, "DELETE_ME")
        assert env_var is None

    def test_get_all(self, db_session: Session):
        """모든 환경변수 조회 테스트"""
        EnvVarCRUD.create(db_session, "KEY1", "VALUE1")
        EnvVarCRUD.create(db_session, "KEY2", "VALUE2")
        all_vars = EnvVarCRUD.get_all(db_session)
        assert len(all_vars) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
