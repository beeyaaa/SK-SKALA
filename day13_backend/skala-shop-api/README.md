# SKALA Shop API

Spring Boot, Spring Data JPA, H2, JWT로 구현한 패션 쇼핑몰 REST API 실습 프로젝트입니다.

## 기술 스택

- Java 21
- Spring Boot 4.1
- Spring Web MVC
- Spring Data JPA
- H2 Database
- JJWT 0.11.5
- Lombok
- Gradle

## 실행 방법

```bash
./gradlew bootRun
```

기본 주소는 `http://localhost:8080`입니다.

API 문서:

```text
Swagger UI: http://localhost:8080/swagger-ui.html
OpenAPI JSON: http://localhost:8080/v3/api-docs
OpenAPI YAML: http://localhost:8080/v3/api-docs.yaml
```

전체 테스트는 다음 명령으로 실행합니다.

```bash
./gradlew clean test
```

## 데이터베이스

실행 데이터는 프로젝트의 `data/` 디렉터리에 H2 파일로 저장됩니다. 서버를 다시 실행해도 회원, 상품, 주문 데이터가 유지됩니다.

H2 Console:

```text
http://localhost:8080/h2-console
```

접속 정보:

```text
JDBC URL: jdbc:h2:file:./data/skala-shop-db
User Name: sa
Password: 비어 있음
```

테스트에서는 실제 파일 DB 대신 별도의 H2 메모리 DB를 사용합니다.

## 초기 패션 상품

애플리케이션을 처음 실행하면 다음 상품이 등록됩니다.

| 상품 | 가격 |
|---|---:|
| 오버핏 블레이저 | 129,000 |
| 클래식 코튼 셔츠 | 59,000 |
| 와이드 데님 팬츠 | 79,000 |
| 레더 미니백 | 89,000 |
| 러닝 스니커즈 | 109,000 |

동일한 이름의 상품은 서버 재실행 시 중복 등록되지 않습니다.

## 상품 API

| Method | URI | 설명 |
|---|---|---|
| GET | `/api/products/list?offset=0&count=10` | 상품 목록 조회 |
| GET | `/api/products/search?keyword=셔츠&minPrice=50000&maxPrice=100000` | 상품명·가격 범위 검색 |
| GET | `/api/products/{id}` | 상품 상세 조회 |
| POST | `/api/products` | 상품 등록 |
| PUT | `/api/products` | 상품 수정 |
| DELETE | `/api/products` | 상품 삭제 |

상품 등록 요청 예시:

```json
{
  "productName": "울 니트 카디건",
  "productPrice": 69000
}
```

## 차별화 기능: 상품 검색·가격 필터

상품명 일부, 최소 가격, 최대 가격을 자유롭게 조합하여 상품을 검색할 수 있습니다. 검색 결과에도 기존 목록 API와 동일한 페이징을 적용합니다.

```text
GET /api/products/search?keyword=셔츠&minPrice=50000&maxPrice=100000&offset=0&count=10
```

검색 조건:

- `keyword`: 상품명에 포함될 검색어이며 생략할 수 있습니다.
- `minPrice`: 최소 가격이며 0 이상이어야 합니다.
- `maxPrice`: 최대 가격이며 0보다 커야 합니다.
- `offset`: 0부터 시작하는 페이지 번호입니다.
- `count`: 한 페이지에 표시할 상품 수입니다.

`minPrice`가 `maxPrice`보다 크면 HTTP 400 응답을 반환합니다.

## 고객 API

| Method | URI | 설명 |
|---|---|---|
| GET | `/api/customers/list?offset=0&count=10` | 고객 목록 조회 |
| GET | `/api/customers/{customerId}` | 고객과 주문상품 조회 |
| POST | `/api/customers` | 회원가입 |
| POST | `/api/customers/login` | 로그인 및 JWT Cookie 발급 |
| PUT | `/api/customers` | 고객 포인트 수정 |
| DELETE | `/api/customers` | 고객 삭제 |
| POST | `/api/customers/order` | 상품 주문 |
| POST | `/api/customers/cancel` | 주문 취소 |

회원가입 시 초기 포인트 `1,000,000`이 지급됩니다.

## 실습 시나리오

### 1. SKALA SHOP 개요

고객이 회원가입과 로그인을 한 뒤 상품을 조회하고, 보유 포인트로 상품을 주문하거나 취소하는 쇼핑몰 REST API입니다.

| 구분 | 내용 |
|---|---|
| 핵심 도메인 | 상품(Product), 고객(Customer), 주문상품(OrderItem) |
| 계층 구조 | Controller → Service → Repository → H2 DB |
| 주요 기능 | 상품 CRUD, 고객 관리, 로그인, 상품 주문, 주문 취소 |
| 인증 방식 | 로그인 시 발급된 JWT를 `bff-access` Cookie로 전달 |

