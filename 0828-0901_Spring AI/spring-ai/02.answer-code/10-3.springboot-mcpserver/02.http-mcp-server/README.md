# HTTP(Streamable) MCP Server 실습

## 실습 개요

기존 Spring Boot 기반 API Service(Controller → Service → Repository 구조)에
**MCP(Model Context Protocol) Tool**을 추가로 노출하는 프로젝트입니다.

`01.stdio-mcp-server`와 동일한 User/Product 도메인·구조를 사용하지만, 통신 방식이
**STDIO(표준 입출력)가 아니라 Streamable HTTP**라는 점이 다릅니다. HTTP 기반이므로
별도의 웹 서버 비활성화가 필요 없고, 오히려 **기존 REST API(Controller)를 그대로 살려둔 채
MCP 엔드포인트(`/mcp`)를 추가로 노출**하여 REST API와 MCP Tool을 동시에 서비스할 수 있습니다.

- 통신 방식: Streamable HTTP (HTTP POST/GET 기반, 선택적으로 SSE 스트리밍 지원)
- 대상 도메인: User, Product
- 데이터 저장소: H2 In-Memory Database
- 프로필: `stateless`(세션 미유지, 기본값) / `streamable`(세션 유지)

## 실습 목표

기존 Spring Boot 프로젝트(Controller 기반 REST API)에 아래 두 가지를 추가/변경하여
MCP Server로 전환하는 방법을 이해합니다.

1. **tool 패키지 추가**: 기존 `@RestController`가 처리하던 기능과 동일한 동작을 하는
   `@McpTool` 메서드를 추가 작성 (Controller는 삭제하지 않고 그대로 유지)
2. **application 설정 추가**: Streamable HTTP 모드로 동작하도록 `spring.ai.mcp.server` 관련
   설정(`protocol: STREAMABLE` 또는 `STATELESS`, `streamable-http.mcp-endpoint` 등) 추가

즉, STDIO 버전이 Controller를 Tool로 **교체**했다면, HTTP 버전은 Controller를 유지한 채
Tool 계층을 **추가**하여 같은 서비스 로직을 REST API와 MCP Tool 양쪽으로 노출한다는 점이 핵심입니다.

## 기술 스택

| 구분 | 내용 |
|---|---|
| Language | Java 21 |
| Framework | Spring Boot 4.1.0 |
| AI Framework | Spring AI 2.0.x (MCP Server) |
| 통신 프로토콜 | MCP over Streamable HTTP (STATELESS / STREAMABLE) |
| Database | H2 (In-Memory) |
| ORM | Spring Data JPA |
| API 문서화 | springdoc-openapi (Swagger UI) |
| 빌드 도구 | Gradle / Maven (둘 다 지원) |
| 기타 | Lombok |

## 프로젝트 구조

```
02.http-mcp-server
├── build.gradle / pom.xml
├── claude_desktop_config.json      # Claude Desktop 연동 설정 예시 (mcp-remote 브릿지)
├── run.sh                          # 프로필 선택 실행 스크립트 (stateless|streamable)
└── src/main
    ├── java/com/example/http
    │   ├── HttpMcpServerApplication.java
    │   ├── domain/         # 기존 프로젝트의 Entity 그대로 재사용
    │   │   ├── User.java
    │   │   └── Product.java
    │   ├── repository/     # 기존 프로젝트의 Repository 그대로 재사용
    │   │   ├── UserRepository.java
    │   │   └── ProductRepository.java
    │   ├── service/        # 기존 프로젝트의 Service 그대로 재사용
    │   │   ├── UserService.java
    │   │   └── ProductService.java
    │   ├── controller/      # 기존 REST API: 삭제하지 않고 그대로 유지
    │   │   ├── UserController.java
    │   │   └── ProductController.java
    │   └── tool/            # 신규 추가: REST API와 별개로 MCP Tool 계층 추가
    │       ├── UserTools.java
    │       └── ProductTools.java
    └── resources
        ├── application.yaml            # 코드 변경: 공통 설정(DB, MCP 서버 이름 등)
        ├── application-streamable.yaml # 신규 추가: Streamable HTTP(세션 유지) 프로필
        ├── application-stateless.yaml  # 신규 추가: Stateless HTTP(세션 미유지) 프로필
        └── data.sql
```

