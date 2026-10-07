# 🦜 생성형 AI 서비스 개발의 이해·활용 (LangChain) 완전 정리

> 💡 **한 줄 요약** — LLM 기반 서비스는 "확률적으로 답하는 시스템"이라 전통 개발과 근본이 다르고, LangChain은 이 불확실한 LLM을 **표준 인터페이스(Runnable)** 위에 올려 프롬프트·모델·파서·도구·검색을 **파이프(`|`)로 조립**할 수 있게 만든 프레임워크다.

**출처**: `5_생성형 AI 서비스 개발의 이해 활용 (LangChain).pdf` (총 162페이지, 2026.09, SK AX)

**범위**: 전체 162p — LLM 서비스 개발론부터 LangChain 컴포넌트, Integration, Runnable 내부 구조, Gradio UI까지

---

## 📑 목차

| # | 챕터 | 핵심 질문 | 슬라이드 |
|---|---|---|---|
| 1 | LLM 기반 AI 서비스 개발 | 기존 개발과 뭐가 다르고, 왜 어려운가? | p3~p18 |
| 2 | LangChain 컴포넌트 | LangChain은 무엇을 조립해 서비스를 만드는가? | p19~p82 |
| 3 | Integrations | 외부 모델·DB·도구를 어떻게 연결하는가? | p83~p137 |
| 4 | Runnable의 이해 | 파이프 연산자 뒤에서 실제로 무슨 일이 일어나는가? | p138~p157 |
| 5 | AI 서비스 개발을 위한 UI (Gradio) | 만든 체인을 어떻게 화면에 붙이는가? | p158~p162 |
| ★ | 전체 흐름 한 장 요약 | — | — |
| ★ | 시험/면접 대비 핵심 문답 | — | — |

> ⚠️ Notion에서는 목차 클릭 이동을 위해 이 표 아래에 네이티브 **목차(Table of contents) 블록**을 하나 추가하세요. 마크다운 앵커 링크(`](#제목)`)는 Notion에서 죽은 링크가 됩니다.

---

# 1. LLM 기반 AI 서비스 개발

> 📍 p3~p18 | 전통적 소프트웨어와의 근본적 차이, 실무에서 부딪히는 5대 난관, 그리고 그것을 뚫는 개발 방법론

## 1-1. 기존 IT 서비스 개발과의 핵심 차별점

가장 중요한 전제는 하나다. **전통 SW는 결정론적(Deterministic), LLM 서비스는 확률론적(Probabilistic)이다.**

| 비교 항목 | 기존 IT 서비스 개발 (전통적 SW) | LLM 기반 AI 서비스 개발 |
|---|---|---|
| **시스템 성격** | 결정론적(Deterministic): 동일한 입력에 언제나 동일한 출력 반환 | 확률론적(Probabilistic): 동일한 입력에도 가변적 결과 생성 가능 |
| **핵심 제어 로직** | 명시적 코드(if/else, 알고리즘, 비즈니스 로직 함수) | 자연어 프롬프트, 컨텍스트 엔지니어링, 모델 가중치 |
| **입출력 데이터 형태** | 구조화된 데이터(JSON, SQL 테이블, 원시 타입) | 비정형 자연어 텍스트, 멀티모달 데이터 |
| **테스트 및 검증** | 단위 테스트(Unit Test)를 통한 참/거짓 및 상태 검증 | 벤치마크 평가, LLM-as-a-Judge, 의미론적 유사도 검증 |

> ⭐ **핵심** — "코드로 로직을 짠다"가 아니라 "프롬프트와 컨텍스트로 **행동을 유도한다**"로 제어 패러다임이 바뀐다. 그래서 테스트도 `assert result == 42`가 아니라 "이 답이 충분히 좋은가?"를 **다른 모델에게 채점시키는** 방식이 된다.

## 1-2. LLM 기반 AI 서비스 개발의 주요 어려움

강의는 어려움을 **5개 축**으로 나눈다.

### ① 비결정론적 특성과 출력 제어의 한계

- **환각(Hallucination)**
  - 모델이 사실과 다른 내용을 그럴듯하게 생성하는 현상은 **완전히 제거하기 어려움**
  - RAG 파이프라인의 검색 정확도(Retrieval Accuracy)가 높더라도 **파싱 및 추론 단계에서 왜곡**이 발생할 수 있음
- **스키마 강제성 불안정**
  - JSON 모드나 구조화된 출력(Structured Outputs)을 사용하더라도, 예외적인 프롬프트나 장문 컨텍스트에서는 구문 오류(Syntax Error)나 스키마 불일치가 **간헐적으로** 발생
- **프롬프트 드리프트(Prompt Drift)**
  - 상용 파운데이션 모델(OpenAI, Anthropic 등)의 **버전 업데이트나 미세 조정**에 따라, 기존에 잘 동작하던 프롬프트가 예기치 않게 오작동할 위험

### ② 정량적 평가 및 CI/CD 구축의 난해함

- **단순 Pass/Fail 테스트 불가**
  - "답변이 유용한가?", "톤앤매너가 적절한가?", "문맥을 충실히 반영했는가?" 같은 **정성적 요소**를 자동화된 파이프라인으로 측정하기 어려움
- **평가 프레임워크 구축 비용**
  - 기존 NLP 메트릭의 한계로 인해 고성능 모델을 평가자로 쓰는 **LLM-as-a-Judge**, Faithfulness/Answer Relevance 등을 평가하는 **RAGAS** 프레임워크 등을 도입해야 하며, 이 과정 자체에 추가 비용과 레이턴시가 발생

### ③ 지연 시간(Latency) 및 인프라 비용 트레이드오프

- **추론 시간의 물리적 한계**
  - 일반 REST API가 수십~수백 밀리초 단위로 응답하는 반면, LLM 추론은 **토큰 수와 디코딩 속도**에 따라 수 초에서 수십 초 소요
  - 이를 해결하기 위해 **서버 전송 이벤트(SSE) 기반 스트리밍 UI 설계**와 **비동기 큐 처리**가 필수
- **운영 비용 예측의 불안정성**
  - 사용자 트래픽의 단순 호출 횟수가 아니라 **'입출력 토큰 총량'**에 따라 과금되므로, 프롬프트 최적화 실패나 **무한 루프 에이전트** 발생 시 비용이 기하급수적으로 폭증

### ④ 보안 및 신뢰성(Safety) 취약점

- **프롬프트 인젝션(Prompt Injection)**
  - 시스템 지침을 무력화하거나 비인가 데이터를 탈취하려는 사용자 입력(**간접 인젝션** 포함)을 기존 방화벽이나 정규식만으로 원천 차단하기 어려움
- **데이터 프라이버시 및 거버넌스**
  - 사용자 입력에 포함된 개인정보(PII)의 외부 API 전송 통제, 기업 내부 기밀 데이터의 모델 학습 격리, 인메모리 컨텍스트 누출 방지 등 거버넌스 설계가 복잡

### ⑤ 복잡해진 복구/디버깅(Observability)

- 전통적인 버그는 **스택 트레이스**를 추적해 코드 라인을 특정할 수 있음
- LLM 서비스의 오류는 "어떤 검색 청크가 주입되었는지", "토큰화 과정에서 손실이 있었는지", "시스템 프롬프트의 어떤 제약이 모델 추론을 왜곡했는지" **복합적인 요인**으로 발생
- **전방위적인 트레이싱 도구(LangSmith 등) 없이는 근본 원인 분석이 매우 어려움**

```plain text
전통 SW 디버깅            LLM 서비스 디버깅
─────────────            ────────────────────────────
에러 발생                 "답이 이상함"
   ↓                         ↓
스택 트레이스              어디가 문제?
   ↓                      ├─ 검색된 청크가 틀렸나?
코드 라인 특정             ├─ 토큰화에서 잘렸나?
   ↓                      ├─ 시스템 프롬프트 제약 탓인가?
수정                      └─ 모델 버전이 바뀌었나?
                             ↓
                          트레이싱(LangSmith) 없으면 추측만 반복
```

## 1-3. LLM 기반 AI 서비스 개발 방법론

LLM 기반 AI 서비스 개발은 고정된 로직을 작성하는 전통적 워크플로우와 달리, **프롬프트 · 데이터 증강 · 모델 튜닝 간의 상호작용 및 지속적 평가**를 중심으로 진행된다.

### ① 문제 정의 및 아키텍처 스펙트럼 선택

요구사항의 복잡도, 데이터 도메인의 폐쇄성, 비용 및 레이턴시 제약을 고려하여 최적의 기술 방식을 결정한다.

| 방식 | 언제 쓰는가 | 핵심 |
|---|---|---|
| **Prompt Engineering** | 기본 모델 능력으로 충분할 때 | 인컨텍스트 러닝(In-context Learning)을 활용한 **제로샷/퓨샷** 설계 |
| **RAG** (Retrieval-Augmented Generation) | 실시간 데이터·최신 지식·사내 보안 문서가 필요할 때 | 검색 인덱스에서 조회하여 **컨텍스트에 주입** |
| **Fine-Tuning** | 특정 말투(Tone & Manner), 고정된 JSON 출력 스키마, sLLM의 전문 도메인 지식 내재화가 필요할 때 | 모델 가중치 자체를 조정 |
| **AI Agent** | 단일 응답을 넘어 여러 단계를 스스로 밟아야 할 때 | 도구 호출(Tool Calling), 다단계 계획(Planning), 분기 및 루프(Loop)를 통한 목표 달성형 구조 |

> 💡 **팁** — 이 4가지는 배타적 선택지가 아니라 **스펙트럼**이다. 실무에서는 "RAG + 프롬프트 엔지니어링 + 가벼운 Agent"처럼 겹쳐 쓰는 경우가 대부분이다.

### ② 데이터 엔지니어링 및 파이프라인 구축

- **정형/비정형 데이터 가공**: PDF, 마크다운, DB 레코드 등의 텍스트 **청킹(Chunking)** 및 노이즈 제거
- **임베딩 및 인덱싱**: 도메인 적합 임베딩 모델 선정, 메타데이터 필터링 구조 설계, 벡터 DB(Vector DB) 및 키워드 기반 **하이브리드 검색(Hybrid Search)** 적용

### ③ 관측 가능성(Observability) 및 컨텍스트 제어

- **입출력 모니터링**: 시스템 프롬프트, 도구 실행 결과, 사용자 입력을 **단계별로 추적하는 트레이싱** 구축 (LangSmith 등)
- **컨텍스트 윈도우 관리**: 대화 세션 누적에 따른 토큰 초과 방지, 동적 청크 필터링, 대화 요약(Summarization) 기법 적용

### ④ LLMOps 및 정량적 평가(Evaluation)

- **골든 데이터셋(Golden Dataset) 구축**: 도메인별 표준 질의응답 세트 구성
- **다계층 평가 지표 도입**: 단순 구문 일치(BLEU/ROUGE)를 넘어 **답변 충실도(Faithfulness)**, **관련성(Answer Relevance)**, 환각 여부를 검증하는 **RAGAS 메트릭** 및 **LLM-as-a-Judge** 파이프라인 구성
- **회귀 테스트 자동화**: 프롬프트나 인덱싱 전략 수정 시 기존 평가 세트에 미치는 영향을 지속 검증하는 **CI/CD 통합**

## 1-4. 주요 개발 Framework별 장단점

| Framework | 주 용도 및 핵심 개념 | 장점 | 단점 |
|---|---|---|---|
| **LangChain** | 범용 LLM 오케스트레이션 (Chains, LCEL) | • 방대한 생태계 및 모델/DB/도구 연동 컴포넌트 보유<br>• 빠른 프로토타이핑 및 다양한 통합 기능 | • 과도한 추상화 레이어로 인한 내부 디버깅 난이도 증가<br>• 복잡한 다단계 에이전트 제어의 한계 |
| **LangGraph** | 상태 기반 순환 에이전트 (Directed Graph, State Machine) | • 노드/엣지 기반의 명시적 분기 및 루프 제어 용이<br>• 영속성(Persistence)과 체크포인트를 통한 휴먼인더루프(Human-in-the-loop) 구현 탁월 | • 상태 정의 및 그래프 모델링에 따른 초기 학습 곡선 존재<br>• 단순 선형 체인 구현에는 오버엔지니어링 가능성 |
| **LlamaIndex** | 데이터 수집/인덱싱 및 심층 RAG (Data Ingestion, Workflows) | • 고급 청킹 전략, 계층형 인덱스 등 데이터 연동에 특화<br>• 구조화/비구조화 데이터를 LLM과 결합하는 RAG 성능 우수 | • 비즈니스 로직 및 범용 다중에이전트 오케스트레이션 기능은 상대적으로 보조적<br>• 프레임워크 자체의 API 변화 빈도 |
| **CrewAI** | 역할 기반 멀티 에이전트 협업 (Role, Task, Crew) | • 직관적인 페르소나 설정 및 빠른 협업 워크플로우 구성<br>• 역할 분담 기반의 작업(조사, 요약, 검수 등) 구현 용이 | • 에이전트 간 불필요한 토큰 소모 및 호출 루프 발생 위험<br>• 미세한 상태 조건 제어 및 엄격한 결정론적 분기 처리 제약 |
| **각 Vendor의 전용 SDK** (OpenAI, Google 등) | 특정 Vendor의 Model 사용 시 최적화 | • 자사 모델 사용에 최적화<br>• 자사 타 제품군과의 연동 시 편리함, 호환성 등 | • 모델 변경 시 구현 변경 어려움 |

