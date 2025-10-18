from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core import settings

# SQLAlchemy 엔진 생성
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # 연결 유효성 검사
    pool_size=10,  # 연결 풀 크기
    max_overflow=20,  # 최대 오버플로우 연결 수
    echo=False  # SQL 로그 출력 (개발 시 True로 설정 가능)
)

# 세션 로컬 클래스 생성
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Base 클래스 생성 (모든 모델이 상속받을 기본 클래스)
Base = declarative_base()


# 데이터베이스 세션 의존성
def get_db():
    """
    FastAPI 의존성 주입을 위한 데이터베이스 세션 생성 함수

    Usage:
        @app.get("/items")
        def read_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 데이터베이스 초기화 함수
def init_db():
    """
    데이터베이스 테이블 생성 함수
    모든 모델이 import된 후 호출해야 함
    """
    Base.metadata.create_all(bind=engine)


# 데이터베이스 연결 테스트 함수
def test_db_connection():
    """
    데이터베이스 연결 테스트 함수
    """
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        print("✓ 데이터베이스 연결 성공")
        return True
    except Exception as e:
        print(f"✗ 데이터베이스 연결 실패: {e}")
        return False