## 기존 Spring Boot 프로젝트에서 무엇을 바꿔야 하는가

### 1. 의존성 추가

`01.stdio-mcp-server`와 **완전히 동일한 의존성**을 사용합니다. STDIO냐 Streamable HTTP냐는
런타임 설정(`application.yaml`)에서 결정되며, 의존성 자체는 바뀌지 않습니다.

**Gradle (`build.gradle`)**

```groovy
ext {
    springAiVersion = '2.0.0'
}

dependencies {
    // 기존 의존성은 유지
    implementation 'org.springframework.boot:spring-boot-starter-web'
    implementation 'org.springframework.boot:spring-boot-starter-data-jpa'
    implementation 'org.springframework.boot:spring-boot-starter-validation'

    // MCP Server 의존성 추가 (STDIO와 동일한 starter)
    implementation 'org.springframework.ai:spring-ai-starter-mcp-server-webmvc'
}

dependencyManagement {
    imports { mavenBom "org.springframework.ai:spring-ai-bom:${springAiVersion}" }
}
```

**Maven (`pom.xml`)**

```xml
<dependencyManagement>
    <dependencies>
        <dependency>
            <groupId>org.springframework.ai</groupId>
            <artifactId>spring-ai-bom</artifactId>
            <version>2.0.1</version>
            <type>pom</type>
            <scope>import</scope>
        </dependency>
    </dependencies>
</dependencyManagement>

<dependencies>
    <!-- MCP Server 의존성 추가 (STDIO와 동일한 starter) -->
    <dependency>
        <groupId>org.springframework.ai</groupId>
        <artifactId>spring-ai-starter-mcp-server-webmvc</artifactId>
    </dependency>
</dependencies>
```

> `spring-ai-starter-mcp-server-webmvc`는 `application.yaml`의 `spring.ai.mcp.server.protocol`
> 값(`STREAMABLE` / `STATELESS`)에 따라 HTTP 엔드포인트로 MCP를 노출합니다. `stdio: true`를 설정한
> STDIO 버전과 동일한 의존성으로 두 가지 통신 방식을 모두 지원합니다.

### 2. application 설정 추가

STDIO 버전은 웹 서버를 껐지만, HTTP 버전은 반대로 **웹 서버를 그대로 켜둔 채**
MCP 프로토콜과 엔드포인트만 지정합니다. 공통 설정과 프로필별 설정을 분리했습니다.

**공통 설정 (`application.yaml`)**

```yaml
server:
  port: 8081

spring:
  application:
    name: http-mcp-server
  profiles:
    active: stateless   # stateless(기본) 또는 streamable

  ai:
    mcp:
      server:
        enabled: true          # MCP 서버 활성화
        name: http-mcp-server
        version: 1.0.0
        instructions: "HTTP MCP Server providing User and Product management tools"
        type: SYNC              # 동기 방식
        annotation-scanner:
          enabled: true         # @McpTool 어노테이션 스캔 활성화
```

**Streamable 프로필 (`application-streamable.yaml`, 세션 상태 유지)**

```yaml
spring:
  config:
    activate:
      on-profile: streamable

  ai:
    mcp:
      server:
        protocol: STREAMABLE              # Streamable HTTP 프로토콜 활성화
        resource-change-notification: true
        tool-change-notification: true
        prompt-change-notification: true
        streamable-http:
          mcp-endpoint: /mcp               # MCP 엔드포인트 경로
          keep-alive-interval: 30s         # 연결 유지 간격
```

**Stateless 프로필 (`application-stateless.yaml`, 세션 상태 미유지)**

