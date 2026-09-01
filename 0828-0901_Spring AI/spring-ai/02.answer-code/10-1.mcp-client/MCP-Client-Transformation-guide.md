# @Tool 프로젝트를 MCP Client로 전환하기

이 문서는 09.tools(=@Tool 실습 코드)를 기반으로 한 이 프로젝트를 Spring AI MCP Client로 전환하면서
실제로 추가/변경/제거된 항목을 정리한다. 도구 구현 자체는 `10-2.mcp-server`로 옮기고, 이 프로젝트는
Streamable HTTP로 그 서버에 접속해 도구를 원격 호출하는 역할만 담당한다. 채팅 UI(Thymeleaf 화면)는
기존 방식 그대로 유지한다.


## 1. 추가된 것

### 1-1. pom.xml

```xml
<dependency>
    <groupId>org.springframework.ai</groupId>
    <artifactId>spring-ai-starter-mcp-client</artifactId>
</dependency>
```

- MCP Client 자동구성을 활성화하는 스타터다. STDIO/SSE/Streamable-HTTP 커넥션을 모두 지원한다.
- 이 프로젝트는 리액티브 서버가 아니라 Thymeleaf 기반 동기(MVC) 채팅 앱이므로, WebFlux 기반의
  `spring-ai-starter-mcp-client-webflux` 대신 표준(JDK HttpClient 기반) 스타터를 사용했다.

### 1-2. application.yml

```yaml
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

- `connections.tool-server`는 임의로 붙인 커넥션 이름이며, `10-2.mcp-server`가 8081 포트에서
  `/mcp` 경로로 노출한 Streamable HTTP 엔드포인트를 가리킨다.
- `spring.ai.mcp.client.toolcallback.enabled`는 기본값(true)이라 별도 설정 없이도
  `SyncMcpToolCallbackProvider` 빈이 자동 생성된다.


## 2. 변경된 것

### 2-1. ChatController

```java
// 변경 전
@Autowired
private DateTimeTools dateTimeTools;
@Autowired
private FileSystemTool fileSystemTool;
@Autowired
private WeatherTools weatherTools;
...
.tools(dateTimeTools, fileSystemTool, weatherTools)

// 변경 후
private final SyncMcpToolCallbackProvider mcpToolCallbackProvider;
...
.tools(mcpToolCallbackProvider.getToolCallbacks())
```

- 로컬 `@Tool` 빈을 직접 주입해서 넘기던 방식에서, MCP Client가 원격 서버로부터 조회해온
  도구 목록(`SyncMcpToolCallbackProvider#getToolCallbacks()`)을 넘기는 방식으로 바뀌었다.
- 애플리케이션 입장에서 `ChatClient.prompt().tools(...)`를 호출하는 코드 형태 자체는 동일하다.
  차이는 도구 목록의 출처가 "로컬 빈"이냐 "원격 MCP 서버"냐 뿐이다.


## 3. 제거된 것

- `tools` 패키지 전체(`DateTimeTools.java`, `FileSystemTool.java`, `WeatherTools.java`)를 삭제했다.
  도구 구현(비즈니스 로직)이 `10-2.mcp-server`로 이동했으므로, 같은 로직을 이 프로젝트에 중복으로
  둘 필요가 없다.
- `application.yml`의 `weather.api.*` 설정을 제거했다. 날씨 API 키/URL은 이제 도구를 실제로
  실행하는 `10-2.mcp-server` 쪽에서만 필요하다.
- UI(HomeController, WebConfig, templates, static)와 채팅 모델(OpenAI 등) 설정은
  요구사항대로 기존 방식을 그대로 유지했다.


## 4. 요청 흐름 비교

- 전환 전: 브라우저 → ChatController → ChatClient(로컬 @Tool 메서드 직접 호출) → OpenAI
- 전환 후: 브라우저 → ChatController(8080) → ChatClient
  → (필요 시) MCP Client가 Streamable HTTP로 10-2.mcp-server(8081)의 `/mcp` 호출 → 도구 실행 결과 반환
  → OpenAI로 최종 응답 생성


## 5. 동작 확인

1. `10-2.mcp-server`를 먼저 8081 포트로 기동한다.
2. 이 프로젝트(`10-1.mcp-client`)를 8080 포트로 기동한다. 기동 로그에서 MCP 커넥션(`tool-server`)이
   정상 연결되었는지 확인한다.
3. 브라우저에서 `http://localhost:8080` 채팅 화면으로 "서울 날씨 알려줘", "현재 시간 알려줘" 같은
   질문을 하면, ChatClient가 MCP Client를 통해 원격 도구를 호출해 응답한다.
