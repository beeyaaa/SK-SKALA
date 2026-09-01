# STDIO MCP Server 실습

## 실습 개요

기존 Spring Boot 기반 API Service(Controller → Service → Repository 구조)를
**MCP(Model Context Protocol) Tool**로 전환하는 프로젝트입니다.

REST API로 노출되던 User/Product CRUD 기능을 REST Controller 없이,
**MCP Tool(`@McpTool`)** 형태로 노출하여 Claude Desktop과 같은 MCP Client가
STDIO(표준 입출력) 프로토콜을 통해 직접 호출할 수 있도록 구성합니다.

- 통신 방식: STDIO (표준 입출력 기반, 별도의 HTTP 포트 사용 안 함)
- 대상 도메인: User, Product
- 데이터 저장소: H2 In-Memory Database

## 실습 목표

기존 Spring Boot 프로젝트(Controller 기반 REST API)에 아래 두 가지를 추가/변경하여
MCP Server로 전환하는 방법을 이해합니다.

1. **tool 패키지 추가**: 기존 `@RestController`가 담당하던 요청 처리를 `@McpTool`이 붙은
   컴포넌트로 대체
2. **application 설정 추가**: STDIO 모드로 동작하도록 `spring.ai.mcp.server` 관련 설정 추가

즉, **Controller 계층만 MCP Tool 계층으로 교체**되고, Domain/Repository/Service 계층은
기존 Spring Boot 프로젝트를 그대로 재사용한다는 점이 핵심입니다.

## 기술 스택

| 구분 | 내용 |
|---|---|
| Language | Java 21 |
| Framework | Spring Boot 4.1.0 |
| AI Framework | Spring AI 2.0.x (MCP Server) |
| 통신 프로토콜 | MCP over STDIO |
| Database | H2 (In-Memory) |
| ORM | Spring Data JPA |
| 빌드 도구 | Gradle / Maven (둘 다 지원) |
| 기타 | Lombok |

## 프로젝트 구조

```
01.stdio-mcp-server
├── build.gradle / pom.xml
├── claude_desktop_config.json      # Claude Desktop 연동 설정 예시
└── src/main
    ├── java/com/example/stdio
    │   ├── StdioMcpServerApplication.java
    │   ├── domain/         # 기존 프로젝트의 Entity 그대로 재사용
    │   │   ├── User.java
    │   │   └── Product.java
    │   ├── repository/     # 기존 프로젝트의 Repository 그대로 재사용
    │   │   ├── UserRepository.java
    │   │   └── ProductRepository.java
    │   ├── service/        # 기존 프로젝트의 Service 그대로 재사용
    │   │   ├── UserService.java
    │   │   └── ProductService.java
    │   └── tool/            # 신규 추가: Controller를 대체하는 MCP Tool 계층
    │       ├── UserTools.java
    │       └── ProductTools.java
    └── resources
        ├── application.yaml # 코드 변경: STDIO MCP 설정
        └── data.sql
```

## 기존 Spring Boot 프로젝트에서 무엇을 바꿔야 하는가

### 1. 의존성 추가

기존 `spring-boot-starter-web` 기반 프로젝트에 MCP Server(WebMVC 기반) 스타터를 추가합니다.

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

    // MCP Server(STDIO) 의존성 추가
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
    <!-- MCP Server(STDIO) 의존성 추가 -->
    <dependency>
        <groupId>org.springframework.ai</groupId>
        <artifactId>spring-ai-starter-mcp-server-webmvc</artifactId>
    </dependency>
</dependencies>
```

> `spring-ai-starter-mcp-server-webmvc`는 이름은 webmvc이지만, `application.yaml`에서
> `stdio: true`로 설정하면 내장 톰캣을 띄우지 않고 STDIO 모드로 동작합니다.

### 2. application 설정 추가 (`application.yaml`)

기존 프로젝트의 DB 설정 등은 그대로 두고, 아래 `spring.ai.mcp.server` 설정을 추가합니다.
STDIO 프로토콜은 표준 출력(stdout)을 JSON-RPC 메시지 전용 채널로 사용하므로,
**콘솔 로그 출력과 웹 서버를 반드시 비활성화**해야 합니다.

```yaml
spring:
  main:
    web-application-type: none   # 웹 서버 비활성화 (STDIO 전용)
    banner-mode: log             # 배너를 stdout이 아닌 로그로 출력

  ai:
    mcp:
      server:
        name: stdio-mcp-server
        version: 1.0.0
        instructions: "STDIO MCP Server providing User and Product management tools"
        stdio: true               # STDIO 프로토콜 활성화
        type: SYNC                # 동기 방식 (비동기는 ASYNC)
        annotation-scanner:
          enabled: true           # @McpTool 어노테이션 스캔 활성화

logging:
  pattern:
    console:                      # 콘솔(stdout) 출력 비활성화 (필수)
  level:
    root: WARN
  file:
    name: /tmp/stdio-mcp-server.log   # 로그는 파일로만 출력