### 2. 고객의 상품 주문 여정

| 단계 | 고객 행동 | API |
|---:|---|---|
| 1 | ID와 비밀번호로 회원가입하고 초기 포인트 지급 | `POST /api/customers` |
| 2 | 로그인하고 JWT Cookie 발급 | `POST /api/customers/login` |
| 3 | 판매 상품 목록과 상세 정보 조회 | `GET /api/products/list`, `GET /api/products/{id}` |
| 4 | 원하는 상품을 수량만큼 주문하고 포인트 차감 | `POST /api/customers/order` |
| 5 | 고객 정보와 주문 상품 목록 확인 | `GET /api/customers/{customerId}` |
| 6 | 주문 수량을 취소하고 포인트 환급 | `POST /api/customers/cancel` |

### 3. 비즈니스 규칙과 예외 처리

- 회원가입 시 초기 포인트 `1,000,000`을 지급합니다.
- 보유 포인트가 상품 가격보다 부족하면 `INSUFFICIENT_FUNDS`로 주문을 거부합니다.
- 같은 상품을 다시 주문하면 기존 주문 수량에 누적합니다.
- 주문을 취소하면 수량을 차감하고, 수량이 0이 되면 주문상품을 삭제합니다.
- 주문과 취소는 로그인 Cookie가 필요합니다.
- 존재하지 않는 고객이나 상품을 조회하면 `DATA_NOT_FOUND`를 반환합니다.
- 잘못된 요청 본문·쿼리·경로 값은 전역 예외 처리기가 HTTP 400으로 변환합니다.
- 주문과 취소는 `@Transactional`로 처리하여 포인트와 주문 수량을 함께 반영합니다.

### 4. API 호출 순서

아래 요청은 PDF의 End-to-End 실습 흐름인 회원가입 → 로그인 → 상품 조회 → 주문 → 주문 확인 → 주문 취소 순서입니다.

#### 1) 회원가입

```bash
curl -X POST http://localhost:8080/api/customers \
  -H 'Content-Type: application/json' \
  -d '{"customerId":"skala01","customerPassword":"pw1234"}'
```

#### 2) 로그인 및 Cookie 저장

```bash
curl -X POST http://localhost:8080/api/customers/login \
  -H 'Content-Type: application/json' \
  -c cookies.txt \
  -d '{"customerId":"skala01","customerPassword":"pw1234"}'
```

#### 3) 상품 목록 확인

```bash
curl 'http://localhost:8080/api/products/list?offset=0&count=10'
```

#### 4) 상품 주문

```bash
curl -X POST http://localhost:8080/api/customers/order \
  -H 'Content-Type: application/json' \
  -b cookies.txt \
  -d '{"productId":1,"quantity":2}'
```

#### 5) 주문 내역 확인

```bash
curl http://localhost:8080/api/customers/skala01
```

#### 6) 주문 취소

```bash
curl -X POST http://localhost:8080/api/customers/cancel \
  -H 'Content-Type: application/json' \
  -b cookies.txt \
  -d '{"productId":1,"quantity":1}'
```

## 공통 응답

성공:

```json
{
  "result": 0,
  "code": 0,
  "message": null,
  "body": {}
}
```

실패:

```json
{
  "result": 1,
  "code": 400,
  "message": "INSUFFICIENT_FUNDS",
  "body": null
}
```

## JWT 설정

개발 환경에서는 기본 JWT 비밀키를 사용합니다. 환경변수로 덮어쓸 수 있습니다.

```bash
export JWT_SECRET='32바이트 이상의 안전한 비밀키'
./gradlew bootRun
```

JWT의 기본 만료 시간은 1시간입니다.

## 입력값 검증

요청 JSON은 Jakarta Bean Validation의 `@Valid`, `@NotBlank`, `@NotNull`, `@Positive`로 검증합니다. 쿼리·경로 파라미터는 `@Validated`, `@Min`, `@Positive`로 검증합니다.

검증 실패는 `GlobalExceptionHandler`가 다음 형식의 HTTP 400 응답으로 변환합니다.

```json
{
  "result": 1,
  "code": 400,
  "message": "VALIDATION_FAILED",
  "body": {
    "quantity": "수량은 1 이상이어야 합니다."
  }
}
```

## 참고

- 주문과 취소는 로그인 Cookie가 필요합니다.
- 비밀번호는 응답 JSON에서 `null`로 처리됩니다.
- 현재 비밀번호 저장 방식은 교육용 평문 방식입니다. 실제 서비스에서는 BCrypt 등의 해시 방식을 사용해야 합니다.
- `offset`은 실제로 페이지 번호이며 0부터 시작합니다.
