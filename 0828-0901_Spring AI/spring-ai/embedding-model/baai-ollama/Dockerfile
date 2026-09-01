## Ollama 베이스 이미지에 BAAI/bge-m3 임베딩 모델을 미리 내려받아 포함시키는 이미지
##
## - ollama/ollama 이미지를 기반으로, 빌드 시점에 ollama serve를 잠시 띄워
##   Hugging Face(BAAI/bge-m3)의 GGUF 모델을 pull한 뒤 그대로 이미지 레이어에 포함시킨다.
## - BAAI/bge-m3 원본 저장소는 GGUF가 아니므로, GGUF로 변환된 미러 저장소
##   (CompendiumLabs/bge-m3-gguf)에서 F16 파일을 받는다. 가중치 자체는 BAAI/bge-m3와 동일하다.
## - 컨테이너 최초 기동 시 모델을 매번 다시 받을 필요가 없어 기동이 빠르다.

FROM ollama/ollama:latest

# 빌드 시 --build-arg 로 변경 가능
# OLLAMA_MODEL : Hugging Face GGUF 모델 참조 (기본값: bge-m3 F16)
# EMBED_ALIAS  : 애플리케이션에서 사용할 짧은 모델 이름
ARG OLLAMA_MODEL=hf.co/CompendiumLabs/bge-m3-gguf:F16
ARG EMBED_ALIAS=bge-m3
ENV OLLAMA_MODEL=${OLLAMA_MODEL}
ENV EMBED_ALIAS=${EMBED_ALIAS}
ENV OLLAMA_HOST=0.0.0.0

# 빌드 시점에 ollama 서버를 백그라운드로 띄운 뒤 모델을 pull하고,
# 긴 Hugging Face 경로 대신 쓰기 편한 별칭(bge-m3)으로 복사한 다음 서버를 종료한다.
RUN (ollama serve &) && \
    sleep 5 && \
    ollama pull "${OLLAMA_MODEL}" && \
    ollama cp "${OLLAMA_MODEL}" "${EMBED_ALIAS}" && \
    ollama list && \
    (pkill ollama || true)

EXPOSE 11434

ENTRYPOINT ["ollama", "serve"]
