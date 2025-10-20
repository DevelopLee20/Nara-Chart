from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
import os


class Settings(BaseSettings):
    """
    애플리케이션 환경 변수 설정
    환경 변수를 우선적으로 사용하고, .env 파일이 있으면 보조적으로 사용
    """
    model_config = SettingsConfigDict(
        # .env 파일이 없어도 에러 발생하지 않도록 설정
        env_file=".env" if os.path.exists(".env") else None,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        # 환경 변수를 .env 파일보다 우선
        env_prefix=""
    )

    # 애플리케이션 기본 설정
    MODE: str = "dev"
    APP_TITLE: str = "Nara-Chart API"
    APP_DESCRIPTION: str = "나라장터 입찰 데이터 분석 API"
    APP_VERSION: str = "1.0.0"

    # CORS 설정
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"
    ALLOWED_HOSTS: str = "*"

    # 서버 포트 설정
    WEB_PORT: int = 8000
    DOCKER_PORT: int = 8000
    BACKEND_PORT: int = 8000
    FRONTEND_PORT: int = 3000

    # Gunicorn 설정
    TIMEOUT: int = 120
    KEEP_ALIVE: int = 5
    WORKERS: int = 1

    # PostgreSQL Database Configuration
    POSTGRES_USER: str = "nara_dev_user"
    POSTGRES_PASSWORD: str = "nara_dev_password_123"
    POSTGRES_DB: str = "nara_chart_dev"
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432

    # Redis Configuration
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""

    # Backend Configuration
    APP_ENV: str = "development"
    DEBUG: bool = True
    LOG_LEVEL: str = "debug"
    SECRET_KEY: str = "dev-secret-key-for-development-only-do-not-use-in-production"

    # Frontend Configuration
    REACT_APP_API_URL: str = "http://localhost:8000"
    NODE_ENV: str = "development"

    @property
    def DATABASE_URL(self) -> str:
        """
        PostgreSQL 데이터베이스 URL 생성
        """
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    @property
    def CORS_ORIGINS_LIST(self) -> List[str]:
        """
        CORS origins를 리스트로 변환
        """
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]


# 전역 설정 인스턴스
settings = Settings()
