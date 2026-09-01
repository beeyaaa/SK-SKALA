#!/bin/bash

# build.sh로 빌드한 Ollama 임베딩 전용 이미지(BAAI/bge-m3)를 컨테이너로 실행한다.
# 채팅용 Ollama 컨테이너(11434 포트), qwen3-embedding 컨테이너(11435 포트)와
# 동시에 실행할 수 있도록 컨테이너 이름과 호스트 포트를 다르게 사용한다.

set -e

IMAGE_NAME="skala-registry.skala-ai.com/library/ollama-qwen3-embedding:1.0"
CONTAINER_NAME="ollama-qwen3-embedding"
HOST_PORT=11436

if docker ps -a --format '{{.Names}}' | grep -qx "$CONTAINER_NAME"; then
  docker start "$CONTAINER_NAME"
else
  docker run -d \
    --name "$CONTAINER_NAME" \
    -p "$HOST_PORT:11434" \
    -v ollama-qwen3-embedding-model:/root/.ollama \
    "$IMAGE_NAME"
fi

echo "Ollama(embedding: qwen3)가 http://localhost:$HOST_PORT 에서 대기 중입니다."
