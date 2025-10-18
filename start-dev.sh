#!/bin/bash

set -e

# 색상 코드
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Nara-Chart 개발 환경 시작${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# .env.dev 파일 확인
if [ ! -f .env.dev ]; then
    echo -e "${RED}❌ .env.dev 파일이 없습니다.${NC}"
    exit 1
fi

# docker-compose-dev.yml 파일 확인
if [ ! -f docker-compose-dev.yml ]; then
    echo -e "${RED}❌ docker-compose-dev.yml 파일이 없습니다.${NC}"
    exit 1
fi

# Docker가 실행 중인지 확인
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker가 실행되고 있지 않습니다.${NC}"
    echo -e "${YELLOW}   Docker Desktop을 실행해주세요.${NC}"
    exit 1
fi

# 기존 컨테이너 정리 (필요한 경우)
if [ "$(docker ps -q -f name=nara-chart)" ]; then
    echo -e "${YELLOW}⚠️  기존 컨테이너가 실행 중입니다. 재시작합니다...${NC}"
    docker-compose -f docker-compose-dev.yml --env-file .env.dev down
fi

echo -e "${GREEN}🚀 개발 환경 시작 중...${NC}"
echo ""

# Docker Compose 실행
docker-compose -f docker-compose-dev.yml --env-file .env.dev up -d --build

# 서비스가 준비될 때까지 대기
echo ""
echo -e "${YELLOW}⏳ 서비스가 시작될 때까지 대기 중...${NC}"
sleep 5

# 컨테이너 상태 확인
echo ""
echo -e "${BLUE}📊 컨테이너 상태:${NC}"
docker-compose -f docker-compose-dev.yml --env-file .env.dev ps

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}✅ 개발 환경 시작 완료${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${BLUE}🌐 서비스 URL:${NC}"
echo -e "  - Frontend:     ${GREEN}http://localhost:3000${NC}"
echo -e "  - Backend:      ${GREEN}http://localhost:8000${NC}"
echo -e "  - API Docs:     ${GREEN}http://localhost:8000/docs${NC}"
echo -e "  - PostgreSQL:   ${GREEN}localhost:5432${NC}"
echo -e "  - Redis:        ${GREEN}localhost:6379${NC}"
echo ""
echo -e "${BLUE}🛠️  유용한 명령어:${NC}"
echo -e "  - 로그 확인:    ${YELLOW}docker-compose -f docker-compose-dev.yml --env-file .env.dev logs -f${NC}"
echo -e "  - 컨테이너 중지: ${YELLOW}./stop-dev.sh${NC}"
echo -e "  - 재시작:       ${YELLOW}./start-dev.sh${NC}"
echo ""
