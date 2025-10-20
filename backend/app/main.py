from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.db import get_db, init_db, test_db_connection
from app.core import settings
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    애플리케이션 시작 및 종료 이벤트 처리
    """
    # 시작 시
    print("=== 애플리케이션 시작 ===")

    # 데이터베이스 연결 테스트
    test_db_connection()

    # 데이터베이스 테이블 생성 (models를 import한 후)
    try:
        from app.models import bid_models, env_var_models
        init_db()
        print("✓ 데이터베이스 테이블 초기화 완료")
    except Exception as e:
        print(f"✗ 데이터베이스 초기화 실패: {e}")

    # Redis 연결 테스트
    try:
        from app.clients.redis_client import RedisClient
        RedisClient.test_connection()
    except Exception as e:
        print(f"✗ Redis 연결 테스트 실패: {e}")

    # PostgreSQL에서 Redis로 환경변수 로드
    try:
        from app.db.database import SessionLocal
        from app.services.env_var_service import EnvVarService
        from app.clients.redis_client import get_redis_client

        db = SessionLocal()
        redis_client = get_redis_client()
        env_service = EnvVarService(db=db, redis_client=redis_client)

        count = env_service.load_from_db_to_redis()
        print(f"✓ 환경변수 로드 완료: {count}개")

        db.close()
    except Exception as e:
        print(f"✗ 환경변수 로드 실패: {e}")

    yield

    # 종료 시
    print("=== 애플리케이션 종료 ===")

    # Redis 연결 종료
    try:
        from app.clients.redis_client import RedisClient
        RedisClient.close()
    except Exception as e:
        print(f"✗ Redis 연결 종료 실패: {e}")


app = FastAPI(
    title=settings.APP_TITLE,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    lifespan=lifespan
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터 등록
from app.routers import env_var_router, bid_router
app.include_router(env_var_router.router)
app.include_router(bid_router.router)


@app.get("/health")
def read_health():
    """
    헬스 체크 엔드포인트
    """
    return {"status": "ok"}


@app.get("/db-health")
def check_db_health(db: Session = Depends(get_db)):
    """
    데이터베이스 연결 상태 확인
    """
    try:
        # 간단한 쿼리 실행
        db.execute(text("SELECT 1"))
        return {"database": "connected"}
    except Exception as e:
        return {"database": "disconnected", "error": str(e)}