### 🖍️ 프레임워크 선택 가이드라인

- **RAG 파이프라인의 완성도 및 데이터 커넥터가 핵심인 경우**: LlamaIndex를 중심으로 파이프라인을 설계하고 인덱싱 품질을 극대화하는 방식이 적합
- **상태 제어, 오류 복구, 사용자 승인 단계가 필요한 복잡한 에이전트인 경우**: LangGraph를 도입하여 명시적 그래프 구조로 워크플로우를 통제하는 방식이 유리
- **문서 요약, 리서치, 보고서 작성 등 분업화된 역할 수행인 경우**: CrewAI를 활용해 빠른 프로토타입을 제작하는 방식이 효과적
- **현업 프로덕션 아키텍처의 일반적 패턴**: 단일 프레임워크에 종속되기보다 **LangChain + LangGraph**(상태 관리 및 오케스트레이션) 형태의 하이브리드 조합, 또는 모델 네이티브 Tool Calling API와 경량 오케스트레이터를 혼합하는 방식을 널리 활용

## 1-5. 주요 AI 플랫폼

| 플랫폼 | 설명 | 실습 포인트 |
|---|---|---|
| **Hugging Face** | 300만 개 이상의 모델과 100만 개 이상의 데이터셋을 서비스 중인 **최대의 AI Hub 사이트** | 모델/데이터셋 탐색, Spaces |
| **OpenAI** | Developer quickstart, API Key 발급 및 환경변수 등록 | Chat Model, TTS 기능, Embedding 테스트 |
| **Google GenAI** | Gemini API 문서 (Python/JavaScript/REST) | 생성형 AI, 대화 생성 테스트 |

> ⚠️ **주의** — API Key는 `.zshrc` 같은 환경변수 파일에 넣고 `export OPENAI_API_KEY="..."` 형태로 관리한다. 코드에 하드코딩하면 유출 사고로 직결된다.

---

# 2. LangChain 컴포넌트

> 📍 p19~p82 | LangChain의 패키지 구조부터 Model·Messages·Prompt·Memory·Streaming·Structured Output·LCEL·Agent·Tools까지 9개 기본 컴포넌트 전부

## 2-1. LangChain Introduction — 패키지 구조

LangChain은 **하나의 라이브러리가 아니라 여러 패키지의 계층**이다.

| 패키지 | 무엇이 들어있나 | 특징 |
|---|---|---|
| **langchain** | 애플리케이션의 **인지 구조(cognitive architecture)**를 구성하기 위한 체인과 추출 전략 | • 제3자(third-party) 통합체는 **아님**<br>• 모든 체인·에이전트·추출 전략은 특정 통합체에 속하지 않는 **모든 통합체의 일반적인 것**에 해당 |
| **langchain-core** | chat models, vector stores, tools 같은 **핵심 컴포넌트를 위한 인터페이스를 정의** | • 제3자 통합체가 정의되지는 않음<br>• 의존성은 **경량으로 유지** |
| **langchain-\<provider\>** | 대중적인 통합체별 **자체 패키지** | 적절한 버전관리와 경량화를 위해 분리 (e.g. `langchain-openai`, `langchain-anthropic` 등) |

### Integrations — 왜 이렇게 나눴는가

- **LangChain = 다양한 AI 서비스와 도구를 연결하는 통합 생태계**
- **Provider = AI 모델을 제공하는 회사 또는 플랫폼**
- `langchain-<provider>` 패키지를 통해 각 provider를 LangChain 방식으로 연결
- 표준 인터페이스 덕분에 **OpenAI → Anthropic → Google** 처럼 provider를 쉽게 교체 가능
- **핵심 장점: provider가 달라도 코드 구조를 일관되게 유지할 수 있음**

```plain text
LangChain 생태계 전체 지도
────────────────────────────────────────────────────
[Deployment]  LangGraph Platform  (COMMERCIAL)  ┐
                                                 │  LangSmith
[Components]  Integrations        (OSS)          │  (COMMERCIAL)
                                                 │  ├ Debugging
[Architecture] LangChain (OSS)  LangGraph (OSS)  ┘  ├ Playground
                                                    ├ Prompt Management
                                                    ├ Annotation
                                                    ├ Testing
                                                    └ Monitoring
```

## 2-2. LangChain 기본 컴포넌트 9종 (한눈에)

LangChain은 다음의 컴포넌트들을 **조합해** AI 서비스를 만드는 프레임워크다.

| 컴포넌트 | 한 줄 정의 |
|---|---|
| **Chat Model** | LangChain에서 다양한 LLM을 다루는 표준 인터페이스 |
| **Messages** | 대화를 구성하는 메시지 객체 체계 |
| **Prompt Template** | LLM을 위한 Prompt 생성 |
| **Short-term memory** | 단일 세션 내 대화 기억 |
| **Streaming** | 실시간 응답 처리 방식 |
| **Structured Output** | 정형화된 형식으로 답변 받기 |
| **LCEL** | 컴포넌트를 연결하는 표현식 |
| **Agent** | 스스로 판단하여 행동하는 LLM 기반 실행 단위 |
| **Tools** | LLM이 외부 기능을 호출하도록 돕는 도구 |

---

## 2-3. Model — LLM을 부르는 표준 창구

### 핵심 개념

| | |
|---|---|
| **비유로 말하면** | 어느 나라 콘센트에 꽂아도 작동하는 **멀티 어댑터**. 기기(모델)가 바뀌어도 플러그(코드)는 그대로. |
| **정확히 말하면** | LangChain에서 LLM을 호출하는 **표준화된 인터페이스**. OpenAI, Anthropic, Google 등 다양한 제공사의 모델을 동일한 방식으로 사용. |

- `init_chat_model` 함수로 **모델 문자열만 바꿔** 손쉽게 교체 가능
- 온도(temperature), 최대 토큰 등 생성 파라미터 설정 가능
- Chat 모델과 완성형(Completion) 모델로 구분되며, **현재는 Chat 모델이 표준**

### Model 인터페이스의 장점

- 특정 벤더에 종속되지 않는 **벤더 중립적 설계**
- 모델 교체 시 비즈니스 로직 코드를 거의 수정하지 않아도 됨
- **Runnable 인터페이스를 공유**해 체인(Chain) 구성에 바로 활용 가능
- 동기(sync)와 비동기(async) 호출을 모두 지원
- 재시도(retry), 캐싱 등 부가 기능도 표준 인터페이스로 제공

### Model 파라미터

| 파라미터 | 설명 |
|---|---|
| `temperature` | 답변의 창의성/무작위성 조절 (0~2) |
| `max_tokens` | 생성할 최대 토큰 수 |
| `top_p` | 확률 분포 상위 비율만 고려 |
| `model` | 사용할 모델 이름 |

- **temperature가 낮을수록** 일관되고 보수적인 답변
- **temperature가 높을수록** 다양하고 창의적인 답변

### 실습: Model 초기화

```python
from langchain.chat_models import init_chat_model

model = init_chat_model(
    "gpt-4",
    model_provider="openai",
    temperature=0.7
)

response = model.invoke("LangChain의 장점을 설명해줘")
print(response.content)
```

### 실습: 다양한 모델 교체

```python
# OpenAI 모델
model_openai = init_chat_model("gpt-4", model_provider="openai")

# Google 모델
model_google = init_chat_model("gemini-2.5-flash-lite", model_provider="google_genai")

for m in [model_openai, model_google]:
    print(m.invoke("한 문장으로 자기소개 해줘").content + "\n\n")
```

> ⭐ **핵심** — 이 코드에서 `for m in [...]` 루프가 그대로 도는 것이 LangChain의 존재 이유다. Vendor SDK를 직접 썼다면 두 모델의 호출 코드가 완전히 달랐을 것이다.

### 💡 Model 활용 팁

- 프로토타입 단계에서는 **저렴하고 빠른 모델**로 먼저 검증
- 정확도가 중요한 단계에서는 **고성능 모델로 전환**
- 반복 호출이 많은 서비스는 **캐싱(Caching)**으로 비용 절감
- 모델별 강점(추론, 코드, 멀티모달 등)을 파악해 목적에 맞게 선택

---

## 2-4. Messages — 대화의 최소 단위

### 핵심 개념

- **Messages**: LLM과의 대화를 구성하는 **표준화된 메시지 객체**
- **역할(role)**에 따라 여러 종류로 구분됨

| 메시지 타입 | 역할 |
|---|---|
| **SystemMessage** | 모델의 페르소나, 규칙 지정 |
| **HumanMessage** | 사용자 입력 |
| **AIMessage** | 모델의 응답 (Tool 호출 포함 가능) |
| **ToolMessage** | 도구 실행 결과 반환 |

- 메시지들은 **리스트 형태로 순서대로** 모델에 전달됨
- **이 순서가 곧 대화의 문맥(Context)을 형성**

### 실습: Messages 활용

```python
from langchain_core.messages import SystemMessage, HumanMessage

messages = [
    SystemMessage(content="당신은 친절한 프로그래밍 튜터입니다."),
    HumanMessage(content="파이썬 리스트와 튜플의 차이를 알려줘")
]

response = model.invoke(messages)
print(response.content)
```

### AIMessage와 Tool 호출

- `AIMessage`는 단순 텍스트뿐 아니라 **`tool_calls` 정보를 포함**할 수 있음
- 모델이 도구 호출이 필요하다고 판단하면 `tool_calls` 필드에 호출 정보 기록
- 이후 해당 도구를 실행하고 결과를 **`ToolMessage`로 다시 전달**
- 이 과정이 반복되며 **Agent의 사고-행동 루프**가 형성됨

```python
print(response.tool_calls)
# [{'name': 'get_weather', 'args': {'city': '서울'}, 'id': 'call_123'}]
```

### 실습: 대화 흐름 구성 (멀티턴)

```python
conversation = []
conversation.append(SystemMessage(content="당신은 요리 전문가입니다."))
conversation.append(HumanMessage(content="김치찌개 레시피 알려줘"))

response = model.invoke(conversation)
conversation.append(response)

conversation.append(HumanMessage(content="더 맵게 하려면?"))
response2 = model.invoke(conversation)
print(response2.content)
```

> ⭐ **핵심** — "더 맵게 하려면?"이라는 **지시어만으로 된 질문**이 통하는 이유는, 앞선 메시지 전부를 리스트로 다시 보냈기 때문이다. LLM 자체는 **상태가 없다(stateless).**

### ⚠️ Messages 관리 시 유의점

- 메시지 리스트가 길어지면 **Context Window 제한**에 유의
- 시스템 메시지는 대화 전체에 영향을 주므로 **신중하게 설계**
- **사용자별/세션별로 메시지 기록을 분리 관리**해야 함
- 메시지 직렬화(JSON 변환) 시 **타입 정보 손실**에 주의

---

## 2-5. Prompt Template — 프롬프트를 코드에서 분리하기

### 핵심 개념

| | |
|---|---|
| **비유로 말하면** | 빈칸만 채우면 되는 **계약서 양식**. 매번 처음부터 쓰지 않는다. |
| **정확히 말하면** | 변수만 바꿔가며 재사용할 수 있는 **프롬프트 틀(템플릿)**. 중괄호 변수(`{}`)로 자리표시. |

