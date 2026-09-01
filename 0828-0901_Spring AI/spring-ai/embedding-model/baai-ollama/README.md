# ollama-baai-embedding

`ollama-qwen3-embedding` 과 동일한 구조로, 임베딩 모델만 **BAAI/bge-m3** 로 교체한 버전입니다.

## 모델 정보

- 원본: [BAAI/bge-m3 · Hugging Face](https://huggingface.co/BAAI/bge-m3)
  (다국어, dense/sparse/multi-vector 검색 지원, 567M)
- Ollama 는 GGUF 포맷만 pull 할 수 있고 BAAI/bge-m3 원본 저장소에는 GGUF 파일이 없으므로,
  가중치가 동일한 GGUF 미러 저장소
  [CompendiumLabs/bge-m3-gguf](https://huggingface.co/CompendiumLabs/bge-m3-gguf) 의 F16 파일을 사용합니다.
- 빌드 시 긴 Hugging Face 경로(`hf.co/CompendiumLabs/bge-m3-gguf:F16`)를
  짧은 별칭 `bge-m3` 로 복사(`ollama cp`)해 두므로, 애플리케이션에서는 `bge-m3` 이름으로 호출하면 됩니다.

## 사용법

```bash
# 1) 이미지 빌드 (빌드 시점에 모델을 이미지 레이어에 포함)
./build.sh

# 2) 컨테이너 실행 (호스트 11436 포트)
./run-ollama.sh

# 3) 동작 확인
./03.test.sh
```

## 포트 정리

| 컨테이너 | 용도 | 호스트 포트 |
|----------|------|-------------|
| ollama | 채팅 | 11434 |
| ollama-qwen-embedding | qwen3-embedding | 11435 |
| ollama-baai-embedding | bge-m3 | 11436 |

## 환경 변수

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `IMAGE_NAME` | `ollama-baai-embedding` | 빌드할 이미지 이름 |
| `IMAGE_TAG` | `1.0` | 이미지 태그 |
| `EMBED_MODEL` | `hf.co/CompendiumLabs/bge-m3-gguf:F16` | pull 할 Hugging Face GGUF 모델 (예: `:F32` 로 변경 가능) |
| `EMBED_ALIAS` | `bge-m3` | 애플리케이션에서 사용할 짧은 모델 이름 |
| `BASE_URL` | `http://localhost:11436` | 테스트 대상 서버 주소 |
