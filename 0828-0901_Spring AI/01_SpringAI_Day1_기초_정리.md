# 🌱 Spring AI 1일차 — 기초 완전 정리

> 💡 **한 줄 요약**
> Spring AI는 **"기업의 DATA와 API를 AI 모델에 연결"** 하기 위한 프레임워크다.
> Spring Data가 JPA/Mongo/Redis를 `Repository`로 추상화했듯, Spring AI는 OpenAI/Claude/Gemini를 **`ChatModel` 하나로 추상화**하고, 그 위에 `ChatClient`라는 Fluent API를 얹어 **프롬프트 구성 → 옵션 → Advisor/Tool → 호출 → 결과 파싱**을 한 줄 체이닝으로 처리한다.

**출처**: `SPRING AI 이해_v1.4.pdf` (총 349p) · SK C&C
**범위**: PDF p3 ~ p157 (1일차 전체)
**실습 코드**: `git clone https://github.com/himang10/spring-ai.git` → `01.training code`(빈칸 채우기용) / `02.answer code`(정답)

> ℹ️ 이 문서의 `p번호`는 **PDF 뷰어 기준 물리 페이지**입니다. 슬라이드 우하단에 인쇄된 번호보다 항상 **1 큽니다**. (예: 본문 p114 = 슬라이드 footer "113")

---

## 📑 목차