- 매번 프롬프트 문자열을 직접 조합하지 않고, 중괄호 변수(`{}`)로 자리표시
- 사용자 입력, 검색 결과 등 동적인 값을 템플릿에 끼워 넣어 완성된 프롬프트 생성
- LangChain의 `ChatPromptTemplate`, `PromptTemplate` 클래스로 구현
- **프롬프트를 코드와 분리해 관리할 수 있어 유지보수성이 크게 향상**
- 여러 개발자가 동일한 프롬프트 품질을 유지하도록 돕는 **표준화 도구**

### 두 가지 템플릿

- **PromptTemplate**: 단일 문자열 기반의 단순 템플릿 (완성형 모델용)
- **ChatPromptTemplate**: 여러 메시지(System/Human/AI)로 구성된 템플릿 (**Chat 모델 표준**)
- 템플릿 내 변수는 `{variable_name}` 형태로 작성
- `.invoke()` 또는 `.format()`에 딕셔너리를 전달해 변수 값을 채움
- System 메시지를 템플릿 안에 고정해 모델의 역할/톤을 일관되게 유지 가능

| 구성 요소 | 역할 |
|---|---|
| **System 부분** | 모델의 페르소나, 규칙 지정 |
| **Human 부분** | 사용자 입력이 들어가는 자리 |
| **변수(`{}`)** | 실행 시점에 채워지는 동적 값 |

### 실습: Prompt Template 기본

```python
from langchain_core.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_messages([
    ("system", "당신은 {role} 전문가입니다. 친절하고 간결하게 답변하세요."),
    ("human", "{question}")
])

formatted = prompt.invoke({"role": "영양", "question": "다이어트에 좋은 저녁 메뉴 추천해줘"})
print(formatted.to_messages())
# [SystemMessage(content='당신은 영양 전문가입니다. 친절하고 간결하게 답변하세요.', ...),
#  HumanMessage(content='다이어트에 좋은 저녁 메뉴 추천해줘', ...)]
```

### 💡 Prompt Template 작성 팁

- **변수명은 의미가 명확하게 드러나도록** 작성 (`{q}` 보다 `{question}`)
- System 메시지에는 **역할, 톤, 제약 조건**을 구체적으로 명시
- 자주 쓰는 템플릿은 **별도 파일/모듈로 분리**해 재사용성 확보
- **템플릿 변경 이력을 관리**해 프롬프트 품질을 지속적으로 개선

---

## 2-6. Short-term memory — 세션 내 대화 기억

### 핵심 개념

- **Short-term memory**: 하나의 대화 세션 내에서 **이전 메시지를 기억**하는 기능
- 사용자가 이전에 한 말을 참고해 일관된 대화 유지
- **세션이 종료되거나 초기화되면 사라지는 일시적 기억**
- 장기 기억(Long-term memory)과 구분되는 개념

### 왜 필요한가

- 메모리가 없으면 매 요청마다 **문맥 없는 독립적인 대화**가 됨
- "그거 다시 설명해줘"와 같은 **지시어(대명사) 이해 불가**
- 멀티턴 대화형 서비스(챗봇 등)에는 **필수적인 기능**
- 다만 **무제한 저장 시 Context Window 초과** 문제 발생 가능

### 구현 방식

- **메시지 리스트 누적**: 가장 단순한 방식, 모든 메시지를 계속 추가
- **Checkpointer 기반 상태 저장**: LangGraph에서 세션별 상태를 자동 저장
- **Thread ID**: 각 대화 세션을 구분하는 고유 식별자
- 동일한 Thread ID로 호출하면 이전 대화 상태를 불러와 이어감

```python
config = {"configurable": {"thread_id": "user-123"}}
```

### 실습: Short-term memory

```python
from langgraph.checkpoint.memory import InMemorySaver
from langchain.agents import create_agent

checkpointer = InMemorySaver()
agent = create_agent(model=model, tools=[], checkpointer=checkpointer)

config = {"configurable": {"thread_id": "session-1"}}

agent.invoke({"messages": [{"role": "user", "content": "내 이름은 민준이야"}]}, config)
result = agent.invoke({"messages": [{"role": "user", "content": "내 이름이 뭐라고 했지?"}]}, config)
print(result["messages"][-1].content)
# 당신의 이름은 민준이라고 말씀하셨습니다.
```

### ⚠️ 메모리 관리 시 주의점

- **세션별 메모리를 적절히 분리하지 않으면 다른 사용자 정보가 섞일 위험**
- 저장된 메모리가 커지면 **비용과 지연시간 증가**
- 민감 정보(개인정보 등)는 메모리 저장 시 **보안 고려 필요**
- 필요 시 오래된 메시지를 **요약하거나 삭제하는 정책** 수립

### 실무 적용 사례

- **고객 상담 챗봇**: 세션 내내 고객의 문의 이력 기억
- **개인 비서 AI**: 사용자의 선호와 이전 요청 기억
- **교육용 챗봇**: 학생의 이전 질문 수준을 파악해 난이도 조절

---

## 2-7. Streaming — 체감 속도를 바꾸는 기술

### 핵심 개념

- **Streaming**: 모델의 응답을 한 번에 받지 않고 **토큰 단위로 순차 전달받는 방식**
- 사용자는 답변이 생성되는 과정을 실시간으로 확인 가능 (**ChatGPT의 타이핑 효과**)
- 긴 답변일수록 **체감 응답 속도가 크게 개선**됨
- LangChain에서는 `stream()` 메서드로 간단히 구현

### 왜 필요한가

- 전체 응답 생성까지 기다리면 긴 대기 시간 발생
- 스트리밍을 사용하면 **첫 토큰이 도착하는 즉시 화면에 표시** 가능
- 사용자 경험(UX) 측면에서 매우 중요한 기능
- 챗봇, 실시간 협업 도구 등에서 **표준적으로 사용됨**

### 실습: 동기 Streaming

```python
for chunk in model.stream("인공지능의 역사를 3문단으로 설명해줘"):
    print(chunk.content, end="", flush=True)
```

### 비동기 Streaming

- `astream()`을 사용하면 비동기 방식으로 스트리밍 처리 가능
- 웹 서버(FastAPI 등)에서 **여러 사용자 요청을 동시에 처리**할 때 유용
- 비동기 스트리밍은 **서버 자원을 효율적으로 활용**

```python
async for chunk in model.astream("파이썬의 장점을 알려줘"):
    print(chunk.content, end="")
```

### ⚠️ Streaming 적용 시 고려사항

- 프론트엔드(UI)에서 **점진적 렌더링 처리** 필요
- **네트워크 연결(WebSocket, SSE 등) 설계** 필요
- 스트리밍 도중 오류 발생 시 **부분 응답 처리 전략** 필요
- **Structured Output과 함께 사용할 때는 파싱 방식에 유의** (JSON이 완성되기 전까지는 파싱 불가)

---

## 2-8. Structured Output — 자유 텍스트를 데이터로

### 핵심 개념

| | |
|---|---|
| **비유로 말하면** | 자유 서술형 답안 대신 **객관식 답안지(OMR 카드)**를 주는 것. 채점(파싱)이 기계적으로 가능해진다. |
| **정확히 말하면** | LLM의 응답을 자유 텍스트가 아닌 **정해진 데이터 구조(JSON, Pydantic 모델)**로 받는 방식. |

- JSON, Pydantic 모델 등 **원하는 스키마에 맞춰 응답 생성**
- 애플리케이션에서 응답을 **파싱 없이 바로 활용 가능**
- `with_structured_output()` 메서드로 간단히 적용

### 왜 필요한가

- 자유 텍스트 응답은 일관된 파싱이 어려움
- 예: `"이름: 홍길동, 나이: 20살"` 형태는 **오타나 순서 변화에 취약**
- 정형화된 출력은 프로그램에서 **바로 필드 단위로 접근 가능**
- **API 연동, 데이터베이스 저장** 등에 필수적인 기능

### 실습: Structured Output

```python
from pydantic import BaseModel

class PersonInfo(BaseModel):
    name: str
    age: int
    job: str

structured_model = model.with_structured_output(PersonInfo)
result = structured_model.invoke(
    "홍길동은 28살이고 개발자로 일하고 있습니다. 정보를 추출해줘"
)

print(result)
print(result.name, result.age, result.job)
# name='홍길동' age=28 job='개발자'
# 홍길동 28 개발자
```

### 내부 동작

- 대부분 **Function Calling(도구 호출) 방식을 내부적으로 활용**
- 지정한 스키마를 하나의 **"도구"처럼 모델에 전달**
- 모델은 텍스트 응답 대신 스키마에 맞는 **구조화된 인자를 반환**
- 일부 모델은 **JSON 모드를 직접 지원**하기도 함

### 활용 사례

- **이력서 파싱**: 자유 형식 이력서에서 이름/경력/기술 스택 추출
- **주문 정보 추출**: 고객 문의에서 상품명/수량/배송지 추출
- **감정 분석**: 텍스트에서 감정 라벨과 신뢰도 점수 추출
- **폼 자동 작성**: 대화 내용을 기반으로 정형 폼 데이터 생성

---

## 2-9. Output Parser / Pydantic / JSON / Schema

Structured Output을 떠받치는 4개의 개념이다.

| 개념 | 역할 |
|---|---|
| **Pydantic** | 데이터 검증과 스키마 정의를 위한 라이브러리 |
| **JSON** | 구조화된 데이터 교환 형식 |
| **Schema** | 응답의 형태를 정의하는 설계도 |
| **Validation** | 생성된 데이터가 규칙에 맞는지 검증하는 과정 |

### Output Parser 개요

- **Output Parser**: LLM의 텍스트 응답을 원하는 데이터 형태로 변환하는 컴포넌트
- 가장 단순한 형태는 `StrOutputParser` (텍스트만 추출)
- 고급 형태는 JSON, Pydantic 객체 등으로 파싱
- **LCEL 체인의 마지막 단계에 주로 위치** (`prompt | model | parser`)

### Pydantic

- **Pydantic**: Python의 데이터 검증 및 설정 관리 라이브러리
- 클래스 기반으로 데이터 구조(스키마)를 정의
- **타입 힌트를 활용해 자동으로 데이터 유효성 검사 수행**
- LangChain의 Structured Output 기능의 **핵심 기반 라이브러리**
- FastAPI 등 다른 유명 프레임워크에서도 널리 사용됨

#### 모델 정의하기

- `BaseModel`을 상속받아 클래스 형태로 데이터 구조 정의
- 각 필드는 타입과 함께 **설명(Field description)**을 추가할 수 있음
- **이 설명은 LLM이 어떤 값을 채워야 하는지 이해하는 데 활용됨** ← 매우 중요

```python
from pydantic import BaseModel, Field

class MovieReview(BaseModel):
    title: str = Field(description="영화 제목")
    rating: int = Field(description="1~5점 사이의 평점")
    summary: str = Field(description="한 줄 감상평")
```

#### 실습: Pydantic + LLM

```python
structured_model = model.with_structured_output(MovieReview)

result = structured_model.invoke(
    "인터스텔라는 정말 감동적이었어요. 5점 만점에 5점 주고 싶어요"
)

print(result)
print(result.title, result.rating, result.summary)
# title='인터스텔라' rating=5 summary='정말 감동적이었어요.'
# 인터스텔라 5 정말 감동적이었어요.
```

#### 필드 검증 기능

- 필드에 **제약 조건(constraint)**을 추가해 값의 범위 제한 가능
- 예: 평점은 반드시 1~5 사이의 값이어야 함

```python
from pydantic import Field

class MovieReview(BaseModel):
    rating: int = Field(ge=1, le=5, description="1~5점 사이의 평점")
```

- **조건을 벗어나는 값이 들어오면 자동으로 오류 발생**

#### 중첩 Pydantic 모델

- Pydantic 모델 안에 다른 Pydantic 모델을 필드로 포함 가능
- 복잡한 구조의 데이터도 **계층적으로 표현 가능**

```python
class Actor(BaseModel):
    name: str
    role: str

class MovieInfo(BaseModel):
    title: str
    actors: list[Actor]
```

### JSON

- **JSON(JavaScript Object Notation)**: 키-값 쌍으로 구성된 **경량 데이터 교환 형식**
- 대부분의 프로그래밍 언어와 API에서 표준으로 사용
- 사람이 읽기 쉬우면서도 프로그램이 파싱하기 쉬운 구조
- LLM의 Structured Output은 **내부적으로 JSON 형태를 거치는 경우가 많음**

```json
{
  "name": "홍길동",
  "age": 28,
  "skills": ["Python", "LangChain"],
  "is_student": false
}
```

