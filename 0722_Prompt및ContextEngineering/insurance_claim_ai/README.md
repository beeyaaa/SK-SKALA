# 보험사고 검토 AI

## 구성

- `main.py`: 담당자 자연어 입력 및 전체 워크플로 실행
- `build_index.py`: 판례·법률·약관 PDF 임베딩 및 Vector DB 생성
- `src/agents/`: 입력 구조화, 판례·법률 Agent, 고객 조회, 약관 검색, 리포트
- `src/orchestrator.py`: Agent와 업무 모듈 실행 순서
- `src/pdf_parsers.py`: 판례·법률·약관 PDF 구조화
- `src/vector_store.py`: 임베딩과 Chroma 검색
- `data/`: 판례·법률 PDF와 고객 CSV

```text
data/
├── customers.csv
├── contracts.csv
├── coverages.csv
├── accident_history.csv
├── case_law.pdf
├── laws.pdf
└── Sample_Automobile_Insurance_Policy_Terms.pdf
```

## 실행

`.env`의 `OPENAI_API_KEY=` 뒤에 API 키를 입력합니다.

```bash
python -m pip install -r requirements.txt
python build_index.py
python main.py
```

`main.py`를 실행하면 담당자가 다음 내용을 직접 입력합니다.

1. 사고 접수번호
2. 고객 ID (`C1024`로 테스트)
3. 자연어 사고 설명

사고 설명은 여러 줄로 붙여넣을 수 있습니다. 마지막 줄을 입력한 후
빈 줄에서 Enter를 한 번 더 누르면 분석이 시작됩니다.

예시:

```text
고객 김민수는 2026년 7월 24일 강남구 테헤란로에서 2차로를
진행하다 급하게 유턴을 시도했고, 뒤에서 1차로를 따라오던
오토바이와 충돌했습니다. 제한속도는 시속 70km였으며 상대
오토바이는 블랙박스 분석상 약 112km로 주행했습니다.
고객 차량 예상 수리비는 400만원이고 상대 오토바이 예상
수리비는 800만원입니다. 고객 차량은 좌측 전방이 파손됐고
블랙박스가 있습니다. 인명피해는 현재까지 확인되지 않았습니다.
```

결과는 담당자 검토용 초안이며 과실비율이나 보험금을 자동 확정하지 않습니다.
예상 지급액은 LLM이 아닌 Python 계산 코드가 판례 참고 과실비율과
`coverages.csv`의 담보·가입금액·자기부담금 데이터를 적용해 계산합니다.
보험약관은 조항 단위로 `vector_db/terms`에 저장하며, 제6조·제9조·
제10조·제16조의 산식과 한도·자기부담금을 지급액 계산에 적용합니다.

기본 터미널 출력은 구성요소별 핵심 결과와 최종 결론만 표시합니다.
디버깅을 위해 전체 JSON이 필요하면 `.env`에 다음 값을 추가합니다.

```env
VERBOSE_RESULTS=true
```
