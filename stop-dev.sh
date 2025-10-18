#!/bin/bash

set -e

# 색상 코드
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Nara-Chart 개발 환경 중지${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# docker-compose-dev.yml 파일 확인
if [ ! -f docker-compose-dev.yml ]; then
    echo -e "${RED}❌ docker-compose-dev.yml 파일이 없습니다.${NC}"
    exit 1
fi

# .env.dev 파일 확인
if [ ! -f .env.dev ]; then
    echo -e "${RED}❌ .env.dev 파일이 없습니다.${NC}"
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

echo -e "${YELLOW}🛑 서비스 중지 및 데이터 삭제 중...${NC}"
docker-compose -f docker-compose-dev.yml --env-file .env.dev down -v

echo ""
echo -e "${GREEN}✅ 개발 환경 중지 완료${NC}"
echo ""
