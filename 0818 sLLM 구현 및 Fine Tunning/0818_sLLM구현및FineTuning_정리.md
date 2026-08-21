# 🤖 sLLM 구현 및 Fine-Tuning 완전 정리

> 💡 **한 줄 요약**
> **"모든 문제에 가장 큰 모델이 필요한 것은 아니다."**
> 작은 모델(sLLM)을 골라서 → 우리 업무에 맞게 학습시키는(Fine-Tuning) 전 과정을,
> **왜 필요한가 → 어떤 모델을 고르나 → 내부는 어떻게 생겼나 → 어떻게 학습하나 → 어떻게 튜닝하나 → 뭐가 고장나나** 순서로 정리합니다.

**출처** : `4) 생성형AI_3.sLLM구현 및 Fine Tunning_박병선p.pdf` (총 106p, 박병선)
**범위** : 1장 Why sLLM? ~ 7장 Fine-Tuning Troubleshooting (전체)

---

## 📑 목차

| # | 챕터 | 핵심 질문 | 슬라이드 |
|---|---|---|---|
| 1 | [Why sLLM?](#1-why-sllm) | 왜 작은 모델을 쓰는가? | p3~14 |
| 2 | [sLLM 모델 탐색과 선택](#2-sllm-모델-탐색과-선택) | 어떤 모델을 고를 것인가? | p15~30 |
| 3 | [Inside the LLM : Transformer Recap](#3-inside-the-llm--transformer-recap) | 모델 안에서 무슨 일이 일어나는가? | p31~43 |
| 4 | [How LLM Learns](#4-how-llm-learns) | LLM은 어떻게 학습하는가? | p44~55 |
| 5 | [Fine-Tuning Map](#5-fine-tuning-map) | 무엇을 배우고, 어떻게 업데이트할 것인가? | p56~73 |
| 6 | [Fine-Tuning Techniques](#6-fine-tuning-techniques) | LoRA와 QLoRA는 어떻게 동작하는가? | p74~98 |
| 7 | [Fine-Tuning Troubleshooting](#7-fine-tuning-troubleshooting) | 무엇이 잘못되고, 어떻게 막는가? | p99~104 |
| ★ | [전체 흐름 한 장 요약](#-전체-흐름-한-장-요약) | 전부 어떻게 연결되는가? | — |
| ★ | [시험/면접 대비 핵심 문답](#-시험면접-대비-핵심-문답) | 뭘 기억해야 하는가? | — |

---

# 1. Why sLLM?

## 1-1. From Millions to Billions — Scale-up이 만든 LLM의 발전

> LLM의 성능 경쟁은 더 많은 **Parameter, Data, Compute**를 투입하는 **Scale-up**을 중심으로 발전

- 더 많은 **Parameters** → 복잡한 패턴과 관계를 학습하고, 모델의 표현 능력을 확장
- 더 많은 **Training Data** → 다양한 지식과 문맥을 학습하며 범용성을 향상
- 더 많은 **Compute** → 대규모 모델과 데이터를 효과적으로 학습할 수 있는 기반 제공
- ⚠️ Scale-up은 동시에 더 많은 **메모리, 학습·추론 비용, 컴퓨팅 인프라**를 요구

```plain text
        ●                ●●●              ●●●●●●●
                        ●●●●●           ●●●●●●●●●●        ● ● ● ·  ·   ·
                        ●●●●            ●●●●●●●●●●
     GPT-1             GPT-2               GPT-3          Frontier LLMs
     117M              1.5B                175B        Hundreds of Billions
      2018             2019                2020       of Parameters and Beyond
  ─────────────────── Parameter Scale-up ──────────────────────→
```

> 🤔 **여기서 이 강의의 출발 질문이 나옵니다.**
> **"모든 AI 서비스에 이렇게 큰 모델이 필요할까?"**

## 1-2. 왜 작은 모델이 다시 주목받는가? — 큰 모델이 항상 최선은 아니다

| 대규모 LLM의 부담 | 작은 모델의 강점 |
|---|---|
| 높은 추론 비용 | 낮은 운영 비용 |
| 대용량 GPU 메모리 필요 | 제한된 자원에서도 구동 |
| 느린 응답과 네트워크 의존 | 빠른 응답과 로컬 실행 |
| 민감 데이터의 외부 전송 | 내부망·온디바이스 활용 |
| 범용 모델의 과도한 성능 | 특정 업무에 최적화 가능 |

- ✓ 대규모 LLM은 뛰어난 범용성을 제공하지만, **실제 서비스에서는 높은 비용과 운영 부담이 함께 발생**
- ✓ 비용, 속도, 보안, 내부망 운영을 고려하면 작은 모델이 더 적합한 경우 관찰 → **sLLM에 대한 기업의 실제 요구 증가**
- ✓ 범용 성능 경쟁 → 비용·속도·보안 고려 → **업무에 맞는 작은 모델 선택도 하나의 옵션**

> ✅ **이 강의 전체를 관통하는 문장**
> **"모든 문제에 작은 모델이 필요한 것은 아니다.**
> **그러나 모든 문제에 가장 큰 모델이 필요한 것도 아니다."**

## 1-3. 과거의 작은 모델과 지금의 작은 모델은 다르다

### 작지만, 충분히 강해졌다

- 특정 업무에서는 **대규모 모델에 근접한 성능**
- 낮은 추론 비용과 빠른 응답 속도
- 제한된 GPU와 로컬 환경에서도 실행
- 보안이 중요한 **내부망·온디바이스 배포**
- 적은 자원으로 **업무 맞춤형 미세조정**

```plain text
┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│    Better    │+ │ High-Quality │+ │  Knowledge   │+ │    Post-     │+ │ Quantization │
│ Architecture │  │Training Data │  │ Distillation │  │   Training   │  │              │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       └─────────────────┴────────────┬────┴─────────────────┴─────────────────┘
                                      ↓
                        ┌─────────────────────────────┐
                        │    Capable Small Models     │
                        └─────────────────────────────┘
```

> 💬 **강의 인용**
> *"과거에는 작은 모델이 곧 제한된 성능을 의미했지만,*
> *지금은 효율적인 설계와 학습을 통해 작은 모델의 성능 한계가 빠르게 확장"*

## 1-4. sLLM을 어떻게 정의할 것인가? — sLLM은 얼마나 작은 모델인가?

### 소형 언어 모델(Small Language Model, SLM or sLLM)이란?

> sLLM은 **LLM보다 상대적으로 적은 파라미터와 연산 자원을 사용**하며, **제한된 환경이나 특정 목적에서도 효율적으로 활용할 수 있도록 설계된 언어 모델**

| 판단 기준 | 상대적으로 작은 모델의 특성 |
|---|---|
| **파라미터 수** | 더 적음 |
| **필요한 연산량** | 더 적음 |
| **메모리 요구량** | 더 낮음 |
| **범용성** | 상대적으로 제한적 |
| **활용 범위** | 특정 과업과 환경에 집중 |

> 📌 **파라미터 기준 — 통일된 정의는 없다**
> *"SLM의 분류 기준은 아직 명확하지 않다. 일부 연구는 **10억 개 미만의 파라미터**로 정의하지만, 다른 연구는 **더 큰 모델과 비교한 상대적 개념**으로 본다. 현재 통일된 정의에 대한 합의는 없다."*
> — 2025, ACM Computing Surveys, *A Comprehensive Survey of Small Language Models in the Era of Large Language Models*

> 💡 **시험 포인트**: "sLLM은 몇 B 이하인가?"에 절대적인 답은 **없습니다.** 상대적·맥락적 개념입니다.

## 1-5. ⭐ 언제 sLLM을 선택하는가? (1) — 같은 업무도 규모가 다르면 답이 다르다

> **상용 LLM을 사용할 수 없는 순간, 현실적 제약**

같은 "고객 응대"라도 **호출량과 업무 성격**에 따라 정답이 갈립니다.

| | 💬 **하루 10여건의 고객 상담 Agent** | 🔁 **하루 10만건의 고객문의 자동 분류 Agent** |
|---|---|---|
| **업무** | 고객의 다양한 상담에 대응 필요 | 배송 문의 / 환불 요청 / 결제 오류 / 제품 불량 / 기타 |
| **특성** | • 사용자가 질문을 **자유롭게 입력**<br>• **다양한 주제**에 대응해야 함<br>• **호출량이 적음**<br>• 빠르게 서비스를 만들어야 함 | • 입력과 출력 **형식이 정해져 있음**<br>• 동일한 작업을 **대량으로 반복**<br>• 빠른 응답과 **낮은 건당 비용**이 중요<br>• **고객 정보**가 포함될 수 있음 |
| **→ 중요한 것** | **범용성 · 개발 속도** | **비용 · 속도 · 안정성** |
| **→ 선택** | 상용 LLM API | **sLLM** |

> 💡 **핵심 직관**
> 건당 비용이 작아도 **10만 건이면 총비용은 커집니다.**
> 반대로 하루 10건이면 sLLM을 만들고 운영하는 비용이 API 비용보다 비쌉니다.
> **"호출량 × 업무의 정형성"** 이 sLLM 선택의 1차 기준입니다.

## 1-6. ⭐ 언제 sLLM을 선택하는가? (2) — 8가지 현실적 제약

| 상황 | 사례 | 상용 LLM 사용의 문제 |
|---|---|---|
| **민감한 데이터를 다룰 때** | 환자 진료기록 요약, 고객 상담 분석 | 데이터를 외부 API로 전송하기 어려움 |
| **보안이 중요한 업무일 때** | 사내 기밀문서 검색, 국방·금융 시스템 | 외부 클라우드 연결 자체가 제한될 수 있음 |
| **인터넷을 사용할 수 없을 때** | 공장 설비, 자동차, 오프라인 단말기 | 네트워크 장애 시 서비스가 중단됨 |
| **호출량이 매우 많을 때** | 매일 수백만 건의 문서 분류 | 건당 비용은 작아도 전체 비용이 커짐 |
| **즉각적인 응답이 필요할 때** | 실시간 음성 명령, 이상 상황 감지 | 네트워크와 서버 처리시간이 누적됨 |
| **특정 업무만 반복할 때** | 스팸 분류, 품목 코드 분류 | 범용 LLM의 높은 성능이 과도할 수 있음 |
| **모델을 직접 통제해야 할 때** | 응답 형식 고정, 금지 표현 통제 | 모델 버전과 정책 변경의 영향을 받을 수 있음 |
| **조직에 맞게 조정해야 할 때** | 사내 용어·업무 규칙 적용 | 데이터와 모델을 직접 학습·관리하기 어려움 |

> 🗂 **외우기 쉽게 3덩어리로**
> - **못 보낸다** (1,2) : 민감정보 · 보안
> - **못 기다린다 / 못 감당한다** (3,4,5) : 오프라인 · 호출량 · 지연시간
> - **내 맘대로 못 한다** (6,7,8) : 과도한 성능 · 통제 불가 · 커스터마이징 불가

## 1-7. sLLM의 주요 활용 영역 (sLLM Applications)

강의는 활용 영역을 **3가지 카테고리**로 나눕니다.

### ① Enterprise AI : 반복되는 기업 업무 → 작고 빠른 전용 AI

- 기업에는 **분류·추출·태깅·요약**처럼 단순하지만 **대량으로 반복되는** AI 업무가 존재
- 이러한 반복적이고 명확한 기업 업무에는 **작고 효율적인 모델이 경쟁력**이 될 수 있음

#### 📌 Case: AT&T | Customer Interaction Classification — *"Simple Task × High Volume → sLLM"*

| | 내용 |
|---|---|
| **기업** | 미국 최대 통신사의 획기적인 고객 서비스 개선 사례 |
| **질문** | *하루 수백만 건의 단순한 AI 업무에도 가장 큰 LLM이 필요할까?* |
| **Problem** | 수많은 고객 상담 내용을 지속적으로 분석하고 유형화해야 함 |
| **Solution** | • 고객 상담 데이터를 **Fine-tuned sLLM으로 자동 분류**<br>• 대규모 LLM 대신 특정 분류 업무에 최적화된 작은 모델 활용<br>• 대량의 상담 데이터를 낮은 비용으로 빠르게 처리 |
| **Results** | ✓ **85% Cost Reduction**<br>✓ Performance & Quality Maintained |

```plain text
[Customer-Agent Conversations]  →  [Fine-tuned sLLM]  →  [Interaction Classification]
                                                              ↓
                                              Churn · Service Issues · Outreach
```

#### 📌 Case: Trustpilot | Review Analysis — *"High-volume + Latency → sLLM"*

| | 내용 |
|---|---|
| **기업** | 덴마크 소재의 세계적인 온라인 Customer Review Platform. 수억 건의 소비자 리뷰를 수집·분석하여 기업과 소비자의 의사결정을 지원 |
| **질문** | *모든 리뷰를 거대 LLM으로 처리할 필요가 있는가?* |
| **Problem** | • 월간 활성 사용자 **6천만명**, 하루 약 **20만건**의 신규 리뷰<br>• 매일 대량의 짧은 텍스트가 계속 유입 + 단순하지만 반복되는 NLP Task |
| **Solution** | • 수백만 건을 처리해야 하기 때문에 매 리뷰마다 거대한 모델을 호출하는 것보다 **작은 모델을 해당 업무에 최적화**<br>• **Fine-tuned Gemma** → Real-time architecture for big data |
| **Result** | ✓ Real-time Processing · Scalability · Cost Efficiency |

### ② Task-specific AI : 특정 Task → Fine-tuning으로 전문화

> **General Capability를 조금 포기하더라도** 특정 Task에서 **충분한 성능 + 낮은 비용 + 빠른 속도**를 얻기 위해서 sLLM을 Fine-Tuning

#### 📌 Case: Epic System × Microsoft Phi-3

| | 내용 |
|---|---|
| **기업** | 미국의 대표적인 **EHR(Electronic Health Record)** SW 기업 |
| **질문** | *수많은 의료 기록에서 환자의 핵심 이력을 빠르게 파악할 수 없을까?* |
| **Problem** | 복잡하고 방대한 Patient History → 의료진의 높은 Review 부담 |
| **Solution** | • **Microsoft Phi-3 (3.8B)** 활용 검토 → Complex Patient History Summarization<br>• Inpatient Insight, 응급실용 문제요약, 이식환자 임상노트 등 |
| **Why sLLM?** | Lower Cost · Efficiency · Task-specific AI |
| **Results** | ✓ **업무시간 30%+ 절감**<br>✓ **간호 기록 작성 85% 감소** |

#### 📌 Case: Bayer | E.L.Y. Crop Protection Mini — *"General-purpose Model → Domain-specific Model"*

| | 내용 |
|---|---|
| **기업** | 아스피린으로도 유명한 독일의 글로벌 생명과학 기업 (제약/농업/작물과학) |
| **질문** | *이 지역에서 이 작물에 이 제초제를 사용할 수 있는가?* |
| **Problem** | • 방대한 Crop Protection 제품·규제 정보<br>• 지역·작물·시기별로 다른 적용 조건<br>• 전문가의 문서 검색 및 기술팀 문의에 많은 시간 소요 |
| **Solution** | • 농업 전문 **Domain-specific sLLM**<br>• Bayer가 보유한 **Product Label Data + Regulatory Rules + Expert-authored Q&A**를 이용해 Fine-tuning |
| **Results** | ✓ 며칠 또는 몇주가 걸리던 업무 → **30초 이내 단축**<br>✓ **5–10% Productivity Gain** |

```plain text
[ sLLM ]  +  [ Bayer Domain Data ]        →  [ Fine-tuning ]
                Product Labels                     ↓
                Regulatory Rules          [ E.L.Y. Crop Protection Mini ]
                Expert Q&A                         ↓
                                          [ Agricultural Expert Q&A ]
```

### ③ On-device AI : AI를 Cloud가 아니라 Device 안으로

- sLLM은 단순히 **"작은 ChatGPT"가 아니라, AI를 서버에서 PC와 스마트폰 안으로 가져오는 핵심 기술**
- **Privacy, Offline, Latency focus**

#### 📌 Case: Apple On-device Foundation Model

- Apple은 **Apple Intelligence**를 위해 약 **3B parameter**의 On-device Foundation Model을 개발
- 이를 **글 다듬기, 알림 요약, 텍스트 이해** 등의 기능에 활용

```plain text
Cloud LLM :   [Device] → [Internet] → [Server] → [Model] → [Server] → [Device]
On-device :   [Device] → [Model] → [Result]
```

**Writing Benchmarks (Summarization)**

| 구분 | 모델 | 점수 |
|---|---|---:|
| **Server** | Apple Server | **9.5** |
| | GPT-4 | 9.5 |
| **On-Device** | **Apple On-Device (약 3B)** | **9.1** |
| | Mistral-7B | 8.9 |

> 🤯 **약 3B 모델이 7B 모델을 이겼습니다.** 크기가 성능을 결정하는 절대 법칙이 아니라는 실증.

## 1-8. AI Agent : 하나의 거대한 AI → 여러 전문 AI의 조합

> *"One Model for Everything → Right Model for Each Task"*

- 최근 AI 시스템에서는 **작은 전문 모델과 큰 범용 모델을 조합하는 구조**가 중요해지고 있음
- **Agent / Router**는 요청에 따라 적절한 모델과 도구를 선택하고, 여러 전문 AI를 하나의 시스템으로 연결
- ⭐ **향후 AI 엔지니어에게 요구되는 역량 중 하나는 업무 특성에 따라 적절한 모델을 선택하고 조합하는 역량**

```plain text
                    ┌──→ [ Document Classification sLLM ]  Classify documents into categories
                    │
   ┌──────────┐     ├──→ [ Information Extraction sLLM ]   Extract key information from text
   │ AI Agent │ ────┤
   └──────────┘     ├──→ [ Function Calling sLLM ]         Call external APIs or tools
                    │
                    └──→ [ Complex Reasoning → Large Model ]  Handle complex reasoning
                                                              and open-ended questions
```

| 원칙 | 내용 |
|---|---|
| **Efficiency** | 단순한 작업은 작은 모델이 처리 → **GPU 자원과 비용 절감** |
| **Specialization** | 각 sLLM을 특정 데이터로 Fine-tuning → **특정 업무에 최적화** |
| **Performance** | **어려운 문제만 Large LLM으로 전달** → 필요한 곳에 큰 모델의 추론 능력 사용 |

> 💡 **머리는 크게, 손발은 가볍게.** 판단·복잡한 추론은 큰 모델, 정형 반복 처리는 sLLM.

---

# 2. sLLM 모델 탐색과 선택

## 2-1. 대표적인 Open-weight Model Family

| Model Family | 개발사 | 주요 특징 | 적합한 활용 |
|---|---|---|---|
| **Llama** | Meta | Open-weight 생태계를 확산시킨 대표 모델군, 다양한 도구·커뮤니티 지원 | 범용 LLM, Fine-tuning, 연구·서비스 |
| **Qwen** | Alibaba | 소형부터 대형까지 폭넓은 규모, 다국어·코딩·추론 등 다양한 모델군 | 범용 AI, Coding, Agent, Fine-tuning |
| **Gemma** | Google | Gemini 기술 기반의 경량 Open Model, On-device부터 Server까지 다양한 크기 | Local/Edge AI, Multimodal, Fine-tuning |
| **Phi** | Microsoft | 적은 Parameter로 높은 효율을 지향하는 Small Language Model 계열 | Task-specific AI, Edge, 기업 업무 특화 |

> ⚠️ **자주 하는 오해**
> "Llama"는 **하나의 모델이 아닙니다.** 하나의 **Model Family** 안에 여러 크기·용도의 모델이 존재합니다.

## 2-2. 모델 선택의 2단계 구조

```plain text
          [ Model Family ]
                 ↓
   Llama  /  Qwen  /  Gemma  /  Phi
                 ↓
          [ Model Size ]
                 ↓
  Small ←─────────────────────→ Large
  0.5B    1B    3B    7B    14B   …
    ↓                          ↓
 Faster Inference          High Capability
 Lower Memory              Higher Memory
 Fewer Resources           More Resources
```

> ✅ **핵심 문장**
> **"Model Selection = Resource Efficiency ↔ Capability"**
> 고려요소 : **Task · Quality · Memory · Latency · Cost**

### sLLM의 Capability(능력)란?

- 모델의 **종합적인 문제 해결 능력**, 더 다양하고 복잡한 Task를 수행할 수 있는 잠재적 능력
- Reasoning(추론), Language Understanding(언어 이해), Coding 등
- **복합적인 이해 + 추론 + 생성**이 필요한 업무일수록 높은 Capability 요구
- ⚠️ **Model Size가 커질수록 Capability가 높아지는 것은 "일반적 경향"이지 "절대 법칙"은 아님**
  (→ 1장 Apple 3B vs Mistral 7B 사례가 반례)

## 2-3. Hugging Face에서 모델 찾기

모델은 **Hugging Face**(https://huggingface.co/models)에서 탐색합니다.

**필터 축들:**

| 필터 | 예시 | 무엇을 거르나 |
|---|---|---|
| **Tasks** | Text Generation, Image-Text-to-Text, Text-to-Speech… | 무엇을 하는 모델인가 |
| **Parameters** | `<1B` / `6B` / `12B` / `32B` / `128B` / `>500B` | 내 GPU에 올라가는가 |
| **Libraries** | PyTorch, Transformers, GGUF, Diffusers… | 내 코드에서 쓸 수 있는가 |
| **Apps** | vLLM, llama.cpp, MLX LM, LM Studio, Ollama… | 내 실행 환경에서 돌아가는가 |
| **Licenses** | apache-2.0, mit… | 상업적으로 써도 되는가 |

> 💬 **Collections 활용**
> 공식 개발사 계정의 **Collections**(예: `huggingface.co/collections/Qwen/qwen35`)에 들어가면
> 한 세대의 모델들이 한 번에 정리되어 있어 탐색이 훨씬 빠릅니다.

## 2-4. ⭐ Base Model vs Instruct Model

이건 **반드시 구분해야 하는 개념**입니다. 이름이 똑같아 보여도 완전히 다른 모델입니다.

```plain text
Qwen/Qwen3.5-4B        ← Instruct Model (Post-trained)
Qwen/Qwen3.5-4B-Base   ← Base Model (Pre-trained only)
```

### 모델이 만들어지는 워크플로우

```plain text
   [Large-scale Data]
           ↓
      [Pre-training]      ← 대규모 텍스트로 언어 능력 형성
           ↓
      [Base Model]        ← "다음 토큰 예측"만 할 줄 아는 상태
           ↓
     [Post-training]      ← SFT / RLHF / Alignment …
           ↓
    [Instruct Model]      ← 지시를 따르고 대화할 수 있는 상태
```

### 비교표

| 항목 | **Instruct Model** | **Base Model** |
|---|---|---|
| 상태 | **Post-trained 모델** | **Pre-trained Base 모델** |
| 대화/지시 수행 | 바로 가능 | 아직 미흡 |
| 질문 → 답변 | 지시·수행·대화에 최적화 | **다음 토큰 예측**이 기본 목적 |
| 바로 Chat 활용 | 적합 | 부적합 |
| 추가 Fine-tuning | 가능 | 가능 |
| 주요 용도 | Chat, Agent, 추가 SFT | 계속된 Pretraining, 전문적인 FT |

> 🚨 **실무 함정**
> Base Model에 "안녕?"이라고 물으면 대화가 아니라 **문장을 이어 쓰기 시작합니다.**
> "안녕? 안녕하세요. 안녕히 가세요. 안녕은 인사말로…" 같은 식.
> **일반적인 SFT/QLoRA를 할 거면 → Instruct 모델을 우선 검토**하는 게 안전합니다.

## 2-5. Hugging Face Model Card 읽는 법

> ✅ **최신 모델보다 중요한 것은 "내 Task와 환경에 적합한 모델인가?"**

### Model Card에서 확인해야 할 핵심 정보 5가지

| # | 확인 항목 | 질문 |
|---|---|---|
| (1) | **Publisher** | Official인가 Community인가? |
| (2) | **Task** | Text / Vision / Multimodal? |
| (3) | **Size & Type** | 1B / 4B / 8B · **Base / Instruct** |
| (4) | **License** | Commercial use allowed? |
| (5) | **Compatibility** | Transformers / PEFT / Quantization 지원? |

### 태그(Badge)별 의미

| 표시 | 의미 | 실무적으로 보는 것 |
|---|---|---|
| `Qwen / Qwen3.5-4B` | Publisher / Model | 원 개발사가 공개한 모델인가? 파생모델인가? |
| `Image-Text-to-Text` | Task | 입력/출력 및 모델 용도, 무엇을 하는 모델인가? |
| `Transformers` | Library | 어떤 라이브러리에서 사용할 수 있는가? |
| `Safetensors` | Weight Format | 모델 weight 저장 형식 |
| `qwen_3_5` | Architecture / Model tag | 모델 계열·구조 |
| `conversational` | Capability / Task tag | 대화형 사용을 고려한 모델 |
| `Eval Results` | Evaluation | 공개된 평가 결과는 존재하는가? |
| `apache-2.0` | License | 상업적 활용에 문제가 없는가? 사용·수정·배포 조건 |

## 2-6. Model Tree — 파생 모델 읽기

```plain text
Model tree for Qwen/Qwen3.5-4B
  Base model ─── Qwen/Qwen3.5-4B-Base
    └ Finetuned (101)      ← this model
        ├ Adapters       485 models
        ├ Finetunes      464 models
        ├ Merges          10 models
        └ Quantizations  343 models
```

| 용어 | 의미 |
|---|---|
| **Adapters** | LoRA 등 **PEFT로 학습한 추가 가중치**를 Adapter 형태로 배포 |
| **Finetunes** | 원 모델을 특정업무·전문분야 등 **추가 학습하여 별도의 파생 모델**로 배포 |
| **Merges** | 여러 모델이나 학습 결과의 **weight를 결합**하여 만든 모델 |
| **Quantization** | **저정밀도 형태로 변환**하여 메모리와 추론 자원 요구량을 낮춘 모델 |

> 💡 `Qwen3.5-4B-Base` → **Post-training** → `Qwen3.5-4B` 라는 관계가 여기서 보입니다.

## 2-7. ⚖️ License도 모델 선택 기준이다

> ⚠️ **Open-weight ≠ Free to use without restrictions**
> 가중치를 공개했다고 해서 마음대로 써도 되는 건 아닙니다.

### ① Permissive Open Source (사용 제약이 적은 오픈소스)

상업적 이용·수정·배포를 폭넓게 허용하며, 소스/모델을 수정해 만든 결과물도 **반드시 동일한 오픈소스 라이선스로 공개할 필요가 없음**.

| License | 특징 | 핵심 차이 |
|---|---|---|
| **MIT** | 매우 단순하고 자유로운 라이선스 | 저작권·라이선스 고지 유지가 핵심 |
| **BSD** | MIT와 유사한 permissive license | 버전에 따라 저작자·기관 이름을 홍보에 사용하는 것을 제한 |
| **Apache-2.0** | 자유로운 사용 + 보다 상세한 법적 조항 | **명시적인 특허(Patent) 사용권**과 NOTICE 등의 규정 포함 |

> 💼 **기업 입장에서 Apache-2.0이 선호되는 이유**
> **명시적 patent grant(특허 사용 허가)** 와 **patent termination(특허 소송 시 권리 소멸)** 조항을 가지고 있어, 특허 리스크가 예측 가능합니다.

```plain text
Apache-2.0
  Commercial Use             ✓
  Modification / Fine-tuning ✓
  Redistribution             ✓
  Explicit Patent Grant      ✓
```

### ② Model-specific License (모델 개발사가 별도로 정한 조건)

- 상업적 이용·수정·Fine-tuning이 가능하더라도 **사용 제한, 재배포 조건 등 모델별 약관을 별도로 확인**해야 함
- **Ex) Gemma Series** = 상업적 활용 가능 + **Google의 사용 제한 정책 준수 필요**
- **Ex) Llama** = 상업적 활용 가능 + **Meta의 모델별 Community License 조건 확인**

### ③ Restricted License (제한적 라이선스)

- **Research Only / Non-commercial / Academic Only** 등
- 연구·교육 등 특정 목적으로 사용 범위를 제한
- 모델이 공개되어 있어도 **상업적 이용·서비스 배포·파생 모델 활용 등이 제한될 수 있음**
- **Ex) BrainIAC**, '26년 공개 뇌 MRI foundation model : **Research-Only License**

> 🚨 **실무 체크포인트**
> "Hugging Face에 올라와 있으니까 써도 되겠지"는 **틀렸습니다.**
> 서비스에 넣기 전 반드시 라이선스 원문을 확인하세요.

## 2-8. ⭐ Model Selection : Practical Guide

어떤 sLLM을 선택해야 할까? — **6단계 결정 프로세스**

```plain text
[ Task ]
   ↓          무엇을 시킬 것인가?
   │          Text Generation · Classification · Coding · Multimodal …
[ Model Family ]
   ↓          어떤 계열을 사용할 것인가?
   │          Qwen · Llama · Gemma · Phi …
[ Model Size ]
   ↓          내 환경에서 실행 가능한가?
   │          1B · 4B · 8B · 14B …
   │          Capability ↔ Memory · Latency · Cost
[ Model Type ]
   ↓          어떻게 사용할 것인가?
   │          일반적인 SFT / QLoRA  → Instruct 우선 검토
   │          Continued Pre-training → Base 검토
[ License ]
   ↓          실제 서비스에 사용할 수 있는가?
   │          Commercial Use / Modification / Redistribution 확인
   │          Apache-2.0 · MIT · Model-specific · Restricted …
[ Compatibility ]
              내 환경에서 실제로 Fine-tuning 가능한가?
              GPU / Quantization / Framework 지원 확인
              Transformers · PEFT · TRL · bitsandbytes · Unsloth …
```

## 2-9. ⭐ 모델에 부족한 것을 어떻게 채울 것인가? — Prompt vs RAG vs Fine-Tuning

이 세 가지를 헷갈리는 사람이 정말 많습니다. **"무엇이 부족한가"로 구분**하면 명확해집니다.

| 모델에 부족한 것 | 우선 고려 | 역할 |
|---|---|---|
| **지시·맥락 제공** | **Prompt** | 입력에 필요한 지시와 Context 제공 |
| **외부·최신 지식 활용** | **RAG** | 필요한 지식을 검색하여 Context로 제공 |
| **특정 Task·행동 학습** | **Fine-Tuning** | 모델의 **행동과 응답 패턴**을 학습 |

### 예시로 구분하기

| 질의 | 시스템 | 답 |
|---|---|---|
| *"올해 우리 회사의 출장비 규정이 얼마인가?"* | 사내 규정 Q&A 시스템 | → **RAG** : 규정 문서를 찾아 응답 |
| *"고객 문의에 항상 우리 회사 상담 양식으로 답변해줘"* | 고객 상담 자동화 시스템 | → **Fine-Tuning** : 원하는 응답 방식과 패턴을 학습 |

> ✅ **핵심 3문장**
> 1. **Knowledge → RAG / Behavior → Fine-Tuning**
> 2. Fine-Tuning으로도 지식을 넣을 수 있지만, **변하는 외부 지식**을 활용하는 문제라면 우선 RAG를 검토하는 경향
> 3. **Fine-Tuning의 주목적은 지식을 저장하는 것이 아니라, 모델의 행동을 바꾸는 것**

### ❓ Q. 도메인 특화 sLLM은 RAG가 더 적합하지 않아?

금융 전문 sLLM을 구축하는 경우로 보면:

| 질의 유형 | 적합한 방법 | 이유 |
|---|---|---|
| *"2026년 현재 회사의 대출상품 금리는 얼마인가?"* | **RAG** | 금리가 바뀔 때마다 모델을 다시 Fine-Tuning할 이유가 없음 |
| *"이 고객의 상담 기록을 보고 정상/관심/이탈위험으로 분류하라."* | **Fine-Tuning** | 반복되는 **입력/출력 패턴 자체**를 모델이 안정적으로 수행하도록 만드는 문제이기 때문 |

### ❓ Q. Fine-Tuning이 행동을 바꾸는 거라면, 프롬프트와 뭐가 달라?

같은 분류 질의를 두 가지로 처리해보면:

```plain text
Case 1)  긴 System Prompt + 5개 Example + Input  →  Qwen 1.7B  →  결과
Case 2)  Input                                    →  Specialized Qwen 1.7B  →  원하는 결과
```

> ✅ **Fine-Tuning의 가치는 단순히 "도메인 지식을 넣는다"가 아니라,**
> **작은 모델도 특정 업무를 안정적이고 반복적으로 수행하도록 전문화하는 데 있음**

Case 1은 매 호출마다 긴 프롬프트 토큰 비용을 내고, 결과도 흔들립니다.
Case 2는 프롬프트가 짧아지고(=비용↓·지연↓), 출력이 일관됩니다.

## 2-10. From sLLM to Fine-Tuning

```plain text
      [ Open sLLM ]
      사전 학습된 범용 모델
             ↓
   ┌─── 우리 Task에 적용시 한계 ───┐
   │  출력 형식 불일치              │  형식,길이,구조가 요구와 다름
   │  Task 성능 부족                │  특정 업무에서 정확도와 품질 낮음
   │  업무응답 패턴 불일치          │  도메인 특성, 표현 방식이 맞지 않음
   │  결과 일관성 부족              │  같은 입력에도 출력 품질이 흔들림
   └────── Task Adaption ──────────┘
             ↓
      [ Fine-Tuning ]
      모델을 우리의 Task에 특화 학습
```

> ✅ **좋은 범용 모델이 곧 좋은 업무 모델은 아님**
> 범용 sLLM을 우리의 Task와 응답 방식에 맞게 **Adaptation** 필요 → **Fine-Tuning**

이제 두 가지 질문이 남습니다. **이것이 3~5장의 주제입니다.**
- 그런데 LLM의 Fine-Tuning에서는 **무엇을 정답으로 놓고 학습**하는 것일까?
- **수십억 개의 Parameter를 전부 다시 학습**해야 할까?

---

# 3. Inside the LLM : Transformer Recap

> 🎯 **이 장의 목표**
> Fine-Tuning에서 "무엇이 바뀌는지" 이해하려면 **가중치 행렬(W)** 이 뭘 하는지 알아야 합니다.
> 그래서 먼저 **내적 → 행렬곱 → 선형변환 → Softmax → Attention** 순서로 기초를 다집니다.

## 3-1. Dot Product (내적)

### 계산

두 벡터 a, b가 이루는 각이 θ일 때:

$$\vec{a} \cdot \vec{b} = |\vec{a}||\vec{b}|\cos\theta = \sum_{i=1}^{d} a_i b_i$$

```plain text
a = [1, 2, 3],  b = [4, 5, 6]

aᵀb = [1 2 3] · [4 5 6]ᵀ
    = 1×4 + 2×5 + 3×6
    = 4 + 10 + 18 = 32
```

### 내적의 숨은 의미 (Implicit meaning)

- 벡터의 내적은 기하학적으로 **한 벡터를 다른 벡터 위로 정사영시킨 길이 × 다른 벡터의 길이**
- **크기와 방향을 모두 고려한 "유사도" 개념**

| 정사영된 길이 | 벡터간 각도 | 유사도 |
|---|---|---|
| **짧다** | 크다 | **작다** |
| **길다** | 작다 | **크다** |

> 💡 **왜 이게 중요한가?**
> Attention이 "어떤 토큰이 어떤 토큰을 주목하는가"를 계산할 때 쓰는 것이 바로 **이 내적**입니다.
> **내적이 크다 = 두 토큰이 문맥적으로 관련이 깊다.**

## 3-2. Matrix Multiplication (행렬곱)

```plain text
A(2×3)        B(3×2)        AB(2×2)

[2 1 3]       [5 2]         [20 29]
[4 0 2]   ×   [1 4]    =    [26 22]
              [3 7]

(AB)₁₁ = (2·5) + (1·1) + (3·3) = 10 + 1 + 9 = 20
(AB)₁₂ = (2·2) + (1·4) + (3·7) = 4 + 4 + 21 = 29
```

> ✅ **핵심**
> - 행렬곱의 각 원소는 **행(Row) 벡터와 열(Column) 벡터의 내적(Dot Product)**
> - **Matrix Multiplication = Row × Column Dot Products**

## 3-3. 선형변환 (Linear Transformation)

```plain text
x = [1  2  3]     W = [2   0]        y = [4  1]
     (1×3)            [1  -1]  →         (1×2)
                      [0   1]
                      (3×2)
```

3차원 벡터 x는 행렬 W와 곱을 통해 **2차원 벡터로 선형변환**됩니다.

### Definition

- 선형변환은 벡터의 **덧셈과 배수 관계를 유지**하면서, 벡터를 다른 벡터로 매핑하는 함수. **행렬곱은 이러한 선형변환을 계산하는 방법**
- 벡터를 **회전·확대·축소·반사**하거나 다른 차원의 벡터로 바꾸되, **공간의 직선성과 원점을 보존**하는 변환

> 💡 **직관**
> **선형변환은 벡터 x를 새로운 좌표로 이동시킵니다.**
> LLM 안의 `W_Q`, `W_K`, `W_V` 같은 가중치 행렬이 하는 일이 정확히 이겁니다.
> → **6장 LoRA는 바로 이 W를 어떻게 효율적으로 바꿀 것인가에 대한 이야기입니다.**

## 3-4. Softmax function : Scores to Probabilities

$$\text{Softmax}(z_i) = \frac{e^{z_i}}{\sum_{j=1}^{n} e^{z_j}}$$

| Score | → | Softmax |
|---|---|---|
| 2.1 | → | 0.58 |
| 1.3 | → | 0.26 |
| 0.2 | → | 0.09 |
| -0.5 | → | 0.07 |

**Concept**
- Softmax는 여러 실수 점수를 **비교 가능한 확률 분포로 변환**
- 각 점수가 전체에서 차지하는 **상대적 비중**을 계산
- 모든 출력값은 **0과 1 사이**
- 출력값의 **합은 1**
- 입력값의 **상대적인 크기 관계를 유지**

## 3-5. ⭐ Transformer Encoder — Scaled Dot-Product Self Attention

예제 문장: **"I study AI hard"**

### Step 1. Input Vector → Q, K, V 생성

Input vector에 서로 다른 가중치 행렬을 곱해 3개를 만듭니다.

```plain text
                 ┌── ×W^Q ──→  Q (query)   "내가 누구를 참고하지? 어디에 집중할래?"
[Input vector] ──┼── ×W^K ──→  K (key)     "Query 토큰들로부터 참고될 수 있는 정보"
                 └── ×W^V ──→  V (value)   "실제 전달되는 정보"
```

> 💬 **도서관 비유**
> - **Q(query)** = 내가 찾는 검색어
> - **K(key)** = 각 책의 색인(제목표)
> - **V(value)** = 그 책의 실제 내용
>
> 검색어(Q)와 색인(K)을 대조해 관련도를 매기고, 관련도만큼 내용(V)을 섞어 옵니다.

### Step 2. Score Matrix = Q · Kᵀ

```plain text
        I   study  AI  hard
   I  [               ]
study [   Score      ]     ←  Q 와 Transpose된 K 간 matrix multiplication
   AI [   Matrix     ]
 hard [               ]
```

- Score Matrix의 첫 row는 **Q의 "I"와 K의 각 토큰 벡터가 매칭되어 만들어짐 (Dot product)**
- 단어간 **문맥상 관계가 높을수록 큰 값**
- **(i, j) 셀값의 의미 : i번째 토큰이 j번째 토큰을 얼마나 주목하느냐?**

### Step 3. Scaling (÷√d_k) → Softmax

```plain text
Score Matrix  →  (1) Divide by √d_k  →  (2) Softmax(확률화)  →  Attention Score

        I    study   AI   hard
   I  [0.8   0.2    0.0   0.0]
study [ …                     ]
```

> ❓ **왜 √d_k로 나누는가?** (자주 나오는 질문)
> - Q, K 벡터 **차원(d_k)이 커질수록 내적 값의 분산이 커져서**, Softmax 함수의 **기울기(gradient)가 매우 작아지는 문제**가 발생
> - 이를 해소하기 위해 **K 차원수의 제곱근으로 나눠줌** — 일종의 **Scaling**
> - 이후 Softmax를 통해 확률화를 진행
> - 이로써 내적 값의 크기 범위가 **안정화**되고, **Softmax가 적당한 기울기를 유지**
>
> 💡 즉, **Gradient Vanishing 방지 장치**입니다.

### Step 4. Attention Score × V = Attention Output

```plain text
[Attention Score] · [V (value)] = [Attention Output (Vector Representation)]
```

- 토큰간 **연관성(유사도)** 를 담고 있는 Attention Score Matrix는 각 토큰이 다른 토큰을 얼마나 주목해야 하는지에 대한 **가중치 행렬**
- 이에 **실제 정보(V)를 행렬곱하여 문맥 벡터를 생성** = 각 토큰이 **다른 토큰들의 정보를 비율대로 섞어 만든 새 표현**

### 최종 수식

$$\text{Attention}(Q, K, V) = \text{Softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right)V$$

```plain text
     Scaled Dot-Product Attention

            [ MatMul ]        ← × V
                ↑
            [ SoftMax ]
                ↑
            [ Mask (opt.) ]   ← Decoder에서 사용 (3-6절)
                ↑
            [ Scale ]         ← ÷ √d_k
                ↑
            [ MatMul ]        ← Q × Kᵀ
             ↑     ↑     ↑
             Q     K     V
```

## 3-6. Transformer Decoder — Masked Self Attention (Causal Masking)

### Problem

- 어텐션 메커니즘은 **모든 단어들이 나와 있을 때** 서로 간의 문맥을 파악하는 것이지, 그 주어진 문장 **그 다음에 토큰을 예상하기 위한 구조는 아님**
- 주어진 정보를 가지고 **다음 단어를 예측하는 구조로 변경**하려면?

### Ideation — 셀프어텐션을 디코더로 사용하기

```plain text
I ______________
I study ________
I study AI _____
```

- **주어진 토큰들만 가지고** 서로를 참조하여 알맞은 피처들을 뽑아내고 그를 기반으로 **다음 토큰을 예측**하도록 한다면?
- 생성은 **주어진 토큰 안에서 다음 토큰을 예상하는 것**, 그렇게 해보자

### Masked Self Attention

미래 토큰을 **X(차단)** 처리합니다.

```plain text
Attention Score (하삼각만 살아있음)

        I    study   AI   hard
   I  [1.0    X      X     X ]
study [0.3   0.7     X     X ]
   AI [0.1   0.3    0.6    X ]
 hard [0.3   0.2    0.1   0.4]
```

**Learning**
- 주어진 토큰들 사이의 문맥을 학습하여 **다음 토큰 예측**
- 이때 **Y는 다음 토큰**
- Training step마다 Attention Score와 **Ground Truth와 비교하여 Loss 계산**

> 💡 **왜 이게 중요한가?**
> Masking이 없으면 모델은 "정답을 커닝"하게 됩니다. "I study __" 를 예측할 때 이미 "AI"를 봤다면 학습이 의미가 없죠.
> **Causal Mask = 커닝 방지 장치.**

---

# 4. How LLM Learns

## 4-1. The Big Picture of LLM Training

```plain text
        [ Text ]              "오늘 날씨가 정말 좋다"
        학습 데이터
            ↓
      [ Tokenization ]        [오늘] [날씨] [가] [정말] [좋다]
        토큰 변환
            ↓
  ┌→ [ Next Token Prediction ]  입력 : [오늘] [날씨] [가] [정말]
  │     다음 토큰 확률 예측       출력 : [좋다] 0.62 / [춥다] 0.15 / [맑다] 0.08 …
  │         ↓
  │   [ Loss ]                 정답 토큰의 예측 확률은 충분히 높은가?
  │     정답과 예측 비교         예측된 확률분포를 정답과 비교
  │         ↓
  │   [ Backpropagation ]      Gradient 계산
  │     Gradient 계산
  │         ↓
  └── [ Parameter Update ]     오차가 줄어드는 방향으로 파라미터 수정
        가중치 수정             Repeat across batches and epochs
```

> ✅ **LLM Learning**
> - 다음 토큰을 더 잘 예측하도록 오차를 계산하고, Parameter를 반복적으로 업데이트하는 과정
> - **Predict → Compare → Update → Repeat**
> - **LLM은 "예측의 오차"로부터 학습합니다.**

## 4-2. Transformer로 들어가는 Token의 여정

```plain text
   [ Text ]                "오늘 날씨가 정말 좋다"
   원문 데이터
      ↓ Tokenizer
   [ Tokens ]              [오늘] [날씨] [가] [정말] [좋다]
   토큰 변환
      ↓ Vocabulary Encoding
   [ Token IDs ]           [1245] [892] [31] [5102] [5721]
   토큰ID 변환
      ↓ Embedding Lookup
   [ Token Embeddings ]    [e₁] [e₂] [e₃] [e₄] [e₅]
   벡터 변환
      ↓ Transformer Blocks
   [ Contextualization ]   [z₁] [z₂] [z₃] [z₄] [z₅]
   문맥이 반영된 표현 생성
```

- **Tokenizer**는 텍스트를 Token으로 분할하고 각 Token을 **Vocabulary의 ID로 변환**
- 모델 내부에서는 각 Token ID에 대응하는 **Embedding Vector를 조회**
- **Transformer Blocks**이 주변 Token과의 관계를 반영하여 **Contextual Representation**을 생성

## 4-3. From Raw Text to Training Data — 정답은 어디서 오는가?

> 🎯 **핵심 질문의 답: "정답 라벨을 사람이 붙이지 않습니다. 다음 토큰이 정답입니다."**

### Training Data Sample

**Raw Text = "오늘 날씨가 정말 좋다"**

| Position | 1 | 2 | 3 | 4 |
|---|---|---|---|---|
| **Input** | [오늘] | [날씨] | [가] | [정말] |
| **Label** | [날씨] | [가] | [정말] | [좋다] |
| Input IDs | [1245] | [892] | [31] | [5102] |
| Label IDs | [892] | [31] | [5102] | [5721] |

**How Training Samples Are Created**
- Tokenizer는 원문을 Token Sequence로 변환
- Input의 각 Token **다음에 오는 Token을 Label로 구성**
- 따라서 Input과 Label은 **한 Token만큼 Shift된 관계**

> ✅ **"각 위치의 Label은 바로 다음 Token"**
> 이것이 **Self-Supervised Learning(자기지도학습)** 입니다. 라벨링 비용이 0이라 대규모 학습이 가능했던 이유.

## 4-4. Causal Language Modeling

### 무엇을 학습할 것인가?

| Position | Input (실제로 참조할 수 있는 문맥) | Label |
|---|---|---|
| 1 | [오늘] | [날씨] |
| 2 | [오늘] [날씨] | [가] |
| 3 | [오늘] [날씨] [가] | [정말] |
| 4 | [오늘] [날씨] [가] [정말] | [좋다] |

이전 Token을 바탕으로 다음 Token을 예측하는 학습 방식:

$$P(x_1, \ldots, x_T) = \prod_{t=1}^{T} P(x_t \mid x_{<t})$$

### 어떤 정보를 볼 수 있는가? — Causal Mask

✓ : Attention 허용 / ✗ : 차단

| Q\K | 오늘 | 날씨 | 가 | 정말 | 좋다 |
|---|---|---|---|---|---|
| **오늘** | ✓ | ✗ | ✗ | ✗ | ✗ |
| **날씨** | ✓ | ✓ | ✗ | ✗ | ✗ |
| **가** | ✓ | ✓ | ✓ | ✗ | ✗ |
| **정말** | ✓ | ✓ | ✓ | ✓ | ✗ |
| **좋다** | ✓ | ✓ | ✓ | ✓ | ✓ |

> ✅ 학습 시 **전체 Token Sequence를 한 번에 입력**하지만, Causal Mask가 각 위치에서 **미래 Token을 참조하지 못하도록 제한**

## 4-5. ⚠️ Context Length vs Attention Cost — 왜 긴 문맥이 비싼가

### Why Attention Becomes a Bottleneck

```plain text
  4 × 4 Attention Matrix          8 × 8 Attention Matrix
  Context Length: 4 Tokens        Context Length: 8 Tokens
                        Context 2×
     4 × 4 = 16          ────→        8 × 8 = 64
     Attention Pairs                  Attention Pairs
```

**Context가 2배 → 연산은 4배**

| Context Length | Attention 관계 수 | 상대 비용 |
|---|---|---|
| 1K tokens | 약 1M | **1×** |
| 2K tokens | 약 4M | **4×** |
| 4K tokens | 약 16M | **16×** |
| 8K tokens | 약 64M | **64×** |

- Self-Attention은 각 Token과 **다른 모든 Token 간의 관계를 계산**
- 따라서 Context Length가 T일 때 Attention Score Matrix의 크기는 **T×T**
- Context가 길어질수록 연산량과 메모리 사용량이 **빠르게 증가**
- 이는 **Long-Context LLM의 주요 병목** 중 하나가 됨

### Causal Mask를 써도 여전히 O(T²)

```plain text
| Q\K |X₁ |X₂ |X₃ |X₄ | # Ref. |
| X₁  | ✓ | ✗ | ✗ | ✗ |   1    |
| X₂  | ✓ | ✓ | ✗ | ✗ |   2    |
| X₃  | ✓ | ✓ | ✓ | ✗ |   3    |
| X₄  | ✓ | ✓ | ✓ | ✓ |   4    |
                          ─────
              1 + 2 + 3 + 4 = 10
```

유도:

$$1 + 2 + \cdots + T = \frac{T(T+1)}{2} = \frac{1}{2}T^2 + \frac{1}{2}T \approx \frac{1}{2}T^2 \approx O(T^2)$$

| T | ½T² | ½T |
|---|---|---|
| 10 | 50 | 5 |
| 1,000 | 500,000 | 500 |
| 10,000 | **50,000,000** | 5,000 |

> ✅ Causal Mask Attention의 참조 관계는 Full Attention의 **약 절반**이지만, Context Length에 따른 **증가율은 여전히 T²**
> → 상수배 절감일 뿐 **차수(order)는 그대로**입니다.

## 4-6. Teacher Forcing — 학습할 때는 실제 Token, 생성할 때는 예측 Token

**Concept**
- Teacher Forcing은 학습 시 모델이 이전에 예측한 Token이 아니라, **학습 데이터에 있는 실제 정답 Token을 다음 위치의 입력 문맥으로 제공**하는 방식

| **Training: Teacher Forcing** | **Inference: Autoregressive Generation** |
|---|---|
| 실제 이전 Token 사용 | 모델이 생성한 이전 Token 사용 |
| 정답 Sequence가 존재 | 정답 Sequence가 없음 |
| 여러 위치의 예측을 **병렬 계산** | 일반적으로 **한 Token씩 순차 생성** |
| 오류가 다음 입력으로 직접 전파되지 않음 | **생성 오류가 이후 문맥에 누적**될 수 있음 |

### 같은 오답이 나왔을 때의 차이

```plain text
[Training]                              [Inference]
모델 예측 : [오늘] → [기온이] <잘못됨>    모델 예측 : [오늘] → [기온이] <잘못됨>
        ↓                                       ↓
다음 학습 문맥)                          다음 토큰 예측)
[오늘] [날씨가]  ⭕                       [오늘] [기온이] → 다음 Token 예측
[오늘] [기온이]  ❌                       (틀린 토큰이 문맥에 그대로 포함)
```

- **학습**: 모델이 잘못 예측했더라도, 다음 위치에는 **실제 정답이 포함된 문맥을 제공**
- **추론**: 모델이 잘못된 Token을 생성하면 **그 Token이 다음 문맥에 포함** → 오류 누적(Exposure Bias)

## 4-7. 긴 Corpus를 LLM은 어떻게 학습할까?

**Long Corpus → Fixed-length Token Sequences → Training**

```plain text
                All Token Stream
[1][2][3][4] [5][6][7][8] [9][10][11][12] …
└ Sequence 1 ┘└ Sequence 2┘└ Sequence 3 ─┘
                    ↓
Sequence Length = 4
  Sequence 1 : [1][2][3][4]
  Sequence 2 : [5][6][7][8]
  Sequence 3 : [9][10][11][12]
```

- 일정한 길이의 Token Sequence로 구성하여 **반복적으로 학습**
- 각 Sequence가 **Transformer의 학습 입력 단위**가 됨
- Attention의 크기도 한 번에 처리하는 **Sequence Length에 의해 결정** (4×4)

## 4-8. LLM은 다음 토큰을 어떻게 선택할까? — Next Token Probability Distribution

```plain text
  [ Transformer Output — Hidden States ]
    (Sequence Length × Hidden Size) = (512 × 1,024)
                 ↓
  [ Linear / LM Head ]
    Weight: 1,024 × Vocabulary Size
    (512 × 1,024) × (1,024 × V)
                 ↓
  [ Logits ]
    (512 × Vocabulary Size)
                 ↓
  [ Softmax ]  Applied Across Vocabulary Dimension
                 ↓
  [ Next-Token Probability Distribution For Every Position ]

    Position 1   →  "날씨가" 70%  |  "오늘은" 15%  | …
    Position 2   →  "정말"  40%  |  "매우"   30%  | …
    Position 3   →  "좋다"  80%  |  "맑다"   10%  | …
      ⋮
    Position 512 →  "."     60%  |  "!"      20%  | …
```

- Transformer는 **모든 토큰 위치에서 다음 토큰의 확률분포를 동시에 계산**
- 각 토큰의 Hidden State를 **LM Head가 Vocabulary 크기의 Logit으로 변환**

## 4-9. ⭐ Cross-Entropy Loss : 예측에서 학습으로

$$L = -\sum_{i=1}^{V} y_i \log(p_i)$$

> **높은 정답 확률은 낮은 Loss로, 낮은 정답 확률은 높은 Loss로**

| 정답 토큰을 몇 %로 예측했나 | Loss = −log(p) |
|---|---|
| 100% | −log(1) = **0** |
| 80% | −log(0.8) = **0.22** |
| 60% | −log(0.6) = **0.51** |
| 40% | −log(0.4) = **0.91** |
| 20% | −log(0.2) = **1.6** |

> ✅ **확률(확신)이 낮을수록 loss값(패널티)은 기하급수적으로 증가**

### Loss 산출 예시

| 토큰 | 정답 (yᵢ) | 예측 확률 (pᵢ) |
|---|---|---|
| **좋다** | **1** | 0.80 |
| 맑다 | 0 | 0.12 |
| 춥다 | 0 | 0.05 |
| 덥다 | 0 | 0.03 |

$$L = -[1\log(0.80) + 0\log(0.12) + 0\log(0.05) + 0\log(0.03)] = -\log(0.80) \approx 0.223$$

> 💡 **정답이 아닌 토큰은 yᵢ=0이라 전부 사라집니다. 결국 "정답 토큰에 몇 %를 줬느냐"만 남습니다.**

- Cross-Entropy Loss는 **정답 토큰에 부여한 확률을 예측 오차로 변환**
- 각 위치의 Cross-Entropy Loss를 **평균**하고, 이를 **역전파**하여 모델의 파라미터를 업데이트

---

# 5. Fine-Tuning Map

## 5-1. Pre-training : 범용 언어 능력의 형성

**Concept**
- 대규모 텍스트를 사용해 **문법·어휘·지식** 등 언어 전반의 기초 능력을 학습
- **정답 라벨 없이** 텍스트 자체에서 학습 신호를 만드는 **자기지도학습(Self-Supervised Learning)** 방식
- **다음 토큰 예측**을 통해 범용적인 언어 표현과 생성 능력을 형성
- **특정 작업이나 서비스에 최적화된 상태는 아님**

```plain text
   Pre-Training                    Fine-Tuning
(Computationally Expensive)         (Cheaper)

     [ LLM ]         ────────→        [ LLM ]
        ↑                                ↑
  Large Unlabeled Corpus         Small Labeled Corpus
```

## 5-2. What is Fine-Tuning?

> **Pre-trained Model에 추가 데이터를 학습시켜 특정 목적에 맞게 능력과 행동을 조정하는 과정**

**Concept**
- 이미 사전 학습된 모델에 추가 데이터를 학습시켜 특정 목적에 맞게 모델의 능력과 행동을 조정
- 처음부터 모델을 다시 학습하지 않고, 학습된 언어 능력을 기반으로 **Task · Domain · Preference**에 적응
- 모델을 실제 업무와 서비스 요구사항에 맞게 조정하는 **Model Adaptation** 과정

| Pre-training | Fine-Tuning |
|---|---|
| 범용적인 언어 능력 형성 | 특정 목적에 맞게 능력과 행동 조정 |
| 대규모 일반 텍스트 | 상대적으로 작고 목적에 맞게 구성된 데이터 |
| 모델의 기초 능력 구축 | 학습된 능력의 적응과 특화 |
| 높은 학습 비용 | 상대적으로 적은 비용과 시간 |

## 5-3. Fine-Tuning이 필요한 순간 (4가지)

> Prompt와 RAG만으로 일관되게 구현하기 어려운 능력과 행동을 모델에 학습

### ① 특정 작업 능력 강화 (Task Adaptation)
- 범용 모델은 다양한 작업을 수행하지만, 특정 작업에서는 **정확도와 일관성이 부족**할 수 있음
- 분류·요약·정보 추출·코드 생성 등 반복되는 Task에 특화된 수행 능력을 학습
- **ex)** 의료 기록의 핵심 항목을 빠짐없이 추출하는 전문 요약

### ② 도메인 언어와 표현 학습 (Domain Adaptation)
- 의료·법률·금융·과학 등 전문 분야의 용어, 표현 방식과 문서 구조를 학습
- 도메인 특유의 문맥과 표현 방식을 이해하고 해당 분야에 적합한 응답을 생성
- **ex)** 의료 논문의 표현과 문서 구조에 익숙한 도메인 모델

### ③ 일관된 응답 행동 학습 (Behavior Customization)
- 응답 형식·문체·절차·정책 등 반복적으로 요구되는 행동 패턴을 학습
- **긴 System Prompt 없이도** 일정한 형식과 스타일로 응답하도록 조정
- **ex)** 고객 문의에 항상 회사의 상담 절차와 지정된 형식, 문체로 응답

### ④ 작은 모델의 실용적 성능 확보 (Efficient Specialization)
- 대형 범용 모델 대신 작은 모델을 특정 업무에 집중적으로 학습시켜 실용적인 성능 확보
- 반복 호출이 많은 고정 업무에서 **추론 비용과 지연시간을 줄일 가능성**이 있음
- **온프레미스 환경**에서 특정 업무에 최적화된 전용 모델로 활용 가능
- **ex)** 대형 범용 LLM API → 특정 분류 업무에 특화된 Fine-Tuned sLLM

### ⭐ 정리: Why sLLM? + Why Fine-Tuning?

| **Why sLLM?** | **Why Fine-Tuning?** |
|---|---|
| 왜 **작은 모델**을 선택하는가? | 왜 모델을 **추가 학습**하는가? |
| Model Choice & Deployment | Capability & Behavior Adaptation |
| Privacy · Control · Efficiency | Adaptation · Specialization · Consistency |

> ✅ **Fine-Tuned sLLM = Why sLLM? + Why Fine-Tuning?**

## 5-4. ⭐⭐ Fine-Tuning은 어떻게 설계할까? — 2개의 축

> *"What should the model learn, and how should its parameters be updated?"*
>
> **Fine-Tuning Strategy = Learning Objective × Update Method**

**이 장의 핵심입니다.** Fine-Tuning 방법론은 두 개의 독립적인 축으로 이해합니다.

## 5-5. 축 1️⃣ — What to Learn : 무엇을 학습할 것인가?

| | **Continued Pre-training** | **Supervised Fine-Tuning** | **Preference Alignment** |
|---|---|---|---|
| **학습 목적** | 도메인의 언어와 지식에 적응 | 원하는 업무와 응답 방식 학습 | 더 바람직한 답변 기준 학습 |
| **학습 데이터** | 도메인 원문 말뭉치 | 입력과 모범 답변 | 선호·비선호 답변 쌍 |
| **모델이 배우는 것** | 전문 용어·표현·문서 패턴 | 지시 수행·출력 형식·말투 | 유용성·안전성·응답 품질 |
| **대표 방법** | Domain-Adaptive Pre-training | Instruction Tuning | RLHF |

### ① Continued Pre-training — *"이 분야의 원문을 더 학습하라"*

- 별도의 질문과 답변을 만들지 않고, **원문 자체를 학습 데이터로 사용**
- 도메인의 용어, 표현, 문서 구조와 지식 분포에 적응
- 기존 Base Model의 **다음 토큰 예측 학습을 이어서 수행**
- 모델은 다음 내용을 학습: 도메인 전문 용어 / 문장과 문서의 표현 방식 / 개념 간 관계 / 도메인에서 자주 등장하는 지식과 패턴

**대상 문서:** 금융 보고서 · 의료 논문 · 법률 문서 · 소스 코드 · 사내기술문서

```plain text
Data Example
수정 듀레이션은 시장금리 변화에 대한 채권 가격의 민감도를 나타내는 지표이다.
```

### ② Supervised Fine-Tuning (SFT) — *"이런 요청에는 이렇게 답하라"*

- 사용자의 입력과 **사람이 작성한 모범(정답) 답변**을 학습
- **질문–답변, 지시–수행** 형태
- 특정 업무 수행 방식과 원하는 출력 형식을 습득
- 모델은 다음 내용을 학습: 사용자 지시를 따르는 방법 / 질문에 답변하는 방식 / 요약·분류·추출 등의 업무 수행 절차 / 원하는 말투와 출력 형식 / 조직이나 서비스의 응답 패턴

```plain text
Data Example
Question:  듀레이션을 초보자에게 설명해 주세요.
Answer:    듀레이션은 금리가 변할 때 채권 가격이
           얼마나 움직이는지를 나타내는 지표입니다.
```

### ③ Preference Alignment — *"여러 답변 중 이런 답변이 더 좋다"*

- 하나의 질문에 대한 **여러 답변을 비교**하고, 사람이 더 선호하는 답변의 특성을 학습
- 답변 간 비교 또는 평가 데이터를 활용
- **유용성, 정확성, 안전성** 등 바람직한 답변의 기준을 학습
- **SFT 이후** 모델의 응답 품질과 행동을 추가로 정렬
- 모델은 다음과 같은 선호 기준을 학습: 더 유용한 답변 / 더 정확하고 명확한 답변 / 안전한 답변 / 불필요하게 장황하지 않은 답변 / 조직의 정책과 가치에 맞는 답변

```plain text
Data Example
Question : 감기에 항생제를 먹어야 하나요?

Preference Answer :
감기는 대부분 바이러스성이라 항생제가
중요하지 않습니다. 정확한 판단은 의료진과 상담하세요.

Non-Preference Answer :
항생제를 복용하면 빨리 좋아질 수 있습니다.
```

## 5-6. 축 2️⃣ — How to Update : 파라미터를 어떻게 학습할 것인가?

> 이 축에는 **두 갈래**뿐입니다 — **Full Fine-Tuning**(5-7)과 **PEFT**(5-9).

| | **Full Fine-Tuning** | **PEFT** (Parameter-Efficient Fine-Tuning) |
|---|---|---|
| **업데이트 범위** | 모델의 **전체** 파라미터 | 일부 파라미터 또는 **추가 모듈** |
| **Base Model** | 전체 가중치 업데이트 | **대부분의 가중치 고정(Freeze)** |
| **학습 자원** | 매우 큼 | 상대적으로 작음 |
| **저장 용량** | 모델 전체를 저장 | **작은 Adapter만 저장** |
| **대표 방법** | Full Parameter Update | **LoRA · QLoRA** |
| **적합한 상황** | 충분한 GPU와 대규모 데이터 | 제한된 자원에서 빠른 실험과 배포 |

## 5-7. ⭐ Full Fine-Tuning — *"모델 전체를 다시 학습한다"*

> 📄 **자료 p67 · p69** — Fine-Tuning Map : *How to Update*

### Concept

- 모델의 **모든 파라미터**를 학습
- 모델의 표현과 행동을 폭넓게 변경 가능
- 높은 GPU 메모리와 학습 비용 필요
- 데이터가 부족하면 **기존 능력이 손상될 위험** 존재
- 작업별로 변경된 **전체 모델을 각각 저장** 필요
    - 고객 상담 모델 → 전체 7B 체크포인트 저장
    - 금융 분석 모델 → 전체 7B 체크포인트 저장

```plain text
            Base Model Parameters
  ██ ██ ██ ██ ██ ██ ██ ██ ██ ██ ██ ██
         All Parameters Updated
                   ⇩
```

```plain text
7B Base Model  →  Full Fine-Tuning  →  7B Fine-Tuned Model (Full Model Checkpoint)
```

### When to Use? — 4가지 경우

| # | 상황 | 설명 |
|---|---|---|
| 1 | **학습·저장 비용보다 최고의 성능이 중요한 경우** | 모든 파라미터가 자유롭게 변할 수 있어 더 큰 성능 향상 가능. 코드·수학처럼 새로운 복잡한 능력을 학습하는 연구에서는 Full FT가 PEFT보다 정확도와 데이터 효율성이 높았다고 보고 |
| 2 | **전체 파라미터를 안정적으로 학습할 충분한 데이터가 있는 경우** | 대규모 SFT 데이터로 Base Model에 지시문 이해, 대화 형식 학습, 추론 능력을 본격적으로 학습시키는 경우 (Base Model → Instruction Model) |
| 3 | **모델을 광범위하게 변화시켜야 하는 경우** | 의료·법률·금융·과학처럼 기존 모델의 언어 분포와 크게 다른 대규모 말뭉치를 학습시켜, 모델의 내부 표현과 도메인 이해 자체를 바꾸려는 경우 (Continued Pre-training). Meta의 의료 특화 모델 **Meditron** 사례 : SFT & Full-FT |
| 4 | **모델 규모가 상대적으로 작고 자원이 충분할 때** | 수억~수십억 파라미터 규모의 sLLM은 Full Fine-Tuning 비용이 현실적일 수 있음. 이런 경우 하나의 완성된 전용 모델을 만드는 선택이 가능 |

> ✅ **사라진 방법이 아니라, 최대 성능과 근본적인 모델 변화가 필요할 때 선택하는 방법**

> 🔗 출처(Meditron) : https://ai.meta.com/blog/llama-2-3-meditron-yale-medicine-epfl-open-source-llm

## 5-8. 📎 [참고] Model Checkpoint

**Concept**
- 학습 중 특정 시점의 모델 상태를 저장한 파일 또는 파일 묶음
- 일반적으로 다음 정보가 포함될 수 있음: 모델의 학습된 **가중치**, 모델 **구조와 설정**, **Optimizer 상태**, **Learning-rate**, 현재 학습 **Step 또는 Epoch**
- 이를 저장하면 **학습을 중단한 지점부터 다시 시작**하거나, 특정 시점의 모델을 평가·배포할 수 있음

| 표현 | 강조점 |
|---|---|
| **Model** | 모델 자체 또는 구조와 기능 |
| **Model Weights** | 학습된 파라미터 값 |
| **Checkpoint** | 특정 학습 시점에 저장된 모델 상태 |
| **Full Model Checkpoint** | 전체 모델 파라미터를 포함한 저장 결과 |
| **Adapter Checkpoint** | LoRA 등 추가 학습 파라미터만 저장한 결과 |

> ✅ Full Fine-Tuning은 **목적별로 전체 모델 가중치를 포함한 체크포인트를 저장**하는 반면,
> ✅ LoRA는 **동일한 Base Model을 공유**하고 **작은 Adapter Checkpoint만 별도로 저장**

## 5-9. ⭐ PEFT — *"Base Model은 고정하고, 작은 부분만 학습한다"*

> 📄 **자료 p70 · p71** — Fine-Tuning Map : *How to Update*

**Concept**
- 기존 모델의 **대부분을 동결(Freeze)**
- 소수의 파라미터 또는 **추가된 Adapter만 학습**
- 학습 메모리와 저장 비용을 크게 절감
- **하나의 Base Model에 여러 Adapter를 교체**하여 활용 가능
- 제한된 GPU 환경에서 실무적으로 널리 사용

```plain text
Frozen Base Model  +  Trainable Parameters (작음)
       ↓
7B Base Model  →  PEFT  →  Adapter Parameters (Small Adapter Checkpoint)
```

> ✅ **PEFT의 핵심은 모든 파라미터를 바꾸는 것이 아니라, 필요한 변화를 얼마나 효율적으로 학습하는가에 있다**

### When to Use? — 4가지 경우

| # | 상황 | 설명 |
|---|---|---|
| 1 | **학습·저장 비용을 줄여야 하는 경우** | 일부 파라미터만 학습하므로 GPU 메모리와 학습 비용 절감. 전체 모델이 아닌 작은 Adapter만 저장하므로 체크포인트 저장/배포 부담이 작음 |
| 2 | **제한된 자원으로 빠르게 모델을 맞춤화하는 경우** | Full Fine-Tuning이 어려운 **단일 GPU 또는 제한된 환경**에서도 대규모 모델의 튜닝이 가능 |
| 3 | **하나의 Base Model을 여러 Task에 활용하는 경우** | 공통 Base Model은 그대로 유지하고, 고객 상담·문서 요약·코드 생성 등 **Task별 Adapter만 별도로 학습**. 서비스 목적에 따라 Adapter를 교체할 수 있어 여러 모델을 효율적으로 운영 |
| 4 | **반복적인 실험과 업데이트가 필요한 경우** | 학습 시간이 짧고 체크포인트가 작아 데이터·학습 설정을 바꾸며 빠르게 실험하기에 적합. 새로운 데이터나 업무가 추가될 때 전체 모델을 다시 학습하지 않고 **Adapter만 업데이트** 가능 |

> ✅ **효율성·유연성·확장성이 중요할 때 PEFT가 실용적인 기본 선택**

## 5-10. ⭐ What to Learn × How to Update = Fine-Tuning Strategy

```plain text
┌─── WHAT TO LEARN? ────┐        ┌──── HOW TO UPDATE? ────┐
│  Learning Objective   │        │    Update Method       │
│                       │   +    │                        │
│ Continued Pre-training│        │ Full-Parameter Update  │
│ Supervised Fine-Tuning│        │          or            │
│ Preference Alignment  │        │ PEFT (LoRA · QLoRA)    │
└───────────────────────┘        └────────────────────────┘
              ↓                              ↓
              └──────────┬───────────────────┘
                         ↓
              [ Fine-Tuning Strategy ]
```

> ✅ **학습목적이 같아도 업데이트 방식은 달라질 수 있고, 같은 업데이트 방식도 여러 학습 목적에 적용할 수 있음**

| Learning Objective | Update Method | Resulting Strategy |
|---|---|---|
| Continued Pre-training | Full-Parameter Update | Full-Parameter Continued Pre-training |
| SFT | Full-Parameter Update | Full-Parameter SFT |
| SFT | **QLoRA** | **QLoRA-based SFT** |
| Preference Alignment | **LoRA** | **LoRA-based Alignment** |

> 💡 **가장 흔한 실무 조합**: **QLoRA-based SFT** (제한된 GPU + 업무 특화)

## 5-11. From Base Model to Aligned Model — 학습 단계는 조합하는 것

```plain text
                [ Base Model ]
                ↙            ↘
   [Supervised           [Continued Pre-training]
    Fine-Tuning]                  ↓
        │              [Domain-adapted Base Model]
        │                         ↓
        │              [Supervised Fine-Tuning]
        ↓                         ↓
 [Instruction Model]    [Domain Instruction Model]
        ↘                         ↙
          [ Preference Alignment ]
              RLHF · DPO
                    ↓
             [ Aligned Model ]
```

> ✅ **Fine-Tuning 기법은 양자택일이 아니라, 목적에 따라 학습 단계를 선택하고 조합하는 과정**
> - SFT와 Continued Pre-training은 **경쟁 관계가 아니라 순차적으로 조합할 수 있는 학습 단계**
> - Continued Pre-training은 **선택적으로 거치는 단계**이며, 이후 SFT로 연결할 수 있음
> - 모델 개발은 하나의 고정된 경로가 아니라, 목적에 따라 학습 단계를 선택하고 조합하는 과정

---

# 6. Fine-Tuning Techniques

## 6-1. Fine-Tuning에서는 무엇이 바뀌는가? — ΔW

```plain text
[Additional Training Data]  →  [Pre-trained Model]  →  [Learn Weight Update]  →  [Fine-tuned Model]
  Task · Domain · Preference          W_pt                     ΔW                       W_ft
```

$$W_{\text{fine-tuned}} = W_{\text{pre-trained}} + \Delta W$$

> **How should ΔW be learned?**
> - **Full Fine-Tuning** : 전체 가중치를 직접 업데이트
> - **PEFT** : Base Model을 동결하고 **효율적인 구조로 작은 변화량 학습**

> 💡 **여기가 6장의 출발점입니다.** Fine-Tuning이란 결국 **ΔW를 구하는 문제**입니다.

## 6-2. PEFT Techniques 지형도

```plain text
              [ PEFT ]
     Parameter-Efficient Fine-Tuning
        ↙        ↓         ↘
[Adapter-based][Prompt-based][Low-rank Adaptation]
                                    ↓
                              ┌── [ LoRA ] ──┐
                              │ Low-Rank Adaptation
                              │      ↓  Quantization + LoRA
                              │  [ QLoRA ]
                              └  Quantized Low-Rank Adaptation
```

**Overview**
- PEFT는 전체 모델이 아닌 **일부 파라미터만 효율적으로 학습**하는 방법론
- PEFT에는 **Adapter-based, Prompt-based, Low-rank Adaptation** 등 다양한 접근이 존재
- **LoRA**는 가중치 변화량을 **저차원 행렬로 학습**하는 대표적인 PEFT 기법
- **QLoRA**는 **양자화된 기반 모델에 LoRA를 적용**해 GPU 메모리 사용량을 더욱 줄이는 방법

## 6-3. LoRA의 Motivation

### Key Idea — Intuitive View
- 정말 특정 Task를 위해 모델의 **모든 파라미터**를 업데이트해야 할까?
- Task에 필요한 변화만 작게 학습할 수 없을까?
- 모델의 파라미터는 매우 많지만,
  **특정 Task에 필요한 변화는 몇 가지 핵심 패턴으로 표현**할 수 있지 않을까?

### Key Idea — Mathematical View
- **특정 Task에 필요한 변화는** 전체 파라미터 공간보다 **훨씬 낮은 차원의 부분공간에 존재**할 수 있지 않을까?
- 그렇다면 기존 가중치는 고정하고, 가중치 변화량만 **Low-rank 행렬로 표현해 학습**할 수 있지 않을까?

> 💬 **비유**
> 7B 모델 전체를 바꾸는 건 **집 전체를 리모델링**하는 것.
> LoRA는 **벽지만 바꾸는 것**입니다. 방의 용도를 바꾸는 데 벽을 허물 필요는 없죠.

## 6-4. Math Essentials for LoRA

### ① Matrix Multiplication & Shape

중간 차원이 일치하면 두 행렬을 곱해 원하는 Shape의 행렬을 만들 수 있음.

```plain text
  (5, 2)  ×  (2, 10)  =  (5, 10)
     ↑          ↑
     └── 중간 차원 2가 일치 ──┘
```

### ② Rank

행렬 W는 입력 x를 출력 y로 변환하는 선형변환: $y = Wx$

- **Rank는 행렬 W가 만들어낼 수 있는 선형독립적인 출력 방향의 최대 개수**
- Rank가 2라면 모든 출력은 두 개의 독립적인 방향의 조합으로 표현

$$Wx = c_1(x)w_1 + c_2(x)w_2$$

```plain text
        [1 0 1]                    [1]        [0]        [1]
W  =    [0 1 1]  = [w₁ w₂ w₃]  w₁=[0]   w₂ = [1]   w₃ = [1]
        [0 0 0]                    [0]        [0]        [0]

                                  w₃ = w₁ + w₂   ← 독립이 아님!  ∴ rank(W) = 2
```

### ③ Rank of a Matrix Product

- 행렬곱은 두 선형변환을 차례로 적용하는 과정
- **앞 단계에서 표현하지 못한 독립적인 방향을 다음 단계가 새롭게 복원할 수 없음**
- 따라서 곱의 Rank는 두 행렬 중 **더 작은 Rank를 넘을 수 없음**

$$B \in \mathbb{R}^{m \times k}, \quad A \in \mathbb{R}^{k \times n} \Rightarrow BA \in \mathbb{R}^{m \times n}$$
$$\text{rank}(BA) \le \min(\text{rank}(B), \text{rank}(A)) \le k$$

> 💡 **이 부등식이 LoRA의 수학적 근거입니다.** 중간 차원 k(=r)를 작게 잡으면, 결과 행렬의 rank도 자동으로 r 이하로 제한됩니다.

### ④ Low Rank Factorization

행렬 M을 중간 차원 r을 갖는 두 행렬의 곱으로 표현하는 것:

$$M = BA, \quad B \in \mathbb{R}^{m \times r}, \quad A \in \mathbb{R}^{r \times n}$$

- **r << min(m, n)** 이면 결과 행렬은 **저차원 구조**를 가짐
- 이렇게 r을 제한하여 저차원으로 근사하는 것을 **Low-Rank Factorization**이라 함
- 중간 차원이 실제 Rank와 같은 경우, 즉 정확히 **r = rank(M)** 이면 **Rank Factorization**이라 함

```plain text
   B          A            M = BA
 (5, 2)  ×  (2, 10)   =    (5, 10)
```

## 6-5. ⭐ LoRA의 핵심: Low-Rank Weight Update

```plain text
r = 2,   rank(ΔW) ≤ 2

   B          A             ΔW = BA         |         W
 (5, 2)  ×  (2, 10)   =     (5, 10)    ← Same Shape →  (5, 10)

LoRA weights                          Original weights
• r=2로 분해 → (5,2), (2,10) Matrix 학습   • (5,10) Matrix 직접학습
• Trainable parameters = 30            • Trainable parameters = 50
• Trainable Parameters 40% 감소
```

계산: (5×2) + (2×10) = 10 + 20 = **30** vs 5×10 = **50** → **40% 감소**

> 💡 **작은 예제라 40%지만, 실제 LLM에서는 절감률이 훨씬 극적입니다.**
> 예: d=4096, r=16 → 원본 4096×4096 = 16.7M vs LoRA 16×(4096+4096) = 131K → **약 99.2% 감소**

## 6-6. LoRA : Low-Rank Adaptation

> **Pre-trained weight는 고정하고, Low-Rank로 제한된 가중치 변화량만 학습**

**How LoRA Works**
- 사전학습 가중치 **W₀는 고정**
- 가중치 변화량을 두 개의 작은 행렬로 구성: $\Delta W = BA$
- Fine-Tuning 과정에서는 **A, B만 학습**: $h = W_0x + BAx$
- 중간 차원 r이 작으므로 학습 파라미터가 크게 감소: $r \ll \min(d_{in}, d_{out})$

```plain text
              h
              ↑
        ┌─────┴─────┐
        │           │
 [Pretrained    [  B = 0  ]  ← B는 0으로 초기화
   Weights ]    [    ↑ r  ]
  W ∈ ℝ^(d×d)   [  A = 𝒩(0,σ²) ]  ← A는 랜덤 초기화
        │           │
        └─────┬─────┘
              x
```

> 🔍 **초기화 트릭**: **B=0, A=랜덤**으로 초기화합니다.
> 그러면 학습 시작 시점에 BA = 0이므로 **모델이 Base Model과 정확히 동일한 출력**을 냅니다.
> 즉, "망가진 상태에서 시작"하지 않고 안전하게 출발합니다.

> ✅ **Full Fine-Tuning은 W 전체를 업데이트하지만, LoRA는 Task 적응에 필요한 Low-Rank 변화량만 학습**
>
> 📄 *Hu et al., "LoRA: Low-Rank Adaptation of Large Language Models," ICLR 2022*

## 6-7. LoRA 성능 — 논문 결과

> **LoRA는 Full Fine-Tuning 대비 약 0.02% 수준의 파라미터로 동등하거나 더 우수한 성능을 달성**

| Model & Method | # Trainable Parameters | WikiSQL Acc.(%) | MNLI-m Acc.(%) | SAMSum R1/R2/RL |
|---|---:|---:|---:|---|
| GPT-3 (FT) | **175,255.8M** | **73.8** | 89.5 | 52.0/28.0/44.5 |
| GPT-3 (BitFit) | 14.2M | 71.3 | 91.0 | 51.3/27.4/43.5 |
| GPT-3 (PreEmbed) | 3.2M | 63.1 | 88.6 | 48.3/24.2/40.5 |
| GPT-3 (PreLayer) | 20.2M | 70.1 | 89.5 | 50.8/27.3/43.5 |
| GPT-3 (Adapter^H) | 7.1M | 71.9 | 89.8 | 53.0/28.9/44.8 |
| GPT-3 (Adapter^H) | 40.1M | 73.2 | **91.5** | 53.2/29.0/45.1 |
| **GPT-3 (LoRA)** | **4.7M** | 73.4 | **91.7** | **53.8/29.8/45.9** |
| **GPT-3 (LoRA)** | **37.7M** | **74.0** | 91.6 | 53.4/29.2/45.1 |

> 🤯 **4.7M vs 175,255.8M** — **약 0.0027%** 의 파라미터로 MNLI-m에서 Full FT(89.5)를 **이겼습니다(91.7)**.

## 6-8. ⭐ LoRA Hyper-parameters — 핵심 4요소

```python
from peft import LoraConfig, get_peft_model

lora_config = LoraConfig(
    r=16,
    lora_alpha=32,
    lora_dropout=0.05,
    target_modules=[
        "q_proj",
        "k_proj",
        "v_proj",
        "o_proj",
    ],
    bias="none",
    task_type="CAUSAL_LM",
)

model = get_peft_model(
    model,
    lora_config,
)

model.print_trainable_parameters()
```

| Hyper-parameter | 의미 | 주요 영향 |
|---|---|---|
| **r** | Low-Rank 중간 차원 | 표현력 · 학습 파라미터 수 |
| **lora_alpha** | LoRA 변화량의 스케일 | 기존 출력에 반영되는 강도 |
| **target_modules** | LoRA를 적용할 모듈 | 학습 범위 · 파라미터 수 |
| **lora_dropout** | LoRA 경로의 Dropout | 과적합 방지 · 일반화 |

> ✅ LoRA는 **Rank, Scaling, Dropout, 적용 모듈**을 설정하여 모델에 Low-Rank 학습 경로를 추가
> ✅ **표현력과 효율성 사이의 Trade-off**를 결정

### ① Rank r

$$A \in \mathbb{R}^{r \times d_{in}}, \quad B \in \mathbb{R}^{d_{out} \times r}$$
$$\text{rank}(\Delta W) \le r$$
$$N_{\text{LoRA}} = r(d_{in} + d_{out})$$

- LoRA가 **학습할 수 있는 변화 공간의 크기**를 결정
- **r ↑** : 높은 표현력, 파라미터 증가, **과적합 가능성 증가**
- **r ↓** : 파라미터 감소, 낮은 메모리 사용, **제한된 표현력**
- **r을 두 배로 하면 LoRA 파라미터 수도 거의 두 배**

### ② LoRA Alpha α

$$h = W_0x + \frac{\alpha}{r}BAx$$
$$\text{LoRA Scaling} = \frac{\alpha}{r}$$

- α는 학습된 Low-Rank 변화량이 **기존 모델에 반영되는 강도**를 조절
- **α ↑** : LoRA 변화량을 **강하게 반영**
- **α ↓** : LoRA 변화량을 **보수적으로 반영**
- 지나치게 크면 학습이 불안정하거나 기존 능력을 크게 변경할 수 있음
- ⚠️ **유의할 점은 α 자체보다 α/r의 관계를 보는 것**

> 💡 관례적으로 **α = 2r** (예: r=16 → α=32) → Scaling = 2.0

### ③ Target Modules

$$W_q, \quad W_k, \quad W_v, \quad W_o$$
$$\text{"q\_proj", "k\_proj", "v\_proj", "o\_proj"}$$

- LoRA를 Transformer의 **어떤 가중치 행렬에 적용할지** 결정
- **많은 모듈에 적용** : 표현력과 학습 파라미터 증가
- **일부 모듈에 적용** : 파라미터와 메모리 절감
- 같은 r이라도 **적용 모듈이 많아지면 전체 Trainable Parameters가 크게 증가**

> 💡 `q_proj`/`k_proj`/`v_proj`/`o_proj`는 3장에서 본 **W^Q, W^K, W^V** 와 Attention 출력 투영입니다.
> **3장을 배운 이유가 여기서 드러납니다.**

### ④ LoRA Dropout

$$h = W_0x + \frac{\alpha}{r}BA(\text{Dropout}(x))$$

- LoRA 경로의 입력 일부를 학습 중 확률적으로 제거
- **0.0** : Dropout을 적용하지 않음
- **0.05** : 약한 정규화
- **0.1** : 상대적으로 강한 정규화
- 작은 데이터셋에서 **과적합이 우려되면 높이는 것을 검토**

### 📎 Implementation Settings (기타 설정)

| Hyper-parameter | 의미 | 일반적인 설정 |
|---|---|---|
| **bias** | Bias 파라미터도 학습할지 결정 | `"none"` |
| **task_type** | 모델이 수행할 Task 유형 | `"CAUSAL_LM"` |
| **modules_to_save** | LoRA 외에 함께 학습·저장할 모듈 | Task에 따라 설정 |
| **init_lora_weights** | (A,B) 초기화 방식 | 기본값 사용 |
| **use_rslora** | Rank-Stabilized LoRA 사용 여부 | 선택적, True/False |

$$\text{Vanilla: } \text{Scaling} = \frac{\alpha}{r} \qquad \text{Rank-Stabilized: } \text{Scaling} = \frac{\alpha}{\sqrt{r}}$$

> 💡 **rsLoRA**: r을 크게 잡을 때 α/r이 너무 작아지는 문제를 √r로 완화합니다.

## 6-9. ⭐⭐ Practical Guide — 실무 기본값 (외워두세요)

| 하이퍼파라미터 | 가장 일반적인 설정 | 비고 |
|---|---|---|
| **target_modules** | `q_proj, k_proj, v_proj, o_proj`<br>`gate_proj, up_proj, down_proj` | Attention + MLP 전체, **QLoRA 표준** |
| **r (rank)** | **16** | 8~32 범위에서 가장 무난한 값 |
| **lora_alpha** | **32** | 관례적으로 **r의 2배** |
| **lora_dropout** | **0.05 ~ 0.1** | 데이터 적으면 0.1 권장 |
| **bias** | `"none"` | 학습 파라미터 최소화, 가장 흔함 |
| **task_type** | `"CAUSAL_LM"` | 언어모델 파인튜닝시 고정값 |

- **r** : 4~8 (매우 가벼움, 간단한 태스크), **16 (가장 무난하고 널리 쓰임)**, 32~64 (복잡한 태스크, 데이터 많을 때)
- **alpha/r 비율**이 실제 스케일링 강도를 결정 (보통 **2.0 비율** 사용)
- **Dropout** : 데이터가 적으면 0.1, 많으면 0.05 정도로 낮춰도 무방

## 6-10. Quantization — 더 적은 비트로 가중치 표현하기

| 표현 방식 | 가중치당 비트 | 10억 개 가중치 |
|---|---:|---:|
| **FP32** (32 bit Floating Point) | 32-bit | 약 **4 GB** |
| **FP16** (16 bit Floating Point) | 16-bit | 약 **2 GB** |
| **INT8** (8-bit Integer) | 8-bit | 약 **1 GB** |
| **NF4** (4-bit Normal Float) | 4-bit | 약 **0.5 GB** |

**Effect**
- 비트 수가 줄어들수록 **메모리 사용량 감소**
- 하드웨어와 연산 커널이 지원하는 경우 **연산 효율 향상 가능**
- 표현 정밀도가 낮아지면서 **표현 가능한 값의 수 감소**
- 원본 값과 근사값 사이에 **Quantization Error 발생**할 수 있음

> ✅ **Quantization은 모델의 가중치를 더 적은 비트로 근사하여 메모리 사용량을 줄임**

> 💡 **실전 감각**: 7B 모델 → FP16이면 약 14GB (24GB GPU에 겨우), NF4면 약 3.5GB (**노트북 GPU에서도 가능**)

## 6-11. Scalar Quantization

**Concept**
- 벡터의 각 원소를 제한된 개수의 이산적인 값 중 하나로 **개별 매핑**하여, 더 적은 비트로 근사 표현하는 방식
- 각 원소를 **독립적으로** 양자화
- 16/32-bit Floating Point 가중치를 **INT8 또는 4-bit** 등의 저정밀 표현으로 변환

### Case 1. Uniform Quantization (균등 양자화)

```plain text
Step 1. 표현 범위 결정 (Range)
  [3.75, -2.98, 1.43, 0.87, -4.21]
  벡터를 탐색하여 양자화할 실수 값의 최소값과 최대값을 결정 → [-5, 5]

Step 2. 스케일링 (Scaling)
  최소값과 최대값을 기준으로 범위를 정규화
  실수 범위 [-5, 5]를 INT8 범위 [-127, 127]에 대응
  → 실수 값을 일정한 비율로 확대하여 정수 범위로 변환 (8-bit 표현)

Step 3. 반올림 및 클리핑 (Rounding & Clipping)
  변환된 값을 가장 가까운 정수로 반올림
  INT8 범위를 벗어난 값은 -127 또는 127로 제한
  최종 값을 8-bit 정수로 저장
```

$$q = \text{clip}\left(\text{round}\left(x \times \frac{127}{5}\right), -127, 127\right)$$

| Original (float32) | 3.75 | −2.98 | 1.43 | 0.87 | −4.21 |
|---|---:|---:|---:|---:|---:|
| **Quantized (INT8)** | **95** | **−76** | **36** | **22** | **−107** |

### Case 2. NF4 Quantization (Non-uniform, 비균등)

```plain text
Step 1. Block 분할 및 범위 결정 (Block-wise Range)
  가중치를 작은 Block 단위로 분할
  각 Block에서 절댓값이 가장 큰 값인 Absmax를 계산
  Block별로 서로 다른 양자화 범위를 적용

Step 2. 정규화 (Normalization)
  Block의 각 가중치를 Absmax로 나눔
  모든 값을 [-1, 1] 범위로 정규화

Step 3. NF4 값으로 매핑 (Nearest NF4 Mapping)
  정규화된 각 가중치를 가장 가까운 NF4 값으로 매핑
  NF4는 분포를 고려한 16개의 비균등한 값을 사용
  선택된 NF4 값의 위치를 4-bit Index로 저장
```

```plain text
        Weight Distribution (정규분포)
                  ╱‾‾╲
               ╱        ╲
            ╱              ╲
  ────────╱                  ╲────────
  -1.0    |  |  ||||||||  |  |    +1.0
    Wider Spacing  Denser  Wider Spacing
                 Spacing
```

- **가중치가 많이 분포하는 영역에 양자화 값을 더 촘촘하게 배치**
- 가중치를 16개의 NF4 값으로 근사하여 **4-bit Index로 저장**
- NF4는 적은 수의 값만 사용하면서도, **가중치 분포에 맞게 양자화 값을 배치하여 정보 손실을 줄이는 접근**

> ✅ **양자화 값은 반드시 일정한 간격으로 배치할 필요가 없다**

> 💬 **직관**: 신경망 가중치는 대부분 0 근처에 몰려 있습니다. 균등 간격으로 나누면 0 근처가 뭉개지죠.
> **사람이 많이 사는 곳에 버스 정류장을 더 촘촘히 놓는 것**과 같은 아이디어입니다.

## 6-12. ⭐ QLoRA : Quantization + LoRA

> **Base Model은 작게 저장하고, LoRA Adapter만 학습**

**Concept**
- QLoRA는 Base Model을 **4-bit로 저장하고 고정한 상태**에서, 작은 LoRA Adapter만 학습하는 방법
- Base Model의 주요 가중치를 **4-bit NF4로 저장**하여 GPU 메모리 사용량 절감
- 학습 과정에서는 **저정밀 Base Model을 고정**하고, LoRA의 **ΔW=BA만 학습**
- LoRA의 파라미터 효율성에 Base Model의 저장 메모리 절감을 결합

```plain text
        LoRA                          QLoRA
         ⊕                              ⊕
    ┌────┴────┐                   ┌─────┴────┐
[Pre-trained  ]  [B]         [Quantized     ]  [B]
[Weights      ]  [ ]         [Weights       ]  [ ]
[W (FP16)  🔒 ]  [A]         [W̃ (NF4)   🔓 ]  [A]
    └────┬────┘                   └─────┬────┘
         X                              X
```

> ✅ **Quantization은 Base Model의 저장 메모리를 줄이고, LoRA는 학습할 파라미터를 줄인다.**
>
> 📄 *Dettmers et al., "QLoRA: Efficient Finetuning of Quantized LLMs," NeurIPS 2023*

## 6-13. QLoRA는 메모리를 어떻게 아끼는가? — 3가지 장치

> **저장(NF4) + 압축(Double Quant) + 관리(Paged Optimizer) = 메모리 사용량 최소화**

### ① NF4 (NormalFloat 4-bit) — *"가중치를 작게 저장한다"*
- Base Model의 가중치를 32bit/16bit가 아닌 **4bit로 저장**
- 신경망 가중치가 **정규분포를 따른다는 특성에 최적화된 데이터 타입**
- 같은 4bit라도 **일반 정수형(INT4)보다 정보 손실이 적음**

### ② Double Quantization — *"양자화 상수도 다시 압축한다"*
- 양자화 과정에는 **"양자화 상수(quantization constant)"** 라는 보조 값이 별도로 저장되는데, 이것 자체도 용량을 차지함
- QLoRA는 이 양자화 상수를 **한 번 더 양자화해서 추가로 압축**
- 파라미터당 **약 0.4bit를 추가 절감** (모델이 클수록 효과 커짐)

### ③ Paged Optimizer — *"메모리 스파이크를 대비한다"*
- 학습 중 특정 순간 메모리 사용량이 **급증(spike)** 해서 GPU 메모리가 부족해지는 경우 발생
- **NVIDIA 통합 메모리 기능**을 활용해, 넘치는 부분을 **CPU 메모리로 자동 이동(paging)** 시켰다가 필요할 때 다시 불러옴
- **OOM(Out of Memory) 에러 없이** 큰 모델 학습을 안정적으로 지속 가능

> 💬 **비유**: OS의 **가상 메모리(스왑)** 와 같은 아이디어입니다.
> (→ Day3 DB 파트에서 배운 Buffer/Page 개념과 발상이 동일합니다.)

## 6-14. QLoRA Hyper-parameters

| Hyper-parameter | 의미 | 일반적인 설정 |
|---|---|---|
| **load_in_4bit** | Base Model을 4-bit로 로드 | `True` |
| **bnb_4bit_quant_type** | 4-bit 양자화 데이터 타입 | `"nf4"` |
| **bnb_4bit_use_double_quant** | Quantization Constant도 다시 양자화 | `True` |
| **bnb_4bit_compute_dtype** | 실제 행렬 연산에 사용할 정밀도 | `torch.bfloat16` |

```python
import torch
from transformers import BitsAndBytesConfig

quant_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_quant_type="nf4",
    bnb_4bit_use_double_quant=True,
    bnb_4bit_compute_dtype=torch.bfloat16,
)
```

> ✅ **QLoRA 설정은 3개 부분으로 구성 = Quantization + LoRA + Training**
> ✅ `bnb_4bit_compute_dtype` : `torch.bfloat16` (A100, H100 등 최신 GPU), `torch.float16` (T4, V100 등 구형 GPU)
> ✅ `bnb_4bit_use_double_quant` : 성능 저하 거의 없고, 메모리는 추가 절감되어 **관례적으로 True**

> 🚨 **자주 하는 실수**: 저장은 4bit지만 **연산은 bfloat16으로 합니다.**
> 즉 `load_in_4bit=True`여도 계산할 때는 잠깐 고정밀로 되돌려서 곱합니다. "4bit로 계산한다"가 아닙니다.

---

# 7. Fine-Tuning Troubleshooting

## 7-1. Data Problems

> **모델은 데이터의 의도뿐 아니라 데이터에 포함된 오류와 편향까지 학습한다**

### ① Poor Dataset Quality — *"Garbage In, Garbage Out"*
- 잘못된 정답, 중복 데이터, 불완전하거나 모순된 응답
- 샘플마다 다른 답변 형식·문체·상세 수준
- 소량의 고품질 데이터보다 **대량 확보에 치중**
- 데이터의 오류와 노이즈가 **올바른 응답 패턴처럼 학습됨**
- 결과적으로 응답 품질이 불안정해지고 잘못된 형식이 반복됨

### ② Dataset Bias — *"Biased Data, Biased Behavior"*
- 특정 주제·표현·클래스·답변 유형에 **편중된 데이터**
- 유사한 예시만 반복되고 다양한 상황이나 **예외 사례가 부족**
- 실제 사용 환경과 학습 데이터 사이에 **분포 차이 발생**
- 자주 등장한 패턴을 과도하게 선호하고 **드문 요청에는 취약**
- 결과적으로 편향되거나 획일적인 응답을 생성

> 🛠 **How to Reduce the Risk**
> - Data Cleaning · Deduplication · Balanced Sampling
> - Format Standardization · Quality Review

## 7-2. Training Problems

> **좋은 학습은 Train Loss를 낮추는 것이 아니라, 새로운 데이터에서도 성능을 높이는 것**

### ① Overfitting — *"Learning the Dataset, Not the Task"*
- 학습 데이터에는 잘 답하지만 **새로운 입력에서는 성능 저하**
- 작거나 다양성이 부족한 데이터셋을 **과도하게 반복 학습**
- 학습 문장과 응답 형식을 일반화하지 못하고 **그대로 암기**
- **Train Loss는 계속 감소하지만 Validation Loss는 증가** ← 가장 확실한 신호
- 표현이 조금만 바뀌어도 응답 품질이 크게 저하됨

### ② Training Instability — *"Unstable Loss and Gradients"*
- Loss가 크게 진동하거나 감소하지 않고 발산
- 지나치게 높은 **Learning Rate**로 가중치가 급격하게 변화
- 부적절한 **Batch Size 또는 Gradient Accumulation** 설정
- **Gradient Explosion**이나 수치 정밀도 문제 발생
- 실행할 때마다 학습 결과와 최종 성능이 크게 달라짐

> 🛠 **How to Reduce the Risk**
> - **Overfitting**: Fewer Epochs · Early Stopping · More Diverse Data
> - **Training Instability**: Lower Learning Rate · Adjust Batch Size

## 7-3. Model Behavior Problems

> **모델은 원하는 답변 방식은 학습하면서도, 정확한 사실까지 학습하는 것은 아니다**

### ① Catastrophic Forgetting — *"New Skills, Lost Capabilities"*
- **새로운 능력을 학습하는 과정에서 기존 능력이 저하되는 현상**
- 일반 지식, 추론, 언어 이해, 지시 수행 능력이 약화될 수 있음
- 특정 도메인이나 응답 형식에 **편중된 데이터가 주요 원인**
- 과도한 학습으로 기존 가중치가 크게 변경
- **특정 Task의 성능은 높아지지만 범용 성능은 오히려 하락**

### ② Hallucination — *"Fluent but Incorrect Answers"*
- **Fine-Tuning이 사실성과 정확성을 자동으로 높이지는 않음**
- 잘못되거나 불완전한 학습 데이터가 부정확한 답변을 강화
- 답을 알 수 없는 상황에서도 학습된 응답 형식을 모방
- 도메인 밖 질문에 대해서도 그럴듯한 답변 패턴을 반복
- **문체와 형식은 개선되지만 사실 오류와 과도한 확신은 남을 수 있음**

> 🛠 **How to Reduce the Risk**
> - **Forgetting** : Lower LR · Fewer Epochs · **Mix General Data** · **PEFT**
> - **Hallucination** : Quality Data · **Abstention Examples** · **RAG** · Verification

> 💡 **왜 PEFT가 Forgetting을 줄이는가?**
> Base Model 가중치를 **동결**하기 때문입니다. 원본이 안 바뀌니 기존 능력이 덜 손상됩니다.
> → **2장의 "Knowledge는 RAG, Behavior는 FT"** 원칙이 여기서 다시 나옵니다.

## 7-4. ✅ Fine-Tuning Checklist

> **Improve target behavior without losing general capabilities**

### Before Training
- [ ] Fine-Tuning으로 해결할 **문제와 목표 행동이 명확한가?**
- [ ] 데이터의 **정답·형식·문체가 정확하고 일관적인가?**
- [ ] 중복 데이터와 지나치게 유사한 샘플을 제거했는가?
- [ ] 실제 사용 환경의 입력과 **예외 상황**을 포함하고 있는가?
- [ ] **Train·Validation 데이터를 분리**했는가?
- [ ] 학습 전 **Base Model의 응답을 저장**했는가? ← 비교 기준

> 📌 **Prepare Data and Baseline** : Inspect Samples / Remove Duplicates · Split Dataset / **Save Baseline Outputs**

### During Training
- [ ] **Train Loss와 Validation Loss를 함께** 확인했는가?
- [ ] **Validation Loss가 증가하기 시작하지 않는가?** ← Overfitting 신호
- [ ] Learning Rate와 Epoch가 과도하지 않은가?
- [ ] Loss가 크게 진동하거나 **NaN이 발생하지 않는가?**
- [ ] 정기적으로 **Checkpoint를 저장**하고 있는가?
- [ ] **가장 좋은 Validation 성능의 Checkpoint를 선택**했는가?

> 📌 **Monitor the Training Process** : Train/Validation Loss / Learning Curve / Saved Checkpoints / Sample Outputs

### After Training
- [ ] 동일한 평가 질문에서 **Base Model보다 목표 성능이 개선**되었는가?
- [ ] 학습에 사용하지 않은 **새로운 표현에도 잘 대응**하는가?
- [ ] 학습 문장을 그대로 **암기하거나 반복하지 않는가?**
- [ ] 기존의 일반 지식·추론·지시 수행 능력이 **유지**되는가? ← Forgetting 체크
- [ ] 근거가 없을 때 **추측하지 않고 답변을 유보**하는가? ← Hallucination 체크
- [ ] 사실성·편향·환각을 **별도의 평가 질문**으로 확인했는가?

> 📌 **Evaluate Improvement** : **Base vs. Fine-Tuned** / **Seen vs. Unseen** / **In-domain vs. Out-of-domain**

### 평가 Prompt 유형

| 평가 유형 | 확인 목적 |
|---|---|
| **Target Task** | 학습하려던 행동이 개선되었는가? |
| **Unseen Variation** | 표현이 달라져도 일반화되는가? |
| **General / Out-of-domain** | 기존 능력 저하나 억지 답변이 없는가? |

---

# 🧭 전체 흐름 한 장 요약

```plain text
┌─────────────────────────────────────────────────────────────────────────┐
│ [1장] WHY sLLM?                                                          │
│  Scale-up의 한계 → 비용·속도·보안·통제                                    │
│  "모든 문제에 가장 큰 모델이 필요한 것은 아니다"                          │
│  Better Arch + Good Data + Distillation + Post-Train + Quantization      │
└───────────────────────────────┬─────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────────────┐
│ [2장] 어떤 모델을 고를 것인가?                                            │
│  Task → Family(Llama/Qwen/Gemma/Phi) → Size → Type(Base/Instruct)        │
│       → License(Apache/MIT/Model-specific/Restricted) → Compatibility    │
│                                                                          │
│  ⭐ 부족한 걸 채우는 3가지                                                │
│     지시·맥락 부족  → Prompt                                             │
│     외부·최신 지식  → RAG        (Knowledge)                             │
│     특정 Task·행동  → Fine-Tuning (Behavior)                             │
└───────────────────────────────┬─────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────────────┐
│ [3장] 모델 내부 (Transformer Recap)                                       │
│  Dot Product(유사도) → Matrix Mult → 선형변환(W) → Softmax(확률)          │
│  Attention(Q,K,V) = Softmax(QKᵀ/√d_k)·V                                  │
│  Decoder = + Causal Mask (미래 토큰 차단)                                 │
│              ↑ 여기서 나온 W_Q,W_K,W_V가 6장 LoRA의 target_modules        │
└───────────────────────────────┬─────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────────────┐
│ [4장] 어떻게 학습하는가?                                                  │
│  Text → Token → ID → Embedding → Transformer → Logits → Softmax          │
│  Label = "다음 토큰" (Self-Supervised, 라벨링 비용 0)                     │
│  Loss  = Cross-Entropy = −log(정답토큰 확률)                              │
│  Predict → Compare → Update → Repeat                                     │
│  ⚠️ Attention 비용 = O(T²)  → Long-context 병목                          │
│  Teacher Forcing(학습) vs Autoregressive(추론)                            │
└───────────────────────────────┬─────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────────────┐
│ [5장] Fine-Tuning Map                                                    │
│                                                                          │
│   W_fine-tuned = W_pre-trained + ΔW                                      │
│                                                                          │
│   Fine-Tuning Strategy = Learning Objective × Update Method              │
│   ┌──────────────────────┬────────────────────────┐                     │
│   │ WHAT to Learn        │ HOW to Update          │                     │
│   ├──────────────────────┼────────────────────────┤                     │
│   │ Continued Pre-train  │ Full Fine-Tuning       │                     │
│   │ SFT                  │ PEFT (LoRA · QLoRA)    │                     │
│   │ Preference Alignment │                        │                     │
│   └──────────────────────┴────────────────────────┘                     │
│   Base → (CPT) → SFT → Preference Alignment → Aligned Model              │
└───────────────────────────────┬─────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────────────┐
│ [6장] LoRA / QLoRA                                                       │
│  ΔW = BA,  rank(BA) ≤ r ≪ min(d_in, d_out)                              │
│  h = W₀x + (α/r)·BA·Dropout(x)      W₀는 고정, A·B만 학습                │
│  실무 기본값: r=16, alpha=32, dropout=0.05~0.1, bias=none                │
│                                                                          │
│  QLoRA = NF4(4bit 저장) + Double Quant(상수 재압축) + Paged Optimizer     │
│          → Base는 4bit로 눕히고, LoRA Adapter만 학습                     │
└───────────────────────────────┬─────────────────────────────────────────┘
                                ↓
┌─────────────────────────────────────────────────────────────────────────┐
│ [7장] 뭐가 고장나는가?                                                    │
│  Data     : Poor Quality(GIGO) / Bias                                    │
│  Training : Overfitting / Instability                                    │
│  Behavior : Catastrophic Forgetting / Hallucination                      │
│                                                                          │
│  Checklist: Before(Baseline 저장) → During(Val Loss 감시) →              │
│             After(Base vs FT, Seen vs Unseen, In vs Out-of-domain)       │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🎓 시험/면접 대비 핵심 문답

| # | 질문 | 핵심 답변 |
|---|---|---|
| 1 | sLLM의 명확한 정의는? | **없다.** ACM Computing Surveys(2025) 기준 통일된 정의 부재. 상대적·맥락적 개념 |
| 1-1 | **언제 sLLM을 선택하는가? (핵심)** | **호출량 × 업무의 정형성.** 하루 10여건 자유로운 상담 → 상용 API(범용성·개발속도). 하루 10만건 정형 분류 → sLLM(비용·속도·안정성) |
| 1-2 | 상용 LLM을 못 쓰는 8가지 상황은? | ①민감데이터 ②보안 ③오프라인 ④대량 호출 ⑤즉각 응답 ⑥단순 반복업무 ⑦직접 통제 필요 ⑧조직 맞춤 필요 → **"못 보낸다 / 못 기다린다·못 감당한다 / 내 맘대로 못 한다"** |
| 1-3 | sLLM 활용 영역 3가지는? | **Enterprise AI**(반복 기업업무: AT&T, Trustpilot) / **Task-specific AI**(특정 Task 전문화: Epic×Phi-3, Bayer) / **On-device AI**(Cloud→Device: Apple) |
| 1-4 | 작은 모델이 강해진 5가지 이유는? | Better Architecture + High-Quality Training Data + Knowledge Distillation + Post-Training + Quantization → **Capable Small Models** |
| 1-5 | AI Agent 구조에서 sLLM의 역할은? | *One Model for Everything → Right Model for Each Task*. 분류·추출·Function Calling은 sLLM, **복잡한 추론만 Large Model**. Efficiency·Specialization·Performance |
| 2 | Base vs Instruct 차이는? | Base = Pre-trained만 된 상태, **다음 토큰 예측**이 목적 / Instruct = **Post-trained**, 지시 수행·대화 가능. 일반 SFT/QLoRA는 **Instruct 우선 검토** |
| 3 | RAG vs Fine-Tuning 판단 기준은? | **Knowledge → RAG, Behavior → Fine-Tuning.** 자주 바뀌는 외부 지식은 RAG. FT의 주목적은 지식 저장이 아니라 **행동 변경** |
| 4 | Attention에서 √d_k로 나누는 이유는? | d_k가 커지면 내적 분산↑ → Softmax **기울기 소실**. Scaling으로 값 범위를 안정화해 적당한 gradient 유지 |
| 5 | Causal Mask가 하는 일은? | 각 위치에서 **미래 토큰 참조 차단**. 전체 시퀀스를 한 번에 넣으면서도 "커닝"을 막음 |
| 6 | LLM 학습의 정답 라벨은 어디서 오나? | **다음 토큰이 곧 정답.** Input과 Label은 1토큰 Shift 관계 → Self-Supervised, 라벨링 비용 0 |
| 7 | Cross-Entropy Loss의 의미는? | L = −log(정답 토큰 예측 확률). 100%→0, 20%→1.6. **확신이 낮을수록 패널티가 기하급수 증가** |
| 8 | Attention 비용이 O(T²)인 이유는? | 각 토큰이 모든 토큰과 관계 계산 → T×T 행렬. Causal Mask를 써도 ½T² → **차수는 그대로 O(T²)** |
| 9 | Teacher Forcing이란? | 학습 시 **모델 예측이 아니라 실제 정답 토큰**을 다음 입력 문맥으로 제공. 추론(Autoregressive)에서는 불가 → 오류 누적 |
| 10 | Fine-Tuning 설계의 2축은? | **Learning Objective**(CPT / SFT / Preference Alignment) **×** **Update Method**(Full FT / PEFT) |
| 11 | Full FT를 쓰는 4가지 경우는? | ① 최고 성능 필요 ② 충분한 데이터 ③ 모델을 광범위하게 변경(CPT) ④ 모델이 작고 자원 충분 |
| 12 | LoRA의 수학적 근거는? | rank(BA) ≤ min(rank B, rank A) ≤ **k(=r)**. 중간 차원 r을 작게 잡으면 ΔW의 rank가 자동으로 제한 |
| 13 | LoRA 수식은? | ΔW = BA, **h = W₀x + (α/r)·BAx**. W₀ 고정, A·B만 학습 |
| 14 | B를 0으로 초기화하는 이유는? | 학습 시작 시 BA=0 → **Base Model과 동일한 출력**에서 안전하게 출발 |
| 15 | α와 r의 관계에서 중요한 건? | α 자체가 아니라 **α/r 비율**(Scaling). 관례적으로 α=2r → Scaling 2.0 |
| 16 | LoRA 실무 기본값은? | **r=16, lora_alpha=32, lora_dropout=0.05~0.1, bias="none", task_type="CAUSAL_LM"**, target=q/k/v/o_proj (+gate/up/down_proj) |
| 17 | LoRA 논문 성능 결과는? | GPT-3 175B에서 **4.7M 파라미터(약 0.0027%)** 로 MNLI-m **91.7** 달성 → Full FT(89.5)보다 우수 |
| 18 | NF4가 INT4보다 나은 이유는? | 신경망 가중치가 **정규분포**를 따르므로, 값이 몰린 영역에 양자화 값을 **더 촘촘히 비균등 배치** → 정보 손실 감소 |
| 19 | QLoRA의 3가지 메모리 절감 장치는? | ① **NF4** (4bit 저장) ② **Double Quantization** (양자화 상수 재압축, 파라미터당 ~0.4bit) ③ **Paged Optimizer** (스파이크 시 CPU로 paging → OOM 방지) |
| 20 | QLoRA에서 4bit로 계산하나? | **아니다.** 저장만 NF4, 연산은 `bnb_4bit_compute_dtype`(bfloat16/float16)로 수행 |
| 21 | Catastrophic Forgetting 대응은? | Lower LR · Fewer Epochs · **Mix General Data** · **PEFT**(Base 동결이라 원본 손상 적음) |
| 22 | Hallucination 대응은? | Quality Data · **Abstention Examples**(모를 땐 모른다고 답하는 예시) · **RAG** · Verification |
| 23 | Overfitting의 가장 확실한 신호는? | **Train Loss는 계속 감소하는데 Validation Loss는 증가** |
| 24 | 학습 전 반드시 저장해야 할 것은? | **Base Model의 응답(Baseline Outputs)** — 개선 여부를 비교할 기준이 없으면 평가 자체가 불가능 |
| 25 | 학습 후 평가 3축은? | **Base vs Fine-Tuned / Seen vs Unseen / In-domain vs Out-of-domain** |

---

*본 문서는 SK AX의 컨텐츠 자산을 학습 목적으로 정리한 것으로, 무단 사용 및 불법 배포 시 법적 조치를 받을 수 있습니다.*