- **객체(Object)**: 중괄호 `{}` 로 표현되는 키-값 쌍
- **배열(Array)**: 대괄호 `[]` 로 표현되는 목록
- **값의 타입**: 문자열, 숫자, 불리언, 배열, 객체, null

#### 실습: LLM으로부터 JSON 응답 받기

```python
from langchain_core.output_parsers import JsonOutputParser

parser = JsonOutputParser()
prompt = ChatPromptTemplate.from_messages([
    ("human", "다음의 정보로부터 이름, 나이, 직업을 json 형식으로 추출해줘. {text}")
])

chain = prompt | model | parser

result = chain.invoke({"text": "홍길동, 28세, 개발자입니다"})
print(type(result))   # <class 'dict'>
print(result)
print(result["이름"])
# <class 'dict'>
# {'이름': '홍길동', '나이': 28, '직업': '개발자'}
# 홍길동
```

#### ⚠️ JSON 파싱 시 발생하는 문제

- LLM이 완벽한 JSON 형식이 아닌 텍스트를 생성할 위험 존재 (따옴표 누락 등)
- `JsonOutputParser`는 **일부 형식 오류를 자동으로 보정**하기도 함
- 프롬프트에 "**반드시 JSON 형식으로만 답하라**"는 지시를 명확히 포함하는 것이 중요
- **안전성이 중요한 서비스는 Pydantic 기반 구조화 출력을 우선 권장**

### Schema

- **Schema**: 데이터가 어떤 필드와 타입으로 구성되는지 정의하는 **설계도**
- Pydantic 모델 자체가 하나의 Schema 역할을 수행
- LLM에게 Schema를 전달하면, **해당 구조에 맞춰 응답을 생성하도록 유도**
- JSON Schema는 다양한 언어/도구 간 **공통 표준 형식**으로도 널리 사용됨

```json
{
  "title": "MovieReview",
  "type": "object",
  "properties": {
    "title": {"type": "string", "description": "영화 제목"},
    "rating": {"type": "integer", "description": "1~5점 평점"}
  },
  "required": ["title", "rating"]
}
```

- Pydantic 모델은 `.model_json_schema()` 로 이러한 JSON Schema로 변환 가능
- LangChain은 **내부적으로 이 schema를 Function Calling 형태로 모델에 전달**

```python
schema = MovieReview.model_json_schema()
print(schema)

# LangChain 내부적으로 이 schema가 Function Calling 형태로 모델에 전달됨
structured_model = model.with_structured_output(MovieReview)
```

#### ✅ Schema 설계 Best Practice

- 필드명은 **의미가 명확하게 드러나도록** 작성
- **각 필드에 description을 반드시 추가**해 LLM의 이해를 도움
- 너무 많은 필드보다는 **꼭 필요한 필드만** 포함
- 선택적(Optional) 필드와 필수(Required) 필드를 **명확히 구분**

---

## 2-10. LCEL — 컴포넌트를 잇는 파이프

### 핵심 개념

| | |
|---|---|
| **비유로 말하면** | 리눅스 셸의 `cat file \| grep x \| wc -l`. 앞의 출력이 뒤의 입력으로 자동으로 흐른다. |
| **정확히 말하면** | LCEL(LangChain Expression Language) — LangChain 컴포넌트를 연결하는 **선언적 문법**. |

- Prompt, Model, Parser 등을 **파이프(`|`) 연산자로 순서대로 연결**
- 모든 구성요소가 **Runnable 인터페이스를 공유**해 자유롭게 조합 가능
- `invoke()`, `stream()`, `batch()` 등 동일한 실행 방식을 모든 체인에 그대로 적용 가능
- 복잡한 파이프라인도 **간결한 한 줄 코드로 표현**할 수 있음

### 실습: LCEL 파이프 연산자

```python
from langchain_core.output_parsers import StrOutputParser

chain = prompt | model | StrOutputParser()

result = chain.invoke({"role": "여행", "question": "3박 4일 제주 일정 짜줘"})
print(result)
```

### LCEL의 장점

- **가독성**: `prompt | model | parser` 처럼 **실행 흐름이 코드에 그대로 드러남**
- **재사용성**: 각 단계를 독립적인 컴포넌트로 분리해 다른 체인에서도 재사용 가능
- **일관된 실행 방식**: 어떤 체인이든 동일한 방식(invoke/stream/batch)으로 호출
- **병렬/순차 조합**: RunnableParallel, RunnableSequence와 자유롭게 결합 가능
- **부가 기능 내장**: 재시도(`with_retry`), Fallback(`with_fallbacks`) 등을 손쉽게 적용

---

## 2-11. Agent — 스스로 판단하고 행동하는 LLM

### 핵심 개념

- **Agent**: 주어진 목표를 달성하기 위해 **스스로 판단하고 행동하는 LLM 실행 단위**
- 단순 질의응답과 달리 **여러 단계에 걸쳐 추론과 행동을 반복**
- 필요 시 Tool(도구)을 호출해 외부 정보를 얻거나 작업 수행
- 행동 결과를 **관찰(Observation)**한 뒤 다음 행동을 결정
- LangChain에서는 `create_agent` 등의 API로 손쉽게 구성 가능
- 복잡한 업무 프로세스를 자동화하는 데 활용됨

### 동작 원리 — ReAct 패턴

```plain text
      ┌──────────────────────────────────┐
      │                                  │
      ▼                                  │
 사고(Reasoning) ──→ 행동(Action) ──→ 관찰(Observation)
 "뭘 해야 하지?"    "이 도구 호출"      "결과가 이렇군"
      │                                  │
      └──── 목표 달성 or 최대 반복 도달 ──┘
                       ↓
                      종료
```

- LLM이 "**다음에 어떤 도구를 호출할지**" 스스로 결정
- 도구 실행 결과를 다시 LLM에 전달해 다음 판단에 활용
- 목표 달성 또는 **최대 반복 횟수에 도달하면 종료**
- 이러한 반복 구조를 **ReAct(Reasoning + Acting) 패턴**이라고도 부름

### 실습: LangChain Agent 생성

```python
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

model = ChatOpenAI(model="gpt-4")

def get_weather(city: str) -> str:
    """도시의 날씨 정보를 반환합니다."""
    return f"{city}는 현재 맑음, 22도입니다."

agent = create_agent(model=model, tools=[get_weather])
result = agent.invoke({"messages": [{"role": "user", "content": "서울 날씨 알려줘"}]})
print(result["messages"][-1].content)
# 서울은 현재 맑음 상태이며, 온도는 22도입니다.
```

### ⚠️ Agent 설계 시 고려사항

- **도구 개수**: 너무 많으면 LLM이 도구 선택에 혼란을 겪을 수 있음
- **명확한 도구 설명(docstring)**: LLM이 도구 용도를 이해하는 **핵심 단서**
- **최대 반복 횟수 제한**: 무한 루프 방지
- **에러 처리**: 도구 실행 실패 시 대응 로직 필요
- **비용 관리**: 반복 호출이 많을수록 API 비용 증가

### Agent 활용 사례

- **여행 예약 에이전트**: 항공권 검색 → 호텔 검색 → 예약 순차 처리
- **데이터 분석 에이전트**: 질문 분석 → SQL 생성 → 실행 → 결과 요약
- **코드 수정 에이전트**: 버그 위치 파악 → 코드 수정 → 테스트 실행
- **리서치 에이전트**: 웹 검색 → 정보 취합 → 보고서 작성

---

## 2-12. Tools — LLM의 손과 발

### 핵심 개념

- **Tools**: LLM이 스스로 할 수 없는 작업(계산, 검색, DB 조회 등)을 수행하도록 돕는 함수
- 일반 Python 함수에 **설명(docstring)**을 추가해 도구로 등록
- LLM은 **도구의 이름과 설명을 보고** 호출 여부와 인자를 스스로 결정
- **도구 실행은 개발자의 코드에서 이루어지며, 결과만 LLM에 전달됨**
- LangChain은 `@tool` 데코레이터로 손쉽게 도구를 정의하도록 지원

> ⭐ **핵심** — LLM은 도구를 "실행"하지 않는다. **"이 도구를 이런 인자로 부르라"는 지시(JSON)를 반환할 뿐**이고, 실제 실행은 개발자 코드가 한다. 보안 설계의 출발점이 이 지점이다.

### Tool 정의 방법

- 함수의 **타입 힌트와 docstring이 LLM에게 전달되는 설명 역할**
- 명확하고 구체적인 설명일수록 LLM이 올바르게 호출
- 여러 개의 도구를 리스트로 묶어 Agent/Model에 바인딩
- 도구는 검색, 계산, DB 조회, 외부 API 호출 등 다양한 형태 가능

```python
from langchain_core.tools import tool

@tool
def add_numbers(a: int, b: int) -> int:
    """두 정수를 더한 값을 반환합니다."""
    return a + b
```

### Tool 바인딩과 호출

- `model.bind_tools([...])` 로 모델에 도구 목록을 연결
- 모델은 사용자의 질문에 따라 **도구 호출이 필요한지 판단**
- 필요하다고 판단하면 응답에 `tool_calls` 정보 포함
- 개발자는 이 정보를 바탕으로 실제 함수를 실행하고 결과를 반환

```python
model_with_tools = model.bind_tools([add_numbers])
response = model_with_tools.invoke("3과 5를 더하면?")
print(response.tool_calls)
# [{'name': 'add_numbers', 'args': {'a': 3, 'b': 5}, 'id': 'call_DrXiNx5tIRfjQEzeeSovrmM5', 'type': 'tool_call'}]
```

### 실습: 검색 도구 연결

```python
from langchain_tavily import TavilySearch

search_tool = TavilySearch(max_results=3)

agent = create_agent(model=model, tools=[search_tool, add_numbers])
result = agent.invoke({
    "messages": [{"role": "user", "content": "오늘 서울 날씨와 12+30을 알려줘"}]
})
print(result["messages"][-1].content)
# 오늘 서울의 날씨는 다음과 같습니다:
# - 날씨: 흐리고 한때 비
# - 최저/최고기온: 23℃ / 27℃
# - 강수확률: 60%
# 12와 30을 더하면 42가 나옵니다.
```

### ✅ Tool 설계 Best Practice

- **하나의 도구는 하나의 명확한 기능만** 수행하도록 설계
- **입력 인자는 최소한으로**, 타입은 명확하게 지정
- 실패 가능성이 있는 도구는 **에러 메시지를 반환하도록** 처리
- 민감한 작업(결제, 삭제 등)은 사람의 확인(**Human-in-the-loop**) 단계 추가 고려

---

# 3. Integrations

> 📍 p83~p137 | 외부 모델·도구·인프라·데이터를 LangChain에 붙이는 방법. RAG 5대 구성요소가 여기 다 있다.

## 3-1. Integration 관점에서 바라 본 chat model

LLM 기반 애플리케이션 개발을 위한 LangChain 기본 컴포넌트 중 **가장 기본이 되는 model component**다.

```python
init_chat_model(
    model: str | None = None,
    *,
    model_provider: str | None = None,
    configurable_fields: Literal["any"] | list[str] | tuple[str, ...] | None = None,
    config_prefix: str | None = None,
    **kwargs: Any,
) -> BaseChatModel | _ConfigurableModel
```

| 인자 | 설명 |
|---|---|
| `init_chat_model` | model 제공자와 이름을 통해 초기화 하는 함수 |
| `model` | model 이름 |
| `model_provider` | model 제공자 |
| `configurable_fields` | 설정 가능한 model parameter 지정 |
| `config_prefix` | 설정 가능한 model parameter의 prefix 지정 |
| `**kwargs` | model 생성 시 전달하는 인자 |

### 모델 문자열 표기법 — prefix form을 권장

`model` 인자는 **provider prefix를 붙인 형태**(`'openai:gpt-5.5'`)를 쓰는 것이 권장된다. bare 모델명(`'claude-opus-4-7'`)도 허용되지만 provider 추론은 **best-effort이며 보장되지 않는다.**

```python
gpt_4o_mini = init_chat_model(
    "openai:gpt-4o-mini",     # ← "provider:model" 형태
)

gemini = init_chat_model(
    "google_genai:gemini-2.5-flash-lite",
)
```

**prefix 기반 provider 추론 규칙 (대소문자 무시):**

