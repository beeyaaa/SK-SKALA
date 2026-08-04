# Spring Boot 의존성 주입 샘플

`Controller → Service → Repository` 계층의 생성자 기반 의존성 주입을
로그와 주석으로 확인할 수 있는 학습용 프로젝트다.

## 기술 구성

- Java 21
- Spring Boot 3.5.15
- Gradle 8.14.3 Wrapper
- Spring Web
- Spring Data JPA
- Validation
- H2 Database
- springdoc-openapi 2.8.17
- Swagger UI

## 프로젝트 열기

압축을 해제한 뒤 VS Code에서 폴더를 연다.

```bash
cd springboot-di-sample
code .
```

macOS에서 최초 실행 권한을 설정한다.

```bash
chmod +x gradlew
```

## 실행

```bash
./gradlew bootRun
```

의존성 캐시를 새로 확인해야 하는 경우:

```bash
./gradlew bootRun --refresh-dependencies
```

## 접속 주소

- Swagger UI: http://localhost:8080/swagger-ui.html
- OpenAPI JSON: http://localhost:8080/v3/api-docs
- H2 Console: http://localhost:8080/h2-console

H2 Console 접속 정보:

```text
JDBC URL : jdbc:h2:mem:didb
User Name: sa
Password : 입력하지 않음
```

## DI 확인 로그

실행 콘솔에서 다음과 비슷한 로그를 확인한다.

```text
[DI 확인] MemberServiceImpl 생성
[DI 확인] 주입된 Repository 클래스: jdk.proxy...$Proxy...

[DI 확인] MemberController 생성
[DI 확인] 주입된 Service 클래스: ...MemberServiceImpl...Proxy...

[Spring Bean 및 의존성 주입 확인]
Controller Bean : ...
Service Bean    : ...
Repository Bean : ...
호출 흐름        : Controller → Service → Repository
```

프록시의 실제 클래스명과 숫자는 환경에 따라 달라질 수 있다.

## 핵심 생성자 주입 코드

Controller가 Service를 주입받는다.

```java
public MemberController(MemberService memberService) {
    this.memberService = memberService;
}
```

Service가 Repository를 주입받는다.

```java
public MemberServiceImpl(MemberRepository memberRepository) {
    this.memberRepository = memberRepository;
}
```

생성자가 하나뿐이면 `@Autowired`를 생략해도 Spring이 자동으로 주입한다.

## API 테스트

VS Code에 REST Client 확장이 설치되어 있다면 `api-test.http` 파일에서
각 요청 위의 `Send Request`를 눌러 실행할 수 있다.

터미널에서도 테스트할 수 있다.

```bash
curl -X POST http://localhost:8080/api/members           -H "Content-Type: application/json"           -d '{"name":"홍길동","email":"hong@example.com"}'

curl http://localhost:8080/api/members
```

## Maven Central 429 오류가 발생할 때

```bash
./gradlew --stop
./gradlew clean build --refresh-dependencies
```

계속 `429 Too Many Requests`가 나오면 잠시 후 다시 실행하거나
교육장·회사 Wi-Fi 대신 다른 네트워크로 전환해 확인한다.
