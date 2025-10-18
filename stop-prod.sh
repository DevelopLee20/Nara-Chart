#!/bin/bash

set -e

# 색상 코드
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Nara-Chart 프로덕션 환경 중지${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# docker-compose-prod.yml 파일 확인
if [ ! -f docker-compose-prod.yml ]; then
    echo -e "${RED}❌ docker-compose-prod.yml 파일이 없습니다.${NC}"
    exit 1
fi

# .env.prod 파일 확인
if [ ! -f .env.prod ]; then
    echo -e "${RED}❌ .env.prod 파일이 없습니다.${NC}"
    exit 1
fi

# Docker가 실행 중인지 확인
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker가 실행되고 있지 않습니다.${NC}"
    exit 1
fi

# 실행 중인 컨테이너 확인
if [ -z "$(docker ps -q -f name=nara-chart)" ]; then
    echo -e "${YELLOW}⚠️  실행 중인 컨테이너가 없습니다.${NC}"
    exit 0
fi

echo -e "${YELLOW}⚠️  프로덕션 환경을 중지합니다.${NC}"
read -p "계속하시겠습니까? (y/N): " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${RED}작업을 취소했습니다.${NC}"
    exit 1
fi

# 백업 디렉토리 생성
mkdir -p backups

# 백업
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

if [ -f .env.prod ]; then
    source .env.prod
fi

POSTGRES_USER=${POSTGRES_USER:-nara_prod_user}
POSTGRES_DB=${POSTGRES_DB:-nara_chart_production}

echo -e "${BLUE}💾 백업 중...${NC}"
docker-compose -f docker-compose-prod.yml --env-file .env.prod exec -T postgres pg_dump -U ${POSTGRES_USER} ${POSTGRES_DB} > "backups/backup_${TIMESTAMP}.sql"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ 백업 완료: backups/backup_${TIMESTAMP}.sql${NC}"
else
    echo -e "${RED}❌ 백업 실패${NC}"

echo -e "${YELLOW}🛑 서비스 중지 중...${NC}"
docker-compose -f docker-compose-prod.yml --env-file .env.prod down

echo ""
echo -e "${GREEN}✅ 프로덕션 환경 중지 완료${NC}"
echo ""