| 모델 prefix | 추론되는 provider |
|---|---|
| `gpt-...`, `o1...`, `o3...` | openai |
| `claude...` | anthropic |
| `amazon....`, `anthropic....`, `meta....` | bedrock |
| `gemini...` | google_vertexai (다음 major에서 기본값 변경 예정 — `model_provider`로 고정 권장) |
| `command...` | cohere |
| `accounts/fireworks...` | fireworks |
| `mistral...`, `mixtral...` | mistralai |
| `deepseek...` | deepseek |
| `grok...` | xai |
| `sonar...` | perplexity |
| `solar...` | upstage |
| `chatgpt...`, `text-davinci...` | openai (legacy) |

**`model_provider`를 명시적으로 쓰는 것이 나은 경우:**

- provider가 **동적**일 때 (config나 환경변수에서 읽어와서 문자열을 이어붙여야 하는 상황)
- `model`과 `model_provider`를 `configurable_fields`로 **런타임에 독립적으로 교체**하고 싶을 때 (예: 같은 모델명을 다른 호스트로 라우팅)

**지원 값과 필요한 통합 패키지:**

| model_provider | 필요 패키지 |
|---|---|
| `openai` | langchain-openai |
| `anthropic` | langchain-anthropic |
| `azure_openai` | langchain-openai |
| `azure_ai` | langchain-azure-ai |
| `google_vertexai` | langchain-google-vertexai |
| `google_genai` | langchain-google-genai |
| `anthropic_bedrock`, `bedrock`, `bedrock_converse` | langchain-aws |
| `cohere` | langchain-cohere |
| `fireworks` | langchain-fireworks |
| `together` | langchain-together |
| `mistralai` | langchain-mistralai |
| `huggingface` | langchain-huggingface |
| `groq` | langchain-groq |
| `ollama` | langchain-ollama |

> 💡 **팁** — 강의는 **핀 고정된 모델 ID**(`'claude-haiku-4-5-20251001'`)를 움직이는 별칭(`'claude-haiku-4-5'`)보다 선호하라고 권한다. 별칭이 업스트림에서 다른 버전을 가리키게 되면 **프롬프트 드리프트**가 그대로 발생하기 때문이다.

### 내부 구현 — `_BUILTIN_PROVIDERS`

`langchain/libs/langchain_v1/langchain/chat_models/base.py` 를 열어보면 provider 이름 → (패키지, 클래스, 호출자) 매핑 딕셔너리가 그대로 들어있다.

```python
_BUILTIN_PROVIDERS: dict[str, tuple[str, str, Callable[..., BaseChatModel]]] = {
    "anthropic": ("langchain_anthropic", "ChatAnthropic", _call),
    "anthropic_bedrock": ("langchain_aws", "ChatAnthropicBedrock", _call),
    "azure_ai": ("langchain_azure_ai.chat_models", "AzureAIChatModel", _call),
    "google_genai": ("langchain_google_genai", "ChatGoogleGenerativeAI", _call),
    "openai": ("langchain_openai", "ChatOpenAI", _call),
    # ...
}

def _call(cls: type[BaseChatModel], **kwargs: Any) -> BaseChatModel:
    return cls(**kwargs)
```

> ⭐ **핵심** — `init_chat_model`은 마법이 아니라 **문자열 → 클래스 딕셔너리 조회 + 인스턴스화**다. 이 구조를 직접 확인하는 것이 이 슬라이드의 학습 목표였다.

### Chat models 연동

- LangChain은 **수십 개 이상의 Chat model 제공사**를 표준 인터페이스로 지원
- OpenAI, Anthropic, Google, Cohere, **로컬 모델(Ollama)** 등 연동 가능
- 각 제공사별 패키지(`langchain-openai`, `langchain-anthropic` 등) 설치 필요
- `init_chat_model`을 사용하면 **제공사 전환이 코드 한 줄로 가능**
- 멀티모달(이미지, 음성) 입력을 지원하는 모델도 증가하는 추세

```python
from langchain.chat_models import init_chat_model

gpt_4o_mini = init_chat_model("openai:gpt-4o-mini")
gemini = init_chat_model("google_genai:gemini-2.5-flash-lite")

for m in [gpt_4o_mini, gemini]:
    print(m.invoke("오늘 기분이 어때?").content + "\n\n")
```

### Chat models 선택 기준

| 기준 | 설명 |
|---|---|
| **성능** | 추론/코드/멀티모달 능력 수준 |
| **비용** | 토큰당 과금 정책 |
| **지연시간** | 응답 속도 |
| **데이터 정책** | 데이터 학습 활용 여부, 보안 정책 |

- **서비스 목적과 예산에 맞는 모델 선택이 중요**

### Chat models 통합 관리 — 멀티모델 전략

- 여러 모델을 동시에 활용하는 **멀티모델 전략**도 가능
- **간단한 작업은 저렴한 모델, 복잡한 작업은 고성능 모델로 라우팅**
- **Fallback** 설정으로 특정 모델 장애 시 다른 모델로 자동 전환

```python
model_with_fallback = model_primary.with_fallbacks([model_backup])
```

## 3-2. 기타 컴포넌트 (Integration 대상 전체)

- **Tools and toolkits**: 다양한 도구 묶음 연동
- **Middleware, Sandboxes, Backends**: 실행 환경과 흐름 제어
- **Checkpointers**: 상태 저장 및 재개
- **Retrievers, Text splitters, Embedding models, Vector stores**: 검색 기반 응답(**RAG**)의 핵심 구성요소
- **Document loaders**: 다양한 문서 형식을 불러오는 방법

---

## 3-3. Tools and toolkits

- **Toolkit은 관련된 여러 도구를 하나의 묶음으로 제공**
- 예: SQL Database Toolkit, 파일 시스템 Toolkit, Gmail Toolkit
- 각 Toolkit은 해당 도메인에 필요한 도구들을 **미리 구성해 제공**
- 개발자가 도구를 하나하나 정의할 필요 없이 빠르게 활용 가능

| Toolkit | 제공 기능 |
|---|---|
| **SQLDatabaseToolkit** | 테이블 조회, 쿼리 실행 |
| **FileManagementToolkit** | 파일 읽기/쓰기/목록 조회 |
| **RequestsToolkit** | HTTP 요청 수행 |
| **GmailToolkit** | 메일 조회/발송 |

### 실습: SQL Toolkit

```python
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain_community.utilities import SQLDatabase

db = SQLDatabase.from_uri("sqlite:///company.db")
toolkit = SQLDatabaseToolkit(db=db, llm=model)

agent = create_agent(model=model, tools=toolkit.get_tools())
result = agent.invoke({"messages": [{"role": "user", "content": "직원 수를 알려줘"}]})
print(result["messages"][-1].content)
```

### 커스텀 Toolkit 구성

- 여러 개의 `@tool` 함수를 리스트로 묶으면 **간단한 커스텀 Toolkit 구성 가능**
- 사내 시스템(ERP, CRM 등) 전용 Toolkit을 직접 개발하는 경우도 많음
- 도구 간 **일관된 네이밍 규칙**을 정하면 유지보수에 유리
- 보안이 중요한 도구는 **권한 검증 로직을 반드시 포함**

### ⚠️ Toolkit 설계 시 유의사항

- 도구 수가 많아지면 **LLM의 선택 정확도가 떨어질 수 있음**
- 유사한 기능의 도구는 하나로 통합하는 것이 유리
- 각 도구의 설명은 **중복 없이 명확하게** 작성
- 프로덕션 배포 전 충분한 테스트로 오작동 방지

---

## 3-4. Middleware — 파이프라인 전후에 끼어드는 계층

- **Middleware**: Agent 실행 파이프라인의 **전/후 단계에 개입하는 컴포넌트**
- 로깅, 입력 검증, 응답 필터링 등 **공통 로직을 재사용 가능하게 함**
- 여러 Middleware를 순서대로 연결(Chain)해 파이프라인 구성

### 활용 예

- **로깅 Middleware**: 모든 요청/응답을 기록
- **속도 제한(Rate Limiting) Middleware**: 과도한 호출 방지
- **콘텐츠 필터 Middleware**: 부적절한 입력/출력 차단
- **인증 Middleware**: 사용자 권한 확인 후 실행 허용

```python
def logging_middleware(state, next):
    print(f"요청 시작: {state['messages'][-1].content}")
    result = next(state)
    print("요청 완료")
    return result
```

---

## 3-5. Sandboxes — LLM이 만든 코드를 가두는 방

- **Sandbox**: 코드나 도구를 **격리된 안전한 환경에서 실행하는 공간**
- 특히 **LLM이 생성한 코드를 직접 실행할 때 보안상 매우 중요**
- 시스템 파일 접근, 네트워크 사용 등을 **제한적으로 허용**
- 대표적으로 **Docker 컨테이너**, 클라우드 기반 실행 환경 등이 활용됨

### 왜 필요한가

- LLM이 생성한 코드에는 **의도치 않은 오류나 악성 코드가 포함될 수 있음**
- 실제 서버 환경에서 직접 실행하면 시스템 전체에 영향 가능
- Sandbox는 문제가 발생해도 본 시스템에 영향을 주지 않도록 격리
- **코드 실행형 에이전트(Code Interpreter 등)의 핵심 안전장치**

```python
# 개념적 예시: 코드 실행 도구를 Sandbox 환경에서 호출
result = sandbox_tool.run(code="print(1 + 1)")
print(result.output)  # "2"
```

### ⚠️ 적용 시 고려사항

- **실행 시간 제한(Timeout)**으로 무한 루프 방지
- **메모리/CPU 사용량 제한** 설정 필요
- **외부 네트워크 접근 여부를 명확히 정책화**
- 실행 결과 로그를 남겨 **사후 감사(Audit)** 가능하게 구성

---

## 3-6. Backends — 실행과 상태가 사는 곳

- **Backend**: Agent/Chain이 실제로 실행되고 **상태가 관리되는 인프라 계층**
- 로컬 메모리 기반부터 분산 서버 기반까지 다양하게 구성 가능
- 어떤 Backend를 쓰느냐에 따라 **확장성, 안정성**이 달라짐
- Checkpointer, 캐시 저장소 등도 넓은 의미의 Backend에 포함

| Backend 유형 | 특징 |
|---|---|
| **In-Memory** | 빠르지만 서버 재시작 시 데이터 소실 |
| **SQLite/Postgres** | 영구 저장, 중소규모 서비스에 적합 |
| **Redis** | 빠른 캐시성 저장, 세션 관리에 유리 |
| **분산 클라우드 인프라** | 대규모 트래픽 처리에 적합 |

```python
from langgraph.checkpoint.postgres import PostgresSaver

checkpointer = PostgresSaver.from_conn_string(
    "postgresql://user:pass@localhost:5432/langgraph"
)
agent = create_agent(model=model, tools=[], checkpointer=checkpointer)
```

---

## 3-7. Checkpointers — 상태의 스냅샷

- **Checkpointer**: LangGraph에서 실행 상태를 **특정 시점 기준으로 저장하는 컴포넌트**
- **Short-term memory 구현의 핵심 기반 기술**
- 각 단계(Step)마다 상태를 저장해 **중단 후 재개가 가능**
- **Thread ID**로 여러 세션의 상태를 독립적으로 관리

| Checkpointer | 특징 |
|---|---|
| **InMemorySaver** | 개발/테스트용, 휘발성 |
| **SqliteSaver** | 파일 기반 영구 저장 |
| **PostgresSaver** | 프로덕션급 영구 저장 |

- **운영 환경에서는 영구 저장이 가능한 Checkpointer 사용 권장**

```python
from langgraph.checkpoint.sqlite import SqliteSaver

checkpointer = SqliteSaver.from_conn_string("checkpoints.db")
agent = create_agent(model=model, tools=[], checkpointer=checkpointer)

config = {"configurable": {"thread_id": "student-01"}}
agent.invoke({"messages": [{"role": "user", "content": "복습 시작할게"}]}, config)
```

### 활용: 재개와 롤백 (Time Travel)

- 특정 시점(Checkpoint)으로 되돌아가는 기능(**Time Travel**) 지원
- 오류 발생 시 **이전 정상 상태로 복구** 가능
- **사람이 중간에 개입(Human-in-the-loop)하는 시나리오에 필수적**
- 디버깅 시 특정 단계의 상태를 그대로 재현 가능

### ⚠️ 성능 고려

- **매 단계 저장**이므로 저장소 I/O 비용 발생
- 상태 데이터가 커지면 저장/조회 속도에 영향
- 오래된 세션은 주기적으로 정리(삭제) 정책 필요
- 저장소 선택은 서비스 트래픽 규모에 맞게 결정

---

## 3-8. RAG 5대 구성요소

