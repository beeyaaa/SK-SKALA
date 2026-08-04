# Day 1 종합 실습 - 데이터 수집 미니 파이프라인

## 실행 목적

- `asyncio.gather()`와 `httpx`를 이용한 API 3개 동시 수집
- Pydantic v2 모델을 이용한 타입·범위 검증
- 검증 데이터의 CSV·Parquet 저장
- 동일 데이터의 읽기·쓰기 시간 및 파일 크기 비교
- pytest 스키마 테스트와 ruff 코드 품질 검사

## 프로젝트 구조

```text
.
├── main.py           # 전체 파이프라인 진입점
├── src/              # 데이터 수집 파이프라인 기능 모듈
│   ├── collectors.py     # 비동기 API 수집
│   ├── transformers.py   # 필드 추출 및 Pydantic 검증
│   ├── models.py         # API별 Pydantic v2 모델
│   └── storage.py        # CSV·Parquet 저장과 성능 측정
├── tests/            # 스키마 검증 테스트
├── output/           # 실행 결과 파일
└── report.md         # API·검증·성능 실행 결과
```

## 설치 및 실행

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

## 품질 검사

```bash
pytest
ruff check .
```

## 결과 파일

- API별 CSV·Parquet 파일
- `output/benchmark_results.csv`
- `report.md`

## 오류 처리

- HTTP 상태 오류, 타임아웃, JSON 파싱 오류 처리
- API 3개 중 실패한 요청을 모아 `CollectionError`로 보고
- Pydantic `ValidationError` 처리
- 저장·재로딩 행 수 불일치 처리