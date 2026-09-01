# 🔌 Spring AI 3일차 — MCP · Agent 완전 정리

> 💡 **한 줄 요약**
> 2일차의 **Tool Calling은 "내 애플리케이션 안의 Java 메서드"** 만 부를 수 있었다.
> **MCP(Model Context Protocol)** 는 그 Tool을 **프로세스/서버 밖으로 꺼내 표준 프로토콜(JSON-RPC)로 공유**하는 규격이다.
> 그리고 **Agent** = `System Prompt(역할)` + `Tool(행동)` + `ChatMemory(기억)` + `RAG(지식)` 를 하나의 `ChatClient`에 묶은 것. 그 이상도 이하도 아니다.

**출처**: `SPRING AI 이해_v1.4.pdf` (총 349p) · SK C&C
**범위**: PDF p280 ~ p349 (3일차 전체)
**실습 코드**: `01.training code/10-1.mcp-client`, `10-2.mcp-server`, `11.simple-agent`, `12.multi-agent`, `13.practice-guide`

> ℹ️ 이 문서의 `p번호`는 **PDF 뷰어 기준 물리 페이지**입니다. 슬라이드 우하단 인쇄 번호보다 **1 큽니다**.

---

## 📑 목차

| # | 챕터 | 핵심 질문 | 슬라이드 |
|---|---|---|---|
| 1 | [MCP 개념과 아키텍처](#1-mcp-개념과-아키텍처) | Tool Calling과 뭐가 다른가? | p280~p288 |
| 2 | [Client-Server 호출 흐름](#2-clientserver-호출-흐름) | 요청 하나에 몇 번 오가나? | p289~p295 |
| 3 | [MCP Protocol — STDIO](#3-mcp-protocol--stdio) | 로컬 프로세스는 어떻게 통신하나? | p296~p317 |
| 4 | [MCP Protocol — Streamable HTTP](#4-mcp-protocol--streamable-http) | 원격 서버는 어떻게 통신하나? | p318~p335 |
| 5 | [Agent 이해](#5-agent-이해) | Agent는 결국 무엇인가? | p336~p344 |
| 6 | [종합 실습 — RAG 기반 추천 서비스](#6-종합-실습--rag-기반-추천-서비스) | 최종 제출물은? | p345~p348 |
| ★ | [전체 흐름 한 장 요약](#-전체-흐름-한-장-요약) | — | — |
| ★ | [시험/면접 대비 핵심 문답](#-시험면접-대비-핵심-문답) | — | — |
| ⚠️ | [원문 용어 검증 노트](#️-원문-용어-검증-노트) | — | — |

---

# 1. MCP 개념과 아키텍처

> 📍 **p280~p288** | Model Context Protocol 이해

## 1-1. MCP란 (p281)

| | 설명 |
|---|---|
| **비유로 말하면** | **USB-C 규격**. 어느 회사의 기기든, 어느 회사의 충전기든 같은 포트로 꽂힌다. MCP는 "AI ↔ 외부 시스템"의 USB-C다. |
| **정확히 말하면** | **자연어로 동작하는 AI**와 **API·DB·업무 시스템처럼 구조화된 인터페이스로 동작하는 시스템** 사이를 연결하는 **표준 중간 계층**. |

> ⭐ **목적 한 줄**: LLM을 **"지식 기반으로 답변하는 모델"** 에서 **"외부 시스템과 연결되어 작업을 수행하는 AI Agent"** 로 확장하기 위한 **표준 프로토콜**.

**Tool Calling vs MCP**

| | Tool Calling (2일차) | MCP (3일차) |
|---|---|---|
| **Tool의 위치** | 같은 애플리케이션 **내부**의 Java 메서드 | **다른 프로세스 / 다른 서버** |
| **연결 방식** | `@Tool` 어노테이션 + `.tools(obj)` | **JSON-RPC 2.0** 프로토콜 (STDIO / Streamable HTTP) |
| **재사용** | 그 앱 안에서만 | **여러 AI 클라이언트가 공유** (Claude Desktop, Cursor, 내 앱 …) |
| **어노테이션** | `@Tool`, `@ToolParam` | `@McpTool`, `@McpToolParam` |

## 1-2. MCP Architecture — 3개의 역할 (p282) ⭐⭐

```plain text
[ p282 — Model Context Protocol Architecture ]

  Server는 외부 시스템을                         Host는 사용자의
  Tool, Resource 형태로 제공                     자연어 요청을 이해
         ┌──────────┐                              ┌──────────┐
         │  Server  │ ╌╌╌╌╌┐            ┌╌╌╌╌╌╌╌╌╌ │   Host   │
         └──────────┘      │            │          └──────────┘
    ╌ Database Connection  │  ┌──────────────────┐   ╌ Chat Application
    ╌ API Access           ├──│       MCP        │───┤ ╌ Code Assistant
    ╌ Task Execution       │  │   Architecture   │   │
                           │  └────────┬─────────┘   │
                           ┘           │             └
                                  ┌────┴─────┐
                                  │  Client  │
                                  └──────────┘
                              ╌ Communication Interface
                              ╌ Data Exchange
                              Client는 MCP 통신을 담당
```

| 역할 | 담당 | 구체적 예시 |
|---|---|---|
| **Host** | 사용자의 **자연어 요청을 이해**하는 AI 애플리케이션 | Chat Application, Code Assistant (Claude Desktop, Cursor, 우리가 만든 Spring Boot 앱) |
| **Client** | **MCP 통신을 담당**하는 중개자 | Communication Interface, Data Exchange |
| **Server** | 외부 시스템을 **Tool, Resource 형태로 제공** | Database Connection, API Access, Task Execution |

> ⚠️ **혼동 주의**: Host와 Client는 보통 **같은 애플리케이션 안에** 있다. Spring AI에서는 `spring-ai-starter-mcp-client` 의존성을 넣은 우리 앱이 Host이자 Client다.

## 1-3. MCP Client (p283)

LLM과 MCP Server를 연결해 **도구를 실제로 사용할 수 있게 하는 중개자**.

**역할 4가지**
- `tools/list` 요청으로 **사용 가능한 도구 목록을 로딩**
- `tools/call` 요청으로 **특정 도구 실행**
- LLM이 필요할 때 MCP Server의 도구 호출을 **자동 오케스트레이션**
- **SSE / STDIO / Streamable HTTP** 같은 전송 방식 제공

## 1-4. MCP Server (p284)

MCP 프로토콜을 구현한 서버.

```plain text
       ┌──────────────┐        ┌────────────────────┐
       │   json-rpc   │        │      json-rpc      │
       │    STDIO     │        │  streamable HTTP   │
       └──────────────┘        └────────────────────┘
        (로컬 프로세스)              (원격 서버)
```

## 1-5. MCP 작동 방식 — 6단계 (p285) ⭐

| # | 단계 |
|---|---|
| ① | MCP 서버의 **`tools/list`** 엔드포인트를 호출해 사용 가능한 툴 목록 검색 (`ToolCallbackProvider`) |
| ② | 사용자가 MCP **Host**에게 요청 Prompt를 전달 |
| ③ | 사용자의 Prompt + 사전에 받아온 **Tool List를 LLM에 전달**. LLM은 Tool List 중 사용할 Tool들을 선택해서 응답 |
| ④ | MCP Client를 통해 MCP Server에게 **`tools/call`** 엔드포인트로 해당 툴 사용을 요청 |
| ⑤ | MCP Server의 Tool 응답 + 기존 사용자 Prompt를 **다시 LLM에 전달**하고, LLM은 이를 기반으로 최종 응답을 생성 |
| ⑥ | MCP Host는 LLM 모델로부터 받은 최종 응답을 가공해 **사용자에게 전달** |

> ⭐ **핵심**: `tools/list`는 보통 **앱 시작 시 1번**, `tools/call`은 **요청마다** 발생한다.

## 1-6. MCP 3계층 아키텍처 (p286~p287)

| 계층 | 역할 |
|---|---|
| **MCP Session (Middle)** | MCP **표준 스펙(기능 정의, 규격)** 을 다루는 핵심 계층. **Tools, Resources, Prompts**를 관리<br>· 클라이언트/서버 연결: 연결 초기화 및 협상(**Capability Negotiation**)<br>· 기능 노출 및 발견: 서버가 어떤 도구(Tools), 어떤 데이터(Resources)를 가지고 있는지 목록 구성<br>· **동적 JSON Schema 생성**: Java 클래스나 메서드를 분석해서 LLM이 이해할 수 있는 JSON Schema로 자동 생성 |
| **JSON-RPC (Message)** | 요청/응답 메시지 표준 포맷 |
| **Transport** | STDIO, Streamable HTTP, Stateless |

**초기화 3단계 (p287)**

```plain text
① Client → Server : 지원하는 MCP Protocol Version, Client 정보, Client Capability 전달
                    → "나는 이런데 통신 시작할래?"
② Server → Client : 사용할 MCP Protocol Version, Server Capability 반환
                    → "나는 이 버전으로 통신하자"
③ Client → Server : 초기화가 끝났고, 정상 메시지 교환 가능하다는 알림(notification) 전달
```

## 1-7. MCP 메시지 규격 — JSON-RPC (p288)

| 구성 요소 | 설명 |
|---|---|
| **Tool List** | 사용 가능한 도구 목록 조회 |
| **Tool Call** | 특정 도구 호출 |
| **JSON-RPC 기반** | 요청/응답 표준 포맷 |
| **표준 메시지 구조** | 모델이 이해 가능한 tool invocation 형식 |

```json
// tools/list 요청
{
  "jsonrpc": "2.0",
  "method": "tools/list",
  "id": 1
}
```

```json
// tools/call 요청
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "getWeather",
    "arguments": { "city": "Busan" }
  },
  "id": 2
}
```

---

# 2. Client-Server 호출 흐름

> 📍 **p289~p295** | 요청 1건이 실제로 어떻게 왕복하는가

## 2-1. 전체 시퀀스 다이어그램 (p290) ⭐⭐ 시험 단골

```plain text
[ p290 — 호출 흐름 (14단계) ]

 User        MCP Client         LLM        MCP Server        DB
  │              │               │              │             │
  │─1. "모든 사용자 정보를 검색해줘"─►│             │             │
  │              │──────── 2. tools/list ──────►│             │
  │              │◄─── 3. Tool 목록 반환 ───────│             │
  │              │    (getAllUsers, getUserById, etc.)        │
  │              │─4. User Message + Tool 목록─►│             │
  │              │  ("모든 사용자 정보 검색" + tools)          │
  │              │            ┌──────────────┐  │             │
  │              │            │5. Tool Select│  │             │
  │              │            │(getAllUsers) │  │             │
  │              │            └──────────────┘  │             │
  │              │◄─6. 선택된 Tool (getAllUsers)─│             │
  │              │──────── 7. tools/call ──────►│  @McpTool   │
  │              │           (getAllUsers)      │             │
  │              │                              │─8. Query DB►│
  │              │                              │ (SELECT *   │
  │              │                              │  FROM users)│
  │              │                              │◄9. User Data│
  │              │◄──── 10. Tool 실행 결과 ──────│             │
  │              │        (JSON response)       │             │
  │              │─11. 실행 결과 + 프롬프트────►│             │
  │              │   (결과 데이터 + 해석 요청)   │             │
  │              │        ┌────────────────────┐│             │
  │              │        │12. Parse & Format  ││             │
  │              │        │  Result (자연어 변환)││            │
  │              │        └────────────────────┘│             │
  │              │◄─13. 정리된 응답 ────────────│             │
  │              │   ("총 3명의 사용자…")        │             │
  │◄14. 최종 응답 전달─│                        │             │
```

> ⭐ **LLM은 총 2번 호출된다** (4번, 11번). 2일차 Tool Calling과 똑같다. **MCP는 Tool의 위치만 바꿨을 뿐, LLM과의 대화 패턴은 동일하다.**

## 2-2. 상세 흐름 — Spring AI 관점 (p291~p295)

| Step | 방향 | 내용 |
|---|---|---|
| **1** | MCP Client → MCP Server | `POST /mcp` → **`tools/list` 요청** |
| **2** | MCP Server → MCP Client | `tools/list` 응답 → **Tool Definition 목록 수신** (`ToolCallbackProvider`, JSON-RPC 2.0)<br>`"tools": [{"name":"getCurrentWeather","description":"…"}, {"name":"getWeather","inputSchema":…}]` |
| **4** | Spring AI → LLM | 사용자 질문 + **Tool Definitions** 전달 |
| **5** | LLM → Spring AI | **Tool Request 생성** (AssistantMessage의 `tool_calls`) |
| **6~7** | MCP Client → MCP Server | `POST /mcp`: 실제 **Tool Call JSON-RPC Request** → MCP Server에서 실행 후 JSON-RPC로 응답 |
| **8~9** | Spring AI → LLM | 응답을 **ToolResponseMessage**로 전환해서 LLM으로 전달 → LLM이 최종 자연어 답변 생성 |

**Step 4 — Spring AI → LLM (p292)**

```java
// Tool 정보
public final class ToolDefinition {
    private final String name;          // LLM에게 알려주는 메소드 이름
    private final String description;   // LLM이 이해할 수 있는 메소드 설명
    private final String inputSchema;   // 입력 파라미터 JSON Schema
}
```

```json
{
  "model": "gpt-4o",
  "messages": [
    { "role": "system", "content": "필요하면 도구를 사용해." },
    { "role": "user",   "content": "부산 현재 기온 알려줘" }
  ],
  "tools": [ /* ToolDefinition 목록 */ ]
}
```

**Step 5 — LLM → Spring AI (p293)**

```json
{
    "role": "assistant",
    "content": null,
    "tool_calls": [
      {
        "id": "call_1",
        "type": "function",
        "function": {
          "name": "getCurrentWeather",
          "arguments": "{\"city\":\"Busan\"}"
        }
      }
    ]
}
```

> 💡 assistant 메시지의 `tool_calls`로 **"이 도구를 이렇게 호출해"** 라고 지시한다.

**Step 6~7 — MCP Client ↔ MCP Server (p294)**

```json
// 요청: POST /mcp — 실제 Tool Call JSON-RPC Request
{
    "jsonrpc": "2.0",
    "id": "req_002",
    "method": "tools/call",
    "params": {
      "name": "getWeather",
      "arguments": { "city": "Busan" }
    }
}
```

```json
// 응답: JSON-RPC 응답
{
    "jsonrpc": "2.0",
    "id": "req_002",
    "result": {
      "content": { "temp": 14 }
    }
}
```

**Step 8~9 — Spring AI → LLM → 최종 답변 (p295)**

```json
// Spring AI → LLM : ToolResponseMessage
{
    "role": "tool",
    "tool_call_id": "call_1",
    "name": "getWeather",
    "content": "{\"temp\":14}"
}
```

```json
// LLM → Spring AI : 최종 자연어 답변
{
    "role": "assistant",
    "content": "부산의 현재 기온은 14°C 입니다."
}
```

> ⚠️ **`tool_call_id`는 LLM의 Tool 요청(Assistant Request)의 `tool_calls[].id`와 반드시 매칭**되어야 한다.

---

# 3. MCP Protocol — STDIO

> 📍 **p296~p317** | 로컬 프로세스 간 통신

## 3-1. JSON-RPC란 (p297)

MCP Client와 MCP Server는 **JSON-RPC**(`https://www.jsonrpc.org`) 메시지로 통신한다.

| | 설명 |
|---|---|
| **정의** | JSON으로 **원격 함수를 호출**하고 결과를 JSON으로 받는 프로토콜 |
| **전송 계층** | JSON-RPC 메시지를 직렬화/역직렬화해서 주고받으려면 **STDIO 또는 HTTP** 프로토콜이 필요하다 |

> ⭐ **계층 분리**: JSON-RPC는 **메시지 포맷**, STDIO/HTTP는 **운반 수단(Transport)**. 둘은 별개다.

## 3-2. Transport 3종 비교 (p298) ⭐⭐

| 방식 | 설명 | MCP에서의 사용 사례 |
|---|---|---|
| **STDIO** | 로컬 프로세스와 **stdin/stdout**으로 통신. 클라이언트와 서버 간 한번 연결하면 계속 열린 상태 유지 | 로컬 툴 에이전트, 데스크탑 확장 |
| **SSE** *(deprecated)* | `POST /sse` endpoint. 서버가 연결 동안 상태를 유지하며 여러 응답을 순서대로 보냄 | MCP Client와 Server 간 연결 구조 (구버전) |
| **Stateful Streamable HTTP** | Endpoint: `POST /mcp` | **MCP 표준 구조**. tool 호출, thought/progress 전달 |
| **Stateless Streamable HTTP** | Endpoint: `POST /mcp` (세션 없음) | 무상태 서버, 수평 확장 |

> ⚠️ **MCP 2025-03-26 버전 이후부터 SSE 통신 방식이 Streamable HTTP 통신 방식으로 통합**되었다 (p319). 새 프로젝트에서 SSE를 쓰지 말 것.

## 3-3. Content-Type별 전송 방식 (p299)

```plain text
application/json 방식:
  사용자 요청 ─── 10초 기다림 ───► [전체 응답 수신] → 화면 출력

text/event-stream 방식:
  사용자 요청 → [chunk1] → [chunk2] → [chunk3] → … → [완료]
                ↑즉시 출력  ↑즉시 출력  ↑즉시 출력
```

**Chunk로 보내는 이유 3가지**
- 사용자가 생성되는 텍스트를 **실시간으로 볼 수 있음** (ChatGPT처럼)
- **타임아웃 방지** — 긴 응답을 기다리는 동안 HTTP 연결이 끊기지 않음
- **Tool Call 중간 결과 전달** — MCP에서 tool 실행 상태, 진행률 등을 실시간으로 클라이언트에 알릴 수 있음

| | `application/json` | `text/event-stream` |
|---|---|---|
| **전송 방식** | 완성된 JSON 1개를 한 번에 | JSON을 여러 조각(chunk)으로 나눠서 순차 전송 |
| **연결** | 응답 후 종료 | 모든 chunk 전송 완료까지 연결 유지 |
| **클라이언트 처리** | 전체 수신 후 파싱 | 조각 수신할 때마다 즉시 처리 |

## 3-4. STDIO 기반 통신 (p301~p302)

애플리케이션 시작 시 **같은 PC에서 MCP Client와 Server를 실행**하는 경우에 사용하는 방식.
LLM으로부터 도구 호출 요청이 들어오면 MCP Client는 **표준 입출력(STDIO)** 을 이용해서 MCP Server와 통신한다.

```plain text
[ p301 — STDIO 통신 구조 ]

                        동일 PC 내
 ┌─────────────────────────────────┐        ┌──────────────┐
 │  Application                    │        │              │
 │   ┌──────────────┐   메모리 버퍼  │        │  MCP Server  │
 │   │  MCP Client  │◄────────────►│◄──────►│              │
 │   └──────────────┘              │        │              │
 │    System.out.write()           │        │  System.in.read()
 │    System.in.read()             │        │  System.out.write()
 └─────────────────────────────────┘        └──────────────┘
```

**특징 (p302)**

| 특징 | 사용 목적 |
|---|---|
| · HTTP 서버 필요 없음<br>· 네트워크 포트 필요 없음<br>· 서버는 단순히 **표준 입력을 읽고 / 표준 출력으로 결과 쓰기**<br>· 데이터는 반드시 **JSON-RPC 2.0 메시지** | · HTTP 없이도 MCP Server를 만들 수 있게 하기 위함<br>· **에디터·IDE·로컬 프로세스 통합에 최적**<br>· 공식적으로 가장 단순한 트랜스포트 |

> ⭐ 네트워크 없이 동일 프로세스/머신 내부에서 표준 입출력으로 JSON-RPC를 교환하는 **로컬 IPC 방식**. 가장 가볍고 지연이 거의 없어 **개발·테스트용으로 널리 사용**된다.

**3단계**: ① Initialization 요청 (Capability 협상) → ② `tools/list` 요청/응답 → ③ `tools/call` 요청/응답

## 3-5. STDIO 메시지 예시 (p303~p305)

**① 초기화 (Initialization)**

```json
// 1. Client → Server request
{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
      "protocolVersion": "2025-03-26",     // 사용할 MCP 프로토콜 버전
      "clientInfo": { "name": "my-spring-ai-mcp-client", "version": "1.0.0" },
      "capabilities": { }
    }
}
```

```json
// 2. Server → Client Response
{
    "jsonrpc": "2.0",
    "id": 1,
    "result": {
      "protocolVersion": "2025-03-26",     // 서버가 동의하는 버전
      "serverInfo": { "name": "my-spring-ai-mcp-server", "version": "1.0.0" },
      "capabilities": { "tools": { } }
    }
}
```

**② tools/call 요청/응답 (p305)**

```plain text
1. Client → Server Request                 2. Server → Client Response
Content-Length: 120                        Content-Length: 160

{                                          {
    "jsonrpc": "2.0",                          "jsonrpc": "2.0",
    "id": 3,                                   "id": 3,
    "method": "tools/call",                    "result": {
    "params": {                                  "content": [
      "name": "searchFile",                        {
      "arguments": {                                 "type": "text",
        "keyword": "report",                         "text": "report.txt(경로)/src/report.md를 찾았습니다."
        "path": "/src"                              }
      }                                          ]
    }                                          }
}                                          }
```

> 💡 `Content-Length` 헤더가 붙는다. STDIO는 스트림이라 메시지 경계를 알려줘야 하기 때문.

## 3-6. 의존성 (p306)

```xml
<!-- MCP Client -->
<dependency>
    <groupId>org.springframework.ai</groupId>
    <artifactId>spring-ai-starter-mcp-client</artifactId>
</dependency>
```

```xml
<!-- MCP Server -->
<dependency>
    <groupId>org.springframework.ai</groupId>
    <artifactId>spring-ai-starter-mcp-server-webmvc</artifactId>
</dependency>
```

## 3-7. MCP Server 설정 — STDIO (p307~p308) ⭐

```yaml
# application-stdio.yaml (Server)
spring:
  ai:
    mcp:
      server:
        name: stdio-mcp-server
        version: 1.0.0
        instructions: "STDIO MCP Server providing User and Product management tools"
        stdio: true          # STDIO 프로토콜 활성화
        type: SYNC           # 동기 방식
        annotation-scanner:
          enabled: true

  main:
    web-application-type: none    # 웹 서버 비활성화 (STDIO 전용)
    banner-mode: log              # Spring Boot 배너를 로그 파일로 출력 (STDIO 보호)

# STDIO 모드: stdout은 MCP JSON-RPC 전용이므로 콘솔 출력 완전 비활성화
logging:
  pattern:
    console: ""                   # 콘솔(stdout) 출력 비활성화 - STDIO 프로토콜 보호
  file:
    name: logs/mcp-server-stdio.log
```

| 설정 | 의미 |
|---|---|
| `name` / `version` | MCP Client에서 MCP Server를 **식별할 때 사용**하는 정보. initialize 단계에 이름 공유 |
| `stdio: true` | MCP Server의 전송 방식(Transport)을 **STDIO로 설정** |
| `type: SYNC \| ASYNC` | MCP Server를 **MVC(SYNC)** 또는 **WebFlux(ASYNC)** 로 결정 |
| `annotation-scanner.enabled: true` | `@McpTool`이 선언된 자바 메소드를 **자동 로딩** |
| `web-application-type: none` | 네트워크 포트를 열지 않고 **로컬 프로세스로만 수행** |
| `banner-mode: log` | Spring 배너를 표준 출력으로 못 나가게 막고 로그 파일로 전달 |
| `logging.pattern.console: ""` | **표준 출력(stdout)을 차단** |
| `logging.file.name` | 애플리케이션 모든 로그를 파일로 격리 수집 |

> ⚠️⚠️ **STDIO 모드에서 가장 흔한 실수**
> `stdout`은 **MCP JSON-RPC 전용 채널**이다. 여기에 로그·배너·`System.out.println()`이 하나라도 섞이면 **JSON 파싱이 깨져 통신이 죽는다.**
> 그래서 `banner-mode`, `logging.pattern.console`, `web-application-type` 3가지를 반드시 막아야 한다.

## 3-8. 도구 정의 — @McpTool (p309)

내부 `@Tool` 정의와 비슷하며, MCP에서는 **`@Tool` 대신 `@McpTool`, `@ToolParam` 대신 `@McpToolParam`** 을 사용한다.

```java
@Component
@RequiredArgsConstructor
@Slf4j
public class ProductTools {

    private final ProductService productService;

    @McpTool(description = "모든 상품 정보를 조회합니다.")
    public List<Product> getAllProducts() {
        log.info("MCP Tool: getAllProducts called");
        return productService.getAllProducts();
    }

    @McpTool(description = "ID로 특정 상품을 조회합니다.")
    public Product getProductById(
            @McpToolParam(description = "상품 ID", required = true) Long id) {
        log.info("MCP Tool: getProductById called with id={}", id);
        return productService.getProductById(id);
    }
}
```

> 💡 **참고**: `@Tool`을 사용할 수도 있지만, 이 경우 **`MethodToolCallbackProvider`를 통해 Tool Service를 수동으로 등록**해야 한다.

## 3-9. MCP Client 설정 — STDIO (p310)

```yaml
# application-stdio.yaml (Client)
spring:
  ai:
    mcp:
      client:
        type: SYNC
        # STDIO 로컬 서버
        stdio:
          connections:
            tool-server:
              command: java
              args:
                - -jar
                - ../10-2.mcp-server/target/spring-mcp-server-0.0.1-SNAPSHOT.jar
                - --spring.profiles.active=stdio
```

| 설정 | 의미 |
|---|---|
| `spring.ai.mcp.client.type: SYNC` | MCP Client의 동작 방식을 **동기 방식**으로 설정 |
| `tool-server` | MCP Server를 **식별하기 위한 이름** (임의로 지정) |
| `command` / `args` | MCP Server를 **실행하기 위한 명령어** |

> ⭐ **STDIO의 핵심**: MCP Client가 **MCP Server 프로세스를 직접 띄운다.** 그래서 Server를 미리 실행해 둘 필요가 없다. jar만 빌드해 두면 된다.

## 3-10. 🧪 실습 — STDIO MCP Server 만들기 (p311~p313)

`01.training code/10-2.mcp-server`
Tool 과정에서 진행했던 `DateTimeTools`, `FileSystemTools`, `WeatherTools.java`를 MCP Server용으로 변경한다.

**① `resources/application-stdio.yaml` 추가**

```yaml
spring:
  main:
    # STDIO는 표준 입출력으로 통신하므로 내장 웹 서버(Tomcat)를 띄우지 않는다.
    web-application-type: none
    banner-mode: off
  ai:
    mcp:
      server:
        name: my-spring-ai-mcp-server
        version: 1.0.0
        stdio: true
        type: SYNC

logging:
  pattern:
    console:
  file:
    name: logs/mcp-server-stdio.log
  level:
    '[org.springframework.ai.mcp]': DEBUG
```

**② `tools` 패키지 아래에 기존 `09.tools`의 Tool 클래스 복사**
파일: `DateTimeTools.java`, `FileSystemTools.java`, `WeatherTools.java`

**③ 어노테이션 교체: `@Tool` → `@McpTool`, `@ToolParam` → `@McpToolParam`**

```java
@McpTool(description = "현재 Java 애플리케이션이 실행 중인 디렉터리에 새 파일을 생성합니다.")
public String createFile(
        @McpToolParam(description = "생성할 파일명", required = true) String fileName,
        @McpToolParam(description = "파일에 저장할 내용", required = true) String content)
        throws IOException {

    Path file = Paths.get(fileName);
    Files.writeString(file, content);
    return file.toAbsolutePath().toString();
}
```

**④ 빌드 (실행은 안 해도 됨)**

```bash
mvn clean install -DskipTests && ls ./target/spring-mcp-server-0.0.1-SNAPSHOT.jar
```

> 💡 빌드된 코드는 MCP Client에서 STDIO를 위해 **함께 실행**되므로 여기서는 실행할 필요가 없다.

## 3-11. 🧪 실습 — STDIO MCP Client 만들기 (p314~p317)

`01.training code/10-1.mcp-client`

**① `resources/application-stdio.yaml` 추가**

```yaml
spring:
  profiles:
    active: stdio
  ai:
    mcp:
      client:
        name: my-spring-ai-mcp-client
        version: 1.0.0
        type: SYNC
        stdio:
          connections:
            tool-server:
              command: java
              args:
                - -jar
                - ../10-2.mcp-server/target/spring-mcp-server-0.0.1-SNAPSHOT.jar
                - --spring.profiles.active=stdio
```

**참고 — Docker 관리용 MCP Server 등록 (p314~p315)**

```yaml
            docker-server:
              command: npx
              args:
                - -y
                - "@swartdraak/docker-mcp-server@latest"
```

> ⚠️ **외부 MCP Server(`npx` 패키지 등)를 등록하는 것은 그 패키지에 자신의 로컬 환경 접근 권한을 주는 것**입니다. 신뢰할 수 있는 패키지인지 확인하고 사용하세요.

**② `ChatController.java`에 `SyncMcpToolCallbackProvider` 추가 (p316)**

로컬의 Tool 함수 대신 **원격에 있는 Tool을 검색해서 등록**하기 위해 `SyncMcpToolCallbackProvider`를 추가한다.

```java
@RestController
public class ChatController {

    private final ChatClient chatClient;
    private final SyncMcpToolCallbackProvider mcpToolCallbackProvider;

    public ChatController(ChatModel chatModel,
                          ChatMemory chatMemory,
                          SyncMcpToolCallbackProvider mcpToolCallbackProvider) {

        this.mcpToolCallbackProvider = mcpToolCallbackProvider;
        this.chatClient = ChatClient.builder(chatModel)
                .defaultAdvisors(
                        MessageChatMemoryAdvisor.builder(chatMemory).build(),
                        new SimpleLoggerAdvisor())
                .build();
    }

    @GetMapping("/ai")
    public String chat(@RequestParam String request, HttpSession session) {
        return this.chatClient.prompt()
                .advisors(a -> a.param(ChatMemory.CONVERSATION_ID, session.getId()))
                .user(request)
                .toolCallbacks(mcpToolCallbackProvider.getToolCallbacks())   // ← 원격 Tool 등록
                .call()
                .content();
    }
}
```

> ⭐ **2일차와의 유일한 차이**: `.tools(dateTimeTools, weatherTools)` → `.toolCallbacks(mcpToolCallbackProvider.getToolCallbacks())`.
> **나머지 코드는 그대로다.** 이게 MCP 추상화의 힘이다.

**③ 빌드 및 실행 (p317)**

```bash
mvn clean install -DskipTests && java -jar ./target/spring-ai-0.0.1-SNAPSHOT.jar --spring.profiles.active=stdio
```

**체크리스트**
- [ ] UI 화면에서 질문을 넣고 **어떤 도구가 호출되는지 Console 로그로 확인**
- [ ] 두 가지 도구(`FileSystemTool`, `WeatherTool`)를 **복합적으로 사용하는 질문** 실행
  - 사전 조건: `weather.txt` 파일에 "캐나다 토론토 날씨와 서울 날씨를 알려줘"라는 내용이 들어 있어야 함

---

# 4. MCP Protocol — Streamable HTTP

> 📍 **p318~p335** | 원격 서버 통신

## 4-1. HTTP 기반 통신 (p319)

애플리케이션과 MCP Server를 **원격에서 개별적으로 실행**하는 경우에 사용하는 방식.

> ⚠️ **MCP 2025-03-26 버전 이후부터는 SSE 통신 방식이 Streamable HTTP 통신 방식으로 통합**되었다.

```plain text
[ p319 — HTTP 통신 흐름 ]

 ┌─────────────────────────┐                                ┌──────────────────────┐
 │  Application            │                                │    MCP Server        │
 │  ┌──────────────────┐   │  HTTP POST 도구 목록(tool/list) │                      │
 │  │   MCP Client     │───┼───────────────────────────────►│ ToolCallbackProvider │
 │  │                  │◄──┼─── 도구 목록 응답 ─────────────│                      │
 │  │  도구 호출        │───┼─── HTTP POST 도구 호출 ───────►│                      │
 │  │                  │◄──┼─ application/json:            │  @Tool function      │
 │  │                  │   │   요청이 접수됨을 즉시 응답      │                      │
 │  │  결과 수신        │───┼─── HTTP POST 도구 호출 ───────►│                      │
 │  │                  │◄──┼─ text/event-stream stream 응답 │                      │
 │  └──────────────────┘   │                                │                      │
 └─────────────────────────┘                                └──────────────────────┘
```

## 4-2. Stateful vs Stateless (p320) ⭐⭐ 시험 단골

| 구분 | **Streamable HTTP (Stateful)** | **Streamable HTTP (Stateless)** |
|---|---|---|
| **엔드포인트** | 1개 `/mcp` (+ option SSE: `/mcp/sse`) | 1개 `/mcp` |
| **POST 요청 응답** | 직접 응답<br>· 짧은 응답: `application/json`<br>· 긴 대기 시간 응답: `text/event-stream` | 직접 응답<br>· `application/json` |
| **POST 응답 방식** | POST 응답으로 제공 | POST 응답으로 제공 |
| **GET 요청 (SSE 연결)** | **항상 연결 유지** — `GET /mcp` SSE 채널로 Push 지원 | **미지원** |
| **서버 → 클라이언트 알림** | 가능 (`listChanged` 등 이벤트) | **서버 주도 Push 불가** |
| **세션 관리** | `Mcp-Session-Id` 헤더 — Initialize 응답 시 서버 발급 | **없음** |
| **상태 유지** | 세션 단위 헤더 | 없음 |

> ✅ **선택 기준**
> · **Stateful**: 서버가 진행률·이벤트를 밀어줘야 할 때. 대신 세션 상태 때문에 **수평 확장(스케일아웃)이 어렵다.**
> · **Stateless**: 로드밸런서 뒤에 여러 인스턴스를 두는 **클라우드 환경**에 적합.

## 4-3. Stateful Streamable HTTP 메시지 (p321~p323)

**① 초기화 — `Mcp-Session-Id` 발급**

```http
POST /mcp HTTP/1.1
Host: example.com
Content-Type: application/json
Accept: application/json, text/event-stream

{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": { "protocolVersion": "2025-03-26", ... }
}
```

```http
HTTP/1.1 200 OK
Content-Type: application/json
Mcp-Session-Id: 550e8400-e29b-41d4-a716-446655440000     ← 서버가 발급

{
    "jsonrpc": "2.0",
    "id": 1,
    "result": {
      "protocolVersion": "2025-03-26",
      "serverInfo": { ... },
      "capabilities": { ... }
    }
}
```

**② 일반 요청 — JSON 응답 (p322)**

```http
POST /mcp HTTP/1.1
Content-Type: application/json
Accept: application/json, text/event-stream
Mcp-Session-Id: 550e8400-e29b-41d4-a716-446655440000     ← 이후 모든 요청에 포함

{ "jsonrpc": "2.0", "id": 2, "method": "tools/list" }
```

```http
HTTP/1.1 200 OK
Content-Type: application/json
Mcp-Session-Id: 550e8400-e29b-41d4-a716-446655440000

{ "jsonrpc": "2.0", "id": 2, "result": { "tools": [ ... ] } }
```

**③ 장시간 작업 — SSE 응답 (p323)**

```http
HTTP/1.1 200 OK
Content-Type: text/event-stream
Mcp-Session-Id: 550e8400-e29b-41d4-a716-446655440000
Cache-Control: no-cache
Connection: keep-alive

data: {"jsonrpc":"2.0","method":"notifications/progress","params":{...}}

data: {"jsonrpc":"2.0","id":3,"result":{...}}
```

> ⭐ **같은 엔드포인트(`POST /mcp`)인데 응답 Content-Type이 상황에 따라 달라진다.** 짧으면 `application/json`, 길면 `text/event-stream`. 이게 "Streamable" HTTP라는 이름의 이유.

## 4-4. Stateless Streamable HTTP 메시지 (p324~p326)

Stateful과 거의 동일하지만 **`Mcp-Session-Id` 헤더가 없다.**

```http
POST /mcp HTTP/1.1
Content-Type: application/json
Accept: application/json, text/event-stream

{ "jsonrpc": "2.0", "id": 2, "method": "tools/call",
  "params": { "name": "calculate", "arguments": { ... } } }
```

```http
HTTP/1.1 200 OK
Content-Type: application/json

{ "jsonrpc": "2.0", "id": 2,
  "result": { "content": [ { "type": "text", "text": "..." } ] } }
```

장시간 작업 시에도 `text/event-stream`으로 chunk 전송은 가능하지만, **서버가 먼저 Push하는 것은 불가능**하다.

## 4-5. Streamable MCP Server 설정 (p327)

```yaml
# application-stateful-http.yaml
spring:
  ai:
    mcp:
      server:
        name: my-spring-ai-mcp-server
        version: 1.0.0
        annotation-scanner:
          enabled: true          # default는 true
        # 세션 상태를 유지하는 Streamable HTTP. 엔드포인트는 기본값 POST /mcp 를 사용한다.
        protocol: STREAMABLE
        type: SYNC
```

| 설정 | 값 | 의미 |
|---|---|---|
| `protocol` | `STREAMABLE` \| `STATELESS` | 전송 프로토콜 선택 |
| `type` | `SYNC` \| `ASYNC` | MVC / WebFlux 결정 |
| `annotation-scanner.enabled` | `true` (default) | `@McpTool` 자동 로딩 |

> ⭐ **STDIO와의 설정 차이**: `stdio: true`가 사라지고 `protocol: STREAMABLE`이 들어간다. 그리고 **`web-application-type: none`과 로그 차단 설정이 필요 없다** (웹 서버를 띄워야 하므로).

## 4-6. Streamable MCP Client 설정 (p328)

```yaml
# application-streamable.yaml
spring:
  ai:
    mcp:
      client:
        name: my-spring-ai-mcp-client
        version: 1.0.0
        type: SYNC
        streamable-http:
          connections:
            tool-server:
              url: http://localhost:8081
              endpoint: /mcp
```

| 설정 | 의미 |
|---|---|
| `spring.ai.mcp.client.type: SYNC` | MCP Client의 동작 방식을 동기 방식으로 설정 |
| `tool-server.url` | MCP Server 접속을 위한 **URL 정보** |
| `endpoint` | MCP Server **노출 패스** 정보 (`/mcp`) |

> ⭐ **STDIO와의 차이**: `command`/`args`(프로세스 실행)가 사라지고 `url`/`endpoint`(네트워크 주소)로 바뀐다. 즉 **Server를 미리 띄워 놓아야 한다.**

## 4-7. 🧪 실습 — Streamable HTTP (p329~p332)

**① MCP Server: `resources/application-stateful-http.yaml` 추가**

```yaml
spring:
  ai:
    mcp:
      server:
        name: my-spring-ai-mcp-server
        version: 1.0.0
        annotation-scanner:
          enabled: true
        protocol: STREAMABLE
        type: SYNC

logging:
  level:
    '[org.springframework.ai.mcp]': DEBUG
```

**② MCP Server 빌드 및 실행 (p330)**

```bash
mvn clean install -DskipTests && java -jar ./target/spring-mcp-server-0.0.1-SNAPSHOT.jar --spring.profiles.active=stateful-http
```

**③ MCP Client: `resources/application-stateful-http.yaml` 추가 (p331)**

```yaml
spring:
  ai:
    mcp:
      client:
        # 10-2.mcp-server를 --spring.profiles.active=stateful-http 로 기동했을 때 노출되는
        # Streamable HTTP(POST /mcp) 엔드포인트에 접속한다. 세션 상태를 서버에 유지하는(stateful)
        # 방식이라 클라이언트 쪽 커넥션 설정은 stateless와 동일하며, 차이는 서버 프로필에서 결정된다.
        name: my-spring-ai-mcp-client
        version: 1.0.0
        type: SYNC
        streamable-http:
          connections:
            tool-server:
              url: http://localhost:8081
              endpoint: /mcp
```

> ⭐ **중요**: **클라이언트 설정은 stateful/stateless가 동일하다.** 차이는 **서버 프로필에서 결정**된다.

**④ MCP Client 빌드 및 실행 (p332)**

```bash
mvn clean install -DskipTests && java -jar ./target/spring-ai-0.0.1-SNAPSHOT.jar --spring.profiles.active=stateful-http
```

**체크리스트**
- [ ] MCP Server를 **먼저** 8081 포트로 띄운다 (STDIO와 달리 클라이언트가 서버를 실행해 주지 않는다)
- [ ] UI에서 질문 → 어떤 도구가 호출되는지 Console 로그 확인
- [ ] `FileSystemTool` + `WeatherTool` 복합 질문 실행

## 4-8. 🧪 실습 — 나의 Spring Boot를 MCP Server로 전환 (p333~p335)

앞서 Spring Boot 교육 시 만들었던 Spring Boot 애플리케이션을 MCP Server로 구성하고 MCP Client와 연동한다.
MCP Server는 **Streamable HTTP SERVER**로 구성.

**핵심 포인트**
- [ ] `pom.xml`에 **의존성 추가** (`spring-ai-starter-mcp-server-webmvc`)
- [ ] **`tools` 패키지**를 만들고, **기존 Service를 사용하는 Tool**을 생성
- [ ] `application.yaml` 설정

**참조 코드 (p335)**

| 방식 | 경로 | 설명 |
|---|---|---|
| **STDIO** | `02.answer code/10-3.springboot-mcpserver/01.stdio-mcp-server` | STDIO 버전. Claude Desktop 또는 `10-1.mcp-client`와 연동 가능 |
| **Streamable HTTP** | `02.answer code/10-3.springboot-mcpserver/02.http-mcp-server` | Stateful/Stateless 버전. Claude Desktop 또는 `10-1.mcp-client`와 연동 가능 |

각 폴더에서 확인할 것:
- [ ] `tool` 패키지
- [ ] `resources/application.yaml`
- [ ] `pom.xml` 또는 `build.gradle`
- [ ] `README.md`

> ⭐ **이 실습의 의미**: 기존에 만든 **평범한 CRUD Spring Boot 앱**을, Service 계층은 하나도 안 바꾸고 **`tools` 패키지만 얹어서** AI가 쓸 수 있는 도구로 바꾼다. 이게 1일차 p5에서 말한 **"기존 도메인 로직을 AI Tool로 재사용"** 의 실체다.

---

# 5. Agent 이해

> 📍 **p336~p344** | Agent는 결국 무엇인가

## 5-1. Agent의 정의 (p337)

| | 설명 |
|---|---|
| **정의** | 주어진 **목표(Goal)** 를 달성하기 위해 현재 상황을 판단하고, 필요한 **행동(Action)** 을 스스로 선택·실행하며, 그 결과를 다시 **관찰(Observation)** 해서 다음 행동을 결정하는 AI 시스템 |

**Agent의 4대 요소**

| 요소 | 설명 | 예시 |
|---|---|---|
| **① Goal (목표)** | 목표가 있음 | 출장 준비, 장애 원인 분석, 리포트 작성처럼 **달성해야 할 목표**를 가짐 |
| **② Reasoning / Planning (추론/계획)** | 무엇을 할지 추론·판단할 수 있음. 목표를 여러 작업으로 **분해**하고 다음에 수행할 행동을 결정 | 일정 확인 → 항공편 검색 → 호텔 검색 → 결과 비교 |
| **③ Tool Use** | 외부 도구를 사용할 수 있어야 함 | 검색 API, DB, Kubernetes API, MCP Server 등을 **LLM이 필요에 따라 선택** |
| **④ Observation (관찰)** | 행동 결과를 다시 받아들이고 **반복**할 수 있어야 함 | `CrashLoopBackOff`가 발견된 경우 다시 **로그를 확인하는 Tool을 선택**할 수 있음 |

**추가 축**: **Autonomy(자율성)** ↔ **Human In the Loop(사람의 개입)**

> ⭐ **자율성과 안전의 트레이드오프**: 완전 자율 Agent는 위험하다. 중요한 행동(삭제, 결제, 배포) 전에는 **Human In the Loop**로 사람의 승인을 받는 설계가 실무 표준이다.

## 5-2. Agent를 구성하는 핵심 요소 (p338)

> ⭐ **핵심 명제**: LLM이 단순히 답변을 생성하는 것에서 끝나지 않고, **실제로 무엇을 해야 할지 결정하고 행동한다는 것**

```plain text
                       Agent
        ┌──────────┬──────────┬──────────┐
        │   LLM    │  Memory  │  Tools   │
        │  판단/추론 │   기억    │   행동    │
        └──────────┴──────────┴──────────┘
                        │
                 계획/추론 → 행동 → 관찰 → (반복)
```

## 5-3. Agent 실행 구조 — 3 Step (p339~p340) ⭐⭐

> ⭐ **가장 중요한 한 문장 (p339)**
> Agent란 **"LLM에게 목표와 사용 가능한 도구(Tool)를 주고, LLM이 스스로 판단하여 도구를 실행하고 결과를 종합하여 답변하게 만드는 패턴 그 자체"** 다.
> **복잡한 프레임워크가 아니다.**

```plain text
[ p339 — Agent 실행 구조 ]

[사용자 요청] ──► [System Prompt (페르소나/규칙)]
                        │
                        ├── (1) Chat Memory   (이전 대화 맥락 참조)
                        ├── (2) RAG Advisor   (Vector DB 문서 자동 검색)
                        └── (3) Tool Calling  (필요 시 외부 Java 메서드 실행)
                        │
                 [LLM 판단 및 최종 응답 (Structured Output)]
```

**Step 1: 페르소나 및 판단 규칙 정의 (System Prompt)**

LLM이 자신이 어떤 역할(Agent)이며, 어떤 단계로 사고해야 하는지 정의한다.

```plain text
당신은 카페 주문 상담 에이전트입니다. 사용자의 질문이 들어오면
 1) RAG를 통해 메뉴 정보를 확인하고,
 2) 재고가 필요하면 재고 조회 Tool을 호출한 뒤,
 3) 최종 결과를 JSON으로 응답하세요.
```

**Step 2: RAG + Memory + Tool을 ChatClient에 바인딩 (p340)**

Spring AI의 `ChatClient` **하나에 모든 부가 기능을 지능적으로 집결(Orchestration)** 한다.

```java
// ChatClient 생성 시 모든 요소 통합 (Orchestration)
this.chatClient = chatClientBuilder
    .defaultSystem("당신은 [도메인명] 전문 에이전트입니다. 지식 검색과 도구를 사용해 정확히 답변하세요.")
    .defaultAdvisors(
        MessageChatMemoryAdvisor.builder(chatMemory).build(),   // Chat Memory
        QuestionAnswerAdvisor.builder(vectorStore).build()      // RAG (Vector DB)
    )
    .defaultTools("checkInventoryTool", "applyCouponTool")      // Tool Calling
    .build();
```

**Step 3: Structured Output으로 최종 반환**

LLM이 응답 결과를 문자열이 아닌 **규격화된 객체(JSON)** 로 반환하도록 설정한다.

```java
return chatClient.prompt()
        .user(userQuery)
        .call()
        .entity(AgentResponse.class);   // Java Record/DTO 클래스로 자동 매핑
```

> ✅ **결론**: 1일차의 `ChatClient`·`Advisor`·`Structured Output`, 2일차의 `RAG`·`Memory`·`Tool`, 3일차의 `MCP` — **이 전부를 하나의 `ChatClient` 빌더에 조립한 것이 Agent다.** 새로운 기술은 없다.

## 5-4. 🧪 실습 — Single Agent (p341~p342)

`01.training code/11.simple-agent`

**실습 목표**: Tool 함수 호출 기능을 기반으로 아주 단순한 Agent 2개를 직접 만들어본다.
여기서 Agent란 복잡한 프레임워크가 아니라 다음 **3가지 요소의 조합**으로 이해한다.

| # | 요소 |
|---|---|
| ① | **역할을 정의하는 System Prompt** |
| ② | 그 역할 수행에 필요한 **Tool들만 선택적으로 연결** |
| ③ | 대화 상태를 유지하는 **ChatClient** |

`09.tools`에 있는 `DateTimeTools`, `FileSystemTool`, `WeatherTools`를 **그대로 가져와 사용**한다.

```plain text
[ p342 — 두 개의 Agent 구성 ]

 FileManagerAgent                            WeatherGuideAgent
 ┌──────────────┐   fileSystemTool          ┌──────────────┐   WeatherTool
 │              │──► • listFiles            │              │──► • getCurrentWeather
 │  chatClient  │──► • createFile           │  chatClient  │
 │              │──► • readTextFile         │              │──► dateTimeTool
 └──────────────┘                           └──────────────┘   • getCurrentDateTime
```

```java
// FileManagerAgent
private static final String SYSTEM_PROMPT = """
        당신은 서버의 작업 디렉토리 파일을 관리하는 '파일 관리 에이전트'입니다.
        파일 목록 조회, 파일 생성, 텍스트 파일 읽기 도구를 활용해 사용자의 요청을 해결하세요.
        도구로 확인할 수 없는 내용은 추측하지 말고, 모른다고 답하세요.
        """;
```

```java
// WeatherGuideAgent
private static final String SYSTEM_PROMPT = """
        당신은 도시별 날씨 정보를 안내하는 '날씨 안내 에이전트'입니다.
        날씨 조회 도구를 사용해 사용자가 묻는 도시의 현재 날씨를 확인하고,
        기온과 체감 날씨를 이해하기 쉽게 안내하세요.
        도구로 확인할 수 없는 내용은 추측하지 말고, 모른다고 답하세요.
        """;
```

> ⭐ **두 프롬프트의 공통 마지막 문장**: **"도구로 확인할 수 없는 내용은 추측하지 말고, 모른다고 답하세요."**
> 이 한 줄이 **환각(Hallucination) 방지의 핵심 가드레일**이다. 모든 Agent System Prompt에 넣을 것.

- [ ] `README.md` 참고하여 실행
- [ ] 기존 Tool을 Agent로 전환하는 방법을 실습

## 5-5. 🧪 실습 — Multi-Agent Orchestration (p343~p344) ⭐

`01.training code/12.multi-agent`

**실습 목표**: `11.simple-agent`에서 만든 **역할+Tool로 정의된 Agent 여러 개**를, 하나의 **Orchestrator**가 상황에 맞게 골라 쓰는 **Orchestration 기반 Multi-Agent 구조**로 확장한다.

```plain text
[ p344 — Multi-Agent Orchestration 구조 ]

 OrchestratorAgent
 ┌──────────────┐                          FileManagerAgent
 │              │                          ┌──────────────┐   fileSystemTool
 │  chatClient  │───► AgentDelegationTools │              │──► • listFiles
 │              │     • delegateToFileManager  chatClient │──► • createFile
 │              │     • delegateToWeatherGuide│           │──► • readTextFile
 └──────────────┘              │            └──────────────┘
                               │
                               │            WeatherGuideAgent
                               │            ┌──────────────┐   DateTimeTools
                               └───────────►│  chatClient  │──► • getCurrentDateTime
                                            │              │──► WeatherTool
                                            └──────────────┘
```

```java
private static final String SYSTEM_PROMPT = """
        당신은 사용자 요청을 분석해 적절한 전문 에이전트에게 작업을 위임하는 오케스트레이터입니다.
        직접 답을 지어내지 말고, 제공된 Tool의 설명을 참고해 적절한 Tool을 호출하세요.
        - 여러 전문 에이전트가 필요하면 필요한 순서대로 Tool을 호출하세요.
        """;
```

> ⭐⭐ **Multi-Agent의 핵심 트릭**
> **"Agent를 Tool로 감싼다."**
> `AgentDelegationTools`의 `delegateToFileManager`, `delegateToWeatherGuide`는 **평범한 `@Tool` 메서드**이고, 그 안에서 하위 Agent의 `chatClient`를 호출할 뿐이다.
> 즉 **Orchestrator 입장에서 하위 Agent는 그냥 Tool이다.** 새로운 메커니즘이 전혀 필요 없다.

- [ ] `README.md` 참고하여 실행
- [ ] "weather.txt를 읽고 거기 적힌 도시들의 날씨를 알려줘" 같은 **두 Agent가 순차로 필요한 질문**으로 테스트

---

# 6. 종합 실습 — RAG 기반 추천 서비스

> 📍 **p345~p348** | 최종 제출물

## 6-1. 과제 개요 (p346)

훈련생 스스로 **원하는 도메인(주제)** 을 직접 정의하고, 학습한 기술 요소들을 조합하여 **실제 동작하는 RAG 기반 추천 서비스**를 구성한다. **AI Agent 형태 구조**를 고려할 것.

**핵심 목표 3가지**

| 목표 | 설명 |
|---|---|
| **도메인 자율성** | 개인 프로젝트, 관심사, 업무 영역(예: **법률, 카페 레시피, 게임 룰북, 사내 IT지원, 취업 상담** 등) 중 하나를 자율적으로 선택 |
| **핵심 AI 기술 통합** | **RAG, Chat Memory, Vector DB, Tool Call, Structured Output**을 하나의 애플리케이션으로 통합 |
| **Spring AI 기반 Agent 구조 구현** | Spring AI의 **Tool Calling, Advisor**를 조합하여 스스로 판단하고 실행하는 에이전트를 완성 |

## 6-2. 필수 포함 기술 요소 5가지 (p347) ⭐ 채점 기준

| # | 기술 요소 | 요구사항 |
|---|---|---|
| ① | **Embedding + Vector DB (PgVector)** | 선택한 도메인의 텍스트/문서를 **분할(Chunking)** 하여 PgVector에 적재 |
| ② | **RAG (Retrieval Augmented Generation)** | 사용자 질문과 유사한 문서/규정을 Vector DB에서 검색하여 **프롬프트에 제공** |
| ③ | **Chat Memory (대화 맥락 유지)** | 이전 대화 흐름을 기억하여 **맥락에 맞는 연속된 답변** 제공 |
| ④ | **Tool Calling (기능 연동)** | LLM이 스스로 판단하여 조회/작동시킬 수 있는 **Java 메서드/서비스 연동** |
| ⑤ | **Structured Output (구조화된 응답)** | 최종 결과를 **프론트엔드나 타 시스템이 소비할 수 있는 JSON 형태**로 응답 |

**제출 체크리스트**
- [ ] ① 도메인 문서를 `TokenTextSplitter`로 chunking하여 PgVector 적재 (ETL 파이프라인)
- [ ] ② `QuestionAnswerAdvisor` 또는 `RetrievalAugmentationAdvisor` 적용
- [ ] ③ `MessageChatMemoryAdvisor` + `ChatMemory.CONVERSATION_ID` (세션별 대화)
- [ ] ④ `@Tool` 붙은 도메인 메서드 최소 1개 + `.tools(...)` 등록
- [ ] ⑤ `record` DTO 정의 + `.entity(AgentResponse.class)` 반환
- [ ] ⑥ System Prompt로 Agent 페르소나 + 판단 규칙 정의
- [ ] ⑦ "도구로 확인할 수 없는 내용은 추측하지 말 것" 가드레일 문장 포함

**가이드 문서 (p348)**: `01.training code/13.practice-guide/spring-ai-agent-practice-guide.md`

## 6-3. 참고 — 설계 템플릿

과제 시작 전에 아래를 먼저 채워보면 구현이 훨씬 수월합니다.

```plain text
[ 도메인 ]          예) 사내 IT 헬프데스크

[ ① Vector DB에 넣을 문서 ]
   - 무엇을?        예) 사내 IT 규정 PDF, FAQ 문서
   - Reader는?     예) PagePdfDocumentReader
   - chunkSize?    예) 800 토큰 (기본값)

[ ② RAG Advisor ]
   - QuestionAnswerAdvisor로 충분한가?
   - 아니면 RewriteQuery/Compression이 필요한가? (모호한 후속 질문이 많다면 필요)
   - similarityThreshold?  예) 0.7

[ ③ ChatMemory ]
   - Repository?    예) InMemory (로컬 데모) / Redis (배포 시)
   - maxMessages?   예) 20 (10턴)

[ ④ Tool ]
   - Tool 이름 / description / 파라미터
     예) checkTicketStatus / "티켓 번호로 처리 현황을 조회합니다" / ticketId(String)

[ ⑤ Structured Output ]
   record AgentResponse(String answer, List<String> sources, String nextAction) {}

[ ⑥ System Prompt ]
   당신은 ○○ 전문 에이전트입니다.
   1) 먼저 검색된 문서를 확인하고
   2) 필요하면 Tool을 호출한 뒤
   3) 최종 결과를 JSON으로 응답하세요.
   도구와 문서로 확인할 수 없는 내용은 추측하지 말고, 모른다고 답하세요.
```

---

## ★ 전체 흐름 한 장 요약

```plain text
╔══════════════════════════════════════════════════════════════════════════════╗
║                    Spring AI 3일차 — MCP와 Agent                              ║
╚══════════════════════════════════════════════════════════════════════════════╝

═══ MCP: Tool을 프로세스 밖으로 꺼내는 표준 ══════════════════════════════════

  2일차 Tool Calling            →         3일차 MCP
  ┌───────────────────┐                   ┌─────────────┐      ┌─────────────┐
  │ App               │                   │ Host+Client │◄────►│ MCP Server  │
  │  ├ ChatClient     │                   │  ChatClient │JSON- │  @McpTool   │
  │  └ @Tool 메서드    │                   │  MCP Client │ RPC  │  @McpToolParam│
  └───────────────────┘                   └─────────────┘      └─────────────┘
   .tools(obj)                             .toolCallbacks(provider.getToolCallbacks())


 ── 3역할 ──────────────────────────────────────────────────────────
   Host   : 자연어 요청 이해 (Chat App, Code Assistant)
   Client : MCP 통신 담당   (tools/list, tools/call)
   Server : 외부 시스템을 Tool/Resource로 제공


 ── 메시지 계층 ─────────────────────────────────────────────────────
   [MCP Session]  Tools/Resources/Prompts, Capability 협상, JSON Schema 자동 생성
   [JSON-RPC 2.0] { jsonrpc, id, method: "tools/list"|"tools/call", params }
   [Transport]    STDIO  |  Streamable HTTP (Stateful / Stateless)


 ── Transport 선택 ──────────────────────────────────────────────────
                 STDIO              Stateful HTTP        Stateless HTTP
   위치          같은 PC            원격                  원격
   실행          Client가 Server를   Server 먼저 기동      Server 먼저 기동
                 프로세스로 띄움
   세션          연결 유지          Mcp-Session-Id 헤더    없음
   서버 Push     N/A               가능 (GET /mcp SSE)   불가
   확장성        단일 PC            수평 확장 어려움       수평 확장 쉬움
   설정 주의     stdout 오염 금지!   —                    —
                 (banner/logging/
                  web-app-type)


═══ Agent: 새로운 기술이 아니라 "조립" ═══════════════════════════════════════

   Agent = System Prompt (역할·판단 규칙)
         + ChatMemory     (기억)      ← 2일차
         + RAG Advisor    (지식)      ← 2일차
         + Tool / MCP     (행동)      ← 2·3일차
         + Structured Output (계약)   ← 1일차
         ─────────────────────────────
         전부 하나의 ChatClient.Builder에 조립

   chatClientBuilder
       .defaultSystem("당신은 ○○ 전문 에이전트입니다…")
       .defaultAdvisors(MessageChatMemoryAdvisor…, QuestionAnswerAdvisor…)
       .defaultTools("checkInventoryTool", "applyCouponTool")
       .build();
   → .call().entity(AgentResponse.class)


   Single Agent           Multi-Agent Orchestration
   ┌──────────┐           ┌───────────────┐
   │ Agent A  │           │ Orchestrator  │
   │ (Tool 3개)│           │  ↓ Tool로 위임 │
   └──────────┘           │ ┌───┐   ┌───┐ │
   ┌──────────┐           │ │ A │   │ B │ │  ← 하위 Agent를
   │ Agent B  │           │ └───┘   └───┘ │     @Tool로 감쌌을 뿐
   └──────────┘           └───────────────┘
```

---

## ★ 시험/면접 대비 핵심 문답

| # | 질문 | 답 |
|---|---|---|
| 1 | MCP의 정의는? | 자연어로 동작하는 AI와 **구조화된 인터페이스로 동작하는 시스템** 사이를 연결하는 **표준 중간 계층**. LLM을 "답변하는 모델"에서 "작업을 수행하는 AI Agent"로 확장하기 위한 표준 프로토콜 |
| 2 | Tool Calling과 MCP의 차이는? | Tool Calling은 **같은 앱 안의 Java 메서드**를 부른다. MCP는 그 Tool을 **다른 프로세스/서버로 분리**하고 **JSON-RPC 표준**으로 통신하여 여러 AI 클라이언트가 공유할 수 있게 한다 |
| 3 | MCP의 3가지 역할은? | **Host**(자연어 요청 이해) · **Client**(MCP 통신 담당) · **Server**(외부 시스템을 Tool/Resource로 제공) |
| 4 | MCP Client의 4가지 역할은? | ① `tools/list`로 도구 목록 로딩 ② `tools/call`로 도구 실행 ③ LLM 필요 시 자동 오케스트레이션 ④ STDIO/SSE/Streamable HTTP 전송 방식 제공 |
| 5 | MCP 작동 6단계는? | ① `tools/list` 조회 ② 사용자 Prompt 전달 ③ Prompt+ToolList를 LLM에 전달 → Tool 선택 ④ `tools/call`로 실행 요청 ⑤ Tool 응답+Prompt를 다시 LLM에 → 최종 응답 생성 ⑥ Host가 사용자에게 전달 |
| 6 | MCP 3계층은? | **MCP Session**(Tools/Resources/Prompts, Capability 협상, JSON Schema 자동 생성) → **JSON-RPC**(메시지 포맷) → **Transport**(STDIO/HTTP) |
| 7 | Capability Negotiation이란? | 초기화 시 Client가 지원 버전·정보·Capability를 보내고, Server가 동의하는 버전·Capability를 반환하는 **협상 과정** |
| 8 | JSON-RPC의 필수 필드 3개는? | `jsonrpc`("2.0") · `method`(`tools/list`, `tools/call`) · `id`. 요청 시 `params` 추가 |
| 9 | JSON-RPC와 Transport의 관계는? | JSON-RPC는 **메시지 포맷**, STDIO/HTTP는 **운반 수단**. 별개의 계층이다 |
| 10 | MCP 호출 시퀀스에서 LLM은 몇 번 호출되나? | **2번.** ① Tool 선택 ② 결과를 자연어로 정리. 2일차 Tool Calling과 동일 |
| 11 | `tools/list`와 `tools/call`은 각각 언제 호출되나? | `tools/list`는 보통 **앱 시작 시 1번**, `tools/call`은 **요청마다** |
| 12 | STDIO 방식의 특징 4가지는? | HTTP 서버 불필요 / 네트워크 포트 불필요 / 표준 입력 읽고 표준 출력으로 쓰기 / 데이터는 반드시 **JSON-RPC 2.0 메시지** |
| 13 | STDIO 모드에서 반드시 막아야 하는 3가지는? | ① `spring.main.web-application-type: none` ② `banner-mode: off/log` ③ `logging.pattern.console: ""` — **stdout이 MCP JSON-RPC 전용 채널**이라 오염되면 통신이 깨진다 |
| 14 | STDIO에서 MCP Server는 누가 실행하나? | **MCP Client가 `command`/`args`로 직접 프로세스를 띄운다.** 미리 실행해 둘 필요 없이 jar만 빌드하면 된다 |
| 15 | `@Tool`과 `@McpTool`의 차이는? | `@Tool`/`@ToolParam`은 **앱 내부 Tool**, `@McpTool`/`@McpToolParam`은 **MCP Server의 Tool**. `@Tool`도 쓸 수 있지만 `MethodToolCallbackProvider`로 **수동 등록**해야 한다 |
| 16 | `annotation-scanner.enabled`의 역할은? | `@McpTool`이 선언된 자바 메서드를 **자동으로 로딩**할지 결정. default는 `true` |
| 17 | `type: SYNC`와 `ASYNC`의 차이는? | MCP Server를 **MVC(SYNC)** 로 띄울지 **WebFlux(ASYNC)** 로 띄울지 결정 |
| 18 | SSE는 왜 deprecated 되었나? | **MCP 2025-03-26 버전 이후 SSE 통신 방식이 Streamable HTTP로 통합**되었다 |
| 19 | Stateful과 Stateless Streamable HTTP의 결정적 차이 3가지는? | ① **세션**: `Mcp-Session-Id` 헤더 유무 ② **서버 Push**: Stateful만 `GET /mcp` SSE로 가능 ③ **확장성**: Stateless가 수평 확장 유리 |
| 20 | `Mcp-Session-Id`는 누가 언제 발급하나? | **서버가 initialize 응답 시** 발급하며, 이후 클라이언트는 모든 요청 헤더에 포함한다 |
| 21 | 같은 `POST /mcp`인데 응답 Content-Type이 두 가지인 이유는? | 짧은 응답은 `application/json`, 긴 작업은 `text/event-stream`으로 chunk 전송. 이게 **"Streamable"** HTTP라는 이름의 이유 |
| 22 | chunk로 보내는 이유 3가지는? | ① 실시간 출력 ② **타임아웃 방지**(HTTP 연결 유지) ③ **Tool 실행 상태·진행률** 실시간 전달 |
| 23 | STDIO 클라이언트 설정과 HTTP 클라이언트 설정의 차이는? | STDIO는 `command`/`args`(프로세스 실행), HTTP는 `url`/`endpoint`(네트워크 주소). HTTP는 **Server를 미리 띄워야 한다** |
| 24 | Stateful/Stateless에서 클라이언트 설정은 다른가? | **동일하다.** 차이는 **서버 프로필(`protocol: STREAMABLE` vs `STATELESS`)에서 결정**된다 |
| 25 | `.tools(obj)`와 `.toolCallbacks(...)`의 차이는? | `.tools(obj)` — 로컬 `@Tool` 객체 등록. `.toolCallbacks(mcpToolCallbackProvider.getToolCallbacks())` — **원격 MCP Server의 Tool** 등록 |
| 26 | Agent의 4대 요소는? | **Goal**(목표) · **Reasoning/Planning**(추론·계획) · **Tool Use**(도구 사용) · **Observation**(결과 관찰 후 반복) |
| 27 | Agent를 구성하는 3가지 축은? | **LLM**(판단/추론) · **Memory**(기억) · **Tools**(행동) |
| 28 | Agent는 결국 무엇인가? | **복잡한 프레임워크가 아니라** "LLM에게 목표와 Tool을 주고, LLM이 스스로 판단해 Tool을 실행하고 결과를 종합하게 만드는 **패턴 그 자체**" |
| 29 | Agent 실행 구조 3 Step은? | ① **System Prompt**로 페르소나·판단 규칙 정의 ② RAG+Memory+Tool을 **ChatClient에 바인딩(Orchestration)** ③ **Structured Output**으로 규격화된 객체 반환 |
| 30 | Multi-Agent Orchestration의 핵심 트릭은? | **하위 Agent를 `@Tool`로 감싼다.** `delegateToFileManager` 같은 평범한 Tool 메서드 안에서 하위 Agent의 chatClient를 호출할 뿐. Orchestrator 입장에서 하위 Agent는 그냥 Tool이다 |
| 31 | Agent System Prompt에 반드시 넣어야 할 가드레일 문장은? | **"도구로 확인할 수 없는 내용은 추측하지 말고, 모른다고 답하세요."** — 환각 방지의 핵심 |
| 32 | 종합 실습의 필수 기술 요소 5가지는? | ① Embedding+Vector DB(PgVector, Chunking) ② RAG ③ Chat Memory ④ Tool Calling ⑤ Structured Output |

**🧩 Quiz**

<details>
<summary>Q1. STDIO MCP Server를 만들었는데 클라이언트가 "JSON parse error"를 뱉는다. 가장 흔한 원인은?</summary>

- [x] **stdout 오염.** Spring Boot 배너, 콘솔 로그, `System.out.println()` 중 하나가 stdout으로 나가서 JSON-RPC 메시지 스트림을 깨뜨렸다.
- 확인할 것:
  - `spring.main.web-application-type: none`
  - `spring.main.banner-mode: off` (또는 `log`)
  - `logging.pattern.console: ""`
  - 코드 안의 `System.out.println()` 전부 제거 → `log.info()`로 변경
</details>

<details>
<summary>Q2. Streamable HTTP MCP Client를 실행했는데 Connection refused가 난다. STDIO에서는 잘 됐는데?</summary>

- [x] **HTTP 방식은 MCP Server를 먼저 띄워야 한다.** STDIO는 Client가 `command`/`args`로 Server 프로세스를 직접 실행해 주지만, HTTP는 그렇지 않다.
- 순서: ① Server 실행(`--spring.profiles.active=stateful-http`, 8081) → ② Client 실행
</details>

<details>
<summary>Q3. 서버가 클라이언트에게 진행률(progress)을 실시간으로 밀어줘야 한다. Stateful과 Stateless 중 무엇을 골라야 하나?</summary>

- [x] **Stateful.** `GET /mcp` SSE 채널로 서버 주도 Push가 가능하다. Stateless는 **서버 주도 Push가 불가능**하다.
- 단, Stateful은 `Mcp-Session-Id` 세션 상태 때문에 **수평 확장이 어렵다**는 트레이드오프가 있다.
</details>

<details>
<summary>Q4. Multi-Agent에서 Orchestrator가 하위 Agent를 호출하는 메커니즘은 무엇인가?</summary>

- [x] **Tool Calling.** 새로운 메커니즘이 아니다.
- `AgentDelegationTools`의 `delegateToFileManager`, `delegateToWeatherGuide`는 평범한 `@Tool` 메서드이고, 그 안에서 하위 Agent의 `chatClient.prompt()...call()`을 호출한다.
- 즉 **Orchestrator 입장에서 하위 Agent는 그냥 하나의 Tool**이다.
</details>

<details>
<summary>Q5. 기존 CRUD Spring Boot 앱을 MCP Server로 바꾸려면 Service 계층을 고쳐야 하나?</summary>

- [x] **고칠 필요 없다.**
- ① `pom.xml`에 `spring-ai-starter-mcp-server-webmvc` 추가
- ② `tools` 패키지를 새로 만들고, 그 안의 클래스가 **기존 Service를 주입받아** `@McpTool` 메서드로 감싼다
- ③ `application.yaml`에 MCP Server 설정 추가
- 이것이 1일차 p5에서 말한 **"기존 Service·Repository를 AI Tool로 재사용"** 의 실체다.
</details>

---

## ⚠️ 원문 용어 검증 노트

### 정정 (원문 오기)

| # | 슬라이드 | 원문 | 정정 | 비고 |
|---|---|---|---|---|
| 1 | p286 | "MCP Session **Middle**" | "MCP Session (**Middle Layer**)" | 계층 이름 표기 불완전 |
| 2 | p287 | "서버가 사용할 MCP **Provocol** Version" | "**Protocol**" | 오타 |
| 3 | p292 | "4. **sprin** AI → LLM 사용자 질문" | "**Spring** AI" | 오타 (p264에서도 반복) |
| 4 | p298 | "SSE (deprecated) • POST /sse endpoint" | 설명 컬럼과 사용 사례 컬럼이 어긋남 | 표 셀 정렬 오류 |
| 5 | p303 | `"protocolVersion": " 2025-03-26"` | `"2025-03-26"` | **값 앞에 공백** — JSON 파싱 시 문제 가능 |
| 6 | p307 | "annotations scanner.enabled true" | `annotation-scanner.enabled: true` | **`annotations` → `annotation`, 하이픈 표기** |
| 7 | p307, p327 | "type SYNC ASYNC: MCP Server 를 MVC or WebFlux 결정" | `type: SYNC` 또는 `ASYNC` (구분자 명시) | 구분자 누락 |
| 8 | p310 | "STDIO MCP Client를 구성하기 위한 application stdio.yaml" (p328 제목도 동일) | p328은 **Streamable** 설정인데 제목이 "STDIO" | **슬라이드 제목 복사 실수** |
| 9 | p311 | `logging.pattern.console:` (값 없음) | `console: ""` | 빈 문자열을 명시해야 함 |
| 10 | p312 | "**WeattherTools**.java" | `WeatherTools.java` | 오타 |
| 11 | p313, p317, p330, p332 | `mvn clean install -DskipTest` / `java –jar` | `-DskipTests` / `java -jar` | ① 속성명 복수형 ② **en-dash(`–`) → hyphen(`-`)** |
| 12 | p314 | "spring.ai.mcp.client … s**(잘림)**" | 슬라이드 텍스트 박스 잘림 | `stdio.connections` 부분이 잘려 있음 |
| 13 | p319 | 제목이 "HTTP"인데 다이어그램 라벨은 "**동일 PC 내**" | HTTP는 **원격** 통신 방식 | p301(STDIO) 다이어그램 라벨을 복사한 것으로 보임 |
| 14 | p320 | "**Listchanged** 등 이벤트" | `listChanged` | camelCase |
| 15 | p329 | 제목 "실습 Streamable HTTP 를 위한 MCP Server **1/2**" (p330도 1/2) | p330은 **2/2** | 페이지 번호 오기 |
| 16 | p331 | 주석 "`--spring.profiles.active=streamable-http` 로 기동했을 때" | 실제 실행 명령(p330, p332)은 `stateful-http` | **프로필 이름 불일치 — 그대로 따라 하면 실행 실패** |
| 17 | p335 | "STDIO 버전이며, Claude Desktop or 01-1.mcp client와 연동" | 실습 폴더는 `10-1.mcp-client` | 폴더명 표기 오류 |
| 18 | p340 | `new MessageChatMemoryAdvisor(chatMemory)` | `MessageChatMemoryAdvisor.builder(chatMemory).build()` | Spring AI 2.x에서 **생성자 직접 호출은 deprecated**. p231/p235는 builder를 쓰고 있어 슬라이드 간 불일치 |
| 19 | p340 | `.defaultTools("checkInventoryTool", "applyCouponTool")` | 문자열 Bean 이름 방식 | 앞서 배운 방식(`.tools(objectInstance)`)과 다르다. **둘 다 유효**하나 원문에 설명이 없음 |
| 20 | p342 | "Single Agent" 제목인데 p344도 "실습 Single Agent" | p344는 **Multi Agent** | 슬라이드 제목 복사 실수 |
| 21 | p344 | `AgentDelegationTools`가 어떻게 하위 Agent를 부르는지 코드 없음 | 정리본에 메커니즘 설명 추가 | 아래 보완 항목 참조 |
| 22 | p348 | `spring ai agent practice guide.md` | `spring-ai-agent-practice-guide.md` | 공백은 하이픈으로 추정 |

### 보완 (원문에 없어 추가한 설명)

| # | 항목 | 보완 내용 |
|---|---|---|
| 1 | **Host와 Client의 관계** | p282는 Host/Client/Server를 나란히 그려 별개처럼 보이지만, **실무에서 Host와 Client는 같은 애플리케이션 안에 있다.** `spring-ai-starter-mcp-client`를 넣은 우리 Spring Boot 앱이 Host이자 Client다 |
| 2 | **stdout 오염이 왜 치명적인가** | p308이 설정만 나열하고 이유를 설명하지 않는다. **stdout이 곧 JSON-RPC 채널**이므로, 로그 한 줄이 섞이면 클라이언트의 JSON 파서가 깨져 통신 자체가 죽는다. STDIO 디버깅의 90%가 이 문제다 |
| 3 | **STDIO에서 Server 실행 주체** | p310의 `command`/`args`가 의미하는 바 — **MCP Client가 Server 프로세스를 직접 spawn한다.** 그래서 Server를 별도로 띄울 필요가 없다. HTTP 방식과의 가장 큰 운영상 차이 |
| 4 | **Multi-Agent의 실제 구현** | p344에 `AgentDelegationTools`만 그려져 있고 코드가 없다. 실제로는 `@Tool` 메서드 안에서 하위 Agent의 `chatClient`를 호출하는 **평범한 Tool Calling**이다. "Agent를 Tool로 감싼다"가 핵심 |
| 5 | **Human In the Loop** | p337에 단어만 등장하고 설명이 없다. **완전 자율 Agent는 위험하므로**, 삭제·결제·배포 같은 비가역 행동 전에는 사람의 승인을 받는 설계가 실무 표준이다 |
| 6 | **환각 방지 가드레일** | p342의 두 System Prompt 마지막 문장 **"도구로 확인할 수 없는 내용은 추측하지 말고, 모른다고 답하세요"** 가 사실상 가장 중요한 줄이다. 원문은 강조하지 않음 |
| 7 | **외부 MCP Server 등록의 보안 함의** | p315의 `npx @swartdraak/docker-mcp-server` 처럼 외부 패키지를 MCP Server로 등록하는 것은 **그 패키지에 로컬 Docker 제어 권한을 주는 것**이다. 신뢰할 수 있는 소스인지 반드시 확인할 것 |
| 8 | **`Content-Length` 헤더 (p304~p305)** | STDIO는 바이트 스트림이라 **메시지 경계를 알 방법이 없어** `Content-Length` 헤더로 각 JSON-RPC 메시지 길이를 알려준다. HTTP 방식에는 필요 없다 |
| 9 | **Resources / Prompts** | p286에서 MCP Session이 "Tools, **Resources**, **Prompts**"를 관리한다고 하지만, 이 과정은 **Tools만** 다룬다. Resources(읽기 전용 데이터)와 Prompts(재사용 프롬프트 템플릿)는 MCP 스펙의 나머지 두 축이다 |
| 10 | **MCP 프로토콜 버전** | `2025-03-26`은 SSE→Streamable HTTP 통합이 일어난 버전이다. 클라이언트/서버 버전이 다르면 initialize 단계의 **Capability Negotiation**에서 협상된다 |

---

> 📌 **이전 문서**: [2일차 — RAG · ChatMemory · Tool Calling](./02_SpringAI_Day2_RAG와_Tool_정리.md)
> 📌 **처음부터**: [1일차 — Spring AI 기초](./01_SpringAI_Day1_기초_정리.md)