여기부터가 **RAG 파이프라인**이다. 순서대로 읽으면 그대로 파이프라인이 된다.

```plain text
[RAG 전체 파이프라인]

 문서(PDF/Word/Web/CSV)
        │
        ▼  ① Document loader
   Document 객체 (page_content + metadata)
        │
        ▼  ② Text splitter
   Chunk 여러 개 (300~1000자, overlap 50)
        │
        ▼  ③ Embedding model
   벡터 (수백~수천 차원의 실수 배열)
        │
        ▼  ④ Vector store 저장
   Chroma / FAISS / Pinecone / Weaviate
        │
        ▼  ⑤ Retriever 검색 (질문도 임베딩 → 코사인 유사도)
   관련 문서 Top-k
        │
        ▼
   Prompt에 주입 → LLM → 답변
```

### ① Document loaders

- **Document loader**: PDF, Word, 웹페이지 등 다양한 형식의 문서를 **표준화된 형태로 불러오는 도구**
- 로드된 문서는 `Document` 객체(**내용 + 메타데이터**)로 변환됨
- **RAG 파이프라인의 가장 첫 단계**
- 파일뿐 아니라 데이터베이스, API 결과도 로드 가능

| Loader | 지원 형식 |
|---|---|
| **PyPDFLoader** | PDF 문서 |
| **Docx2txtLoader** | Word 문서 |
| **WebBaseLoader** | 웹페이지 |
| **CSVLoader** | CSV 데이터 |
| **NotionDirectoryLoader** | Notion 페이지 |

```python
from langchain_community.document_loaders import PyPDFLoader

loader = PyPDFLoader("company_policy.pdf")
documents = loader.load()

print(len(documents), "페이지 로드됨")
print(documents[0].page_content[:200])
```

**메타데이터의 중요성**

- 각 `Document`는 `page_content`(본문)와 `metadata`(출처, 페이지 번호 등)로 구성
- 메타데이터는 이후 **검색 필터링과 출처 표시**에 활용
- 여러 문서를 로드할 때 **출처를 명확히 남겨두는 것이 중요**
- 실무에서는 사내 다양한 문서 포맷을 통합 로딩하는 파이프라인 구축

### ② Text splitters

- **Text splitter**: 긴 문서를 검색에 적합한 크기의 작은 조각(**Chunk**)으로 나누는 도구
- Context Window와 검색 정확도를 고려해 적절한 크기로 분할
- **문장이 중간에 잘리지 않도록 의미 단위를 고려한 분할이 중요**
- RAG 파이프라인에서 문서 로딩 직후 수행되는 필수 단계

| Splitter | 설명 |
|---|---|
| **CharacterTextSplitter** | 지정 문자 수 기준으로 단순 분할 |
| **RecursiveCharacterTextSplitter** | **문단→문장→단어 순으로 재귀적 분할** |
| **TokenTextSplitter** | 토큰 수 기준으로 분할 |
| **MarkdownHeaderTextSplitter** | 마크다운 제목 구조 기준으로 분할 |

```python
from langchain_text_splitters import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50
)

chunks = splitter.split_text(long_document_text)
print(len(chunks), "개의 조각으로 분할됨")
```

**Chunk 크기 설계 전략**

- **Chunk가 너무 작으면**: 문맥이 부족해 검색 품질 저하
- **Chunk가 너무 크면**: 불필요한 정보까지 포함되어 정확도 저하
- **Overlap(겹침)**을 두면 경계에서 정보 손실 방지
- 일반적으로 **300~1000자 사이에서 실험적으로 최적값 탐색**

### ③ Embedding models

- **Embedding**: 텍스트를 **숫자 벡터로 변환하는 기술**
- 의미가 비슷한 텍스트는 **벡터 공간에서 가까운 위치에 배치됨**
- 이 벡터 간 거리를 계산해 **유사도 검색**이 가능해짐
- OpenAI, Cohere, HuggingFace 등 다양한 Embedding 모델 제공사 존재

**동작 원리**

- 문장을 입력하면 **수백~수천 차원의 실수 벡터**로 출력
- **코사인 유사도(Cosine Similarity)** 등으로 벡터 간 유사도 계산
- 같은 주제의 문장일수록 벡터 방향이 유사하게 학습됨
- 임베딩 모델은 검색뿐 아니라 **분류, 클러스터링**에도 활용

```python
from langchain_openai import OpenAIEmbeddings

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vector = embeddings.embed_query("LangChain은 무엇인가요?")

print(len(vector))      # 벡터 차원 수
print(vector[:5])       # 앞부분 값 확인
```

| 선택 기준 | 설명 |
|---|---|
| **차원 수** | 클수록 표현력↑, 저장/계산 비용↑ |
| **언어 지원** | 다국어(한국어 포함) 지원 여부 |
| **비용** | 임베딩 생성 비용 |
| **도메인 특화** | 특정 분야 전용 모델 존재 여부 |

### ④ Vector stores

- **Vector store**: 임베딩된 벡터를 저장하고 **빠르게 검색할 수 있게 하는 데이터베이스**
- 저장된 벡터 중 질문 벡터와 가장 유사한 것들을 빠르게 찾아줌
- **RAG 파이프라인의 핵심 저장소 역할**

| Vector Store | 특징 |
|---|---|
| **Chroma** | 가볍고 로컬 실습에 적합 |
| **FAISS** | 빠른 유사도 검색, Meta 개발 |
| **Pinecone** | 완전관리형 클라우드 서비스 |
| **Weaviate** | 하이브리드 검색(키워드+벡터) 지원 |

- **프로토타입은 Chroma/FAISS, 프로덕션은 관리형 서비스 고려**

```python
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vector_store = Chroma.from_texts(
    texts=chunks,
    embedding=embeddings
)

results = vector_store.similarity_search("환불 규정 알려줘", k=2)
for r in results:
    print(r.page_content)
```

**⚠️ 운영 고려사항**

- 데이터가 자주 바뀌는 경우 **주기적 재색인(Re-indexing)** 필요
- **메타데이터(출처, 날짜 등)를 함께 저장**해 필터링 검색 지원
- 검색 속도와 정확도 간 **트레이드오프 존재** (인덱스 알고리즘 선택)
- 대규모 서비스는 클라우드 관리형 Vector store 고려

### ⑤ Retrievers

- **Retriever**: 질문과 관련된 정보를 데이터 소스에서 **검색해 가져오는 컴포넌트**
- **RAG(검색 증강 생성)의 핵심 구성요소**
- 벡터 검색, 키워드 검색 등 다양한 검색 방식을 표준 인터페이스로 제공
- Vector Store를 감싸서 `retriever.invoke(query)` 형태로 손쉽게 사용

**동작 원리**

1. 사용자 질문을 임베딩(벡터)으로 변환
2. Vector Store에서 가장 유사한 문서 조각들을 검색
3. 검색된 문서를 LLM에게 함께 전달해 답변 생성에 활용
4. 이 과정을 통해 **LLM이 모르는 최신/사내 정보도 답변 가능**

```python
retriever = vector_store.as_retriever(search_kwargs={"k": 3})
docs = retriever.invoke("환불 정책이 어떻게 되나요?")

for d in docs:
    print(d.page_content[:100])
```

| Retriever 유형 | 설명 |
|---|---|
| **Similarity Retriever** | 벡터 유사도 기반 검색 |
| **MMR Retriever** | 유사도 + **다양성**을 함께 고려 |
| **Self-query Retriever** | 질문에서 **필터 조건까지 자동 추출** |
| **Multi-query Retriever** | 하나의 질문을 여러 방식으로 변형해 검색 |

**💡 성능 향상 팁**

- 검색 결과 수(`k`)를 적절히 조정해 관련성과 비용의 균형 유지
- 문서를 잘게 나누는 **Text splitter 전략이 검색 품질에 큰 영향**
- 필요 시 **Reranking(재정렬)** 기법으로 상위 결과 품질 향상
- 도메인 특화 데이터는 전용 임베딩 모델 사용 고려

---

# 4. Runnable의 이해

> 📍 p138~p157 | `|` 연산자 뒤에서 실제로 무슨 일이 일어나는가. LangChain 전체를 관통하는 단 하나의 추상 인터페이스.

## 4-1. LCEL – Runnable 인터페이스

LCEL(LangChain Expression Language)의 **핵심 기반 프로토콜이자 추상 인터페이스**로, 서로 다른 구성 요소(프롬프트, 모델, 출력 파서 등)를 **일관된 방식으로 연결하고 실행할 수 있도록 표준화**한다.

### Runnable의 핵심 개념 및 설계 목적

- **표준화된 인터페이스 제공**: 모든 컴포넌트(PromptTemplate, ChatModel, OutputParser, Retriever 등)가 **동일한 실행 메서드를 공유**하도록 규격화
- **선언적 파이프라인 구성**: 리눅스 파이프 연산자(`|`)를 활용해 컴포넌트 간 입출력을 직관적으로 연결 (`chain = prompt | model | parser`)

| 메서드 형태 | 동기(Sync) | 비동기(Async) | 주요 용도 |
|---|---|---|---|
| **단일 호출** | `invoke(input, config)` | `ainvoke(input, config)` | 단일 입력값 처리 및 최종 결과 반환 |
| **배치 호출** | `batch(inputs, config)` | `abatch(inputs, config)` | 여러 입력값을 병렬/동시 처리하여 성능 최적화 |
| **스트리밍** | `stream(input, config)` | `astream(input, config)` | LLM의 토큰 생성 등 결과를 실시간 청크 단위로 스트리밍 |

## 4-2. Pipe(`|`) 연산자란?

- **Pipe 연산자(`|`)**: 앞 단계의 출력을 다음 단계의 입력으로 **자동 전달**
- **Unix 파이프(`|`)와 유사한 개념**으로 데이터 흐름을 직관적으로 표현
- `prompt | model | parser` 형태로 전체 파이프라인을 한 줄로 표현 가능
- 각 단계는 독립적으로 테스트하고 재사용할 수 있음

```python
chain = prompt | model | output_parser
```

### 실습: Pipe 연산자 기본

```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

prompt = ChatPromptTemplate.from_template("{topic}에 대해 한 문장으로 설명해줘")
parser = StrOutputParser()

chain = prompt | model | parser
result = chain.invoke({"topic": "머신러닝"})
print(result)
# 머신러닝은 컴퓨터가 명시적으로 프로그래밍 되지 않아도 스스로 학습하고 ...
```

### Pipe 연산자의 장점

- 코드가 간결하고 가독성이 높음
- 각 단계를 독립적인 함수처럼 재사용 가능
- 새로운 단계를 추가/제거하기 쉬운 유연한 구조
- **디버깅 시 특정 단계만 따로 실행해 확인 가능**

```python
debug_chain = prompt | model
print(debug_chain.invoke({"topic": "딥러닝"}))
# content='딥러닝은 인공 신경망을 이용해 데이터를 학습하고, 예측하거나 분류하는 인공지능의 한 분야입니다.' additional_kwargs=...
```

> 💡 **팁** — `| parser`를 떼고 실행하면 **AIMessage 객체 그대로** 나온다. 파서가 어디서 무엇을 벗겨내는지 확인하는 가장 빠른 디버깅 방법이다.

### 체인에 일반 함수 추가하기

- 일반 Python 함수도 **`RunnableLambda`로 감싸 체인에 포함 가능**
- 전처리, 후처리 로직을 체인 안에 자연스럽게 통합

```python
from langchain_core.runnables import RunnableLambda

def to_upper(text: str) -> str:
    return text.upper()

prompt = ChatPromptTemplate.from_template("Explain about the {topic} for elementary school students")

chain = prompt | model | parser | RunnableLambda(to_upper)
result = chain.invoke({"topic": "Machine Learning"})

print(result)
# MACHINE LEARNING IS LIKE TEACHING A COMPUTER TO PLAY A GAME. ...
```

## 4-3. 주요 Runnable 파생 클래스 및 래퍼