```yaml
spring:
  config:
    activate:
      on-profile: stateless

  ai:
    mcp:
      server:
        protocol: STATELESS               # Stateless 프로토콜 활성화
        resource-change-notification: true
        tool-change-notification: true
        prompt-change-notification: true
        streamable-http:
          mcp-endpoint: /mcp
          keep-alive-interval: 30s
```

> STDIO 버전에서 필수였던 `web-application-type: none`, `logging.pattern.console` 비활성화는
> HTTP 버전에서는 **불필요**합니다. HTTP는 별도 포트(`/mcp`)로 통신하므로 콘솔 로그나
> Swagger UI, Actuator 등 기존 웹 기능과 자유롭게 공존할 수 있습니다.
> 두 프로필의 차이는 서버가 세션(`MCP-Session-Id`)을 유지하는지 여부이며, `stateless` 서버는
> 클라이언트로의 역방향 요청(elicitation, sampling, ping)을 지원하지 않습니다.

### 3. tool 패키지 추가 (Controller는 유지)

STDIO 버전과 달리 `@RestController`를 **삭제하지 않고 그대로 둔 채**, 동일한 기능을 수행하는
`@McpTool` 메서드를 `tool` 패키지에 별도로 작성합니다. Service/Repository는 두 계층이
동일하게 주입받아 재사용합니다.

| 기존 (REST API, 유지) | 신규 추가 (MCP Tool) |
|---|---|
| `@RestController` | `@Component` |
| `@GetMapping("/api/products")` | `@McpTool(description = "...")` |
| `@RequestParam` / `@PathVariable` | `@McpToolParam(description = "...", required = true)` |
| `ResponseEntity<T>` 반환 | 도메인 객체/문자열을 그대로 반환 |

예시 (`ProductTools.java`, `ProductController.java`와 동일한 로직을 병행 제공):

```java
@Component
@RequiredArgsConstructor
@Slf4j
public class ProductTools {

    private final ProductService productService; // 기존 Service 그대로 주입

    @McpTool(description = "모든 상품 정보를 조회합니다.")
    public List<Product> getAllProducts() {
        return productService.getAllProducts();
    }

    @McpTool(description = "ID로 특정 상품을 조회합니다.")
    public Product getProductById(
            @McpToolParam(description = "상품 ID", required = true) Long id
    ) {
        return productService.getProduct(id);
    }
}
```

- `@McpTool(description = ...)`: 해당 메서드를 MCP Tool로 등록하고, LLM에게 이 도구가
  무엇을 하는지 설명하는 메타데이터를 제공합니다.
- `@McpToolParam(description = ..., required = ...)`: 파라미터 각각에 대한 설명과
  필수 여부를 정의하여 LLM이 올바른 인자를 채워 호출할 수 있게 합니다.
- 클래스 자체는 `@RestController`가 아닌 일반 `@Component`이면 되고, MCP 서버가
  `annotation-scanner.enabled: true` 설정에 따라 `@McpTool` 메서드를 자동으로 스캔합니다.
- 기존 `ProductController`는 그대로 남아 있으므로, 같은 서버가 `/api/products`(REST)와
  `/mcp`(MCP) 양쪽으로 동일한 기능을 제공합니다.

## 정리: 전환 체크리스트

기존 Spring Boot API 프로젝트를 Streamable HTTP MCP Server로 전환할 때 확인할 항목입니다.

- [ ] `spring-ai-bom` dependencyManagement 및 `spring-ai-starter-mcp-server-webmvc` 의존성 추가
- [ ] `application.yaml`에 `spring.ai.mcp.server.enabled: true`, `annotation-scanner.enabled: true` 추가
- [ ] 프로필별로 `spring.ai.mcp.server.protocol`(`STREAMABLE`/`STATELESS`)과
      `streamable-http.mcp-endpoint` 설정 추가
- [ ] 기존 `@RestController`는 삭제하지 않고 유지 (필요 없다면 STDIO 버전처럼 제거 후 Tool로 대체 가능)
- [ ] 동일 기능을 수행하는 `@McpTool` 메서드를 `tool` 패키지에 추가 작성
- [ ] Domain/Repository/Service 계층은 변경 없이 그대로 재사용

