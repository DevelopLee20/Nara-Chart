# Backend Production Dockerfile for FastAPI
# Multi-stage build for optimized production image

# Build stage
FROM python:3.9-slim as builder

WORKDIR /app

# 환경 변수 설정
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 빌드에 필요한 패키지 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Pipenv 설치
RUN pip install --no-cache-dir pipenv

# Pipfile과 Pipfile.lock 복사
COPY Pipfile Pipfile.lock ./

# 의존성 설치
RUN pipenv install --system --deploy --ignore-pipfile

# 프로덕션 패키지 설치
RUN pip install --no-cache-dir \
    psycopg2-binary \
    redis \
    python-dotenv \
    sqlalchemy \
    alembic \
    gunicorn

# Production stage
FROM python:3.9-slim as production

# 빌드 인자
ARG BUILD_DATE
ARG VERSION
LABEL build_date=$BUILD_DATE
LABEL version=$VERSION

WORKDIR /app

# 환경 변수 설정
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH"

# 런타임에 필요한 패키지만 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 빌드 스테이지에서 Python 패키지 복사
COPY --from=builder /usr/local/lib/python3.9/site-packages /usr/local/lib/python3.9/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# 애플리케이션 코드 복사
COPY . .

# 비루트 사용자 생성 및 권한 설정
RUN groupadd -r appuser && useradd -r -g appuser appuser \
    && chown -R appuser:appuser /app

# 비루트 사용자로 전환
USER appuser

# 포트 노출
EXPOSE 8000

# 헬스체크
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 애플리케이션 실행
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
