# @Tool 프로젝트를 MCP Server로 전환하기

이 문서는 09.tools(=@Tool 실습 코드)를 기반으로 한 이 프로젝트를 Spring AI MCP Server로 전환하면서
실제로 추가/변경/제거된 항목을 정리한다. 목표는 "무엇을 바꿔야 MCP Server가 되는지"를 최소 변경으로
직관적으로 보여주는 것이다.

전송 방식은 Streamable HTTP(POST /mcp)를 사용한다. Spring Boot 4.1 / Spring AI 2.0.0 기준이다.


## 1. 추가된 것

### 1-1. pom.xml

```xml
<dependency>
    <groupId>org.springframework.ai</groupId>
    <artifactId>spring-ai-starter-mcp-server-webmvc</artifactId>
</dependency>
```

- MVC(Tomcat) 기반으로 MCP 프로토콜 엔드포인트를 자동 구성해주는 스타터다.
- 컨트롤러를 직접 작성할 필요 없이 `POST /mcp` 엔드포인트가 자동으로 열린다.
- 기존 spring-boot-starter-web, spring-boot-starter-webflux(WeatherTools의 WebClient용)는 그대로 둔다.

### 1-2. application.yml

```yaml
spring:
  ai:
    mcp:
      server:
        name: my-spring-ai-mcp-server
        version: 1.0.0
        protocol: STREAMABLE
        type: SYNC
```

- `protocol: STREAMABLE` 로 설정해야 최신 MCP 스펙인 Streamable HTTP 전송을 사용한다. (SSE는 deprecated)
- `type: SYNC` 는 동기 방식 서버를 의미한다. `@McpTool`이 붙은 동기 메서드만 등록된다.
- 엔드포인트 경로는 기본값 `/mcp` 를 그대로 사용한다 (커스터마이즈하려면
  `spring.ai.mcp.server.streamable-http.mcp-endpoint` 사용).
- 10-1.mcp-client(포트 8080)와 동시에 기동해서 테스트할 수 있도록 서버 포트를 8081로 변경했다.


## 2. 변경된 것 (@Tool → @McpTool)

`tools` 패키지의 위치와 클래스 구조는 그대로 두고, 애노테이션만 교체했다.

| 기존 | 전환 후 | 비고 |
|---|---|---|
| `org.springframework.ai.tool.annotation.Tool` | `org.springframework.ai.mcp.annotation.McpTool` | 메서드 단위 도구 선언 |
| `org.springframework.ai.tool.annotation.ToolParam` | `org.springframework.ai.mcp.annotation.McpToolParam` | 파라미터 단위 설명/필수 여부 |

예) `DateTimeTools.java`

```java
// 변경 전
@Tool(description = "사용자의 시간대에 맞는 현재 날짜와 시간 정보를 제공합니다.")
public String getCurrentDateTime() { ... }

// 변경 후
@McpTool(description = "사용자의 시간대에 맞는 현재 날짜와 시간 정보를 제공합니다.")
public String getCurrentDateTime() { ... }
```

예) `FileSystemTool.java`, `WeatherTools.java`

```java
// 변경 전
@Tool(description = "...")
public String createFile(
        @ToolParam(description = "생성할 파일명", required = true) String fileName, ...)

// 변경 후
@McpTool(description = "...")
public String createFile(
        @McpToolParam(description = "생성할 파일명", required = true) String fileName, ...)
```

세 클래스 모두 `@Component`는 그대로 유지한다. `spring.ai.mcp.server.annotation-scanner.enabled`
(기본값 true)가 스프링 빈 중에서 `@McpTool`이 붙은 메서드를 스캔해 자동으로 MCP 도구로 등록해준다.
별도의 `ToolCallbackProvider` 빈을 직접 만들 필요가 없다.

### @Tool과 @McpTool의 차이

- `@Tool` (spring-ai-model 모듈): `ChatClient.prompt().tools(...)` 처럼 애플리케이션 내부에서
  같은 JVM 안의 ChatModel에게 직접 바인딩하는 "로컬 도구"용 애노테이션이다. MCP 프로토콜과는 무관하다.
- `@McpTool` (spring-ai-mcp-annotations 모듈): MCP Server Boot Starter가 스캔해서
  MCP 프로토콜(JSON-RPC 기반 tools/list, tools/call)로 원격 클라이언트에게 노출하는 도구용 애노테이션이다.
  같은 프로세스 안에서 로컬로는 호출되지 않는다.
- 즉 `@Tool`은 "이 ChatModel이 쓸 도구", `@McpTool`은 "이 서버에 접속한 모든 MCP 클라이언트가 쓸 도구"라는
  용도 차이다. 두 애노테이션은 동시에 붙일 수도 있지만(이중 노출), 이 프로젝트는 학습 목적상 완전히
  `@McpTool`로 교체해서 차이를 명확히 드러냈다.
- `@ToolParam` / `@McpToolParam`도 동일한 관계다. `description`, `required` 속성 구성은 동일하지만
  각각 로컬 도구 스키마 생성용, MCP 도구 스키마 생성용으로 별도로 동작한다.


## 3. 제거된 것

- `ChatController`의 `dateTimeTools`, `fileSystemTool`, `weatherTools` `@Autowired` 필드와
  `.tools(dateTimeTools, fileSystemTool, weatherTools)` 호출부를 우선 제거했다.
  tools 패키지가 `@McpTool`로 바뀌면서 더 이상 `@Tool` 메서드가 존재하지 않기 때문에, 기존 방식으로는
  로컬 tool-calling이 불가능해졌기 때문이다. (도구는 이제 MCP Client 쪽에서 원격으로 호출한다.
  `10-1.mcp-client` 참고)
- 이어서 `ChatController`, `HomeController`, `WebConfig`, `templates/index.html`,
  `static/css/style.css`, `static/js/chat.js`를 모두 삭제했다. `.tools(...)` 호출이 빠진 `ChatController`는
  일반 대화만 하는 엔드포인트로 남아 있었는데, 이 프로젝트의 목적(도구를 MCP 프로토콜로 노출)과 무관해져서
  더 이상 유지할 이유가 없었다. `HomeController`가 사라지면 그 화면을 그리던 `templates/index.html`,
  `static/css`, `static/js`, 그리고 그 정적 리소스 캐시 설정을 담당하던 `WebConfig`도 함께 참조하는 곳이
  없어져 같이 제거했다. `application.yml`의 `spring.thymeleaf.cache`, `spring.web.resources.*` 설정도
  같은 이유로 제거했다. 채팅 UI는 이제 `10-1.mcp-client`에만 존재한다.
- 이 결과 `spring-boot-starter-thymeleaf`와 OpenAI/Anthropic/Gemini/Ollama 모델 스타터,
  RAG/vector-store/postgres 의존성은 이 프로젝트의 어떤 코드에서도 더 이상 실질적으로 사용되지 않는다.
  다만 pom.xml 자체는 재사용을 고려해 그대로 유지했다 (필요 없다고 판단되면 추가로 정리할 수 있다).


## 4. 동작 확인

서버를 8081 포트로 기동한 뒤, MCP Inspector나 curl로 Streamable HTTP 엔드포인트를 직접 두드려 볼 수 있다.

```bash
curl -i http://localhost:8081/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

`getCurrentDateTime`, `listFiles`, `createFile`, `readTextFile`, `getCurrentWeather` 5개 도구가
목록에 나타나면 전환이 정상적으로 된 것이다.