## 빌드 및 실행

### Gradle

```bash
./gradlew clean build
java -jar build/libs/02.http-mcp-server-1.0.0.jar --spring.profiles.active=stateless
```

### Maven

```bash
./mvnw clean package
java -jar target/http-mcp-server-1.0.0.jar --spring.profiles.active=streamable
```

### 실행 스크립트 사용

```bash
./run.sh              # 기본값: stateless 프로필
./run.sh streamable    # streamable 프로필
```

실행 후 아래 엔드포인트를 사용할 수 있습니다. (기본 포트 `8081`)

| 용도 | URL |
|---|---|
| MCP 엔드포인트 | `http://localhost:8081/mcp` |
| Swagger UI | `http://localhost:8081/swagger-ui.html` |
| H2 Console | `http://localhost:8081/h2-console` |
| Actuator | `http://localhost:8081/actuator` |

## Claude Desktop 연동

Claude Desktop은 Streamable HTTP MCP 서버에 직접 접속하는 기능이 없으므로,
`mcp-remote` 브릿지(npx)를 통해 로컬 HTTP 엔드포인트에 연결합니다.
`claude_desktop_config.json`에 아래와 같이 등록합니다.

```json
{
  "mcpServers": {
    "http-mcp-server": {
      "command": "npx",
      "args": [
        "-y",
        "mcp-remote",
        "http://localhost:8081/mcp"
      ]
    }
  }
}
```

> STDIO 버전이 `java -jar`로 서버 프로세스 자체를 자식 프로세스로 직접 실행했던 것과 달리,
> HTTP 버전은 **서버를 먼저 별도로 기동**(`./run.sh`)해 둔 상태에서 Claude Desktop이
> `mcp-remote`로 그 HTTP 엔드포인트에 접속하는 구조입니다.

등록 후 Claude Desktop을 재시작하면 `getAllUsers`, `createProduct` 등
`tool` 패키지에 정의한 메서드들을 대화 중 자연어 요청으로 호출할 수 있습니다.

## Spring AI MCP Client(10-1.mcp-client) 연동

같은 저장소의 `10-1.mcp-client` 프로젝트(Spring AI MCP Client)에서도 이 HTTP 서버에
직접 접속할 수 있습니다. STDIO 연동이 `spring.ai.mcp.client.stdio.connections`로
자식 프로세스를 실행했다면, HTTP 연동은 `spring.ai.mcp.client.streamable-http.connections`에
서버 URL을 등록하는 방식입니다. (`10-1.mcp-client`의
`src/main/resources/application-stateful-http.yml` / `application-stateless-http.yml` 참고)

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
            # 02.http-mcp-server(User/Product MCP Tool) 연결
            tool-server:
              url: http://localhost:8081
              endpoint: /mcp
```

- STDIO 방식은 클라이언트가 서버 프로세스를 직접 자식 프로세스로 실행(`command`/`args`)했지만,
  HTTP 방식은 **서버가 먼저 기동되어 있어야** 하며, 클라이언트는 `url`/`endpoint`로 접속만 합니다.
- `02.http-mcp-server`를 원하는 프로필(`stateless` 또는 `streamable`)로 먼저 실행한 뒤,
  `10-1.mcp-client`를 해당 프로필(`stateless-http` 또는 `stateful-http`)로 실행하면 됩니다.
- 연결 전 반드시 `./gradlew build` 또는 `./mvnw package`로 `02.http-mcp-server`를 빌드하고,
  `./run.sh [stateless|streamable]` 등으로 서버를 먼저 기동해 두어야 합니다.

등록 후 `10-1.mcp-client`를 실행하면, `stdio-mcp-server`와 마찬가지로 User/Product
관련 도구들이 클라이언트에서 자동으로 인식되어 호출할 수 있습니다.
