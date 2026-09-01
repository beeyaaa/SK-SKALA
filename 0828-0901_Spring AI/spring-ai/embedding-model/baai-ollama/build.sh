#!/bin/bash

# Dockerfile을 기준으로 BAAI/bge-m3 임베딩 모델이 포함된 Ollama 이미지를 빌드하는 스크립트
#
# 사용법:
#   ./build.sh
#   IMAGE_NAME=my-ollama-baai-embedding ./build.sh
#   EMBED_MODEL=hf.co/CompendiumLabs/bge-m3-gguf:F32 ./build.sh

set -e


IMAGE_NAME="ollama-baai-embedding"
IMAGE_TAG="1.0"

# Hugging Face(BAAI/bge-m3)의 GGUF 미러 저장소 F16 파일
EMBED_MODEL="hf.co/CompendiumLabs/bge-m3-gguf:F16"

# 애플리케이션에서 사용할 짧은 모델 이름
EMBED_ALIAS="bge-m3"

echo "이미지(${IMAGE_NAME}:${IMAGE_TAG})를 빌드합니다. (모델: ${EMBED_MODEL} -> ${EMBED_ALIAS})"

docker buildx build \
  --build-arg OLLAMA_MODEL="${EMBED_MODEL}" \
  --build-arg EMBED_ALIAS="${EMBED_ALIAS}" \
  --platform linux/amd64,linux/arm64 \
  -t "${IMAGE_NAME}:${IMAGE_TAG}" \
  -f "./Dockerfile" \
  .

echo "이미지 빌드가 완료되었습니다: ${IMAGE_NAME}:${IMAGE_TAG}"
docker images "${IMAGE_NAME}"
