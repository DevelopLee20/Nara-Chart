#!/bin/bash

set -e

# 색상 코드
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Nara-Chart 프로덕션 환경 시작${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# .env.prod 파일 확인
if [ ! -f .env.prod ]; then
    echo -e "${RED}❌ .env.prod 파일이 없습니다.${NC}"
    echo -e "${YELLOW}   .env.dev 파일을 복사하여 .env.prod를 생성하세요.${NC}"
    exit 1
fi

# docker-compose-prod.yml 파일 확인
if [ ! -f docker compose-prod.yml ]; then
    echo -e "${RED}❌ docker-compose-prod.yml 파일이 없습니다.${NC}"
    exit 1
fi

# Docker가 실행 중인지 확인
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker가 실행되고 있지 않습니다.${NC}"
    echo -e "${YELLOW}   Docker Desktop을 실행해주세요.${NC}"
    exit 1
fi

# 데이터 디렉토리 생성
echo -e "${BLUE}📁 필요한 디렉토리 생성 중...${NC}"
mkdir -p data/postgres data/redis logs/backend logs/nginx logs/nginx-proxy backups backups/postgres scripts ssl nginx/conf.d

# 기존 컨테이너 확인 및 백업
if [ "$(docker ps -q -f name=nara-chart)" ]; then
    echo -e "${YELLOW}🔄 기존 컨테이너가 실행 중입니다. 백업 후 재시작합니다...${NC}"
    echo ""

    # 백업 수행
    if [ -f .env.prod ]; then
        source .env.prod
    fi

    POSTGRES_USER=${POSTGRES_USER:-nara_prod_user}
    POSTGRES_DB=${POSTGRES_DB:-nara_chart_production}
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)

    echo -e "${BLUE}💾 데이터베이스 백업 중...${NC}"
    docker compose -f docker-compose-prod.yml --env-file .env.prod exec -T postgres pg_dump -U ${POSTGRES_USER} ${POSTGRES_DB} > "backups/backup_${TIMESTAMP}.sql" 2>/dev/null

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ 백업 완료: backups/backup_${TIMESTAMP}.sql${NC}"
    else
        echo -e "${YELLOW}⚠️  백업을 건너뜁니다 (컨테이너가 준비되지 않았을 수 있습니다)${NC}"
    fi

    echo ""
    echo -e "${YELLOW}🛑 기존 컨테이너 중지 중...${NC}"
    docker compose -f docker-compose-prod.yml --env-file .env.prod down
    echo ""
fi

# 백업 서비스 포함 여부
PROFILES="--profile backup"

echo -e "${GREEN}🚀 프로덕션 서비스 시작 중...${NC}"
echo ""

# Docker Compose 실행
docker compose -f docker-compose-prod.yml --env-file .env.prod $PROFILES up -d --build

# 서비스가 준비될 때까지 대기
echo ""
echo -e "${YELLOW}⏳ 서비스가 시작될 때까지 대기 중...${NC}"
sleep 5

# 컨테이너 상태 확인
echo ""
echo -e "${BLUE}📊 컨테이너 상태:${NC}"
docker compose -f docker-compose-prod.yml --env-file .env.prod ps

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ 프로덕션 환경 시작 완료${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}🛠️  유용한 명령어:${NC}"
echo -e "  - 로그 확인:    ${YELLOW}docker-compose -f docker-compose-prod.yml --env-file .env.prod logs -f${NC}"
echo -e "  - 재시작:       ${YELLOW}./start-prod.sh${NC}"
echo ""
