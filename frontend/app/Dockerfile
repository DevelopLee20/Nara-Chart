# Frontend Dockerfile for React - Multi-stage build

# Stage 1: Build the React application
FROM node:18-alpine AS build

# 작업 디렉토리 설정
WORKDIR /app

# package.json과 package-lock.json 복사
COPY package*.json ./

# 의존성 설치
RUN npm ci --silent

# 애플리케이션 소스 복사
COPY . .

# 빌드 인자로 환경 변수 받기
ARG REACT_APP_API_URL
ENV REACT_APP_API_URL=$REACT_APP_API_URL

# 프로덕션 빌드
RUN npm run build

# Stage 2: Nginx로 서빙
FROM nginx:alpine

# Nginx 설정 파일 복사 (커스텀 설정이 필요한 경우)
COPY nginx.conf /etc/nginx/conf.d/default.conf

# 빌드된 파일을 Nginx의 기본 디렉토리로 복사
COPY --from=build /app/build /usr/share/nginx/html

# 포트 노출
EXPOSE 80

# Nginx 실행
CMD ["nginx", "-g", "daemon off;"]
