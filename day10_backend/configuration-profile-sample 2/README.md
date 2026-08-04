# Spring Boot Configuration & Profile Sample

JDK 21 + Gradle Wrapper + Spring Boot 기반 Configuration/Profile 예제다.

## 포함 내용

- Gradle Wrapper: `gradlew`, `gradlew.bat`, `gradle/wrapper/*`
- `application.yml` 공통 설정
- `application-local.yml`, `application-dev.yml`, `application-prod.yml`
- `@ConfigurationProperties`와 Java `record`
- 설정값 Validation
- `@Profile` 기반 환경별 Bean 전환
- 환경변수 기반 설정 주입
- 설정 확인 REST API

## 요구사항

- JDK 21
- 별도의 Gradle 설치는 필요하지 않다.
- 최초 실행 시 Gradle 8.14.3 배포본을 자동으로 내려받는다.

## 압축 해제 후 실행 권한

macOS/Linux에서 실행 권한이 유지되지 않은 경우 한 번만 실행한다.

```bash
chmod +x gradlew
```

## Gradle Wrapper 확인

macOS/Linux:

```bash
./gradlew --version
```

Windows:

```bat
gradlew.bat --version
```

## Local 실행

별도 프로파일을 지정하지 않으면 `local` 프로파일이 기본 적용된다.

```bash
./gradlew bootRun
```

설정 확인:

```bash
curl http://localhost:8080/api/config
```

스토리지 서비스 확인:

```bash
curl http://localhost:8080/api/config/storage/sample.txt
```

## Dev 실행

```bash
./gradlew bootRun --args='--spring.profiles.active=dev'
```

환경변수 적용:

```bash
SERVER_PORT=9090 \
EXTERNAL_API_URL=https://custom-dev-api.example.com \
APP_API_KEY=my-dev-key \
./gradlew bootRun --args='--spring.profiles.active=dev'
```

호출:

```bash
curl http://localhost:9090/api/config
```

## Prod 실행

운영 프로파일은 필수 환경변수가 필요하다.

```bash
export EXTERNAL_API_URL=https://api.example.com
export APP_API_KEY=production-secret-key
export FRONTEND_URL=https://www.example.com
export ADMIN_EMAIL=operator@example.com

./gradlew bootRun --args='--spring.profiles.active=prod'
```

JAR 실행:

```bash
./gradlew clean bootJar

java -jar build/libs/configuration-profile-sample-0.0.1-SNAPSHOT.jar \
  --spring.profiles.active=prod
```

## 핵심 API

| API | 설명 |
|---|---|
| `GET /api/config` | 활성 프로파일 및 설정값 확인 |
| `GET /api/config/storage/{filename}` | 프로파일별 StorageService 동작 확인 |

## 프로파일별 Bean

- `local`, `dev`: `LocalStorageService`
- `prod`: `CloudStorageService`

## 운영 시 주의사항

- API Key, 비밀번호, JWT Secret은 YAML에 직접 저장하지 않는다.
- 환경변수, Vault, AWS Secrets Manager 등으로 주입한다.
- 설정 조회 API에서 민감정보를 반환하지 않는다.
