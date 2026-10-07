# Vector DB 실습 1·2

강의의 참고자료 PDF를 바탕으로 만든 실행 코드입니다. 상위 폴더의 `Vector DB_실습_PDF`에서 유형별 PDF 5개를 선택합니다. 1번 SPRi Brief는 파일명 기준 가장 최신 자료를 사용합니다. `--all-pdfs`를 주면 폴더의 PDF를 모두 사용하지만 실행 시간이 크게 늘어납니다.

## 준비

Python 3.11 권장. 최초 실행 시 BGE-M3와 BGE-Reranker 모델을 다운로드합니다. CPU에서는 임베딩과 재정렬에 시간이 걸릴 수 있습니다. Docker에서 Qdrant를 6333 포트로 실행해 두세요.

```bash
cd vector_db_lab
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
curl http://localhost:6333/collections
```

## 실습 1

```bash
python lab.py ingest
python lab.py search 'HBM이란 무엇인가?'
python lab.py search '한국의 반도체 경쟁력은?' --min-page 5
```

`ingest`는 청크와 FAISS 인덱스를 `data/`에 저장하고, Qdrant의 `skala_vector_db_1006` 컬렉션에 같은 청크를 올립니다. **다시 실행하면 이 컬렉션을 교체합니다.** PDF 원본은 수정하지 않습니다. FAISS와 Qdrant 모두 정규화된 1024차원 벡터를 사용합니다.

## 실습 2

```bash
python lab.py compare --json-output data/ragas_input.json
python lab.py compare '보고서들을 종합해 생성형 AI가 요구하는 핵심 반도체 기술과, 한국이 우선 강화해야 할 분야를 설명하시오' --json-output data/integrated_input.json
```

같은 질문의 Dense, BM25, RRF 결합, Reranker 결과 상위 5개를 비교합니다. **검색 결과의 순위가 반드시 강의 슬라이드의 예시처럼 바뀌는 것은 아닙니다.** 특히 BM25는 기본 토큰화를 사용하므로 한국어 형태소 분석기를 연결하면 결과가 달라질 수 있습니다.

`--json-output`은 각 단계의 질문과 검색 문맥을 JSON에 저장합니다. `response`는 비워 둡니다. 아래 평가 스크립트가 같은 GPT-4o mini로 각 단계의 답변을 생성하고 RAGAS 세 지표를 계산합니다. 강의 참고자료에는 RAGAS 실행 코드가 없어 별도로 작성했습니다.

## GPT 답변 생성 + RAGAS 평가

RAGAS와 검색용 라이브러리의 의존성 버전이 달라 평가에는 별도 가상환경을 사용합니다. 검색 결과 JSON을 먼저 만들어 두세요. 이미 `data/ragas_input.json`이 있다면 `compare`를 다시 실행할 필요는 없습니다.

```bash
python3.11 -m venv .ragas-venv
.ragas-venv/bin/python -m pip install -r requirements-ragas.txt
cp .env.example .env
```

`.env`의 `your_api_key_here`를 본인의 OpenAI API 키로 바꾸세요. `.env`는 Git 제외 대상입니다. 이 파일의 키가 터미널에 설정된 `OPENAI_API_KEY`보다 우선합니다. **키를 넣는 것만으로 API가 호출되지는 않습니다.**

```bash
.ragas-venv/bin/python ragas_eval.py --dry-run
.ragas-venv/bin/python ragas_eval.py
.ragas-venv/bin/python ragas_eval.py --input data/integrated_input.json --output data/integrated_results.json
```

`--dry-run`은 입력 행만 확인하고 API를 호출하지 않습니다. 실제 실행은 Dense·Hybrid·Reranker 각 문맥 5개로 짧은 답변을 만들고 Faithfulness, Answer Relevancy, Context Precision without reference를 계산합니다. 결과 JSON(`data/ragas_results.json`)에는 답변과 점수만 저장합니다. 호출별 토큰과 비용 기록은 파일에 남기지 않습니다. 중단 후 같은 명령을 다시 실행하면 완료한 답변과 지표를 건너뜁니다. 입력 JSON을 바꾼 경우 다른 `--output` 경로를 지정하세요.

기본 비용 검사 기준은 `$0.10`이며 `--max-cost-usd 0.05`처럼 바꿀 수 있습니다. **상한은 현재 실행에서만 적용되며 재실행하면 0부터 다시 계산합니다.** API 작업 사이에 검사하므로 마지막 호출 비용만큼 초과할 수 있습니다. 현재 일반 요금인 GPT-4o mini 입력 $0.15/백만 토큰·출력 $0.60/백만 토큰, text-embedding-3-small 입력 $0.02/백만 토큰으로 예상 비용을 계산합니다. 가격이 바뀌면 `ragas_eval.py` 상단의 단가도 업데이트해야 합니다. 답변 생성은 최대 300토큰, 평가 호출은 최대 900토큰으로 제한하고 OpenAI SDK의 자동 재시도는 끕니다. RAGAS가 잘못된 JSON 응답을 다시 요청하거나 응답을 받기 전에 연결이 끊기면 표시된 비용이 실제 청구액과 다를 수 있습니다.

## 제출 자료

실습 1 검색·필터 결과, 실습 2 단계별 비교, HBM 및 통합 질문 RAGAS 검증, RAG 설정 시 고려 사항은 [Notion 실습보고서](https://app.notion.com/p/eunnbibi/db-3f20587e551f80798d3acb5163a932b8)에 정리했습니다. 터미널 실행 화면을 직접 추가할 수 있도록 캡처 자리를 3곳 표시했습니다. 제출 ZIP에는 코드·의존성 목록·README·실행 결과·사용한 PDF 5개와 Notion 보고서 링크를 포함하고, `.env`·가상환경·모델 캐시·임베딩 배열·FAISS 인덱스는 포함하지 않습니다. ZIP을 새 위치에서 풀어 재실행하려면 `ingest`부터 실행하세요.
