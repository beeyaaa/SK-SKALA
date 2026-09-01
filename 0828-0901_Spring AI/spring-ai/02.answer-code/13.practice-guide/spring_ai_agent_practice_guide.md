# [종합실습] 나만의 도메인 맞춤형 AI 상담 에이전트 구축

---

## 1. 실습 개요 및 목표

본 실습은 **수강생 스스로 원하는 도메인(주제)**을 직접 정의하고, 학습한 기술 요소들을 조합하여 **실제 동작하는 AI 상담 에이전트 API**를 구축하는 종합 프로젝트입니다.

### 핵심 목표
* **도메인 자율성:** 개인 프로젝트, 관심사, 업무 영역(예: 법률, 카페 레시피, 게임 룰북, 사내 IT지원, 취업 상담 등) 중 하나를 자율적으로 선택합니다.
* **핵심 AI 기술 통합:** RAG, Chat Memory, Vector DB, Tool Call, Structured Output을 하나의 애플리케이션으로 통합합니다.
* **Spring AI 기반 Agent 구조 구현:** Spring AI의 **System Prompt, Tool Calling, Advisor**를 조합하여 **스스로 판단하고 실행하는 에이전트**를 완성합니다.

---

## 2. 도메인 선정 예시

아래 예시 중 하나를 선택하거나, 본인만의 참신한 도메인을 직접 정의하세요.

| 도메인 | 서비스 컨셉 | RAG 활용 데이터 | 연동할 Tool 예시 |
|---|---|---|---|
| **스마트 카페** | 음료 추천 및 주문 상담 에이전트 | 원두 종류, 음료 레시피, 알레르기 정보 | 실시간 재고 조회 API, 할인 쿠폰 적용 API |
| **게임 도우미** | 게임 룰북 및 캐릭터 빌드 상담 | 게임 아이템/스킬 정보, 패치 노트 | 사용자 캐릭터 레벨 조회, 딜량 계산기 |
| **캠퍼스 라이프** | 대학 수강신청 및 학사행정 상담 | 학사 규정 문서, 졸업 요건 FAQ | 학생 이수 학점 조회, 강의 잔여 여석 조회 |
| **IT 서비스 장애지원**| 사내 개발/인프라 장애 대응 상담 | 시스템 장애 조치 가이드 문서 | 서버 상태 핑(Ping) 테스트, 장애 티켓 발급 |

---

## 3. 필수 포함 기술 요소 (Tech Stack Check)

실습 프로젝트 작성 시 아래 6가지 기술 요소를 **반드시 포함**해야 합니다.

1. **Embedding & Vector DB (PgVector):**
   * 선택한 도메인의 텍스트/문서를 분할(Chunking)하여 PgVector에 적재
2. **RAG (Retrieval-Augmented Generation):**
   * 사용자 질문과 유사한 문서/규정을 Vector DB에서 검색하여 프롬프트에 제공
3. **Chat Memory (대화 맥락 유지):**
   * 이전 대화 흐름을 기억하여 맥락에 맞는 연속된 답변 제공
4. **Tool Calling (기능 연동):**
   * LLM이 스스로 판단하여 조회/작동시킬 수 있는 Java 메서드/서비스 연동
5. **Structured Output (구조화된 응답):**
   * 최종 결과를 프론트엔드나 타 시스템이 소비할 수 있는 JSON 형태로 응답

---

## 4. Agent 만들기 (가이드)

> **"Agent란 별도의 거창한 프레임워크가 아닙니다. LLM에게 [목표]와 [사용 가능한 도구(Tool)]를 주고, LLM이 스스로 판단하여 도구를 실행하고 결과를 종합하여 답변하게 만드는 패턴 그 자체입니다."**

### Agent 구성 3단계 구현 원리

```
[사용자 요청] ──► [System Prompt (페르소나/규칙)] 
                      │
                      ├──► (1) Chat Memory (이전 대화 맥락 참조)
                      ├──► (2) RAG Advisor (Vector DB 문서 자동 검색)
                      └──► (3) Tool Calling (필요시 외부 Java 메서드 실행)
                      │
                      ▼
               [LLM 판단 및 최종 응답 (Structured Output)]
```