| # | 챕터 | 핵심 질문 | 슬라이드 |
|---|---|---|---|
| 1 | [Spring AI 이해](#1-spring-ai-이해) | 왜 Python이 아니라 Spring으로 AI를 만드나? | p3~p15 |
| 2 | [ChatClient API](#2-chatclient-api) | LLM과 대화하는 코드는 어떻게 생겼나? | p16~p39 |
| 3 | [ChatOptions](#3-chatoptions--모델-동작-제어) | Temperature / TopK / TopP는 뭘 조절하나? | p40~p48 |
| 4 | [Prompt & Message](#4-prompt--message) | 좋은 프롬프트는 어떤 4가지로 구성되나? | p49~p73 |
| 5 | [Structured Output](#5-structured-output) | LLM 답변을 Java 객체로 어떻게 받나? | p74~p106 |
| 6 | [Advisor](#6-advisor--요청-가로채기와-기능-향상) | RAG·Memory·Logging을 어떻게 공통화하나? | p107~p128 |
| 7 | [Embedding & VectorStore](#7-embedding--vectorstore) | 의미 검색은 어떤 원리로 동작하나? | p129~p157 |
| ★ | [전체 흐름 한 장 요약](#-전체-흐름-한-장-요약) | — | — |
| ★ | [시험/면접 대비 핵심 문답](#-시험면접-대비-핵심-문답) | — | — |
| ⚠️ | [원문 용어 검증 노트](#️-원문-용어-검증-노트) | — | — |

---

# 1. Spring AI 이해

> 📍 **p3~p15** | AI를 "별도 Python 서비스"로 분리하지 않고, 기존 Spring 애플리케이션 안에서 확장하는 방법

## 1-1. 왜 Spring 기반 AI인가? (3가지 이유, p5)

| # | 이유 | 구체적 내용 |
|---|---|---|
| 1 | **기존 Spring 앱을 그대로 AI로 확장** | 기존 Java/Spring 코드와 개발 역량 재사용 · 별도 Python AI 서비스로 분리할 필요 감소 · 기존 DevOps/운영 체계 활용 |
| 2 | **Enterprise 기능을 AI에도 그대로 적용** | **보안**: Spring Security(OAuth2/JWT/SSO)로 AI 호출의 내부 API·DB 접근 범위 제어<br>**트랜잭션+도메인 로직**: AI 호출 후 DB 저장, 이벤트 발행, SAGA 호출<br>**관측성**: Actuator, Micrometer, Prometheus, Tempo 연동<br>**생태계**: Cloud Native / MSA 솔루션 활용 |
| 3 | **기존 도메인/데이터/서비스를 AI Agent와 결합** | 기존 `Service`·`Repository`를 **AI Tool로 재사용** · 사내 DB·문서·Vector Store를 RAG와 결합 |

## 1-2. 기존 스프링 개발자가 LLM 도입 시 겪는 6가지 문제 (p6~p7)

| 문제 | 설명 |
|---|---|
| **API 파편화** | OpenAI, Anthropic, Bedrock, Ollama 등 벤더마다 요청/응답 스키마·인증 방식·스트리밍 프로토콜이 전부 다름 |
| **모델 종속성** | 모델을 바꾸면 애플리케이션 코드를 수정해야 함 |
| **반복 구현** | 재시도(retry), 타임아웃, 스트리밍 파싱(SSE), 토큰 사용량 로깅을 프로젝트마다 재작성 |
| **AI 패턴 부재** | RAG·대화 메모리·Tool Calling의 표준 인터페이스가 없어 팀마다 제각각 구현 |
| **생태계 단절** | Spring의 DI, AOP, `@ConfigurationProperties`, Micrometer Observability와 자연스럽게 엮이지 않음 |
| **테스트 어려움** | 모델 호출부를 모킹(mocking)하거나 프로바이더를 교체하며 테스트하기 번거로움 |

> ⭐ **핵심 해법**
> Spring의 **추상화 + DI + Auto Configuration**을 AI 영역으로 확대 적용한다.
> `Spring Data : JPA/MongoDB/Redis → Repository` **=** `Spring AI : OpenAI/Anthropic/Gemini → ChatModel`

## 1-3. Spring AI의 목적과 설계 철학 (p8~p9)

| | 내용 |
|---|---|
| **비유로 말하면** | 콘센트 규격(220V)이다. 어느 나라 가전(모델)을 꽂아도 같은 플러그(ChatClient)로 쓸 수 있게 만든 표준 어댑터. |
| **정확히 말하면** | Spring 애플리케이션에서 LLM · Embedding Model · Vector Database · RAG · Tool Calling · MCP 등의 생성형 AI 기능을 **일관된 Spring 방식으로 사용**하도록 제공하는 AI 애플리케이션 프레임워크. |

```plain text
[ p9 — Spring AI의 핵심 설계 철학 ]

        ┌─────────── To There ───────────┐
        │                                ▼
 ┌──────────────────┐            ┌──────────────────┐
 │  Application     │            │                  │
 │  ┌────────────┐  │            │                  │
 │  │ Your Data  │  │   🧠       │  Generative AI   │
 │  └────────────┘  │            │                  │
 │  ┌────────────┐  │            │                  │
 │  │ Your APIs  │  │            │                  │
 │  └────────────┘  │            │                  │
 └──────────────────┘            └──────────────────┘
        ▲                                │
        └─────────── To Here ────────────┘

  Spring AI의 핵심 = "기업 DATA, 기업 API를 AI 모델에 연결하는 것"
```

## 1-4. Spring AI의 특징 (p10)

| 특징 | 의미 |
|---|---|
| **AI Model 추상화** | 다양한 LLM/Embedding Model을 일관된 API로 사용 (OpenAI, Anthropic, Gemini, Ollama 등) |
| **Spring IoC/DI** | AI 구성 요소를 Bean으로 관리하고 DI (`ChatClient`, `ChatModel` 등) |
| **Auto Configuration** | Spring Boot 기반 자동 설정 |
| **ChatClient** | Fluent API를 통한 편리한 LLM 호출 |
| **Advisor** | Memory, RAG 등 AI 요청 처리 기능 확장 |
| **RAG** | Document, Embedding, VectorStore 추상화 |
| **Tool Calling** | Java Method와 LLM을 연결하여 Action 수행 |
| **MCP** | 외부 Tool/Resource 생태계와 연동 |
| **Spring 생태계 통합** | MVC/WebFlux, Security, Data 등과 결합 |

## 1-5. Spring AI 주요 기능 모듈 7가지 (p12)

| 모듈 영역 | 역할 |
|---|---|
| **Models** | `ChatModel`, `EmbeddingModel`, `ImageModel` 등 모델 추상화 |
| **Prompts** | `Prompt`, `Message`(System/User/Assistant), `PromptTemplate` |
| **Structured Output** | `BeanOutputConverter` 등 응답을 Java 객체로 변환 |
| **RAG** | `DocumentReader`, Splitter, `VectorStore`, Advisor |
| **Tool Calling** | `@Tool`, `ToolCallback`, `MethodToolCallbackProvider` |
| **MCP** | MCP Client/Server 통합 |
| **Observability** | Micrometer 기반 트레이싱/메트릭 |

> 💡 **버전 (p13)**: Spring AI **Stable 2.0.0** 기준으로 진행. (그 외 stable: 1.1.8, 1.0.9)
> 문서: `https://docs.spring.io/spring-ai/reference/2.0/getting-started.html`

## 1-6. Spring AI 기반 Agent — 왜 배우나 (p14~p15)

> **Agentic AI란?** 과거의 AI가 단순한 **"글짓기 도구"** 였다면, Agentic AI는 **"일하는 시스템"** 이다.

```plain text
[ p14 — Agent 시나리오 예시 ]

사용자: "내일 비 오면 회의 일정을 실내로 변경해줘"

  ┌─ 추론(Reasoning) ────────────────────────────┐
  │ 1. 내일 날씨 확인 필요      → Weather API 호출  │
  │ 2. 비 오는지 판단          → 조건문 처리        │
  │ 3. 비 온다면              → Calendar API 호출  │
  │ 4. 참석자들에게 알림       → Email API 호출     │
  └──────────────────────────────────────────────┘
                    ↓
  ┌─ 행동(Action) ───────────────────────────────┐
  │ · 날씨 API 호출                               │
  │ · 날씨가 "비"이면 → 회의실 변경 API 호출        │
  │ · 이메일 발송 API 호출                         │
  │ → "회의 장소를 B 회의실로 변경했습니다."         │
  └──────────────────────────────────────────────┘

  Agent의 4요소:  데이터 · 행동 · 기억 · (추론)
```

> ✅ **결론 (p3)**
> 이 과정은 **"Agent를 잘 만드는 방법"** 이 아니라, **"Agent를 만드는 Spring 도구를 이해하고 사용하는 방법"** 을 배우는 과정이다. 즉 **코드로 LLM과 대화하는 방법**이 목표다.

---

# 2. ChatClient API

> 📍 **p16~p39** | AI Model과 상호작용하는 두 계층 — `ChatModel`(저수준 추상화)과 `ChatClient`(고수준 Fluent API)

## 2-1. ChatModel vs ChatClient — 가장 헷갈리는 구분 (p17~p18)

| | **ChatModel** | **ChatClient** |
|---|---|---|
| **비유로 말하면** | 콘센트 규격 자체 (220V 표준) | 멀티탭 + 스위치 (편의 기능이 붙은 것) |
| **정확히 말하면** | 다양한 LLM의 요청·응답 방식을 일관되게 추상화한 **핵심 인터페이스** | `ChatModel` **위에서** Prompt·Advisor·Tool·응답 처리를 조합하는 **고수준 Fluent API** |
| **계층** | 저수준 (Low-level) | 고수준 (High-level Façade) |
| **책임** | ① 이식성(Portability) ② 입출력 변환 | 프롬프트 구성 → 옵션 → Advisor/Tool/Memory → 호출 → 결과 파싱 |

**ChatModel의 2가지 책임 (p17)**

1. **Portable Interface(이식성)**
   - OpenAI(GPT), Anthropic(Claude), Google(Gemini), Ollama 등을 모두 `ChatModel`로 추상화
   - 개발자는 **어떤 모델을 쓰든 동일한 코드**로 상호작용
2. **입출력 변환**
   - 표준 `Prompt` → AI 모델이 이해하는 **Native API 요청 형식(HTTP)** 으로 변환
   - AI Model의 원시 응답(HTTP Response JSON) → Spring 표준 응답 객체 **`ChatResponse`** 로 변환

```plain text
[ p18 — ChatClient / ChatModel / LLM 3계층 ]

 Application        Fluent API      ┌─ Prompt Object ─┐     HTTP POST
   Code      ────►  ChatClient ────►│  List<Message>  │────►  ChatModel  ────► LLM
                                    │  ChatOption     │      JSON            /v1/chat/completions
                                    └─────────────────┘                      /v1/messages
```

## 2-2. 첫 번째 대화 — Hello World (동기, p19 / p24)

```java
@RestController
class MyController {

    private final ChatClient chatClient;

    // Autoconfigured ChatClient.Builder is injected
    public MyController(ChatClient.Builder chatClientBuilder) {
        this.chatClient = chatClientBuilder.build();
    }

    @GetMapping("/ai")
    public String generation(@RequestParam String userInput) {
        // The Fluent API in Action
        return this.chatClient.prompt()   // 1. 대화 시작 → ChatClientRequestSpec
                .user(userInput)          // 2. UserMessage 설정
                .call()                   // 3. 동기 호출 → CallResponseSpec
                .content();               // 4. 응답 본문(String)만 추출
    }
}
```

## 2-3. 비동기 스트리밍 (p25)

```java
@RestController
class MyController {

    private final ChatClient chatClient;

    public MyController(ChatClient.Builder builder) {
        this.chatClient = builder.build();
    }

    @GetMapping(value = "/ai", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public Flux<String> stream(@RequestParam String userInput) {
        return chatClient.prompt()
                .user(userInput)
                .stream()      // → StreamResponseSpec
                .content();    // 토큰/청크 단위로 계속 내려옴
    }
}
```

> 💡 **`.call()` vs `.stream()`**
> `.call()` → `CallResponseSpec` (완성된 응답 1회) / `.stream()` → `StreamResponseSpec` (`Flux<String>` 청크 스트림)
> 스트리밍은 반드시 `produces = MediaType.TEXT_EVENT_STREAM_VALUE`(SSE)를 붙여야 브라우저가 실시간으로 받는다.

## 2-4. Fluent API란? (p20)

코드를 **문장(자연어)처럼 읽히게** 만들기 위해 **메서드 체이닝 + 의미 있는 메서드 이름**으로 설계한 API 스타일.

```java
// 예시 1: Java Stream API
List<String> names = Arrays.asList("Alice", "Bob", "Charlie");
names.stream()
     .filter(n -> n.length() > 3)
     .map(String::toUpperCase)
     .toList();

// 예시 2: Method Chaining의 원리 — setter가 this를 반환한다
class Person {
    private String name;
    private int age;

    public Person setName(String name) {
        this.name = name;
        return this;      // ← 자기 자신을 리턴해야 체이닝이 가능
    }
    public Person setAge(int age) {
        this.age = age;
        return this;
    }
}
```

## 2-5. Prompt / Message / ChatResponse 클래스 구조 (p22~p23, p27~p28)

```java
// [p22] Prompt = Message 목록 + 실행 옵션을 담은 요청 컨테이너
public final class Prompt implements ModelRequest<List<Message>> {
    private final List<Message> messages;   // LLM에 전달할 Message 목록
    private final ChatOptions options;      // 모델 호출 옵션 (model, temperature, maxTokens 등)
}

// [p23] Message = 대화 정보를 "역할별"로 표현하는 sealed interface
public sealed interface Message
        permits SystemMessage, UserMessage, AssistantMessage, ToolResponseMessage {
    String role();      // system | user | assistant | tool
    Object content();   // 보통 String (또는 structured)
}

public class AssistantMessage extends AbstractMessage implements MediaContent {
    private final List<ToolCall> toolCalls;   // ← Tool 호출 요청이 여기 담긴다
}
```

| Message | 의미 |
|---|---|
| `SystemMessage` | LLM의 역할·규칙·지침 |
| `UserMessage` | 사용자의 요청, Text/Media |
| `AssistantMessage` | LLM의 응답, **ToolCall 포함 가능** |
| `ToolResponseMessage` | Tool 실행 결과를 LLM에 전달 |

**ChatResponse 구조 (p27~p28)**

```plain text
ChatResponse
    │
    ├── ChatResponseMetadata      ← 모델 정보, 토큰 사용량, 요청 ID
    │
    └── List<Generation> results  ← LLM이 생성한 결과 후보들 (choices)
             │
             └── Generation
                   └── AssistantMessage output
                          ├── text
                          └── ...
```

```java
public final class ChatResponse {
    private final ChatResponseMetadata chatResponseMetadata;  // 모델 정보, 토큰 사용량, 요청 ID
    private final List<Generation> generations;               // LLM이 생성한 결과 후보들
}
```

| | ChatResponse 역할 | Generation 역할 |
|---|---|---|
| **범위** | LLM 호출 **1회에 대한 전체 결과** | LLM이 만든 **단일 응답 후보** |
| **내용** | `ChatResponseMetadata`(모델 정보/토큰 사용량/요청 ID) + `generations` | 실제 응답 내용 |
| **개수** | 1개 | 일반적으로 1개. **temperature가 높거나 여러 개를 요청하면 여러 개** 가능 |

**추출 레벨 3단계 (p28 / p58)**

```java
ChatResponse rsp     = chatClient.prompt().user("hi").call().chatResponse();  // 전체 메타데이터까지
Generation   msg     = chatClient.prompt().user("hi").call().getResult();     // 응답 후보 1개
String       content = chatClient.prompt().user("hi").call().content();       // 본문 텍스트만
```

## 2-6. ChatClient.Builder — 재사용 가능한 클라이언트 구성 (p26)

```java
// System Prompt + Advisor를 미리 심어둔 ChatClient
ChatClient chatClient =
    ChatClient.builder(chatModel)
        .defaultSystem("""
             당신은 사내 기술지원 AI Agent입니다.
        """)
        .defaultAdvisors(/* ... */)
        .build();
```

**멀티 모델 환경 — `@Qualifier` 기반 DI (p26 / p39)**

```java
@Configuration
public class ChatClientConfig {

    @Bean("openAiChatClient")
    public ChatClient openai(OpenAiChatModel chatModel) {
        return ChatClient.create(chatModel);
    }

    @Bean("anthropicChatClient")
    public ChatClient anthropic(AnthropicChatModel chatModel) {
        return ChatClient.create(chatModel);
    }
}

@Configuration
public class ChatClientExample {
    @Bean
    CommandLineRunner cli(
            @Qualifier("openAiChatClient")     ChatClient openAi,
            @Qualifier("anthropicChatClient")  ChatClient anthropic) {
        // 상황에 따라 골라 쓴다
        return args -> { /* ... */ };
    }
}
```

## 2-7. 의존성 & 설정 (p29~p31)

**pom.xml — BOM(Bill Of Materials)으로 버전 일괄 관리**

```xml
<properties>
    <java.version>21</java.version>
    <maven.compiler.source>21</maven.compiler.source>
    <maven.compiler.target>21</maven.compiler.target>
    <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
    <spring-ai.version>2.0.0</spring-ai.version>
</properties>

<dependencyManagement>
    <dependencies>
        <dependency>
            <groupId>org.springframework.ai</groupId>
            <artifactId>spring-ai-bom</artifactId>
            <version>${spring-ai.version}</version>
            <type>pom</type>
            <scope>import</scope>
        </dependency>
    </dependencies>
</dependencyManagement>
```

**모델별 Starter (p30)**

| 모델 | artifactId |
|---|---|
| OpenAI | `spring-ai-starter-model-openai` |
| Claude | `spring-ai-starter-model-anthropic` |
| Gemini | `spring-ai-starter-model-google-genai` |

**application.yaml (p31)**

```yaml
spring:
  ai:
    model:
      chat: openai            # ← 어떤 모델을 쓸지 여기서 스위치

    # 1) OpenAI (ChatGPT) - 활성화
    openai:
      api-key: ${OPENAI_API_KEY}
      chat:
        options:
          model: gpt-4o-mini
          temperature: 0.7

    # 2) Anthropic (Claude) - 사용하려면 주석 해제 + ai.model.chat: anthropic
    # anthropic:
    #   api-key: ${ANTHROPIC_API_KEY}
    #   chat:
    #     model: claude-sonnet-4-20250514
    #     temperature: 0.7
```

> ⚠️ **API Key는 절대 yaml에 하드코딩하지 말 것.** `${OPENAI_API_KEY}` 환경변수 참조 형태를 유지한다.

## 2-8. 🧪 실습 — Hello World (p32~p38)

**① 환경 준비**

```bash
git clone https://github.com/himang10/spring-ai.git
```

```bash
echo 'export OPENAI_API_KEY=여기에_본인_KEY' >> ~/.zshrc && source ~/.zshrc
```

```bash
brew install kubectl jq curl maven gradle git node && brew install openjdk@21
```

```bash
echo 'export JAVA_HOME=/opt/homebrew/opt/openjdk@21' >> ~/.zshrc && source ~/.zshrc
```

**② `ChatController.java`의 `chat()` — 동기 방식 (p34)**

```java
@GetMapping("/ai")
public String chat(@RequestParam String userInput) {
    // The Fluent API in Action (동기 방식)
    return this.chatClient.prompt()
            .user(userInput)
            .call()
            .content();
}
```

**③ `chatStream()` — 비동기 방식 (p35)**

```java
@GetMapping(value = "/ai/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
public Flux<String> chatStream(@RequestParam String userInput) {
    return this.chatClient.prompt()
            .user(userInput)
            .stream()
            .content();
}
```

**④ 빌드 및 실행 (p36)**

```bash
mvn clean install -DskipTests && java -jar ./target/spring-ai-0.0.1-SNAPSHOT.jar
```

```bash
gradle clean build -x test && java -jar ./build/libs/spring-ai-0.0.1-SNAPSHOT.jar
```

**체크리스트**
- [ ] `localhost:8080` 접속 (Thymeleaf UI 포함되어 있음)
- [ ] "너에 대해 소개해줘" 질문
- [ ] 동기(`/ai`)와 비동기(`/ai/stream`)의 출력 차이 확인 — 스트리밍은 글자가 흘러나온다

> 💡 **Maven repository가 막혀 있을 때 (p37)**
> `spring-ai/repo-setting` 아래의 `settings.xml`(maven) 또는 `init.gradle`(gradle)을 복사해 우회 저장소(`https://maven-central.storage-download.googleapis.com/maven2/`)를 쓴다.

```bash
cp settings.xml ~/.m2/
```

```bash
cp init.gradle ~/.gradle/
```

---

# 3. ChatOptions — 모델 동작 제어

> 📍 **p40~p48** | 프롬프트를 최적화하기 위한 방법 — 모델의 **생성 규칙**을 코드로 제어한다

## 3-1. ChatOptions 인터페이스 (p41)

```java
public interface ChatOptions extends ModelOptions {
    String  getModel();        // 대화에 사용할 모델 이름
    Integer getMaxTokens();    // 생성될 응답의 최대 토큰 수
    Float   getTemperature();  // 응답 다양성 조절 온도 값. 클수록 다양
    Integer getTopK();         // 상위 K개 후보 단어 중 무작위 선택. K가 클수록 다양
    Float   getTopP();         // 누적 확률 P 이하 단어 중 선택. P가 클수록 다양
    // ...
}
```

## 3-2. 주요 옵션 6가지 (p42)

| 구문 | 타입 | 설명 | 비고 |
|---|---|---|---|
| `model` | String | 호출할 AI 모델 식별자 | e.g. `gpt-4o-mini` |
| `temperature` | Double | 토큰 선택의 **무작위성** 조절 | 낮을수록 일관성 |
| `maxTokens` | Integer | 모델이 생성할 최대 토큰 수 | 출력 길이 제한 |
| `topP` | Double | **누적 확률** 기반 Sampling 범위 | e.g. `0.9` |
| `topK` | Integer | 확률 **상위 K개** 토큰만 Sampling 후보로 제한 | 모델에 따라 미지원 |
| `stopSequences` | List\<String\> | 특정 문자열 생성 시 응답 생성을 중단 | 모델에 따라 동작 차이 |

## 3-3. Temperature (p43~p45)

| | 설명 |
|---|---|
| **비유로 말하면** | 주사위의 "찌그러짐 정도". 0.0이면 항상 6만 나오는 찌그러진 주사위, 1.5면 완전 균등한 주사위. |
| **정확히 말하면** | LLM이 다음 토큰을 선택할 때 **확률 분포를 얼마나 보수적으로/다양하게 사용할지** 조절하는 값. 응답의 무작위성(Randomness)과 다양성(Creativity)을 조절한다. |

| Temperature | 특성 | 적합한 용도 |
|---|---|---|
| **0.0** | 매우 결정적이고 일관된 응답 | 코드, 분류, 정보 추출, 정형 응답 |
| **0.7** | 일관성과 다양성의 균형 | 일반 대화, 설명, 문서 작성 |
| **1.0** | 다양성과 창의성이 증가 | 아이디어 생성, 브레인스토밍 |
| **1.5** | 무작위성이 매우 높아짐 | 창작, 다양한 아이디어 탐색 |

```plain text
[ p44~p45 — 확률 분포의 모양이 바뀐다 ]

Temperature = 0.0        Temperature = 0.7          Temperature = 1.5
확률 분포가 "뾰족"        적당히 완만                 확률 분포가 "평탄"

  █                        █                          ▄
  █                        █ ▄                      ▄ ▄ ▄ ▄
  █ _ _ _                  █ ▄ _ _                  ▄ ▄ ▄ ▄ ▄
 좋은                     좋은 유용한                좋은 유용한 강력한 …

→ 같은 질문을 6번 하면 (T=0.7):
   1회 좋은 / 2회 좋은 / 3회 유용한 / 4회 좋은 / 5회 강력한 / 6회 좋은
```

## 3-4. TopK vs TopP (p46)

**Top-K Sampling**: 확률이 높은 **상위 K개**의 토큰만 후보로 남기고 그 안에서 선택.

```plain text
원본 확률           Top K = 2 적용         재정규화(renormalize)
─────────────      ────────────────      ────────────────────
맑네요   50%   →   맑네요   50%  ─┐        맑네요  : 50/80 = 62.5%
흐리네요 30%   →   흐리네요 30%  ─┴─후보    흐리네요: 30/80 = 37.5%
좋네요   10%   →   좋네요   10%   ✗
싫어요    5%   →   싫어요    5%   ✗        K↓ : 후보 제한 → 일관성 증가
기타      5%   →   기타      5%   ✗        K↑ : 후보 증가 → 다양성 증가
```

**Top-P (Nucleus) Sampling**: 확률이 높은 토큰부터 **누적**하여 지정한 확률 P에 도달하는 **최소 후보 집합**에서 선택.

```plain text
Top P = 0.9
맑네요   50%  → 누적 50%   ✔ 후보
흐리네요 30%  → 누적 80%   ✔ 후보
좋네요   10%  → 누적 90%   ✔ 후보 (여기서 P=0.9 도달, 컷)
싫어요    5%  → 제외
기타      5%  → 제외
```

> ⭐ **차이의 본질**
> **Top-K = 개수로 자른다(고정)** / **Top-P = 확률 누적으로 자른다(가변)**
> Top-P는 확률이 한쪽에 쏠린 상황에선 후보를 적게, 고르게 퍼진 상황에선 후보를 많이 뽑는다 → 상황 적응적.

## 3-5. ChatOptions 설정 두 가지 방식 (p47)

```java
// 방식 A: Chain 방식 — 호출할 때마다 인라인으로
String answer = chatClient
     .prompt()
     .user("Spring AI에서 ChatOptions 설정 예제를 보여줘.")
     .options(ChatOptions.builder()
                .model("gpt-4o-mini")
                .temperature(0.5)
                .topP(0.95)
                .build())
     .call()
     .content();
```

```java
// 방식 B: 공통 Bean으로 재사용
@Configuration
public class ChatConfig {

    @Bean
    public ChatOptions.Builder<?> commonChatOptions() {
        return ChatOptions.builder()
                .model("gpt-4o-mini")
                .temperature(0.3);
    }
}
```

## 3-6. 🧪 실습 — Hello World에 ChatOption 추가 (p48)

```java
ChatOptions.Builder<?> chatOptions = ChatOptions.builder()
        .model("gpt-4o-mini")
        .temperature(0.7)
        .topP(0.9)
        .maxTokens(500);

return this.chatClient.prompt()
        .options(chatOptions)     // ← 추가
        .user(userInput)
        .stream()
        .content();
```

> ⚠️ **런타임 옵션이 시작 시점 옵션을 덮어쓴다 (p56)**
> `application.yaml`의 `chat.options`는 **Start-Up 옵션**, `.options(...)`으로 넘긴 것은 **Runtime 옵션**.
> **Runtime 옵션이 항상 우선**한다.

```plain text
[ p56 — Chat Model 호출 흐름 ]

 ┌─ Prompt ────────┐    ┌─ ChatModel / StreamingChatModel ────────┐   ┌─ ChatResponse ─┐
 │ <<Runtime>>     │    │                          <<Start-Up>>   │   │  Generations   │
 │  Chat Options   │───►│  Convert    Merge      ← Chat Options    │   │   ├ Output     │
 │                 │    │   Input  →  Options  →  Convert Output ──┼──►│   └ Metadata   │
 │ List<Message>   │───►│     │                        ▲          │   │  Metadata      │
 │  Instructions   │    │     ▼                        │          │   └────────────────┘
 └─────────────────┘    │  ┌──── Native LLM API ───────┴──┐       │
                        │  │ Request → AI Model → Response│       │
                        │  └──────────────────────────────┘       │
                        └─────────────────────────────────────────┘

 · Instructions는 Text 또는 오디오/이미지/비디오 등 입력 가능(멀티모달)
 · Runtime에 지정된 옵션은 Start-up 시점의 옵션보다 우선
```

---

# 4. Prompt & Message

> 📍 **p49~p73** | 프롬프트를 최적화하기 위한 방법

## 4-1. Prompt란 (p50)

| | 설명 |
|---|---|
| **비유로 말하면** | 신입에게 주는 업무 지시서. 배경 설명 + 할 일 + 자료 + 제출 형식이 다 들어있어야 제대로 된 결과가 온다. |
| **정확히 말하면** | LLM에게 **역할, 맥락(Context), 지시사항, 사용자 질문** 등을 전달하여 모델의 응답 생성을 유도하는 입력. |
| **Spring AI의 Prompt 객체** | LLM에 전달할 **Message들 + 모델 실행 옵션(ChatOptions)** 을 하나로 구성하여 `ChatModel`에 전달하는 **요청 객체**. |

## 4-2. 프롬프트의 4대 구성 요소 (p51) ⭐

| 요소 | 역할 | 예시 |
|---|---|---|
| **① Context (맥락/배경)** | 답변을 판단하는 데 참고할 배경 정보 | · System Persona: "너는 10년 차 시니어 스프링 아키텍트다"<br>· RAG 검색 컨텍스트: "다음은 사내 기술 문서에서 검색된 데이터다"<br>· Conversation History: 이전 턴의 대화 맥락 |
| **② Instruction (지시/작업)** | 모델이 수행할 **구체적인 액션**과 **생각하는 방식**을 통제 | · 구체적 작업 지시: "주어진 코드의 취약점을 분석하고 리팩토링 코드를 작성하라"<br>· 단계별 사고 유도: "먼저 문제 원인을 1단계로 파악한 후, 2단계로 해결책을 제시하라" |
| **③ Input Data (대상 데이터)** | 실제로 처리해야 하는 대상 데이터 | 분석할 소스코드 / 로그 파일 / JSON / 표 데이터 |
| **④ Output Indicator (형식/제약)** | 결과물이 시스템·사용자에게 전달될 때 갖춰야 할 **형식** | · 데이터 스키마 강제: `status: SUCCESS`, `error_code: ...`<br>· 렌더링 형식: Markdown 표, 불릿 포인트<br>· 응답 스타일/제약: 서론·결론 생략 |

**4요소를 다 갖춘 실전 프롬프트 (p52)**

```plain text
### 1. Context (배경 및 역할)
- 당신은 Kubernetes 기반 Spring Boot 3.x MSA 환경을 운영하는 시니어 백엔드 SRE 엔지니어입니다.
- 현재 무중단 배포(Rolling Update) 중 특정 파드에서 메모리 누수 의심 장애가 발생했습니다.

### 2. Instruction (작업 지시 및 추론 규칙)
1. 주어진 Input Data(로그/메트릭)를 분석하여 장애의 근본 원인을 단계별(Step-by-step)로 추론하세요.
2. 해결을 위한 Spring Boot 설정 변경점 또는 K8s 매니페스트 수정 가이드를 1개 이상 도출하세요.
3. [주의] 제공된 근거 자료에 없는 내용은 절대 추측하여 지어내지 말고 "근거 부족"으로 명시하세요.

### 3. Input Data (분석 대상)
[RAG 검색 지식 베이스]
- JVM MaxDirectMemorySize 기본값 및 Netty 메모리 누수 가이드 문서 발췌본
[시스템 로그 / 메트릭]
- 2026-08-16T10:50:00.123Z [ERROR] io.netty.util.internal.OutOfDirectMemoryError:
  failed to allocate 16777216 byte(s) of direct memory

### 4. Output Indicator (출력 규격)
반드시 부가적인 인사말 없이 아래 JSON 스키마 규격으로만 응답하세요:
{
  "root_cause": "장애 근본 원인 분석 요약",
  "reasoning": "...",
  ...
}
```

> ⭐ **4요소 → Message 매핑 (p54)**
> **Context + Instruction → SystemMessage** / **Input Data + 질문 → UserMessage** / **Output Indicator**는 System 또는 User 어느 쪽에도 넣을 수 있다 (Structured Output을 쓰면 자동 주입된다).

## 4-3. Prompt Class 구조 (p53)

```java
public class Prompt implements ModelRequest<List<Message>> {
    private final List<Message> messages;   // System, User, Assistant Message
    private ChatOptions modelOptions;
}
```

```plain text
Message (공통 기본 필드)
├── MessageType messageType        // 메시지 역할 (SYSTEM, USER, ASSISTANT, TOOL)
├── String textContent             // 텍스트 본문 내용
├── List<Media> media              // 멀티모달 데이터 (이미지, 오디오 등)
└── Map<String, Object> metadata   // 토큰 수, 실행 속성 등 부가 정보
```

이것이 실제 HTTP로 나갈 땐 이렇게 직렬화된다:

```json
[
  { "role": "system", "content": "너는 Spring Boot 전문가다. (Context / Instruction)" },
  { "role": "user",   "content": "이 로그 원인을 분석해줘: ... (Input Data)" }
]
```

## 4-4. Message 4종 상세 (p54, p60~p61)

| 메시지 유형 | 역할 | 담기는 프롬프트 요소 |
|---|---|---|
| **SystemMessage** | 규칙·스타일 등 **고정 지침**을 저장 | 공통 Context + Instruction |
| **UserMessage** | 사용자 입력·질문과 대화 이력을 저장 | **4가지 요소 모두 포함 가능** |
| **AssistantMessage** | AI 모델의 응답 메시지 저장 | LLM 응답 (+ ToolCall) |
| **ToolMessage / ToolResponseMessage** | 외부 도구 호출/결과 전달 | Tool Call |

**SystemMessage vs UserMessage (p60)**

| | SystemMessage | UserMessage |
|---|---|---|
| **역할** | 대화에서 무엇을 우선시해야 하는지에 대한 **최상위 지침** | 실제 사용자(사람)가 하는 질문·요청·지시 |
| | 대화 전반의 **규칙, 역할, 톤, 제약사항** 정의 | 모델이 응답해야 할 **주요 입력** |
| | 모델이 어떤 사람/에이전트처럼 행동할지 정함 | 프론트엔드/백엔드에서 사용자의 입력을 담아 보내는 부분 |
| **위치** | 보통 대화의 **맨 앞에 1개**, 필요하면 여러 개 | 매 턴마다 |
| **예시** | "당신은 Spring AI와 MCP를 잘 아는 시니어 백엔드 개발자이자 강사이다. 답변은 항상 한국어로 하고, 예제 코드는 Java와 Spring Boot 위주로 제공한다." | "Spring AI에서 ChatClient로 GPT에게 스트리밍 응답을 받는 코드를 작성해줘. RestController로 구현하고, /ai/stream 엔드포인트로 호출할 수 있게 해줘." |

**AssistantMessage(Tool 요청) vs ToolResponseMessage (p61)**

| | AssistantMessage (Tool 요청용) | ToolResponseMessage |
|---|---|---|
| **역할** | 모델이 응답한 메시지 자체. **사용할 도구 정보**를 Spring으로 전달 | MCP Server로부터 받은 **Tool 실행 결과**를 LLM으로 전달 |
| **방향** | LLM → MCP Client | MCP Server → MCP Client → LLM |
| **예시** | `weatherTool`을 호출하라고 Spring AI에 전달 | `weatherTool` 호출 **결과**를 모델에게 전달 |

```json
// AssistantMessage (LLM → Spring AI)
{
  "role": "assistant",
  "content": null,
  "tool_calls": [
    { "id": "call_1", "type": "function",
      "function": { "name": "getCurrentWeather", "arguments": "{\"city\":\"Busan\"}" } }
  ]
}
```

## 4-5. SystemMessage를 코드로 만들기 (p55)

```java
SystemMessage systemMessage = SystemMessage.builder()
        .text("""
        너는 SKALA Spring AI 교육을 도와주는 조교입니다. 질문에 친절하고 친근하게 답해주세요
        """)
        .build();

// ⚠️ ChatClientRequestSpec.system()은 String/Resource/Consumer만 받으므로
//    이미 만들어진 SystemMessage 객체는 messages()로 등록한다.
return this.chatClient.prompt()
        .messages(systemMessage)
        .user(userInput)
        .stream()
        .content();
```

> ⚠️ **자주 하는 실수**: `.system(systemMessage)` ← **컴파일 안 됨**.
> `.system()`은 `String` / `Resource` / `Consumer<PromptSystemSpec>`만 받는다. `SystemMessage` **객체**는 `.messages(...)`로 넣어야 한다.

## 4-6. Prompt → Native LLM Request 변환 (p59)

Spring AI의 통합 형식이 **각 모델별 네이티브 형식**으로 자동 변환된다.

```json
// Anthropic Claude의 경우 — system이 별도 최상위 필드로 빠진다
{
  "model": "claude-3-5-sonnet-20241022",
  "system": "당신은 친절한 AI 어시스턴트입니다",
  "messages": [
    { "role": "user", "content": "안녕하세요" }
  ]
}
```

> ⭐ OpenAI는 `system`도 `messages` 배열 안에 들어가지만, Claude는 **최상위 `system` 필드**로 분리된다.
> 이 차이를 개발자가 신경 쓰지 않아도 되게 만드는 것이 바로 `ChatModel` 추상화의 존재 이유다.

## 4-7. 🧪 실습 — System Message 적용 (p62~p64)

**① `chat()` 메서드 (동기)**

```java
return this.chatClient.prompt()
        .options(chatOptions)
        .system("""
            너는 바다를 항해하는 해적입니다. 질문에 터프하고 직설적으로 답해주세요
            """)
        .user(userInput)
        .call()
        .content();
```

**② `chatStream()` 메서드 (비동기)**

```java
SystemMessage systemMessage = SystemMessage.builder()
        .text("""
        너는 SKALA Spring AI 교육을 도와주는 조교입니다. 질문에 친절하고 친근하게 답해주세요
        """)
        .build();

return this.chatClient.prompt()
        .options(chatOptions)
        .messages(systemMessage)
        .user(userInput)
        .stream()
        .content();
```

**③ 다른 페르소나로 바꿔보기 (p64)**

```java
// 페르소나 A — 친절한 보조교사
.system("""
    너는 SKALA Spring AI 교육 과정의 친절하고 열정적인 보조교사 '알라'야.
    - 수강생의 질문에 따뜻하고 격려하는 어조로 답변해 줘.
    - 전문 용어는 초보자도 이해하기 쉽게 비유를 들어서 설명해 줘.
    - 답변 끝에는 항상 실습을 응원하는 따뜻한 한 마디를 덧붙여 줘.
    """)

// 페르소나 B — 트러블슈팅 조교
.system("""
    너는 SKALA Spring AI 트러블슈팅 전담 조교야.
    - 수강생이 겪는 에러나 디버깅 질문에 대해 단계별(Step-by-Step)로 문제 원인을 추적하도록 안내해 줘.
    - 1) 예상 원인 2) 확인해야 할 설정/코드 위치 3) 수정 코드 예시 순서로 답변을 구성해 줘.
    - 자주 발생하는 실수(예: API Key 누락, Bean 등록 오류, 버전 불일치 등)가 있다면 함께 짚어 줘.
    """)
```

**체크리스트**
- [ ] `mvn clean install -DskipTests` → `java -jar ./target/spring-ai-0.0.1-SNAPSHOT.jar`
- [ ] `localhost:8080`에서 "너에 대해 소개해줘" 질문
- [ ] System Message를 바꿔가며 답변 **톤**이 바뀌는지 확인

## 4-8. 동적 프롬프트 3가지 방식 (p65~p69)

| 방식 | 사용 빈도 | 주요 사용 목적 / 특징 |
|---|---|---|
| **ChatClient 내장 바인딩** | **높음** | 추가 객체 생성 없이 `.user(text, params)`로 직관적 처리 |
| **PromptTemplate** | 보통 | **외부 파일(Resource) 관리** 및 템플릿 재사용 시 필수 |
| **String.format** | 보통 | 하드코딩된 아주 간단한 동적 파라미터 1~2개 처리 시 |

**① ChatClient 내장 바인딩 (p66)**

```java
import org.springframework.ai.chat.client.ChatClient;

String composerName = "John Williams";

// UserMessageSpec(Consumer<PromptUserSpec>)을 사용한 방식
var data = chatClient
    .prompt()
    .user(u -> u
        .text("Tell me the names of 5 movies whose soundtrack was composed by {composer}")
        .param("composer", composerName)
    );

String answer = data.call().content();
```

**② PromptTemplate — 코드 내 정의 (p67)**

```java
private final PromptTemplate systemPrompt = new PromptTemplate("""
        너는 SKALA Spring AI 교육 과정의 친절하고 열정적인 보조교사 '{aiName}이'야.
            - 수강생의 질문에 따뜻하고 격려하는 어조로 답변해 줘.
            - {terms}는 초보자도 이해하기 쉽게 비유를 들어서 설명해 줘.
            - 답변 끝에는 항상 실습을 응원하는 따뜻한 한 마디를 덧붙여 줘.
        """);

String systemMessage = systemPrompt.render(Map.of(
        "aiName", "스프링",
        "terms",  "스프링 용어"
));
```

**③ PromptTemplate — 외부 `.st` 파일 (p68)** ⭐ 실무에서 가장 유용

```plain text
# resources/prompts/movie-composer.st
Tell me the names of {count} movies whose soundtrack was composed by {composer}.
Please reply in Korean and provide brief descriptions for each movie.
```

```java
// classpath 내의 .st 프롬프트 파일 읽어오기
@Value("classpath:/prompts/movie-composer.st")
private Resource moviePromptResource;

public String getMoviesByComposer(String composerName, int count) {
    // 1. Resource를 이용하여 PromptTemplate 생성
    PromptTemplate template = new PromptTemplate(moviePromptResource);

    // 2. template.render()로 템플릿 변수를 렌더링된 String으로 반환
    String renderedPrompt = template.render(Map.of(
            "count", count,
            "composer", composerName
    ));

    return chatClient.prompt().user(renderedPrompt).call().content();
}
```

> ✅ **왜 외부 파일인가?** 애플리케이션 **코드에서 프롬프트 로직을 분리**하여 재사용성과 유지보수성을 높인다. 프롬프트를 고치려고 Java를 재컴파일할 필요가 없어진다.

**④ String.format (p69)**

```java
String composerName = "John Williams";

// String.format
String userPrompt = String.format(
        "Tell me the names of 5 movies whose soundtrack was composed by %s", composerName);

// Java 15 이상 — String.formatted
String userPrompt2 = "Tell me the names of 5 movies whose soundtrack was composed by %s"
        .formatted(composerName);

String answer = chatClient.prompt().user(userPrompt).call().content();
```

## 4-9. PromptUserSpec 인터페이스 (p70)

```java
interface PromptUserSpec {
    PromptUserSpec text(String text);
    PromptUserSpec text(Resource text, Charset charset);
    PromptUserSpec text(Resource text);
    PromptUserSpec params(Map<String, Object> p);
    PromptUserSpec param(String k, Object v);
    PromptUserSpec media(Media... media);                       // ← 멀티모달
    PromptUserSpec media(MimeType mimeType, URL url);
    PromptUserSpec media(MimeType mimeType, Resource resource);
    PromptUserSpec metadata(Map<String, Object> metadata);
    PromptUserSpec metadata(String k, Object v);
}
```

## 4-10. 🧪 실습 — 동적 프롬프트 적용 (p71~p73)

```java
@RestController
public class ChatController {

    private static final String PROMPT_TEMPLATE = """
           너는 SKALA Spring AI 교육 과정의 친절하고 열정적인 보조교사 {aiName}입니다.
                  - 수강생의 질문에 따뜻하고 격려하는 어조로 답변해 주세요.
                  - {terms}는 초보자도 이해하기 쉽게 비유를 들어서 설명해 주세요.
                  - 답변 끝에는 항상 실습을 응원하는 따뜻한 한 마디를 덧붙여 주세요.
           """;

    private final PromptTemplate systemPrompt = new PromptTemplate(PROMPT_TEMPLATE);
    // ...
}
```

```java
// chat() 메서드에 적용
String systemMessage = systemPrompt.render(Map.of(
        "aiName", "스프링 동기",
        "terms",  "스프링 용어"
));

return this.chatClient.prompt()
        .options(chatOptions)
        .system(systemMessage)
        .user(userInput)
        .call()
        .content();
```

```java
// chatStream() 메서드에 내장 바인딩 방식 적용
return this.chatClient.prompt()
        .system(s -> s.text(PROMPT_TEMPLATE)
                      .param("aiName", "스프링 동기")
                      .param("terms",  "스프링 용어"))
        .user(userInput)
        .stream()
        .content();
```

---

# 5. Structured Output

> 📍 **p74~p106** | LLM의 자유 텍스트를 **Java 객체 / Map / List**로 안전하게 받는 방법

## 5-1. 왜 구조화된 출력이 필요한가 (p75~p77)

| | 설명 |
|---|---|
| **문제의 본질** | LLM은 기본적으로 **자유 형식의 텍스트(Unstructured Text)** 를 생성하도록 설계됨. 그런데 기업 애플리케이션은 **정해진 스키마 규격**(JSON, XML, Java 객체)을 필요로 함. |

**응답이 자유형식 텍스트일 때의 3가지 문제점 (p76)**

| 문제 | 내용 |
|---|---|
| **타입 안전성(Type Safety) 부족** | AI 응답을 DB에 저장하거나 다른 서비스로 전달하려면 파싱이 필수. 단순 문자열이면 매번 파싱 로직을 만들어야 함 |
| **환각(Hallucination) 및 스키마 위반** | "JSON 형식으로 줘"라고 써도 모델이 `"네, 요청하신 JSON입니다: ..."` 같은 설명 문구를 덧붙이거나, **필드명을 마음대로 바꿔** 응답이 깨짐 |
| **시스템 연동의 한계** | API 응답 규격이 보장되어야 다른 Microservice나 UI 컴포넌트가 안정적으로 처리 가능 |

> ⭐ **핵심 명제 (p77)**
> **"LLM의 출력이 다음 단계의 입력이 되는 순간, 구조화는 선택이 아니라 필수"**

**구조화가 필요한 4가지 이유 (p77)**

| # | 이유 | 설명 |
|---|---|---|
| ① | **기계 친화성(Machine readable)** | `{"action":"deploy","target":"prod","risk_level":"high"}` → 바로 코드에 적용 가능<br>`if (result.action().equals("deploy")) { ... }` |
| ② | **계약(Contract)이 가능** | 필드명·타입이 보장되어야 API 명세가 성립 |
| ③ | **검증(Validation) 가능** | 스키마 위반을 코드에서 잡아낼 수 있음 |
| ④ | **Agent/Tool 기반 동작** | Structured Output을 기반으로 **Tool 호출 판단 / RAG 호출 / Agent 호출 / MCP Server 호출**을 결정 |

## 5-2. StructuredOutputConverter 인터페이스 (p78~p79)

```java
public interface StructuredOutputConverter<T>
        extends Converter<String, T>, FormatProvider {

    // LLM에게 요구할 구조화된 출력의 데이터 구조를 JSON Schema로 제공
    default String getJsonSchema() {
        return NO_JSON_SCHEMA;
    }
}
```

**두 개의 얼굴 — 호출 전 / 호출 후 (p79)** ⭐ 시험 단골

| 단계 | 인터페이스·메서드 | 역할 |
|---|---|---|
| **LLM 호출 前** | `FormatProvider.getFormat()` | LLM이 응답을 **어떤 형식으로 만들어야 하는지 알려주는 지시문(Format Prompt)** 생성 |
| **LLM 호출 後** | `Converter.convert(String text)` | LLM 응답 문자열(JSON/CSV 등)을 **Java 객체로 역직렬화** |

```plain text
FormatProvider.getFormat() 이 만들어내는 지시문 예시

  응답은 반드시 다음 JSON 형식을 따라야 합니다:
  {
    "name": string,
    "age": number
  }

작동 방식: 이 Format Prompt 정보는 System Message 뒤에 "자동으로 추가"되어 LLM으로 전달된다.
```

> ⚠️ **중요 (p79)**
> 이 과정은 **최선 노력(Best Effort) 기반**이다. **100% 결과 보장이 어렵다.**
> 모델이 여전히 규격을 어길 수 있으므로 예외 처리를 반드시 준비할 것.

```plain text
[ p80 — Structured Output 변환 흐름 ]

           Before                    │                  After
 ┌──────────────────────────────────────────────────────────────────┐
 │            Structured Output Converter                           │
 │  ┌──────────────────────┐        ┌──────────────────────────┐   │
 │  │ Provide format       │        │ Convert text to          │   │
 │  │ instructions         │        │ structured output        │───┼──► Structured
 │  └──────────┬───────────┘        └───────────▲──────────────┘   │      Output
 └─────────────┼─────────────────────────────── │ ─────────────────┘
               ▼                                │
 Raw Input ──►(+)──► ┌──────────────────┐       │      ┌──────────────┐
                     │ Input + format   │       └──────│ Raw Output   │
                     │ instructions     │              │ (text)       │
                     └────────┬─────────┘              └──────▲───────┘
                              └──────► Call Generic LLM ──────┘

 · Raw Input에 포맷 지시문(format Instruction)을 추가해서 LLM으로 전달
 · LLM 응답을 입력 파라미터로 수신한 Converter가 구조화된 객체로 변환
```

**MapOutputConverter의 실제 지시문 (p81)**

```plain text
Your response should be in JSON format.
The data structure for the JSON should match this Java class: java.util.HashMap
Do not include any explanations, only provide a RFC8259 compliant JSON response
following this format without deviation.

※ RFC8259 compliant JSON : 표준 JSON 문법을 100% 정확히 따르는 JSON
```

## 5-3. Converter 클래스 계층 (p82)

```plain text
      ┌──────────────────┐          ┌───────────┐
      │  FormatProvider  │          │ Converter │        (인터페이스)
      └────────▲─────────┘          └─────▲─────┘
               └──────────┬───────────────┘
                          │
 ┌─────────────────┐  ┌───┴────────────────────┐  ┌───────────────────┐
 │ MessageConverter│  │StructuredOutputConverter│ │ ConversionService │
 └────────▲────────┘  └───────────▲─────────────┘ └─────────▲─────────┘
          │ 1                     │                          │ 1
 ┌────────┴──────────────────┐    │      ┌──────────────────┴──────────────────┐
 │AbstractMessageOutputConverter    │      │ AbstractConversionServiceOutputConverter│
 └────────▲──────────────────┘    │      └──────────────────▲──────────────────┘
          │                       │                          │
 ╔════════╪═══════════════════════╪══════════════════════════╪═════════════════╗
 ║ ┌──────┴──────────┐  ┌─────────┴────────┐  ┌──────────────┴──────────┐      ║
 ║ │MapOutputConverter│  │BeanOutputConverter│ │  ListOutputConverter    │      ║
 ║ └─────────────────┘  └────────┬─────────┘  └─────────────────────────┘      ║
 ╚═══════════════════════════════╪═════════════════════════════════════════════╝
                                 │ 1
                          ┌──────▼──────┐
                          │ ObjectMapper│   ← Jackson으로 역직렬화
                          └─────────────┘
```

## 5-4. Converter 3종 비교 (p84) ⭐

| Converter | 변환 대상 | 주요 용도 | 예시 결과 |
|---|---|---|---|
| **`BeanOutputConverter<T>`** | `String → Java Object` | LLM 응답을 특정 **Java 클래스/record**로 변환 | `Person`, `Movie`, `Order` |
| **`MapOutputConverter`** | `String → Map<String, Object>` | 필드 구조는 있지만 **고정 Java 타입이 필요 없을 때** | `{name: "Kim", age: 30}` |
| **`ListOutputConverter`** | `String → List<String>` | LLM 응답을 **문자열 목록**으로 변환 | `["Java", "Spring", "AI"]` |

## 5-5. BeanOutputConverter (p85~p92)

**① 목표 데이터 구조 정의**

```java
// 생성될 JSON 스키마의 필드 순서를 명시적으로 지정하고 싶을 때 @JsonPropertyOrder 사용
@JsonPropertyOrder({"actor", "movies"})   // actor가 movies보다 먼저 오도록 보장
record ActorsFilms(String actor, List<String> movies) {}
```

**② ChatClient API — `.entity(Class<?>)`**

```java
public ActorsFilms getSingleActorFilms(String question) {
    return chatClient.prompt()
            .user(question)
            .call()
            .entity(ActorsFilms.class);   // ← 이 한 줄이 Converter를 자동 구성한다
}
```

**③ 내부에서 실제로 일어나는 일 (p88~p89)**

```plain text
[ 요청 ]  chatClient.prompt()
             .user(u -> u.text("{actor}에 대한 5개 영화 필모그래피를 생성하세요.")
                         .param("actor", actor))
             .call()
             .entity(ActorsFilms.class);
                      │
                      ▼  HTTP POST application/json
   role: user     → "톰 행크스에 대한 5개 영화 필모그래피를 생성하세요"
   role: system   → (getFormat()이 자동 생성한 JSON Schema 지시문)
                      │
                      ▼
[ 응답 ]  HTTP Response application/json
   { "actor": "Tom Hanks",
     "movies": ["Forrest Gump", "Cast Away", ...] }
                      │
                      ▼  convert()
   Jackson ObjectMapper로 역직렬화(Deserialization) → ActorsFilms 인스턴스
```

**LLM에 실제로 들어가는 System Message (p90)**

```plain text
Your response should be in JSON format.
Do not include any explanations, only provide a RFC8259 compliant JSON response.
Here is the JSON Schema instance your output must adhere to:
{
  "type": "object",
  "properties": {
     "actor": {"type": "string"},
     "movies": {
       "type": "array",
       "items": {"type": "string"}
     }
  },
  "required": ["actor", "movies"]
}
```

**🧪 실습 (p91) — `OutputConverterController.java`**

```java
/**
 * BeanOutputConverter 단일 Bean 메소드
 * GET /ai/bean
 * @return ActorsFilms
 */
@GetMapping("/bean")
public ActorsFilms getSingleActorFilms(@RequestParam String userInput) {
    return chatClient.prompt()
            .user(userInput)
            .call()
            .entity(ActorsFilms.class);
}
```

- [ ] System Message **없이** ChatGPT에 "톰 행크스에 대한 5개 영화 필모그래피를 알려주세요" 질문 → 자유 텍스트로 나옴
- [ ] System Message(위 JSON Schema) **포함**해서 질문 → 순수 JSON으로 나옴
- [ ] Thymeleaf Frontend에서 결과 확인 (`01.training code/03.structured output`)

## 5-6. `List<T>` 변환과 ParameterizedTypeReference (p93~p94) ⭐⭐

```java
@JsonPropertyOrder({"actor", "movies"})
record ActorsFilms(String actor, List<String> movies) {}

// List<ActorsFilms>처럼 제네릭을 포함하는 복잡한 타입은 ParameterizedTypeReference를 써야 한다
List<ActorsFilms> actorsFilms = chatClient.prompt()
        .user(question)
        .call()
        .entity(new ParameterizedTypeReference<List<ActorsFilms>>() {});  // Anonymous Class
```

**왜 필요한가? — 타입 소거(Type Erasure) (p94)**

| | 설명 |
|---|---|
| **비유로 말하면** | 택배 상자에 붙은 "내용물: 사과" 스티커를 배송 중에 떼어버리는 것. 상자는 남지만 뭐가 들었는지 모른다. |
| **정확히 말하면** | Java는 컴파일 이후 **타입 소거(Type Erasure)** 때문에 `List<ActorsFilms>` 같은 구체적 제네릭 타입 정보를 런타임에 알 수 없다. |

```plain text
컴파일 前                       컴파일 後
──────────────────────         ──────────────────
List<ActorsFilms>       ──►    List        ← ActorsFilms 사라짐
List<String>            ──►    List        ← String 사라짐

런타임에 타입 정보가 없으면:
 · Jackson/ObjectMapper는 List<?> 로만 인식
 · List 내부 객체 타입 인식 불가 → 역직렬화 실패

→ ParameterizedTypeReference의 익명 클래스 트릭으로 타입 정보를 런타임까지 보존
```

**LLM에 들어가는 System Message (p101)** — 배열 스키마 + markdown 제거 지시가 추가된다

```plain text
Your response should be in JSON format.
Do not include any explanations, only provide a RFC8259 compliant JSON response
following this format without deviation.
Do not include markdown code blocks in your response.
Remove the (백틱3개)json markdown from the output.
※ 원문은 (백틱3개) 자리에 실제 백틱 3개가 들어갑니다.
Here is the JSON Schema instance your output must adhere to:
{
  "type": "array",
  ...
}
```

**🧪 실습 (p102)**

```java
/**
 * ParameterizedTypeReference<List<ActorsFilms>> 타입을 entity에 적용
 * GET /ai/list-bean
 * @return List<ActorsFilms>
 */
@GetMapping("/list-bean")
public List<ActorsFilms> getMultipleActorsFilms(@RequestParam String userInput) {
    return chatClient.prompt()
            .user(userInput)
            .call()
            .entity(new ParameterizedTypeReference<List<ActorsFilms>>() {});
}
```

- [ ] 질문: "톰 행크스와 빌 머레이에 대한 5개 영화 필모그래피를 알려주세요"

## 5-7. MapOutputConverter (p95~p97, p103~p104)

```java
Map<String, Object> result = chatClient.prompt()
        .user(question)
        .call()
        .entity(new ParameterizedTypeReference<Map<String, Object>>() {});
```

> 💡 미리 정해진 Java 클래스 없이, **유연한 Key-Value 구조**로 응답받고 싶을 때 사용.

**getFormat()이 생성하는 지시문 (p96, p103)**

```plain text
Your response should be in JSON format.
The data structure for the JSON should match this Java class: java.util.HashMap
Do not include any explanations, only provide a RFC8259 compliant JSON response
following this format without deviation.
Remove the (백틱3개)json markdown surrounding the output including the trailing "(백틱3개)".
※ 원문은 (백틱3개) 자리에 실제 백틱 3개가 들어갑니다.
```

**LLM 응답 예시 → `java.util.Map` (p97)**

```json
{ "name": "John", "age": 30, "city": "Seoul" }
```

**🧪 실습 (p104)**

```java
/**
 * MapOutputConverter
 * GET /ai/map
 * @return Map<String, Object>
 */
@GetMapping("/map")
public Map<String, Object> getMapResult(@RequestParam String userInput) {
    return chatClient.prompt()
            .user(userInput)
            .call()
            .entity(new ParameterizedTypeReference<Map<String, Object>>() {});
}
```

- [ ] 질문: "과일 이름과 맛 10종류를 리스트로 제공해줘"

## 5-8. ListOutputConverter (p98~p100, p105~p106)

**getFormat()이 생성하는 지시문 (p99)** — JSON이 아니라 **CSV(쉼표 구분)** 이다

```plain text
Respond with only a list of comma separated values, without any leading or trailing text.
Example format: foo, bar, baz
```

**LLM 응답 예시 (p100)**

```plain text
foo, bar, baz
서울, 부산, 대구
1, 2, 3, 4, 5
```

**🧪 실습 (p106)**

```java
/**
 * ListOutputConverter
 * GET /ai/list
 * @return List<String>
 */
@GetMapping("/list")
public List<String> getListResult(@RequestParam String userInput) {
    return chatClient.prompt()
            .user(userInput)
            .call()
            .entity(new ParameterizedTypeReference<List<String>>() {});
}
```

- [ ] 질문: "아이스크림 맛을 10가지 제시해줘"

---

# 6. Advisor — 요청 가로채기와 기능 향상

> 📍 **p107~p128** | LLM 호출 **전·후**에 개입하여 Memory, RAG, Logging 등 공통 기능을 적용하는 확장 메커니즘

## 6-1. Advisor란 (p108)

| | 설명 |
|---|---|
| **비유로 말하면** | 결재 라인. 기안서(요청)가 LLM에 도착하기 전 여러 부서를 거치며 도장이 찍히고, 답이 돌아올 때 역순으로 다시 거친다. |
| **정확히 말하면** | `ChatClient`의 **요청과 응답 처리 과정에 개입**하여 Prompt를 가공하거나 부가 기능을 적용하는 **Interceptor 형태의 컴포넌트**. |

## 6-2. Advisor의 3가지 역할 (p109)

| 역할 | 설명 |
|---|---|
| **모듈화(Encapsulation)** | RAG, Chat Memory 등 반복적인 AI 패턴을 **재사용 가능한 컴포넌트로 캡슐화** |
| **데이터 변환(Transformation)** | LLM으로 보내는 요청(Prompt)과 LLM에서 오는 응답(Response)을 **동적으로 수정·보강** |
| **이식성(Portability)** | 특정 로직을 Advisor로 분리하여 **여러 AI 모델이나 다양한 유스케이스에 쉽게 적용** |

## 6-3. 배경 지식 — AOP (p110)

**AOP(Aspect Oriented Programming, 관점 지향 프로그래밍)** 는 OOP의 한계를 보완하는 프로그래밍 패러다임.

- OOP는 주로 **기능 단위**로 클래스를 구현
- AOP는 **공통 관심사(Aspect)** 를 모듈화하여 코드 중복을 줄이고 유지보수를 쉽게 함

```plain text
                핵심 관심 (비즈니스 로직)
              ┌────────┬────────┬────────┐
              │ 사용자  │  주문   │  배송   │
              │ 정보    │  정보   │  정보   │
              │ 관리    │  관리   │  관리   │
    로깅  ────►│  ░░░░  │  ░░░░  │  ░░░░  │   ← 횡단 관심(Cross-cutting)
    보안  ────►│  ░░░░  │  ░░░░  │  ░░░░  │
              └────────┴────────┴────────┘
                        AOP

대표적인 공통 관심사(Aspect): 로깅 / 트랜잭션 / 보안 / 성능 측정(Profiling)
```

> ⭐ **Advisor = AI 요청/응답에 대한 AOP.** Spring의 AOP가 메서드 호출을 가로채듯, Advisor는 **LLM 호출**을 가로챈다.

## 6-4. Advisor Chain 구성 요소 (p111~p112, p115)

| 구성 요소 | 설명 |
|---|---|
| **`ChatClientRequest`** | Prompt를 포함한, Advisor Chain을 통과하는 **요청 객체** |
| **`ChatClientResponse`** | Advisor를 거친 ChatClient 계층의 **응답 객체**. 실제 모델 응답인 `ChatResponse`를 포함 |
| **`CallAdvisor`** | Advisor 구현체를 위한 **인터페이스** (동기) |
| **`CallAdvisorChain`** | 여러 Advisor를 순서대로 실행하고 다음 Advisor로 제어를 넘기는 **체인 관리자** |
| **`StreamAdvisor` / `StreamAdvisorChain`** | 위의 **비동기(스트리밍)** 버전 |

```java
// [p115]
public record ChatClientRequest(Prompt prompt, Map<String, Object> context) {
    ChatClientRequest copy();
    Builder mutate();
    static Builder builder();
}

public interface CallAdvisorChain extends AdvisorChain {
    ChatClientResponse nextCall(ChatClientRequest request);
    List<CallAdvisor> getCallAdvisors();
    CallAdvisorChain copy(CallAdvisor after);
}
```

**Advisor 구현 골격 (p112)**

```java
@Component
public class MyAdvisor implements CallAdvisor {

    @Override
    public String getName() {
        return this.getClass().getSimpleName();
    }

    @Override
    public ChatClientResponse adviseCall(ChatClientRequest request, CallAdvisorChain chain) {
        // 1) 전처리 — request를 가공
        // 2) chain.nextCall(request) 로 다음 Advisor에게 넘김
        // 3) 후처리 — 돌아온 response를 가공
        return chain.nextCall(request);
    }

    @Override
    public int getOrder() {
        return 0;   // 낮을수록 먼저 실행
    }
}
```

## 6-5. Advisor 호출 흐름 (p113~p114) ⭐ 시험 단골

```plain text
[ p114 — Advisor Chain Flow ]

              1.call        2.nextCall       3.nextCall       4.Request
Client/    ──────────► [전처리]      ──────► [전처리]   ──────► [전처리]   ──────► LLM Model
Service                Advisor A            Advisor B         Advisor C        (ChatModel Call)
   ▲                (chain.nextCall)    (chain.nextCall)  (chain.nextCall)         │
   │                                                                               │ 5.Response
   │  8.Final Result    7.return           6.return                                ▼
   └──────────────  [후처리]      ◄────── [후처리]     ◄────── [후처리]  ◄──────────┘
                     Advisor A            Advisor B          Advisor C
                  (return response)   (return response)  (return response)
```

> ⭐ **Stack처럼 동작한다.** 전처리는 A→B→C 순서, 후처리는 C→B→A **역순**.

**Advisor 등록 예시 (p113)**

```java
@Slf4j
public class AdvisorA implements CallAdvisor {
    @Override
    public String getName() {
        return this.getClass().getSimpleName();
    }
    // ...
}

@Service
@Slf4j
public class BasicService {
    private ChatClient chatClient;

    // default Advisors를 ChatClient Build 시 구성
    public BasicService(ChatClient.Builder builder) {
        this.chatClient = builder
                .defaultAdvisors(new AdvisorA(), new AdvisorB(), new AdvisorC())
                .build();
    }
}
```

## 6-6. 우선순위 결정 — getOrder() (p116)

| 상수 | 값 |
|---|---|
| `Integer.MIN_VALUE` | −2,147,483,648 (−2³¹) |
| `Integer.MAX_VALUE` | 2,147,483,647 (2³¹−1) |

- `getOrder()`는 Advisor의 실행 순서를 결정하며 **값이 낮을수록 먼저 실행**
- Advisor Chain은 **Stack처럼 동작**
  - **요청 처리 시**: order 값이 **가장 낮은** Advisor가 **가장 먼저** 요청 처리
  - **응답 처리 시**: order 값이 **가장 낮은** Advisor가 **가장 마지막에** 응답 처리
- `Ordered.HIGHEST_PRECEDENCE` = `Integer.MIN_VALUE` → 가장 먼저 실행 보장
- `Ordered.LOWEST_PRECEDENCE` = `Integer.MAX_VALUE` → 가장 나중에 실행 보장

> ⚠️ **동일 order인 경우에는 등록 순서대로** 진행된다.

## 6-7. Context 기반 Advisor 간 데이터 공유 (p117~p119)

| | 설명 |
|---|---|
| **정의** | Advisor Chain이 요청·응답을 처리하는 동안 **Advisor 간에 부가 정보와 상태를 전달**하기 위한 Key-Value 데이터 공간 |
| **Prompt와의 차이** | Prompt는 **LLM에게 직접 전달**되는 것. Context는 **Advisor들끼리만** 공유하는 정보 (LLM에 안 감) |

**① Advisor에 Context 전달하기**

```java
String response = chatClient.prompt()
    .advisors(advisorSpec -> {
        // 초기 Context 데이터 설정
        advisorSpec.param("customData", "BasicService에서 설정한 초기값");
    })
    .user(question)
    .call()
    .content();
```

**② Advisor 안에서 Context 사용 + 새 데이터 추가 (p119)**

> ⚠️ **Context Map은 immutable(불변)** 이다. 변경하려면 **복사본을 만든 후** 새 Context Map을 전달해야 한다.

```java
@Override
public ChatClientResponse adviseCall(ChatClientRequest request, CallAdvisorChain chain) {
    // Context에 데이터 추가
    String additionalInfo = "AdvisorB에서 추가한 정보";
    System.out.println(" - AdvisorB: Context에 데이터 추가 = " + additionalInfo);

    // 기존 context를 복사하고 새 데이터 추가
    Map<String, Object> newContext = new HashMap<>(request.context());
    newContext.put("advisorB_timestamp", System.currentTimeMillis());
    newContext.put("advisorB_info", additionalInfo);

    // 새로운 context로 request 생성
    ChatClientRequest mutatedRequest = request.mutate().context(newContext).build();
    return chain.nextCall(mutatedRequest);
}
```

**실제 Context 활용 흐름 (p118)**

```plain text
ChatClientRequest → Memory Advisor → RAG Advisor → Logging Advisor → ChatModel

 Prompt: "우리 회사 휴가 규정 알려줘"
 Context: { conversationId: "user-100" }
                     │
                     ├─ Memory Advisor: Context에서 conversationId 확인
                     │                  → 해당 사용자의 이전 대화 조회
                     │
                     ├─ RAG Advisor:    문서 검색
                     │                  → 검색 관련 정보를 Context에 저장 가능
                     │
                     └─ Logging Advisor: Context 전체를 로그로 남김
```

## 6-8. 🧪 실습 — 나만의 Advisor 만들기 (p120~p121)

**① `advisor` 패키지 생성 → `AdvisorA.java`, `AdvisorB.java`, `AdvisorC.java` 작성**
`adviseCall` 내부 프린트의 이름만 A/B/C로 다르게 구성한다.

**② `ChatController.java`의 `chat()` 메서드에 등록**

```java
return this.chatClient.prompt()
        .options(chatOptions)
        .system(systemMessage)
        .user(userInput)
        .advisors(new AdvisorA(), new AdvisorB(), new AdvisorC())
        .call()
        .content();
```

- [ ] 실행 후 Spring Boot 로그에서 **A→B→C 전처리 / C→B→A 후처리** 순서로 찍히는지 확인

## 6-9. 내장 Advisor (p122)

| Advisor 이름 | 주요 역할 | 동작 시점 | 사용 목적 |
|---|---|---|---|
| **`SimpleLoggerAdvisor`** | 요청/응답 메시지를 로그로 남김 | 전처리 + 후처리 | 프롬프트/응답 내용 추적, 디버깅 |
| **`SafeGuardAdvisor`** | OpenAI/Anthropic 등 모델의 Safety 정책 기반으로 사용자 입력·LLM 응답 검증 | 전처리(요청 검증)<br>후처리(응답 필터링) | 위험 콘텐츠 방지, 정책 위반 차단 |
| **`MessageChatMemoryAdvisor`** | 대화 히스토리를 자동 관리하여 Prompt에 주입 | 주로 전처리 | Chat Memory 구현, 메시지 저장/로드 |
| **`QuestionAnswerAdvisor`** | VectorStore 검색 결과를 Prompt에 주입 | 전처리 | 기본 RAG |
| **`VectorStoreChatMemoryAdvisor`** | 대화 이력을 Vector Store에 저장/검색 | 전처리 | 장기 기억(Semantic Memory) |

**SafeGuardAdvisor 사용법 (p123)**

```java
public safeGuard(ChatClient.Builder chatClientBuilder) {
    SafeGuardAdvisor safeGuardAdvisor = new SafeGuardAdvisor(
        List.of("욕설", "계좌번호", "폭력", "폭탄", "외설"),          // 차단 키워드
        "해당 질문은 민감한 콘텐츠 요청이므로 응답할 수 없습니다.",       // 차단 시 응답 메시지
        Ordered.HIGHEST_PRECEDENCE                              // 가장 먼저 실행
    );

    this.chatClient = chatClientBuilder
        .defaultAdvisors(safeGuardAdvisor)
        .build();
}

public String advisorSafeGuard(String question) {
    return chatClient.prompt()
        .user(question)
        .call()
        .content();
}
```

## 6-10. 🧪 실습 — 내장 Advisor 적용 (p124~p126)

**① SimpleLoggerAdvisor**

```java
return this.chatClient.prompt()
        .options(chatOptions)
        .system(systemMessage)
        .user(userInput)
        .advisors(new SimpleLoggerAdvisor(Ordered.LOWEST_PRECEDENCE))
        .advisors(new AdvisorA(), new AdvisorB(), new AdvisorC())
        .call()
        .content();
```

```yaml
# application.yaml — LLM과의 통신 로그를 보려면 필수
logging:
  level:
    '[org.springframework.ai]': DEBUG
```

**② SafeGuardAdvisor (p126)**

```java
private final SafeGuardAdvisor safeGuardAdvisor = new SafeGuardAdvisor(
        List.of("욕설", "계좌번호", "폭력", "폭탄", "외설", "소개"),
        "해당 질문은 민감한 콘텐츠 요청이므로 응답할 수 없습니다.",
        Ordered.HIGHEST_PRECEDENCE
);
```

- [ ] "자기를 소개시켜줘" 질문 → **"소개"** 가 차단어에 들어있으므로 거절 응답이 나오는지 확인

## 6-11. 🧪 실습 — Code Review Advisor 만들기 (p127~p128)

기존 사용자 입력:

```plain text
이 코드에서 문제점을 찾아줘.
public void save(User user) {
    repository.save(user);
}
```

`JavaCodeReviewAdvisor`가 자동으로 아래 Context를 앞에 붙이도록 만든다:

```plain text
당신은 Java/Spring 코드 리뷰 전문가입니다.
코드의 문제점, 이유, 개선 방법 순서로 답변하세요.
Java 21과 Spring Boot 3.x 기준으로 답변하세요.
──────────────────────────────────
이 코드에서 문제점을 찾아줘...
```

- [ ] `ChatController.java`의 `/ai`에 advisor 추가
- [ ] `http://localhost:8080` 에서 동작 확인

---

# 7. Embedding & VectorStore

> 📍 **p129~p157** | 임베딩과 Vector 저장소 — 의미 기반 검색의 원리와 구현

## 7-1. Embedding이란 (p130~p132)

| | 설명 |
|---|---|
| **비유로 말하면** | 모든 단어·문장에 **GPS 좌표를 찍는 것**. 의미가 비슷하면 지도상 가까운 위치에 찍힌다. |
| **정확히 말하면** | 텍스트·이미지·음성 등의 데이터가 가진 **의미적 특징을 수치 Vector로 표현**하여, 의미가 유사한 데이터가 벡터 공간에서 **유사한 방향/위치**에 표현되도록 하는 기술. |

**Embedding Model이란 (p131)**

- 대량의 데이터를 학습하여 **의미적 관계가 반영된 벡터 공간**을 만들고, 새로운 텍스트를 그 공간의 **한 점(벡터)** 으로 변환하는 모델
- 학습 과정에서 의미가 비슷한 표현들이 가까이 위치하도록 **벡터 공간(latent space)** 을 형성
- ⚠️ 임베딩은 **학습 데이터 분포에 강하게 의존**한다. **모델이 학습하지 못한 개념은 정확히 배치하지 못한다.**

| 단계 | 내용 |
|---|---|
| **학습 단계** | 대량 데이터 학습을 통해, 의미적으로 비슷한 것들이 벡터 공간에서 자연스럽게 가까워지도록 조정 |
| **사용 단계** | 새로운 입력이 들어오면, 모델은 그 입력을 **이미 형성된 의미 공간 위의 한 점(벡터)** 으로 매핑 |

**차원의 의미는 사람이 정의하지 않는다 (p132)** ⭐

- 각 차원에 "동물", "행동", "감정" 같은 의미를 **사람이 직접 부여하지 않는다**
- 학습 과정에서 모델이 의미적 관계를 표현할 수 있는 **잠재적 특징(Latent Feature)** 을 스스로 학습
- 하나의 의미가 특정 한 차원이 아니라 **여러 차원에 분산되어** 표현될 수 있음

```plain text
"강아지가 달린다" ──┐                       "Spring Boot 서버 개발"
                  ├─ 의미적으로 유사                  ↓
"개가 뛰고 있다"  ───┘                          Vector C
        │
        ▼
  Embedding Model                      → A와 B는 유사하게
    ↓          ↓                        → A/B와 C는 구별되도록 학습
 Vector A   Vector B
   └── 유사 ──┘

※ 같은 Embedding Model에 서로 다른 데이터를 입력해야 같은 공간에서 비교가 성립한다
```

> ⚠️ **매우 중요**: 검색할 때와 저장할 때 **반드시 같은 Embedding Model**을 써야 한다. 모델이 다르면 좌표계 자체가 달라서 유사도가 무의미해진다.

## 7-2. Embedding 적용 분야 4가지 (p134)

| 분야 | 설명 |
|---|---|
| **시맨틱 검색(Semantic Search)** | 키워드가 일치하지 않아도 "무더운 날 마시기 좋은 것"을 검색했을 때 "시원한 아이스 아메리카노" 관련 문서를 찾아내는 기술 |
| **RAG** | LLM이 기업 내부 문서나 최신 데이터를 기반으로 정확하게 답변하도록 문서를 벡터화하여 검색에 활용 |
| **추천 시스템(Recommendation)** | 유저의 행동 패턴과 콘텐츠의 특징을 임베딩하여 유사한 취향의 상품/영상을 추천 |
| **멀티모달(Multi-modal)** | 텍스트와 이미지를 **동일한 벡터 공간**에 임베딩하여, "강아지가 뛰노는 그림"이라는 **텍스트로 실제 강아지 사진을 검색** |

## 7-3. Embedding Model 비교 (p133, p144)

| 순위 | 제공사 | 모델명 | SaaS | 설치형 | 주요 특성 |
|---|---|---|---|---|---|
| 1 | OpenAI | `text-embedding-3-small` | O | X | 비용과 성능의 균형이 좋음. 대부분의 RAG 프레임워크와 벡터 DB에서 쉽게 연동 |
| 2 | OpenAI | `text-embedding-3-large` | O | X | 고성능 임베딩 모델. 다국어 검색과 복잡한 의미 검색에 적합 |
| 3 | BAAI | `BAAI/bge-m3` | O | O | 다국어 성능 우수. Dense·Sparse·Multi-vector 검색 지원 |

**모델별 스펙 (p144)** ⭐ RAG 설계 시 필수 표

| 모델명 | 벡터 차원 | 최대 컨텍스트 (Max Tokens) | 권장 Chunk size | 다국어 지원 |
|---|---|---|---|---|
| `qwen3-embedding:0.6b` | 1,024 | 32,768 (32K) | 500~1,500 토큰 | 100+ 개 언어, MTEB 다국어 64.3점 |
| `qwen3-embedding:4b` | 2,560 | 32,768 (32K) | 1,000~2,000 | 100+ 개 언어, MTEB 다국어 69.4점 |
| `bge-m3` | 1,024 | 8,192 (8K) | 500~1,000 토큰 | 100+ 개 언어 |
| `text-embedding-3-small` | **1,536** | 8,192 (8K) | 800~1,000 | 다국어 우수, MTEB 다국어 62.3점 |
| `text-embedding-3-large` | 3,072 | 8,192 (8K) | 1,000~1,500 | 다국어 매우 우수, MTEB 다국어 58.9~64.6점 |

## 7-4. 벡터 데이터 저장 파이프라인 (p135)

```plain text
  원본 데이터        Embedding Model      Vector Embedding          벡터 DB
──────────────    ────────────────    ──────────────────    ─────────────────
텍스트/이미지/음성 →  원본 데이터를 입력받아 → [0.12, 0.45, 0.88,   →  벡터를 저장하고
                   float 형태의            …, 0.02]              유사도 기반 검색
                   벡터로 변환
```

## 7-5. Vector DB (p136~p138)

| | 설명 |
|---|---|
| **정의** | 고차원 임베딩 벡터(Embedding Vector)를 **저장, 인덱싱 및 검색**하기 위해 최적화된 데이터베이스 |
| **핵심 기능** | **유사도 검색(Similarity Search)** — 기존 DB는 **정확한 일치**를 찾지만, Vector DB는 Query Vector와 **유사한 벡터들**을 반환 |

```plain text
[ p136 — Vector DB 동작 ]

 ┌───────────┐
 │  Content  │──┐
 └───────────┘  │    ┌──────────┐    ┌───────────────────────┐   ┌─────────────────┐
                ├───►│Embedding │───►│  Vector Embedding     │──►│ Vector Database │
 ┌───────────┐  │    │  Model   │    │[0.34,-1.2,0.34,1.3,…] │   │   ● ●    ●   ●  │
 │Application│──┘    └──────────┘    └───────────────────────┘   │  ╱ ●  ●  ╲   ●  │
 └─────▲─────┘  Query                                            │ │ ● ● ●  │      │
       │                                                         │  ╲  ●   ╱   ●   │
       └──────────────────── Query Result ───────────────────────┤   ●  ●          │
                                                                 └─────────────────┘
                                                          ↑ 유사한 벡터들이 모여있는 영역
```

**Vector DB 종류 (p138)**

| 제품 | 유형 | 특징 | 장점 | 적합한 경우 | Enterprise 사용 |
|---|---|---|---|---|---|
| **pgVector** | PostgreSQL 확장 | 기존 RDB에 벡터 타입 추가 | SQL 그대로 사용 | 엔터프라이즈급 데이터 안정성과 복구 체계 | 매우 높음 |
| **Qdrant** | 전용 Vector DB | Rust 기반, HNSW 최적화 | 빠른 검색, 필터링 강함 | 대규모 RAG, SaaS | 매우 높음 |
| **Chroma** | 경량 Vector Store | Python 친화적 | 개발 간편 | PoC, 로컬 개발 | 제한적 |
| **Milvus** | 대규모 분산형 | 고성능 ANN, GPU 지원 | 초대규모 처리 | AI 플랫폼 | 높음 |
| **Weaviate** | Graph + Vector | Hybrid 검색 강점 | 메타데이터+벡터 통합 | 지식 그래프 결합 | 높음 |

> ✅ 이 과정에서는 **pgVector**를 사용한다. 기존 PostgreSQL 운영 노하우를 그대로 쓸 수 있는 게 가장 큰 이유.

## 7-6. 🧪 실습 — pgVector 설치 (p139~p141)

```bash
#!/bin/bash
# pgvector-run.sh
docker run -d \
  --name pgvector \
  --network skala \
  -p 5432:5432 \
  -e POSTGRES_USER="postgres" \
  -e POSTGRES_PASSWORD="postgres" \
  -e POSTGRES_DB="postgres" \
  -v $(pwd)/pgdata:/var/lib/postgresql \
  pgvector/pgvector:pg18
```

```bash
chmod +x pgvector-run.sh && ./pgvector-run.sh
```

**체크리스트**
- [ ] Docker Desktop의 Container 실행 상태 확인
- [ ] DBeaver로 접속: `localhost:5432` / user `postgres` / pwd `postgres`

> ⚠️ 위 비밀번호(`postgres/postgres`)는 **로컬 실습 전용**이다. 운영 환경에 그대로 쓰지 말 것.

## 7-7. 의존성 & 설정 (p142~p143)

```xml
<!-- Spring AI Vector Store - PGVector (PostgreSQL 18 + pgvector 확장) -->
<dependency>
    <groupId>org.springframework.ai</groupId>
    <artifactId>spring-ai-starter-vector-store-pgvector</artifactId>
</dependency>

<!-- PGVector 사용을 위한 JDBC 및 PostgreSQL 드라이버 -->
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-jdbc</artifactId>
</dependency>
<dependency>
    <groupId>org.postgresql</groupId>
    <artifactId>postgresql</artifactId>
    <scope>runtime</scope>
</dependency>
```

```yaml
spring:
  datasource:
    url: jdbc:postgresql://localhost:5432/postgres
    username: postgres
    password: postgres

  ai:
    model:
      chat: openai
      embedding: openai          # ← embedding 모델도 별도로 지정
    openai:
      api-key: ${OPENAI_API_KEY}
      embedding:
        options:
          model: text-embedding-3-small   # ← 의존성 추가 시 EmbeddingModel Bean 자동 생성
      chat:
        options:
          model: gpt-4o-mini
          temperature: 0.7
    vectorstore:
      pgvector:
        initialize-schema: true    # 테이블/스키마 자동 생성
```

```bash
export OPENAI_API_KEY=여기에_본인_KEY
```

## 7-8. EmbeddingModel 인터페이스 (p145~p146)

```plain text
[ p145 — Embedding Model 클래스 다이어그램 ]

                    ┌──────────────────────────────────────────┐
                    │            EmbeddingModel                │
                    │ +call(EmbeddingRequest) : EmbeddingResponse│
                    └───┬──────────────┬───────────────────┬───┘
             request    │              │                   │  response
        ┌───────────────▼──┐   <List<String>,        ┌─────▼──────────────────────────┐
        │ EmbeddingRequest │   EmbeddingResponse>    │      EmbeddingResponse         │
        │+getInstructions()│                         │+getResults() : List<Embedding> │
        │  : List<String>  │                         │+getMetadata()                  │
        │+getOptions()     │                         │  : EmbeddingResponseMetadata   │
        │  : EmbeddingOptions│                       └────────────┬───────────────────┘
        └────────┬─────────┘                                     │ <Embedding>
       List<String>│                                             │
                  ▼                    ▼                         ▼
        ┌──────────────────┐  ┌─────────────────┐   ┌──────────────────────────┐
        │ ModelRequest<T>  │◄─┤     Model       │──►│      ModelResponse       │
        │+getInstructions()│  │ +call(TReq):TRes│   │+getResult() : T          │
        │+getOptions()     │  └─────────────────┘   │+getResults() : List<T>   │
        └──────────────────┘                        │+getMetadata()            │
                                                    └──────────────────────────┘
```

> ⭐ `EmbeddingModel`은 `ChatModel`과 **완전히 같은 패턴**(`Model<TReq, TRes>`)을 따른다. Request/Response/Options 3종 세트.

## 7-9. VectorStore 인터페이스 (p147~p148)

```java
public interface VectorStore extends DocumentWriter, VectorStoreRetriever {

    default String getName() { /* ... */ }

    void add(List<Document> documents);                            // 저장
    void delete(String filterExpression);                          // 삭제
    List<Document> similaritySearch(SearchRequest request);        // 유사도 검색
}
```

- 다양한 벡터 저장소를 **일관된 방식**으로 사용하도록 `VectorStore` 인터페이스 제공
- 구현체는 Spring Boot **Auto-configuration으로 Bean 자동 생성**
- `application.yaml`의 `vectorstore.pgvector.initialize-schema: true`가 스키마를 만들어 준다
- 전체 구현체 목록: `https://docs.spring.io/spring-ai/reference/api/vectordbs.html`

## 7-10. Document Class (p149)

| | 설명 |
|---|---|
| **정의** | 비정형/정형 데이터를 수집·가공하여 Vector Store에 저장하고 검색할 때, **본문 텍스트 + 메타데이터 + 임베딩 벡터**를 하나로 묶어 다루는 Spring AI의 표준 데이터 객체(DTO) |

**3가지 역할**
- Vector Store에 저장하기 위한 **기본 단위**
- 문서 검색 결과를 LLM에 전달하기 위한 **Context 정보 컨테이너**
- 문서 단위를 표준화해서 RAG에 **일관된 자료 구조** 제공 (파일, DB row, 웹페이지, Chat Memory, Chunk 문서 등)

```java
public class Document implements Content {
    private final String id;                   // 문서의 고유 식별자 (UUID 등)
    private String content;                    // 문서의 본문 텍스트 (텍스트 청크)
    private Map<String, Object> metadata;      // 문서 출처, 페이지 번호, 키-값 메타데이터
    private List<Media> media;                 // 이미지, 멀티미디어 데이터 (Multimodal 확장용)
    private List<Double> embedding;            // 임베딩 벡터
}
```

## 7-11. Document 저장 / 검색 / 삭제 (p150~p153)

**① 저장 — `add()` (p150)**

```java
private final VectorStore vectorStore;

DocumentEmbeddingService(VectorStore vectorStore) {
    this.vectorStore = vectorStore;
}

public void addDocuments() {
    List<Document> documents = List.of(
        new Document("spring은 web application을 쉽게 만들기 위한 프레임워크입니다.",
                     Map.of("category", "spring", "year", 1987)),
        new Document("spring ai는 AI 모델과의 통합을 단순화하는 프레임워크입니다.",
                     Map.of("category", "spring", "year", 2021)),
        new Document("vector Store는 임베딩 벡터를 저장하고 유사도 검색을 수행합니다.",
                     Map.of("category", "spring", "year", 2021)),
        new Document("kubernetes는 컨테이너 오케스트레이션 플랫폼입니다.",
                     Map.of("category", "infra", "year", 2014))
    );
    vectorStore.add(documents);   // 내부에서 EmbeddingModel 호출 → 벡터화 → 저장
}
```

**② 검색 — `similaritySearch()` (p151)**

```java
public List<Document> search(String question) {
    // 간단히 쓰려면: vectorStore.similaritySearch(question);
    List<Document> documents = vectorStore.similaritySearch(
        SearchRequest.builder()
            .query(question)              // 유사도 검색에 사용될 텍스트
            .similarityThreshold(0.4)     // 1에 가까울수록 높은 유사도 (default: 0.0)
            .topK(3)                      // 유사도가 높은 상위 K개
            .build());
    return documents;
}
```

**③ 유사도 임계값(Threshold) 가이드 (p152)** ⭐ 실무 필수 표

코사인 유사도(Cosine Similarity, 0.0~1.0) 기준, 검색 결과로 채택할 **최소 점수 기준선**.

| Threshold 값 | 검색 범위 및 품질 | 주 용도 및 특성 |
|---|---|---|
| **0.0** (기본값/비활성 수준) | 전체 검색 | 유사도 점수와 상관없이 요청한 개수(topK)만큼 **무조건** 문서를 채움. 질문과 완전히 무관한 문서(노이즈)도 포함 |
| **0.5~0.6** (느슨한 필터) | 광범위한 연관 검색 | 유의어, 간접적 맥락, 개념적으로 느슨하게 연결된 문서까지 폭넓게 수집. **재현율(Recall)** 이 중요할 때 적합 |
| **0.7~0.75** (실무 권장 기준선) | **균형 잡힌 RAG 검색 (Sweet Spot)** | 실제 RAG 챗봇 및 Q&A 시스템에서 **가장 널리 쓰이는 표준 기본값**. 질문과 직접 관련된 핵심 청크 위주로 필터링 |
| **0.8 이상** (엄격한 필터) | 정밀 검색 | 거의 동일한 의미의 문서만 통과. **정밀도(Precision)** 우선 |

**④ 삭제 — `delete()` (p153)**

```java
// Filter 조건 (year 값이 1987 이상)으로 문서 삭제
public void deleteDocuments() {
    vectorStore.delete("year >= 1987");
}

// 유사도가 80% 이상인 문서를 찾아서 삭제
public String deleteDocumentForSimilarity(String request) {
    log.info("deleteDocumentForSimilarity() request: {}", request);

    List<Document> similarDocuments = vectorStore.similaritySearch(
        SearchRequest.builder()
            .query(request)
            .topK(1)
            .similarityThreshold(0.8)   // 80% 이상 유사한 문서만 검색
            .build());

    // 검색된 문서의 id로 삭제
    vectorStore.delete(similarDocuments.stream().map(Document::getId).toList());
    return "deleted";
}
```

## 7-12. 🧪 실습 — Embedding 코드 확장 (p154~p157)

**① 코드 리뷰** — `01.training code/05.embedding`의 `EmbeddingService.java`, `EmbeddingController.java`
- [ ] `http://localhost:8080` → Embedding 사이드메뉴 → 검색: **"대한민국은 민주국가인가?"**
- [ ] DBeaver로 pgvector에 접속해 실제 저장된 벡터 확인

**② 헌법 5개 조문을 Document로 만들어 등록 (p156)**

```plain text
제1조 ①대한민국은 민주공화국이다. ②대한민국의 주권은 국민에게 있고, 모든 권력은 국민으로부터 나온다.
제2조 ①대한민국의 국민이 되는 요건은 법률로 정한다. ②국가는 법률이 정하는 바에 의하여 재외국민을 보호할 의무를 진다.
제3조 대한민국의 영토는 한반도와 그 부속도서로 한다.
제4조 대한민국은 통일을 지향하며, 자유민주적 기본질서에 입각한 평화적 통일정책을 수립하고 이를 추진한다.
제5조 ①대한민국은 국제평화의 유지에 노력하고 침략적 전쟁을 부인한다. ②국군은 국가의 안전보장과 국토방위의
      신성한 의무를 수행함을 사명으로 하며, 그 정치적 중립성은 준수된다.
```

```java
public void addDocuments() {
    // 대한민국 헌법 제1조 ~ 제5조 Document 목록 생성
    List<Document> documents = List.of(
        new Document("제1조 ①대한민국은 민주공화국이다. ②대한민국의 주권은 국민에게 있고, ...",
                     Map.of("law", "헌법", "article", 1)),
        // ... 제2조 ~ 제5조
    );
    vectorStore.add(documents);
}
```

**③ 검색 시 유사도 0.4 이상만 (p157)**

```java
.similarityThreshold(0.4)
```

- [ ] 질문: **"대한민국의 영토는 어디까지인가?"** → 제3조가 검색되는지 확인
- [ ] pgvector 테이블 내용 검토

---

## ★ 전체 흐름 한 장 요약

```plain text
╔══════════════════════════════════════════════════════════════════════════════╗
║                     Spring AI 1일차 — 전체 지도                                ║
╚══════════════════════════════════════════════════════════════════════════════╝

  [ 애플리케이션 코드 ]
          │
          │  chatClient.prompt()
          │      .options(chatOptions)   ← ③ ChatOptions (model/temperature/topK/topP/maxTokens)
          │      .system(systemMessage)  ← ④ Prompt (Context+Instruction)
          │      .user(userInput)        ← ④ Prompt (Input Data + 질문)
          │      .advisors(...)          ← ⑥ Advisor (Logging/SafeGuard/Memory/RAG)
          │      .call()  또는  .stream()
          │      .entity(Xxx.class)      ← ⑤ Structured Output (Bean/Map/List)
          ▼
  ┌──────────────────────────────────────────────────────────────┐
  │  ② ChatClient  (고수준 Fluent API / Façade)                   │
  │       │                                                      │
  │       ▼  Advisor Chain (Stack 구조)                          │
  │   [전처리 A → B → C] ─────► ChatModel ─────► LLM             │
  │   [후처리 C → B → A] ◄─────              ◄─────              │
  └──────────────────────────────────────────────────────────────┘
          │
          ▼
  ┌──────────────────────────────────────────────────────────────┐
  │  ② ChatModel (저수준 추상화)                                   │
  │     · Prompt → Native API 요청(HTTP) 변환                      │
  │     · Native 응답(JSON) → ChatResponse 변환                    │
  │     · Runtime 옵션 > Start-Up 옵션                             │
  └──────────────────────────────────────────────────────────────┘
          │
          ▼
     OpenAI / Claude / Gemini / Ollama

  ────────────────────────────────────────────────────────────────
  ⑦ 별도 축: Embedding & VectorStore  (2일차 RAG의 준비물)

   원본 텍스트 → EmbeddingModel → Vector(1536차원) → pgVector 저장
                                                        │
                          질문 → EmbeddingModel → Vector ┘ 유사도 검색
                                                        (cosine, topK, threshold)
```

**핵심 대응 관계 한 줄 정리**

| 개념 | Spring의 무엇과 같은가 |
|---|---|
| `ChatModel` | `Repository`(Spring Data) — 벤더 추상화 |
| `ChatClient` | `RestClient` / `JdbcTemplate` — 편의 Façade |
| `Advisor` | AOP `Aspect` / Servlet `Filter` — 횡단 관심사 |
| `Document` | `Entity` — 저장 단위 DTO |
| `VectorStore` | `Repository` 구현체 — 저장/검색 |

---

## ★ 시험/면접 대비 핵심 문답

| # | 질문 | 답 |
|---|---|---|
| 1 | `ChatModel`과 `ChatClient`의 차이는? | `ChatModel`은 벤더별 LLM을 추상화한 **저수준 인터페이스**(이식성 + 입출력 변환). `ChatClient`는 그 위에서 Prompt·Advisor·Tool·응답 처리를 조합하는 **고수준 Fluent API(Façade)** |
| 2 | `.call()`과 `.stream()`의 반환 타입은? | `.call()` → `CallResponseSpec` (최종 `String`/객체). `.stream()` → `StreamResponseSpec` (`Flux<String>`). 스트리밍은 `produces = MediaType.TEXT_EVENT_STREAM_VALUE` 필요 |
| 3 | `ChatResponse`와 `Generation`의 관계는? | `ChatResponse`는 **LLM 호출 1회 전체 결과**(메타데이터 + `List<Generation>`). `Generation`은 **단일 응답 후보**. temperature가 높거나 n을 여러 개 요청하면 Generation이 여러 개 나올 수 있다 |
| 4 | Runtime 옵션과 Start-Up 옵션 중 뭐가 우선? | **Runtime(`.options(...)`) 우선.** `application.yaml`의 설정을 덮어쓴다 |
| 5 | Temperature 0.0 / 0.7 / 1.0 / 1.5의 용도는? | 0.0=코드·분류·정보 추출 / 0.7=일반 대화·문서 작성 / 1.0=아이디어 생성 / 1.5=창작 |
| 6 | Top-K와 Top-P의 차이는? | **Top-K는 개수로 자름(고정)**, **Top-P는 누적 확률로 자름(가변)**. Top-P가 상황 적응적이다 |
| 7 | 프롬프트의 4대 구성 요소는? | **Context**(배경/역할) · **Instruction**(지시/추론 규칙) · **Input Data**(대상 데이터) · **Output Indicator**(출력 형식/제약) |
| 8 | `Message`의 4가지 타입은? | `SystemMessage`(규칙·역할) · `UserMessage`(사용자 입력) · `AssistantMessage`(LLM 응답, ToolCall 포함 가능) · `ToolResponseMessage`(Tool 실행 결과) |
| 9 | `.system()`에 `SystemMessage` 객체를 넘기면? | **컴파일 에러.** `.system()`은 `String`/`Resource`/`Consumer`만 받는다. 객체는 `.messages(systemMessage)`로 넣어야 한다 |
| 10 | 동적 프롬프트 3가지 방식과 각각의 용도는? | **ChatClient 내장 바인딩**(가장 많이 씀, `.user(u -> u.text(...).param(...))`) / **PromptTemplate**(외부 `.st` 파일 관리·재사용) / **String.format**(파라미터 1~2개 하드코딩) |
| 11 | `StructuredOutputConverter`의 두 메서드와 역할은? | **`getFormat()`** — LLM 호출 **전**에 포맷 지시문 생성(System Message 뒤에 자동 추가). **`convert()`** — LLM 호출 **후**에 응답 문자열을 Java 객체로 역직렬화 |
| 12 | Converter 3종과 반환 타입은? | `BeanOutputConverter<T>` → Java Object / `MapOutputConverter` → `Map<String,Object>` / `ListOutputConverter` → `List<String>` |
| 13 | `List<ActorsFilms>`를 받으려면 왜 `ParameterizedTypeReference`가 필요한가? | Java의 **타입 소거(Type Erasure)** 때문에 런타임에 `List<T>`의 `T`를 알 수 없다. 익명 클래스 트릭으로 제네릭 타입 정보를 런타임까지 보존해야 Jackson이 역직렬화할 수 있다 |
| 14 | Structured Output이 100% 보장되나? | **아니다. Best Effort 기반**이다. 모델이 스키마를 어길 수 있으므로 예외 처리가 필요하다 |
| 15 | Advisor는 Spring의 어떤 개념과 같은가? | **AOP(Aspect)**. LLM 호출 전·후에 개입하는 Interceptor. 공통 관심사(RAG/Memory/Logging/Security)를 모듈화 |
| 16 | Advisor Chain의 실행 순서는? | **Stack 구조.** `getOrder()` 값이 **낮을수록 요청 처리는 먼저**, **응답 처리는 나중에**. 전처리 A→B→C, 후처리 C→B→A. 동일 order면 등록 순서 |
| 17 | `Ordered.HIGHEST_PRECEDENCE`의 값은? | `Integer.MIN_VALUE` (−2,147,483,648). 가장 먼저 실행 보장 |
| 18 | Advisor Context와 Prompt의 차이는? | **Prompt는 LLM에게 전달**된다. **Context는 Advisor들끼리만** 공유하는 Key-Value 공간이며 LLM에 가지 않는다. Context Map은 **immutable**이라 수정하려면 복사본을 만들어야 한다 |
| 19 | 내장 Advisor 5가지는? | `SimpleLoggerAdvisor`, `SafeGuardAdvisor`, `MessageChatMemoryAdvisor`, `QuestionAnswerAdvisor`, `VectorStoreChatMemoryAdvisor` |
| 20 | Embedding의 각 차원은 무슨 의미인가? | **사람이 정의하지 않는다.** 모델이 학습 과정에서 잠재적 특징(Latent Feature)을 스스로 형성하며, 하나의 의미가 여러 차원에 분산되어 표현된다 |
| 21 | 저장할 때와 검색할 때 다른 Embedding Model을 써도 되나? | **안 된다.** 좌표계가 달라져서 유사도 계산이 무의미해진다 |
| 22 | `text-embedding-3-small`의 벡터 차원과 최대 토큰은? | **1,536차원 / 8,192(8K) 토큰**. 권장 chunk 800~1,000 |
| 23 | `similarityThreshold` 실무 권장값은? | **0.7~0.75** (Sweet Spot). 0.0은 무조건 topK만큼 채우므로 노이즈가 섞인다 |
| 24 | `Document` 클래스의 5개 필드는? | `id`, `content`(본문 텍스트), `metadata`(출처·페이지 등), `media`(멀티모달), `embedding`(벡터) |
| 25 | Vector DB가 기존 RDB와 다른 점은? | RDB는 **정확한 일치**를 찾고, Vector DB는 **벡터 공간의 거리 기반 유사도 검색**을 한다 |

**🧩 Quiz — 코드를 보고 답하기**

<details>
<summary>Q1. 아래 코드는 컴파일될까?</summary>

```java
SystemMessage sm = SystemMessage.builder().text("너는 조교다").build();
return chatClient.prompt().system(sm).user(input).call().content();
```

- [x] **컴파일 안 된다.** `.system()`은 `String` / `Resource` / `Consumer<PromptSystemSpec>`만 받는다.
- 수정: `.messages(sm)` 으로 바꾼다.
</details>

<details>
<summary>Q2. 이 코드가 런타임에 실패하는 이유는?</summary>

```java
List<ActorsFilms> result = chatClient.prompt()
        .user(q).call().entity(List.class);
```

- [x] **타입 소거(Type Erasure)** 때문에 `List` 안의 원소 타입을 알 수 없어 Jackson 역직렬화가 실패한다.
- 수정: `.entity(new ParameterizedTypeReference<List<ActorsFilms>>() {})`
</details>

<details>
<summary>Q3. Advisor A(order=100), B(order=10), C(order=50)의 전처리·후처리 순서는?</summary>

- [x] **전처리: B(10) → C(50) → A(100)**
- [x] **후처리: A(100) → C(50) → B(10)**
- order가 낮을수록 요청은 먼저, 응답은 마지막에 처리한다.
</details>

<details>
<summary>Q4. `similarityThreshold(0.0)`과 `topK(3)`을 함께 쓰면?</summary>

- [x] 유사도와 **무관하게 무조건 3개**를 채운다. 질문과 전혀 관계없는 문서도 포함되어 LLM이 엉뚱한 답을 할 수 있다.
- 실무에서는 `0.7` 이상을 권장.
</details>

---

## ⚠️ 원문 용어 검증 노트

정리하면서 발견한 원문 PDF의 오타·표기 오류와 보완 사항입니다. **정리본에서는 모두 바로잡았습니다.**

### 정정 (원문 오기)

| # | 슬라이드 | 원문 | 정정 | 비고 |
|---|---|---|---|---|
| 1 | p5 | "기존 스프링 비즈니스 애플레키엿ㄴ을" | "애플리케이션을" | 오타 |
| 2 | p30 | `<artifactId>pring-ai-starter-model-google-genai` | `spring-ai-starter-model-google-genai` | **`s` 누락 — 그대로 붙여넣으면 빌드 실패** |
| 3 | p33 | `echo export OPENAI API KEY ...` | `echo 'export OPENAI_API_KEY=...' >> ~/.zshrc` | 언더스코어 및 리다이렉트 누락 |
| 4 | p33, p36 | `mvn clean install –DskipTest` | `mvn clean install -DskipTests` | ① `–`(en-dash) → `-`(hyphen) ② Maven Surefire 속성명은 **`skipTests`**(복수) |
| 5 | p36 | `./build/lib/spring-ai-...jar` | `./build/libs/spring-ai-...jar` | Gradle 기본 출력 디렉터리는 **`libs`** |
| 6 | p46 | "Token 후보 ... 선택디 집중" | "선택이 집중" | 오타 |
| 7 | p51 | "최상위 치짐" | "최상위 지침" | 오타 |
| 8 | p60 | "규칙, 역할, 톤, 제약사항" 앞 "최상위 치짐" | 동일 | 위와 같은 오타 반복 |
| 9 | p67 | 템플릿 변수 `'{aiName}이'` | 예시 렌더링값이 `"스프링"`이라 `'스프링이'`가 됨 | 조사 처리 주의 (문법 오류는 아님) |
| 10 | p85, p93 | `JsonPropertyOder` | `@JsonPropertyOrder` | **`r` 누락 — 컴파일 실패** |
| 11 | p123, p126 | `List.of("욕설", ..., ”외설")` | `"외설"` | **왼쪽 큰따옴표(`”`)가 섞여 있음 — 컴파일 실패** |
| 12 | p126 | `List.of("욕설", "계좌번호", "폭력", "폭탄", "외설”, "소개",` | 닫는 괄호 누락 | **`)` 가 빠져 있음 — 컴파일 실패** |
| 13 | p139 | `--network skaka` | `--network skala` | 과정명이 SKALA이므로 오타로 판단 |
| 14 | p142 (제목) | "pgVector 기반 **VectorStoreChatMemoryAdvisor** 지원을 위한 pom.xml" | 이 슬라이드는 **Embedding용 VectorStore** 의존성 | p244(ChatMemory 편)의 제목이 잘못 복사된 것 |
| 15 | p147 | `initialize schema: true` | `initialize-schema: true` | YAML 키는 하이픈 |
| 16 | p153 | "(year 의 값이 1987이상일경우)**기분**으로" | "**기준**으로" | 오타 |
| 17 | p154, p156 | 실습 경로가 `01.training code/05.embedding` / `07.embedding`으로 혼재 | 05가 embedding, 07은 rag | 슬라이드 간 경로 표기 불일치 |
| 18 | p157 | `.simualrityThreshold(0.4)` | `.similarityThreshold(0.4)` | **철자 오류 — 컴파일 실패** |
| 19 | p173 | `.withKeepSeparator(ture)` | `.withKeepSeparator(true)` | (2일차 범위지만 여기 기록) |

### 보완 (원문에 없어 추가한 설명)

| # | 항목 | 보완 내용 |
|---|---|---|
| 1 | `ChatOptions` 반환 타입 | p41의 인터페이스는 `Float getTemperature()`인데 p42 표는 `Double`로 적혀 있다. Spring AI 2.x의 `ChatOptions`는 **`Double`** 을 쓴다. 표(p42)가 맞다 |
| 2 | `.entity()` 3가지 형태 | ① `entity(Class<T>)` ② `entity(ParameterizedTypeReference<T>)` ③ `entity(StructuredOutputConverter<T>)` — 원문은 ①②만 다룸 |
| 3 | `chatResponse()` 메서드명 | p28/p58의 `ChatResponse rsp = ...call();` 은 축약 표기. 실제로는 **`.call().chatResponse()`** |
| 4 | Advisor `getOrder()` 기본 동작 | 원문은 "동일 order면 등록 순서"만 언급. 실제로는 `defaultAdvisors()`로 등록한 것이 `.advisors()`로 런타임 등록한 것보다 **먼저 체인에 들어간다** |
| 5 | pgVector 비밀번호 | 실습용 `postgres/postgres`는 **로컬 전용**. 운영 반영 금지 |
| 6 | `similaritySearch` 오버로드 | `similaritySearch(String)`(간편형)과 `similaritySearch(SearchRequest)`(상세형) 두 가지가 있다 |
| 7 | RFC8259 | 원문 각주에 "표준 JSON 문법을 100% 정확히 따르는 JSON"이라고만 되어 있음. 정확히는 **JSON 데이터 교환 형식의 IETF 표준 문서 번호** |
| 8 | MTEB | p144 표의 "MTEB 다국어 점수"에서 MTEB = **Massive Text Embedding Benchmark** (임베딩 모델 성능 벤치마크). 원문에 풀네임 없음 |

---

> 📌 **다음 문서**: [2일차 — RAG · ChatMemory · Tool Calling](./02_SpringAI_Day2_RAG와_Tool_정리.md)
