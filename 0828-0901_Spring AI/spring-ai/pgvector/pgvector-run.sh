#!/bin/bash
set -e

# ============================================
#   - 이미지: pgvector/pgvector:pg18
#     (PostgreSQL 18 + 최신 pgvector 익스텐션, linux/arm64·amd64 모두 지원)
# ============================================

# PostgreSQL(pgvector) 설정
CONTAINER_NAME="pgvector"
IMAGE="pgvector/pgvector:pg18"
NETWORK_NAME="pgvector-net"
PORT="5433"

# 데이터베이스 설정
POSTGRES_USER="postgres"
POSTGRES_PASSWORD="postgres"
POSTGRES_DB="postgres"

# 1. Docker Desktop 실행 여부 확인
if ! docker info &> /dev/null; then
    echo "오류: Docker가 실행 중이 아닙니다. Docker Desktop을 먼저 실행해 주세요."
    exit 1
fi

# 2. 최신 이미지 pull
echo "최신 pgvector 이미지(${IMAGE})를 내려받습니다..."
docker pull ${IMAGE}

# 3. 기존 컨테이너 확인 및 중지/삭제
if [ "$(docker ps -aq -f name=^${CONTAINER_NAME}$)" ]; then
    echo "기존 컨테이너를 중지하고 삭제합니다..."
    docker stop ${CONTAINER_NAME} &> /dev/null || true
    docker rm ${CONTAINER_NAME} &> /dev/null || true
fi

# 4. 네트워크 존재 확인 (없으면 생성)
if ! docker network inspect ${NETWORK_NAME} &> /dev/null; then
    echo "네트워크 ${NETWORK_NAME}이 없습니다. 생성합니다..."
    docker network create ${NETWORK_NAME}
fi

mkdir -p "$(pwd)/pgdata"

echo "PostgreSQL(pgvector) 컨테이너를 시작합니다..."

# 6. Docker 컨테이너 실행
docker run -d \
  --name ${CONTAINER_NAME} \
  --network ${NETWORK_NAME} \
  -p ${PORT}:5432 \
  -e POSTGRES_USER="${POSTGRES_USER}" \
  -e POSTGRES_PASSWORD="${POSTGRES_PASSWORD}" \
  -e POSTGRES_DB="${POSTGRES_DB}" \
  -v "$(pwd)/pgdata:/var/lib/postgresql" \
  --health-cmd="pg_isready -U ${POSTGRES_USER}" \
  --health-interval=2s \
  --health-timeout=5s \
  --health-retries=30 \
  ${IMAGE}