#### Step 1: 페르소나 및 판단 규칙 정의 (System Prompt)
LLM이 자신이 어떤 역할(Agent)이며, 어떤 단계로 사고해야 하는지 정의합니다.
* **예시:** *"당신은 카페 주문 상담 에이전트입니다. 사용자의 질문이 들어오면 (1) RAG를 통해 메뉴 정보를 확인하고, (2) 재고가 필요하면 재고 조회 Tool을 호출한 뒤, (3) 최종 결과를 JSON으로 응답하세요."*

#### Step 2: RAG + Memory + Tool을 단일 ChatClient에 바인딩
Spring AI의 `ChatClient` 하나에 모든 부가 기능을 지능적으로 집결시킵니다.

```java
// ChatClient 생성 시 모든 요소 통합 (Orchestration)
this.chatClient = chatClientBuilder
    .defaultSystem("당신은 [도메인명] 전문 에이전트입니다. 지식 검색과 도구를 사용해 정확히 답변하세요.")
    .defaultAdvisors(
        new MessageChatMemoryAdvisor(chatMemory), // Chat Memory
        QuestionAnswerAdvisor.builder(vectorStore).build() // RAG (Vector DB)
    )
    .defaultTools("checkInventoryTool", "applyCouponTool") // Tool Calling
    .build();
```

#### Step 3: Structured Output으로 최종 반환
LLM이 응답 결과를 문자열이 아닌 규격화된 객체(JSON)로 반환하도록 설정합니다.

```java
public AgentResponse processConsulting(String userId, String userQuery) {
    return chatClient.prompt()
        .user(userQuery)
        .call()
        .entity(AgentResponse.class); // Java Record/DTO 클래스로 자동 매핑
}
```

---

## 5. 실습 단계별 진행 가이드

### Step 1: 도메인 선정 및 데이터 준비
* 본인만의 도메인과 시나리오 정하기 (예: "내 도메인은 X이며, Y 문제를 해결하는 에이전트를 만든다")
* RAG로 사용할 문서 데이터 3~5개 준비 (TXT 또는 JSON 파일)
* Tool로 제공할 Mock 데이터/메서드 1~2개 구상

### Step 2: PgVector 연동 및 RAG 구축
* Docker 기반 PgVector 실행 및 Spring AI 연동 설정
* 준비한 문서 데이터를 Vector DB에 Embedding 후 적재
* Simple Retrieval 테스트 작성 (유사도 검색 동작 확인)

### Step 3: Tool 작성 및 Structured Output DTO 정의
* Agent가 사용할 Java 메서드에 `@Tool` 정의 (예: DB 조회, 계산기 등)
* 최종 결과를 받아볼 Java `record` 또는 Class 작성 (예: `status`, `answer`, `referenceDoc`, `actionTaken` 등)

### Step 4: ChatClient 기반 Agent 통합 및 테스트
* `System Prompt` + `Chat Memory` + `RAG Advisor` + `Tools` 통합
* `.entity(AgentResponse.class)`를 적용하여 Structured Output 반환 확인
* 다단 대화 및 Tool 호출이 제대로 일어나는지 E2E 테스트

### Step 5: 결과 공유 및 데모
* 본인이 만든 도메인 소개 및 시나리오 발표
* 에이전트에 복합 질문을 던져 RAG와 Tool이 동시에 작동하여 JSON을 반환하는 과정 시연

---

## 6. 최종 제출물 스펙

교육생은 다음 구성요소가 포함된 프로젝트를 제출/시연합니다.

1. **도메인 정의서 (간단한 Readme):** 
   * 서비스 목적, RAG 데이터 구성, 사용된 Tool 목록
2. **Spring Boot 애플리케이션 코드:**
3. **API 실행 결과**
   * UI로 구성했을때에는 UI 실행 결과 캡쳐 / API만 구성시 요청과 응답 결과
   * console 로그 스크립트 파일 (실행 과정에서 출력된 로그를 파일로 제공)
