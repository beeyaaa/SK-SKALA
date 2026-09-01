# 작업 중 추가로 판단/추론한 사항

Agent.md의 지시만으로는 명확하지 않아서 스스로 추론했거나, 사용자에게 확인 후 결정한 사항을 정리한다.


## 1. 사용자에게 확인받은 결정 사항

- `mcp-client 디렉토리`는 새로 만들지 않고, 이미 존재하던 상위 폴더의 별도 Maven 프로젝트
  `02.answer-code/10-1.mcp-client`(현재 이 프로젝트와 동일한 @Tool 베이스 코드가 미리 복사되어 있었음,
  git 미추적 상태)를 실제 MCP Client로 전환했다.
- `10-2.mcp-server`(이 프로젝트)는 처음에는 채팅 UI(HomeController, WebConfig, templates, static)와
  무관한 의존성(OpenAI/Anthropic/Gemini/Ollama 모델 스타터, RAG, vector-store, postgresql)을
  삭제하지 않고 그대로 유지하기로 했었다. (향후 재사용을 고려한 사용자 선택)
- 위 결정 때문에 tools 패키지를 `@Tool → @McpTool`로 완전히 교체하면 기존 `ChatController`의
  `.tools(dateTimeTools, fileSystemTool, weatherTools)` 호출이 더는 동작하지 않는 충돌이 생겨,
  이 부분도 확인 후 "@McpTool로 완전 교체하고, ChatController의 해당 호출부만 제거"하는 쪽으로 정리했다.
- 이후 사용자가 다시 "controller 패키지가 정말 필요한지" 물어와서, `ChatController`(이미 도구 호출
  기능이 빠진 상태)와 `HomeController`가 이 프로젝트(순수 MCP Tool Server)의 목적과 무관하다고 판단해
  삭제하는 쪽으로 결론이 바뀌었다. 이때 controller 패키지만 지울지, 거기에 딸린 templates/static/WebConfig도
  같이 지울지 다시 확인했고, "모두 삭제"로 정리했다. (자세한 내용은
  [MCP-Transformation-guide.md](MCP-Transformation-guide.md) 3절 참고)


## 2. 스스로 추론/결정한 사항

- **애노테이션 패키지**: Agent.md에는 `@McpTool`, `@McpToolParam`이라고만 적혀 있었는데, 실제 Maven
  아티팩트(`spring-ai-mcp-annotations:2.0.0`)를 열어 확인한 결과 패키지는
  `org.springframework.ai.mcp.annotation` 이다. (`org.springframework.ai.mcp.server.annotation`이
  아님 - 처음에 이 경로로 작성했다가 컴파일 에러가 나서 jar 내부를 직접 확인해 바로잡았다.)
- **포트 분리**: `10-1.mcp-client`와 `10-2.mcp-server`를 동시에 띄워야 실제로 동작을 확인할 수 있는데,
  두 프로젝트 모두 기존 `server.port: 8080`을 쓰고 있어 충돌한다. 채팅 UI가 있는 클라이언트를 기존대로
  8080에 두고, MCP Server(이 프로젝트)의 포트를 8081로 변경했다.
- **기동 순서**: MCP Client는 기동 시점에 설정된 Streamable HTTP 커넥션(`http://localhost:8081/mcp`)에
  연결을 시도한다. 따라서 실습 시 `10-2.mcp-server`를 먼저 켠 뒤 `10-1.mcp-client`를 켜야 한다.
  순서가 바뀌면 클라이언트 기동이 실패하거나 도구 목록이 비어 있을 수 있다.
- **WebMVC 스타터 선택**: 원래 pom.xml 주석에 "서버는 Tomcat/MVC 유지"라고 명시돼 있었고, 실제로
  `spring-boot-starter-web` 기반이었기 때문에 MCP Server도 WebFlux가 아닌
  `spring-ai-starter-mcp-server-webmvc`를 선택했다. WeatherTools의 `WebClient` 사용을 위해
  `spring-boot-starter-webflux`는 그대로 남겨두었다(원래도 있었음).
- **MCP Client 표준(HttpClient) 스타터 선택**: `10-1.mcp-client`는 Thymeleaf 기반의 동기(MVC) 채팅
  앱이라, 리액티브 전용 `spring-ai-starter-mcp-client-webflux` 대신 표준 `spring-ai-starter-mcp-client`
  (JDK HttpClient 기반)를 선택했다. Streamable HTTP 전송도 이 표준 스타터로 충분히 지원된다.
- **type: SYNC 선택**: 두 프로젝트 모두 원래 블로킹 방식(`WebClient...block()` 등)으로 작성돼 있어서,
  MCP 서버/클라이언트 모두 `SYNC` 타입으로 맞췄다. `@McpTool`은 SYNC 서버에서는 동기 메서드만 등록되므로,
  기존 도구 메서드들의 시그니처(동기 반환 타입)를 바꿀 필요가 없었다.
- **weather.api 설정 이동**: `10-1.mcp-client`의 `application.yml`에 있던 `weather.api.*` 설정은
  실제로 API를 호출하는 로직(`WeatherTools`)이 `10-2.mcp-server`로 옮겨갔으므로 클라이언트 쪽 설정은
  삭제했다. (이 프로젝트에는 원래부터 있던 값이라 그대로 유지)
- **10-2.mcp-server의 `/ai` 엔드포인트 제거**: 처음에는 `ChatController`를 남겨두고 도구 호출 부분만
  뺐지만, 이후 controller 패키지 자체를 삭제하면서 `/ai` 엔드포인트도 함께 사라졌다. 이제 이 프로젝트에서
  "도구가 실제로 동작하는지"는 MCP 프로토콜 엔드포인트(`POST /mcp`, MCP Inspector 또는
  `10-1.mcp-client`)로만 확인할 수 있다.
- **thymeleaf/web.resources 설정 제거**: controller/템플릿/정적 리소스를 지우면서, 그것들만 참조하던
  `spring.thymeleaf.cache`, `spring.web.resources.*` 설정도 application.yml에서 같이 제거했다. 반면
  `pom.xml`의 `spring-boot-starter-thymeleaf`와 채팅 모델/RAG/vector-store/postgresql 의존성은
  이번에도 건드리지 않았다. 이 시점에는 사실상 아무 코드에서도 쓰이지 않지만, "재사용을 위해 유지"라는
  기존 결정 범위를 벗어난 삭제라서 사용자에게 다시 묻지 않고 그대로 두었다. 필요하면 추가로 정리할 수 있다.


## 3. 실행 검증 범위

- `10-2.mcp-server`를 실제로 기동해서 확인했다: `mvn spring-boot:run`으로 8081 포트에 띄운 뒤
  MCP `initialize` 핸드셰이크와 `tools/list`를 curl로 직접 호출했다. 로그에 `Registered tools: 5`가
  찍혔고, `tools/list` 응답에 `getCurrentDateTime`, `createFile`, `listFiles`, `readTextFile`,
  `getCurrentWeather` 5개 도구가 파라미터 스키마(필수 여부 포함)와 함께 정확히 노출되는 것을 확인했다.
  확인 후 프로세스는 종료했다.
- `10-1.mcp-client`가 실제로 이 서버에 접속해 브라우저 채팅에서 "서울 날씨 알려줘" 같은 질문으로
  end-to-end 동작하는 것까지는 확인하지 않았다. 두 애플리케이션을 동시에 띄워야 하고 유효한
  `OPENAI_API_KEY`가 필요해서, 이번 작업에서는 컴파일 검증까지만 진행했다.