| 클래스 | 역할 |
|---|---|
| **RunnablePassthrough** | • 입력을 변형하지 않고 그대로 다음 단계로 전달<br>• `assign()` 메서드를 통해 기존 입력을 유지하면서 **새로운 키-값 쌍을 병합**할 때 주로 사용 |
| **RunnableParallel** (또는 딕셔너리 리터럴 `{}`) | • 여러 Runnable을 **병렬로 동시 실행**하고, 그 결과를 딕셔너리 형태로 취합<br>• 예: 검색기(Retriever) 결과와 원본 질문을 동시에 프롬프트에 매핑할 때 활용 |
| **RunnableLambda** | • 일반 파이썬 함수(`def` 또는 `lambda`)를 Runnable 인터페이스로 변환<br>• 체인 중간의 커스텀 데이터 전처리/후처리 작업에 필수적 |
| **RunnableBranch** | • 조건식에 따라 서로 다른 Runnable 체인으로 **분기 처리** (if-else 패턴) |
| **RunnableWithMessageHistory** | • 상태가 없는 체인에 **세션별 대화 기록(Memory)을 자동으로 주입하고 저장**하도록 래핑 |

## 4-4. 주요 컴포넌트의 RunnableSerializable 구현

LangChain의 주요 컴포넌트가 **실제로 `Runnable`을 상속하고 있음**을 소스 코드로 확인하는 부분이다.

### PromptTemplate 계보

```python
class BasePromptTemplate(
    RunnableSerializable[dict[str, Any], PromptValue], ABC, Generic[FormatOutputType]
):
    """Base class for all prompt templates, returning a prompt."""

class StringPromptTemplate(BasePromptTemplate[str], ABC):
    """String prompt that exposes the format method, returning a prompt."""

class PromptTemplate(StringPromptTemplate):
    """Prompt template for a language model."""
```

### StrOutputParser 계보

```python
class BaseOutputParser(
    BaseLLMOutputParser[T], RunnableSerializable[LanguageModelOutput, T]
):
    """Base class to parse the output of an LLM call."""

class BaseTransformOutputParser(BaseOutputParser[T]):
    """Base class for an output parser that can handle streaming input."""

class StrOutputParser(BaseTransformOutputParser[str]):
    """Extract text content from model outputs as a string."""
```

### ChatOpenAI 계보

```python
class BaseLanguageModel(
    RunnableSerializable[LanguageModelInput, LanguageModelOutputVar], ABC
):
    """Abstract base class for interfacing with language models."""

class BaseChatModel(BaseLanguageModel[AIMessage], ABC):
    """Base class for chat models."""

class BaseChatOpenAI(BaseChatModel):
    """Base wrapper around OpenAI large language models for chat."""

class ChatOpenAI(BaseChatOpenAI):
    """Interface to OpenAI chat model APIs."""
```

### 최상위 — Runnable과 RunnableSerializable

```python
class Runnable(ABC, Generic[Input, Output]):
    """A unit of work that can be invoked, batched, streamed, transformed and composed.

    Key Methods
    ===========

    - `invoke`/`ainvoke`: Transforms a single input into an output.
    - `batch`/`abatch`: Efficiently transforms multiple inputs into outputs.
    - `stream`/`astream`: Streams output from a single input as it's produced.
    - `astream_log`: Streams output and selected intermediate results from an input.
    """

class RunnableSerializable(Serializable, Runnable[Input, Output]):
    """Runnable that can be serialized to JSON."""
```

> ⭐ **핵심** — Prompt도, Model도, Parser도 **결국 전부 `Runnable`이다.** 그래서 `|`로 아무거나 이을 수 있고, 어떤 조합이든 `invoke/stream/batch`가 똑같이 동작한다. 이것이 LangChain 설계의 심장이다.

## 4-5. RunnableSequence — 순차 실행

- **RunnableSequence**: 여러 Runnable을 순서대로 실행하는 체인 객체
- 사실 `A | B | C` 코드는 내부적으로 **`RunnableSequence(A, B, C)`로 변환됨**
- 각 단계의 출력이 다음 단계의 입력으로 그대로 전달됨
- **Pipe 연산자는 RunnableSequence를 만드는 문법적 편의 기능(Syntactic Sugar)**

### 명시적 생성

```python
from langchain_core.runnables import RunnableSequence
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

prompt = ChatPromptTemplate.from_template("{topic}에 대해 한 문장으로 설명해줘")
parser = StrOutputParser()

# chain = prompt | model | parser
chain = RunnableSequence(prompt, model, parser)
result = chain.invoke({"topic": "머신러닝"})

print(result)
```

- **동적으로 체인을 구성해야 할 때 유용** (예: 조건에 따라 단계 수가 달라지는 경우)

### 데이터 흐름

```plain text
입력(dict)
   ↓
Prompt   : 입력을 메시지로 변환    → PromptValue
   ↓
Model    : 메시지로 응답 생성      → AIMessage
   ↓
Parser   : 응답 후처리             → str
   ↓
출력
```

- 각 단계는 **입력 타입과 출력 타입이 명확히 정의**되어 있어야 함
- **타입이 맞지 않으면 실행 시점에 오류 발생**
- 디버깅 시 각 단계의 입출력을 개별적으로 확인하는 것이 효과적

### 실습: 다단계 체인 (요약 → 번역)

```python
summarize_prompt = ChatPromptTemplate.from_template("다음 글을 요약해줘: {text}")
translate_prompt = ChatPromptTemplate.from_template("다음을 영어로 번역해줘: {summary}")

summarize_chain = summarize_prompt | model | parser
translate_chain = translate_prompt | model | parser

full_chain = (
    {"summary": summarize_chain}
    | translate_chain
)
result = full_chain.invoke({"text": """미국에서 50명 이하의 소규모 하객만 초대하는 '마이크로 웨딩' ..."""})
print(result)
# In the U.S., 'micro weddings'—inviting fewer than 50 guests—are becoming popular,
# reflecting rising living costs and changing values among young generations. ...
```

> ⭐ **핵심** — `{"summary": summarize_chain}` 처럼 **딕셔너리 리터럴을 체인에 넣으면 자동으로 RunnableParallel이 된다.** 앞 체인의 결과를 다음 프롬프트의 변수명에 맞춰 매핑하는 관용적 패턴이다.

### 오류 처리

- 특정 단계에서 오류 발생 시 `.with_retry()` 로 **재시도 설정 가능**
- `.with_fallbacks()` 로 오류 시 **대체 체인 실행** 가능
- 각 단계별 실행 시간을 측정해 **병목 구간 파악** 가능

```python
safe_chain = chain.with_retry(stop_after_attempt=3)
```

## 4-6. RunnableParallel — 병렬 실행

- **RunnableParallel**: 여러 Runnable을 **동시에(병렬로) 실행하는 구조**
- **딕셔너리 형태로 여러 체인을 정의하면 자동으로 병렬 실행됨**
- 서로 독립적인 여러 작업을 동시에 처리해 속도 향상
- 예: 하나의 질문에 대해 **요약과 번역을 동시에 수행**

### 실습: RunnableParallel

```python
from langchain_core.runnables import RunnableParallel

summarize_prompt = ChatPromptTemplate.from_template("다음 글을 요약해줘: {text}")
keyword_prompt = ChatPromptTemplate.from_template("다음 글에서 핵심 키워드를 추출해줘: {text}")

parallel_chain = RunnableParallel(
    summary=summarize_prompt | model | parser,
    keywords=keyword_prompt | model | parser
)

result = parallel_chain.invoke({"text": """미국에서 50명 이하의 소규모 하객만 초대하는 '마이크로 웨딩' ..."""})
print(result)
print(result["summary"])
print(result["keywords"])
# {'summary': "미국에서는 젊은 세대의 변화된 가치관과 물가 상승을 고려해 50명 미만의 소규모 하객을 부르는 '마이크로 웨딩'이 유행하고 있다. ...",
#  'keywords': "미국, 50명, 소규모 하객, '마이크로 웨딩', 트렌드, 확산, 물가, 젊은 세대, 가치관, 대규모 결혼식, 소통, 결혼 문화, ..."}
```

### 성능 이점

- 각 작업이 서로 의존하지 않을 때 **전체 처리 시간 단축**
- 예: **순차 실행 시 5초+5초=10초 → 병렬 실행 시 약 5초**
- 여러 개의 검색/모델 호출을 동시에 수행할 때 특히 유용
- ⚠️ 다만 병렬 실행이 많아지면 **API Rate Limit에 유의**해야 함

### RunnableParallel과 RunnableSequence의 조합

실제 서비스에서는 병렬과 순차를 함께 조합하는 경우가 많다. 예: 병렬로 여러 정보를 수집한 뒤, 순차적으로 최종 답변 생성.

```python
full_chain = (
    RunnableParallel(context=retriever, question=lambda x: x["question"])
    | final_prompt
    | model
    | parser
)
```

> ⭐ **핵심** — **이것이 RAG 체인의 표준 형태다.** 검색(`retriever`)과 원본 질문을 병렬로 모아 딕셔너리로 만들고, 그것을 프롬프트의 `{context}`, `{question}`에 꽂아 넣는다.

### 활용 사례

- **다각도 분석**: 감정 분석 + 키워드 추출 + 요약을 동시에 수행
- **다중 검색**: 여러 Vector store에서 동시에 검색 후 결과 통합
- **다국어 서비스**: 여러 언어로 동시에 번역하여 제공

---

# 5. AI 서비스 개발을 위한 UI — Gradio

> 📍 p158~p162 | 만든 체인에 사람이 쓸 수 있는 화면을 붙이는 가장 빠른 방법

## 5-1. Gradio란?

- **Gradio**: 머신러닝/AI 모델의 **데모 UI를 빠르게 만드는 Python 라이브러리**
- **함수 하나를 감싸는 것만으로 입력-출력 인터페이스 자동 생성**
- Hugging Face와의 강력한 통합으로 모델 공유가 매우 쉬움
- 이미지, 오디오, 텍스트 등 다양한 입출력 타입 기본 지원

## 5-2. Gradio 기본 구조 — ChatInterface

```python
import gradio as gr

def chatbot_response(message, history):
    response = agent.invoke({"messages": [{"role": "user", "content": message}]})
    return response["messages"][-1].content

demo = gr.ChatInterface(fn=chatbot_response)
demo.launch()
```

실행 로그 예시:

```plain text
It looks like you are running Gradio on a hosted Jupyter notebook,
which requires `share=True`. Automatically setting `share=True`.
Colab notebook detected. To show errors in colab notebook, set debug=True in launch()
* Running on public URL: https://xxxxxxxx.gradio.live

This share link is temporary and will last for up to 1 week (best effort).
```

> ⚠️ **주의** — Colab/Jupyter 환경에서는 `share=True`가 자동 설정되며, 생성되는 public URL은 **최대 1주일간 유효한 임시 링크**다. 영구 호스팅이 필요하면 Hugging Face Spaces 등을 사용한다.

## 5-3. Gradio 컴포넌트

| 컴포넌트 | 용도 |
|---|---|
| `gr.Textbox` | 텍스트 입력/출력 |
| `gr.Image` | 이미지 입력/출력 |
| `gr.Audio` | 오디오 입력/출력 |
| `gr.Slider` | 숫자 파라미터 조절 |

- **여러 컴포넌트를 조합해 커스텀 인터페이스 구성 가능**

## 5-4. Gradio Blocks로 커스텀 UI 만들기

```python
with gr.Blocks() as demo:
    gr.Markdown("## LangChain 기반 문서 요약기")
    input_text = gr.Textbox(label="원문 입력")
    output_text = gr.Textbox(label="요약 결과")
    btn = gr.Button("요약하기")
    btn.click(fn=summarize_chain.invoke, inputs=input_text, outputs=output_text)

demo.launch()
```

> ⭐ **핵심** — `btn.click(fn=summarize_chain.invoke, ...)` 에 주목하자. LCEL 체인의 `.invoke`를 **그대로 콜백으로 꽂을 수 있는 이유**는 Runnable이 평범한 callable처럼 동작하기 때문이다. 4장과 5장이 여기서 만난다.

---

# ★ 전체 흐름 한 장 요약

