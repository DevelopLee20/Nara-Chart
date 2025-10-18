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
if [ ! -f docker-compose-prod.yml ]; then
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

# 기존 컨테이너 확인
if [ "$(docker ps -q -f name=nara-chart)" ]; then
    echo -e "${YELLOW}⚠️  기존 컨테이너가 실행 중입니다. 재시작합니다...${NC}"
    docker-compose -f docker-compose-prod.yml --env-file .env.prod down
fi

# 백업 서비스 포함 여부
PROFILES="--profile backup"

echo -e "${GREEN}🚀 프로덕션 서비스 시작 중...${NC}"
echo ""

# Docker Compose 실행
docker-compose -f docker-compose-prod.yml --env-file .env.prod $PROFILES up -d --build

# 서비스가 준비될 때까지 대기
echo ""
echo -e "${YELLOW}⏳ 서비스가 시작될 때까지 대기 중...${NC}"
sleep 5

# 컨테이너 상태 확인
echo ""
echo -e "${BLUE}📊 컨테이너 상태:${NC}"
docker-compose -f docker-compose-prod.yml --env-file .env.prod ps

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ 프로덕션 환경 시작 완료${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}🛠️  유용한 명령어:${NC}"
echo -e "  - 로그 확인:    ${YELLOW}docker-compose -f docker-compose-prod.yml --env-file .env.prod logs -f${NC}"
echo -e "  - 컨테이너 중지: ${YELLOW}./stop-prod.sh${NC}"
echo -e "  - 재시작:       ${YELLOW}./start-prod.sh${NC}"
echo ""