```

> stdout에 애플리케이션 로그가 섞여 나가면 MCP Client가 JSON-RPC 메시지를 파싱하지
> 못해 통신이 깨집니다. `logging.pattern.console`을 비워서 콘솔 출력을 반드시 막아야 합니다.

### 3. Controller → Tool 패키지로 전환

기존 `@RestController` + `@GetMapping`/`@PostMapping` 등으로 작성했던 API 엔드포인트를
`tool` 패키지의 `@McpTool` 메서드로 옮깁니다. Service/Repository는 수정 없이 그대로
주입받아 재사용합니다.

| 기존 (REST API) | 전환 후 (MCP Tool) |
|---|---|
| `@RestController` | `@Component` |
| `@GetMapping("/products")` | `@McpTool(description = "...")` |
| `@RequestParam` / `@PathVariable` | `@McpToolParam(description = "...", required = true)` |
| HTTP Status/ResponseEntity 반환 | 도메인 객체/문자열을 그대로 반환 |

예시 (`ProductTools.java`):

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

## 정리: 전환 체크리스트

기존 Spring Boot API 프로젝트를 STDIO MCP Server로 전환할 때 확인할 항목입니다.

- [ ] `spring-ai-bom` dependencyManagement 및 `spring-ai-starter-mcp-server-webmvc` 의존성 추가
- [ ] `application.yaml`에 `spring.main.web-application-type: none`, `banner-mode: log` 추가
- [ ] `application.yaml`에 `spring.ai.mcp.server.stdio: true`, `annotation-scanner.enabled: true` 추가
- [ ] `logging.pattern.console`을 비워 stdout으로의 로그 출력 완전 차단
- [ ] 기존 `@RestController` 클래스를 삭제(또는 유지)하고, 동일 역할의 `@McpTool` 메서드를
      가진 `tool` 패키지 컴포넌트 작성
- [ ] Domain/Repository/Service 계층은 변경 없이 그대로 재사용

## 빌드 및 실행

### Gradle

```bash
./gradlew clean build
java -jar build/libs/01.stdio-mcp-server-1.0.0.jar
```

### Maven

```bash
./mvnw clean package
java -jar target/stdio-mcp-server-1.0.0.jar
```

STDIO 모드이므로 실행 후 터미널에는 별도 출력이 없는 것이 정상입니다.
(모든 로그는 `/tmp/stdio-mcp-server.log` 파일에 기록됩니다.)

## Claude Desktop 연동

`claude_desktop_config.json`에 아래와 같이 빌드된 jar 경로를 등록하면
Claude Desktop이 해당 프로세스를 STDIO로 직접 실행하여 MCP Tool을 사용할 수 있습니다.

```json
{
  "mcpServers": {
    "stdio-mcp-server": {
      "command": "java",
      "args": [
        "-jar",
        "/절대경로/01.stdio-mcp-server-1.0.0.jar"
      ],
      "env": {
        "JAVA_HOME": "/Library/Java/JavaVirtualMachines/jdk-21.jdk/Contents/Home"
      }
    }
  }
}
```

> `args`의 jar 경로는 반드시 본인 환경에서 빌드된 jar의 절대경로로 수정해야 합니다.

등록 후 Claude Desktop을 재시작하면 `getAllUsers`, `createProduct` 등
`tool` 패키지에 정의한 메서드들을 대화 중 자연어 요청으로 호출할 수 있습니다.

## Spring AI MCP Client(10-1.mcp-client) 연동

Claude Desktop 대신, 같은 저장소의 `10-1.mcp-client` 프로젝트(Spring AI MCP Client)에서도
이 STDIO 서버를 자식 프로세스로 직접 실행하여 사용할 수 있습니다.
`10-1.mcp-client`의 `src/main/resources/application-stdio.yml`에 이미 등록되어 있는
`10-2.mcp-server` 연결 방식과 동일하게, `spring.ai.mcp.client.stdio.connections`에
커넥션을 하나 추가하면 됩니다.

```yaml
spring:
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
            stdio-mcp-server:
              command: java
              args:
                - -jar
                - ../../10-3.springboot-mcpserver/01.stdio-mcp-server/target/stdio-mcp-server-1.0.0.jar
```

- `connections` 하위의 키(`stdio-mcp-server`)는 임의로 지정 가능한 커넥션 이름이며,
  클라이언트가 여러 MCP 서버를 동시에 연결할 때 서로 다른 이름으로 구분합니다.
- Claude Desktop의 `claude_desktop_config.json`과 동일하게, `command`/`args`로
  MCP 서버를 별도 실행 없이 클라이언트가 자식 프로세스로 직접 기동해 STDIO로 통신합니다.
- `args`의 jar 경로는 `10-1.mcp-client` 기준 상대 경로(또는 절대 경로)로,
  본인이 빌드한 `01.stdio-mcp-server` jar 위치에 맞게 수정해야 합니다.
  (Gradle로 빌드했다면 `build/libs/01.stdio-mcp-server-1.0.0.jar`,
  Maven으로 빌드했다면 `target/stdio-mcp-server-1.0.0.jar` 경로가 됩니다.)
- 연결 전 반드시 `./gradlew build` 또는 `./mvnw package`로 `01.stdio-mcp-server`를
  먼저 빌드해 실행 가능한 jar를 만들어 두어야 합니다.

등록 후 `10-1.mcp-client`를 `stdio` 프로파일로 실행하면, 기존 `tool-server`,
`docker-server`와 함께 `stdio-mcp-server`의 User/Product 관련 도구들도
클라이언트에서 자동으로 인식되어 호출할 수 있습니다.