```plain text
════════════════════════════════════════════════════════════════════════
                LLM 기반 AI 서비스 개발의 전체 지형도
════════════════════════════════════════════════════════════════════════

[1] 왜 어려운가              [2] 무엇으로 푸는가
────────────────            ──────────────────────────────
확률적 출력       ────────→  Structured Output (Pydantic/JSON Schema)
환각(Hallucination) ──────→  RAG (Loader→Splitter→Embedding→VectorStore→Retriever)
느린 응답         ────────→  Streaming (stream / astream, SSE)
문맥 없음         ────────→  Short-term memory (Checkpointer + thread_id)
평가 불가         ────────→  LLMOps (Golden Dataset, RAGAS, LLM-as-a-Judge)
디버깅 불가       ────────→  Observability (LangSmith 트레이싱)
보안 취약         ────────→  Sandbox + Middleware + Human-in-the-loop
벤더 종속         ────────→  init_chat_model 표준 인터페이스

                            ↓ 이 모든 것을 조립하는 문법

[3] LCEL: chain = prompt | model | parser
                            ↓ 그 밑바닥에는

[4] Runnable 하나뿐
    ├─ invoke / ainvoke    (단일)
    ├─ batch  / abatch     (병렬 배치)
    └─ stream / astream    (스트리밍)

    파생: RunnableSequence(순차) · RunnableParallel(병렬)
          RunnableLambda(함수) · RunnableBranch(분기)
          RunnablePassthrough(통과) · RunnableWithMessageHistory(기억)

                            ↓ 사람이 쓰게 만들면

[5] Gradio: gr.ChatInterface(fn=...) / gr.Blocks()
════════════════════════════════════════════════════════════════════════

[RAG 체인의 표준형]
full_chain = (
    RunnableParallel(context=retriever, question=lambda x: x["question"])
    | final_prompt | model | parser
)

[Agent의 표준형 — ReAct 루프]
사고(Reasoning) → 행동(Action, tool_calls) → 관찰(Observation, ToolMessage) → 반복
```

---

# ★ 시험/면접 대비 핵심 문답

| # | 질문 | 답변 |
|---|---|---|
| 1 | 기존 IT 서비스 개발과 LLM 서비스 개발의 가장 근본적 차이는? | > **A.** 결정론적(Deterministic) vs 확률론적(Probabilistic). 동일 입력에 동일 출력이 보장되지 않으므로 제어 로직도 코드가 아닌 프롬프트/컨텍스트로, 검증도 단위 테스트가 아닌 LLM-as-a-Judge·의미론적 유사도로 바뀐다. |
| 2 | RAG 검색 정확도가 높으면 환각이 사라지는가? | > **A.** 아니다. 검색 정확도(Retrieval Accuracy)가 높더라도 **파싱 및 추론 단계에서 왜곡**이 발생할 수 있어 환각을 완전히 제거하기는 어렵다. |
| 3 | 프롬프트 드리프트(Prompt Drift)란? | > **A.** 상용 파운데이션 모델의 버전 업데이트나 미세 조정에 따라, 기존에 잘 동작하던 프롬프트가 예기치 않게 오작동하는 현상. 핀 고정된 모델 ID를 쓰는 것이 완화책이다. |
| 4 | LLM 서비스의 운영 비용이 예측하기 어려운 이유는? | > **A.** 호출 횟수가 아닌 **입출력 토큰 총량**에 과금되기 때문. 프롬프트 최적화 실패나 무한 루프 에이전트 발생 시 비용이 기하급수적으로 폭증한다. |
| 5 | LangChain / LangGraph / LlamaIndex / CrewAI 각각의 주 용도는? | > **A.** LangChain=범용 오케스트레이션(LCEL), LangGraph=상태 기반 순환 에이전트(그래프·체크포인트·HITL), LlamaIndex=데이터 인덱싱 및 심층 RAG, CrewAI=역할 기반 멀티 에이전트 협업. |
| 6 | 현업 프로덕션에서 가장 흔한 프레임워크 조합은? | > **A.** 단일 프레임워크 종속보다 **LangChain + LangGraph 하이브리드**, 또는 모델 네이티브 Tool Calling API + 경량 오케스트레이터 혼합 방식. |
| 7 | `langchain`과 `langchain-core`의 차이는? | > **A.** `langchain`은 체인·에이전트·추출 전략 등 인지 구조를 담고, `langchain-core`는 chat model·vector store·tool의 **인터페이스만 정의**하며 의존성을 경량으로 유지한다. 둘 다 third-party 통합체를 포함하지 않는다. |
| 8 | Messages 4종류와 각각의 역할은? | > **A.** SystemMessage=페르소나·규칙, HumanMessage=사용자 입력, AIMessage=모델 응답(tool_calls 포함 가능), ToolMessage=도구 실행 결과 반환. 리스트 순서가 곧 문맥(Context)이다. |
| 9 | LLM이 도구를 "실행"하는가? | > **A.** 아니다. LLM은 `tool_calls` 정보(어떤 도구를 어떤 인자로 부를지)만 반환하고, **실제 실행은 개발자 코드**에서 이루어지며 결과만 ToolMessage로 다시 전달된다. |
| 10 | Structured Output은 내부적으로 어떻게 동작하는가? | > **A.** 대부분 **Function Calling(도구 호출)** 방식을 활용한다. 지정한 스키마를 하나의 "도구"처럼 모델에 전달하고, 모델은 텍스트 대신 스키마에 맞는 구조화된 인자를 반환한다. 일부 모델은 JSON 모드를 직접 지원한다. |
| 11 | Pydantic 필드의 `description`이 중요한 이유는? | > **A.** 그 설명이 스키마와 함께 LLM에 전달되어, **LLM이 어떤 값을 채워야 하는지 이해하는 핵심 단서**가 되기 때문이다. |
| 12 | JsonOutputParser와 Pydantic 기반 구조화 출력 중 무엇을 권장하나? | > **A.** 안전성이 중요한 서비스는 **Pydantic 기반 구조화 출력을 우선 권장**한다. LLM이 불완전한 JSON을 생성할 위험이 있기 때문. |
| 13 | LCEL이란 무엇이고 왜 쓰는가? | > **A.** LangChain 컴포넌트를 파이프 연산자로 연결하는 선언적 문법. 모든 구성요소가 Runnable을 공유하므로 가독성·재사용성·일관된 실행 방식(invoke/stream/batch)·병렬 조합·재시도/Fallback 내장을 얻는다. |
| 14 | `A \| B \| C` 는 내부적으로 무엇이 되는가? | > **A.** `RunnableSequence(A, B, C)`. Pipe 연산자는 RunnableSequence를 만드는 **문법적 편의 기능(Syntactic Sugar)**이다. |
| 15 | Runnable의 6개 핵심 메서드는? | > **A.** invoke/ainvoke(단일), batch/abatch(배치 병렬), stream/astream(스트리밍). 추가로 astream_log가 중간 결과까지 스트리밍한다. |
| 16 | RunnableParallel은 언제 쓰는가? | > **A.** 서로 독립적인 작업을 동시 실행할 때. 순차 5초+5초=10초가 병렬 약 5초로 단축된다. RAG에서 `RunnableParallel(context=retriever, question=...)` 형태가 표준 패턴. ⚠️ API Rate Limit 유의. |
| 17 | RunnablePassthrough의 `assign()`은 무엇을 하는가? | > **A.** 기존 입력을 그대로 유지하면서 **새로운 키-값 쌍을 병합**한다. |
| 18 | Short-term memory와 Checkpointer의 관계는? | > **A.** Checkpointer가 Short-term memory 구현의 **핵심 기반 기술**이다. 각 단계마다 상태를 저장하고 thread_id로 세션을 구분하며, Time Travel(롤백)과 Human-in-the-loop을 가능하게 한다. |
| 19 | Checkpointer 3종과 용도는? | > **A.** InMemorySaver(개발/테스트, 휘발성), SqliteSaver(파일 기반 영구), PostgresSaver(프로덕션급 영구). 운영 환경에서는 영구 저장형을 권장. |
| 20 | RAG 파이프라인 5단계를 순서대로 말하면? | > **A.** Document loader → Text splitter → Embedding model → Vector store 저장 → Retriever 검색. 이후 검색 결과를 프롬프트에 주입해 LLM이 답변을 생성한다. |
| 21 | Chunk 크기를 정하는 기준은? | > **A.** 너무 작으면 문맥 부족으로 검색 품질 저하, 너무 크면 불필요한 정보 포함으로 정확도 저하. Overlap(겹침)으로 경계 손실을 방지하며 일반적으로 **300~1000자** 사이에서 실험적으로 탐색한다. |
| 22 | Retriever 4종류의 차이는? | > **A.** Similarity(벡터 유사도), MMR(유사도+다양성), Self-query(질문에서 필터 조건까지 자동 추출), Multi-query(하나의 질문을 여러 방식으로 변형해 검색). |
| 23 | Vector store를 프로토타입과 프로덕션에서 어떻게 나눠 쓰나? | > **A.** 프로토타입은 Chroma/FAISS(로컬·경량), 프로덕션은 Pinecone 같은 완전관리형 또는 하이브리드 검색 지원 Weaviate를 고려한다. |
| 24 | Sandbox가 필요한 이유는? | > **A.** LLM이 생성한 코드에 의도치 않은 오류나 악성 코드가 있을 수 있어, 실제 서버 환경에서 직접 실행하면 시스템 전체에 영향을 줄 수 있기 때문. 코드 실행형 에이전트의 핵심 안전장치다. |
| 25 | Agent 설계 시 무한 루프와 비용 폭증을 어떻게 막는가? | > **A.** 최대 반복 횟수를 제한하고, 도구 실행 실패 시 대응 로직을 두며, Sandbox에 실행 시간 제한(Timeout)과 메모리/CPU 제한을 설정한다. |
| 26 | `init_chat_model`에서 모델 문자열은 어떤 형태를 권장하나? | > **A.** `"openai:gpt-4o-mini"` 같은 **provider prefix 형태**. bare 모델명도 허용되나 provider 추론은 best-effort이며 보장되지 않는다. provider가 동적이거나 런타임 교체가 필요하면 `model_provider`를 별도로 명시한다. |

---

# ⚠️ 원문 용어 검증 노트

정리하면서 확인·보정한 항목들입니다.

| 원문 표기 | 정리본 표기 | 사유 |
|---|---|---|
| `print(response.tool calls)` (p32) | `print(response.tool_calls)` | 슬라이드 이미지에서 언더스코어가 공백으로 렌더링됨. 실제 속성명은 `tool_calls`. |
| `from langchain community.agent toolkits import ...` (p96) | `from langchain_community.agent_toolkits import ...` | 동일 원인. 패키지/모듈명의 언더스코어 누락. |
| `SQLDatabase.from uri(...)`, `toolkit.get tools()`, `create agent(...)` (p96) | `from_uri`, `get_tools`, `create_agent` | 동일 원인. |
| `sandbox tool.run(...)` (p103) | `sandbox_tool.run(...)` | 동일 원인. 참고로 이 슬라이드는 **"개념적 예시"**로 명시되어 있으며, 실제 LangChain API가 아님. |
| `PostgresSaver.from conn string(...)`, `SqliteSaver.from conn string(...)` | `from_conn_string(...)` | 동일 원인. |
| `vector store.as retriever(search kwargs=...)` (p118) | `vector_store.as_retriever(search_kwargs=...)` | 동일 원인. |
| `splitter.split text(...)`, `chunk size=500` (p122) | `split_text(...)`, `chunk_size=500` | 동일 원인. |
| `from langchain chroma import Chroma`, `Chroma.from_texts` (p130) | `from langchain_chroma import Chroma` | 동일 원인. |
| `config = {"configurable": {"thread id": "student-01"}}` (p111) | `"thread_id"` | 동일 원인. `thread_id`가 올바른 키. |
| `def logging middleware(state, next)` (p100) | `def logging_middleware(state, next)` | 동일 원인. 또한 `next`는 파이썬 내장 함수명이므로 실제 구현에서는 다른 이름 권장. |
| `gemini-2.5-flash-lite`, `gpt-4`, `gpt-4o-mini` | 그대로 유지 | 강의 시점의 예시 모델명. 실제 사용 시에는 현재 제공되는 최신 모델 ID로 교체하고, 슬라이드 p85 권고대로 **핀 고정된 모델 ID**를 사용할 것. |
| "Prompt Template**이**란 무엇인가?" (p35) | "Prompt Template**이**란" → 정리본에서는 "Prompt Template — ..." 으로 재구성 | 받침 없는 단어 뒤에는 '란'이 맞음(Prompt Template란). 정리본에서는 제목 형식을 바꿔 회피. |
| "LCEL**이**란 무엇인가?" (p69), "RunnableParallel**이**란" (p154) | 동일 | 동일 사유. |
| p85 `gemini... -> google_vertexai` | 그대로 유지하되 주석 추가 | 원문에 "default changes in next major; pass model_provider to lock in"이 명시되어 있어, **`gemini` prefix의 기본 provider가 향후 변경 예정**임을 본문에 반영함. |

---

📄 **원본**: `5_생성형 AI 서비스 개발의 이해 활용 (LangChain).pdf` (162p, SK AX, 2026.09)
🗓️ **정리일**: 2026-09-11
