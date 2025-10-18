from fastapi import FastAPI, Depends
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
        from app.models import bid_models
        init_db()
        print("✓ 데이터베이스 테이블 초기화 완료")
    except Exception as e:
        print(f"✗ 데이터베이스 초기화 실패: {e}")

    yield

    # 종료 시
    print("=== 애플리케이션 종료 ===")


app = FastAPI(
    title=settings.APP_TITLE,
    description=settings.APP_DESCRIPTION,
    version=settings.APP_VERSION,
    lifespan=lifespan
)


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
