import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.database import Base
from app.clients.redis_client import get_redis_client
import redis


# 테스트용 PostgreSQL 데이터베이스 설정
TEST_DATABASE_URL = "sqlite:///./test_env_vars.db"  # 테스트용 SQLite 사용


@pytest.fixture
def db_session():
    """테스트용 데이터베이스 세션"""
    engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # 테이블 생성
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

    # 테이블 삭제
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def redis_client():
    """테스트용 Redis 클라이언트"""
    try:
        client = get_redis_client()
        # 테스트 전 환경변수 캐시 삭제
        pattern = "env:*"
        keys = client.keys(pattern)
        if keys:
            client.delete(*keys)
        yield client
    except redis.exceptions.ConnectionError:
        pytest.skip("Redis 서버에 연결할 수 없습니다.")


@pytest.fixture
def env_var_service(db_session, redis_client):
    """테스트용 환경변수 서비스"""
    from app.services.env_var_service import EnvVarService
    return EnvVarService(db=db_session, redis_client=redis_client)
