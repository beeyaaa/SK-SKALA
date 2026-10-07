# Agile & MSA 실습 실행 계획

> 오늘은 **Day 1 학습·기획과 Sprint 1 착수**, 내일은 **Sprint 1 완성 후 Sprint 2 확장·통합·발표**까지 진행한다.

---

## 0. 이틀간의 전체 목표

완성된 온라인 강의 MSA 템플릿을 실행하고 구조를 확인한 뒤, 팀 아이디어에 맞게 다음 두 단계로 변경한다.

```text
Sprint 1: 로그인 → 목록 → 상세 → 신청까지 최소 동작 흐름 완성
Sprint 2: 결제/승인 → Kafka 이벤트 → 상태 변경 → 추천까지 확장
```

핵심 원칙은 기능을 많이 만드는 것이 아니라 **사용자가 처음부터 끝까지 실제로 사용할 수 있는 흐름 하나를 먼저 완성하는 것**이다.

### 수정 대상

| 구분 | 서비스·디렉터리 |
|---|---|
| Sprint 1 중심 | `vue-frontend`, `course-service`, `enrollment-service`, 필요 시 `init-db` |
| Sprint 2 중심 | `payment-service`, `enrollment-service`의 Kafka 코드, `recommend-service`, 관련 프론트 화면 |
| 가급적 원본 사용 | `user-service` |
| 수정하지 않음 | `auth-server`, `api-gateway`, `eureka-server`, Kafka·MariaDB 인프라 |

---

# 오늘: Day 1 + Sprint 1 착수

## 1. Agile·MSA 핵심 개념 정리

팀원이 다음 질문에 공통으로 답할 수 있어야 한다.

- 우리 서비스의 이해관계자는 누구인가?
- 이해관계자가 겪는 Pain Point는 무엇인가?
- 가장 먼저 제공해야 하는 핵심 가치는 무엇인가?
- 기능을 왜 Sprint 1과 Sprint 2로 나누는가?
- 각 서비스는 어떤 업무와 데이터를 책임지는가?
- 서비스 간 동기 REST 통신과 비동기 Kafka 이벤트는 어디에 사용하는가?

### User Story 작성

```text
[사용자]는 [목적/가치]를 얻기 위해
[행동/기능]을 하기 원한다.
```

예시:

```text
학생은 원하는 기술을 빠르게 학습하기 위해
관심 분야의 강의를 검색하고 수강신청하기 원한다.
```

### Acceptance Criteria 작성

```text
Given 로그인한 학생이 강의 상세 화면에 있을 때
When 수강신청 버튼을 누르면
Then 수강신청 정보가 생성되고 내 강의 목록에서 확인된다.
```

---

## 2. 완성형 템플릿 정상 동작 확인

수정하기 전에 반드시 원본 시스템이 정상적으로 실행되는지 확인한다.

### 컨테이너 상태 확인

```bash
docker compose -p msa-lecture ps
```

확인 대상:

- MariaDB
- Kafka
- Eureka
- Auth Server
- API Gateway
- User Service
- Course Service
- Enrollment Service
- Payment Service
- Recommend Service

### 접속 주소 확인

| 대상 | 주소 |
|---|---|
| 프론트엔드 | `http://localhost:3000` |
| Eureka | `http://localhost:8761` |
| Gateway | `http://localhost:8080` |
| User Swagger | `http://localhost:8081/swagger-ui/index.html` |
| Course Swagger | `http://localhost:8082/swagger-ui/index.html` |
| Enrollment Swagger | `http://localhost:8083/swagger-ui/index.html` |
| Payment Swagger | `http://localhost:8084/swagger-ui/index.html` |
| Recommend API 문서 | `http://localhost:8085/docs` |

### 원본 시나리오 테스트

1. 회원가입
2. 로그인
3. 강의 목록 조회
4. 강의 상세 조회
5. 수강신청
6. 수강 상태 확인
7. 결제 로그 확인
8. 추천 결과 확인

문제가 발생하면 바로 코드를 변경하지 말고 다음 형식으로 기록한다.

```text
실행한 기능:
호출한 API:
예상 결과:
실제 결과:
HTTP 상태 코드:
관련 서비스 로그:
원인과 해결 과정:
```

---

## 3. 팀 아이디어와 도메인 매핑 확정

온라인 강의 플랫폼의 각 도메인을 팀 주제에 맞게 치환한다.

| 기존 도메인 | 팀 도메인 예시 |
|---|---|
| User | 고객, 환자, 여행자, 구독자 |
| Course | 상품, 콘텐츠, 여행상품, 상담 프로그램 |
| Enrollment | 주문, 예약, 구독, 신청 |
| Payment | 결제, 승인, 계약, 접수 확정 |
| Recommend | 상품 추천, 콘텐츠 추천, 여행지 추천 |

오늘 안에 다음 문장을 확정한다.

```text
우리 팀은 [이해관계자]가 겪는 [Pain Point]를
[AI/추천 기능]으로 해결하는 서비스를 만든다.
```

### 핵심 사용자 흐름 선정

Sprint 1에서는 하나의 흐름만 선택한다.

```text
로그인 → 목록 조회 → 상세 조회 → 신청
```

---

## 4. Sprint 1 Planning

### Sprint Goal

```text
사용자가 로그인한 후 팀 도메인의 항목을 조회하고
신청까지 완료할 수 있는 최소 서비스를 만든다.
```

### Sprint 1과 Sprint 2 범위 구분

| Sprint | 범위 |
|---|---|
| Sprint 1 | 로그인, 목록, 상세, 신청까지 핵심 MVP 흐름 |
| Sprint 2 | 결제·승인, Kafka 이벤트, 상태 자동 변경, 추천 확장 |

### 역할 배분 예시

| 담당 | 작업 |
|---|---|
| 기획·통합 | User Story, API 목록, Sprint Board, 통합 테스트 |
| 프론트엔드 | 목록·상세·신청 화면과 API 연결 |
| Course 담당 | Entity·DTO·Service·API를 팀 도메인에 맞게 변경 |
| Enrollment 담당 | 신청 데이터·상태·API 변경 |
| Sprint 2 담당 | Payment·Kafka·Recommend 확장 준비 |

### Sprint Board 구성

```text
TODO
- 팀 도메인 용어 확정
- User Story 작성
- 목록 API 확인
- 상세 API 확인
- 신청 API 확인
- 목록 화면 수정
- 상세 화면 수정
- 신청 버튼 연결
- 신청 결과 화면 작성
- 통합 테스트

DOING
- 현재 진행 중인 Task

DONE
- 실제 동작 확인까지 완료한 Task
```

Task는 한 사람이 짧은 시간 안에 완료할 수 있을 정도로 나눈다.

```text
나쁜 예: 프론트엔드 완성

좋은 예:
- 강의 목록 API 응답 확인
- CourseCard의 제목 필드 변경
- 신청 버튼에서 POST /api/enrollments 호출
- 신청 성공 후 내 신청 목록으로 이동
```

---

## 5. 오늘 구현할 Sprint 1 최소 범위

### 백엔드

- [ ] 팀 도메인에 맞는 Course 용어와 필드 결정
- [ ] 목록 API 응답 확인
- [ ] 상세 API 응답 확인
- [ ] Enrollment 신청 요청·응답 확인
- [ ] 필요하면 DB 초기 테이블 또는 데이터 변경

### 프론트엔드

- [ ] 서비스명과 주요 화면 문구 변경
- [ ] 목록 화면 연결
- [ ] 상세 화면 연결
- [ ] 신청 버튼 연결
- [ ] 로그인 토큰이 API 요청에 포함되는지 확인

### 수정한 서비스 재빌드

```bash
docker compose -p msa-lecture up -d --build course-service
docker compose -p msa-lecture up -d --build enrollment-service
```

### 로그 확인

```bash
docker compose -p msa-lecture logs -f course-service
docker compose -p msa-lecture logs -f enrollment-service
```

---

## 6. 오늘 종료 전 체크리스트

- [ ] 팀의 이해관계자와 Pain Point를 정했다.
- [ ] AI 솔루션을 한 문장으로 정리했다.
- [ ] Sprint 1과 Sprint 2 기능을 구분했다.
- [ ] 팀원별 담당 서비스와 디렉터리를 정했다.
- [ ] 핵심 User Story와 Acceptance Criteria를 작성했다.
- [ ] 필요한 API 목록을 정리했다.
- [ ] 원본 시스템의 정상 동작을 확인했다.
- [ ] 목록 또는 상세 화면을 팀 도메인에 맞게 변경했다.
- [ ] 신청 API 연결을 시작했다.
- [ ] 미완료 작업과 트러블슈팅을 기록했다.

### 오늘 마지막 공유

```text
오늘 완료한 것:
현재 동작하는 흐름:
남은 작업:
막힌 문제:
내일 첫 번째로 할 일:
```

---

# 내일: Sprint 1 완성 + Sprint 2 + 최종 발표

## 1. 오전 Stand-up

15분 안에 다음 내용을 공유한다.

- 어제 완료한 작업
- 오늘 진행할 작업
- 현재 장애물

공유가 끝나면 Sprint Board를 갱신한다. 장애물의 상세 논의는 Stand-up 이후 별도로 진행한다.

---

## 2. Sprint 1 완성

다음 사용자 흐름을 화면에서 끝까지 실행할 수 있어야 한다.

```text
회원가입
→ 로그인
→ 목록 조회
→ 상세 조회
→ 신청
→ 내 신청 목록 확인
```

### Sprint 1 통합 테스트

- [ ] 비로그인 사용자의 보호된 화면 접근이 차단된다.
- [ ] 로그인 후 토큰이 `sessionStorage`에 저장된다.
- [ ] API 요청에 `Authorization: Bearer ...`가 포함된다.
- [ ] 목록 API가 정상 응답한다.
- [ ] 상세 API가 정상 응답한다.
- [ ] 신청 요청에 올바른 사용자·항목 ID가 전달된다.
- [ ] 중복 신청 시 오류가 적절히 표시된다.
- [ ] 신청 정보가 DB에 생성된다.
- [ ] 브라우저 콘솔에 치명적인 오류가 없다.
- [ ] 팀원이 실제 화면으로 시연할 수 있다.

### Sprint 1 Definition of Done

```text
코드만 작성됨                  → 미완료
API만 개별적으로 성공함         → 미완료
화면에서 전체 시나리오 동작     → 완료
팀원이 데모할 수 있음           → 완료
오류·제한사항이 기록됨          → 완료
```

### Sprint 1 Review

- 실제 화면으로 핵심 사용자 흐름 시연
- 기대 결과와 다른 부분 확인
- 피드백을 Sprint 2 Backlog에 반영

### Sprint 1 Retrospective

```text
Keep: 계속 유지할 방식
Problem: 진행을 방해한 문제
Try: Sprint 2에서 새로 시도할 방식
```

---

## 3. Sprint 2 Planning

### Sprint Goal

```text
신청 이후 결제·이벤트·추천 흐름을 팀 도메인에 맞게 확장하여
전체 서비스 시나리오를 완성한다.
```

### Sprint 2 수정 대상

- `payment-service`
- `enrollment-service`의 Kafka Consumer/Producer
- `recommend-service`
- 결제·상태·추천 결과를 보여주는 프론트엔드 화면

---

## 4. Payment Service 확장

현재 원본 흐름:

```text
신청 생성
→ Payment Service 내부 호출
→ UUID 거래번호 생성
→ 결제 COMPLETED
→ payment.completed 이벤트 발행
```

팀에서 결정할 내용:

- 결제가 팀 도메인에서 어떤 업무를 의미하는가?
- 고정 금액 `99,000원`을 유지하거나 변경할 것인가?
- 성공·실패 조건은 무엇인가?
- Kafka 이벤트에 어떤 필드를 추가할 것인가?

결제가 없는 도메인은 다음처럼 치환할 수 있다.

- 결제 완료 → 예약 승인
- 결제 완료 → 주문 확정
- 결제 완료 → 구독 활성화
- 결제 완료 → 상담 접수 승인

이벤트 payload 예시:

```json
{
  "paymentId": 1,
  "userId": 3,
  "courseId": 10,
  "status": "COMPLETED",
  "paymentMethod": "CARD",
  "amount": 49000
}
```

---

## 5. Kafka 이벤트 연결

확인해야 할 전체 이벤트 흐름:

```text
Payment Service
  └─ payment.completed 발행
        ↓
Enrollment Service
  ├─ 이벤트 수신
  ├─ PENDING → ACTIVE
  ├─ Course 수강 인원 증가
  └─ enrollment.completed 발행
        ↓
Recommend Service
  └─ 이벤트 수신
```

### 로그 확인

```bash
docker compose -p msa-lecture logs -f payment-service
docker compose -p msa-lecture logs -f enrollment-service
docker compose -p msa-lecture logs -f recommend-service
```

확인할 로그:

- `payment.completed 발행 성공`
- `payment.completed 수신`
- `수강 활성화 완료`
- `enrollment.completed 발행 성공`
- `enrollment.completed 수신`

Kafka의 토픽 이름과 Producer/Consumer 구조는 가능하면 유지하고, 업무 필드와 처리 로직을 확장한다.

---

## 6. Recommend Service 확장

현재 추천 규칙:

1. 수강 이력이 없으면 전체 인기 강의 추천
2. 수강 이력이 있으면 가장 많이 수강한 카테고리 계산
3. 해당 카테고리의 미수강 강의 추천

팀 도메인에 맞는 확장 예시:

- 가격대 기반 추천
- 관심 카테고리 기반 추천
- 최근 신청 이력 기반 추천
- 지역·연령·선호도 기반 추천
- 인기 점수와 개인화 점수를 결합한 추천

이번 실습에서는 새로운 AI 모델을 학습하는 것보다 **추천 규칙을 팀의 Pain Point 및 사용자 가치와 연결하는 것**이 중요하다.

---

## 7. 전체 통합 테스트

최종 시나리오를 처음부터 다시 실행한다.

```text
회원가입
→ 로그인
→ 항목 생성 또는 조회
→ 신청
→ 결제/승인
→ Kafka 이벤트
→ 상태 변경
→ 추천 결과 확인
```

### 테스트 결과표

| 단계 | 기대 결과 | 실제 결과 | 상태 |
|---|---|---|---|
| 로그인 | 토큰 발급 |  |  |
| 목록 조회 | 데이터 표시 |  |  |
| 상세 조회 | 선택 항목 표시 |  |  |
| 신청 | PENDING 데이터 생성 |  |  |
| 결제·승인 | COMPLETED 처리 |  |  |
| Kafka | 상태가 ACTIVE로 변경 |  |  |
| 추천 | 추천 목록 반환 |  |  |

### 버그 수정 우선순위

1. 애플리케이션이 실행되지 않는 문제
2. 로그인·토큰 문제
3. 핵심 API가 실패하는 문제
4. 신청→결제→상태 변경이 끊기는 문제
5. 추천 결과 오류
6. 화면 디자인과 문구
7. 부가 기능

핵심 시나리오가 깨진 상태에서는 UI 디자인보다 기능 복구를 우선한다.

---

## 8. 최종 발표 준비

발표 자료에는 다음 내용을 포함한다.

1. 이해관계자와 Pain Point
2. 이를 해결하는 AI 솔루션
3. Sprint 1과 Sprint 2 구분 및 우선순위 근거
4. 팀 도메인으로 치환한 MSA 아키텍처
5. 실제 사용한 API 명세
6. 동작 화면과 상태 변화 스냅샷

### 데모 순서

```text
문제 설명
→ Sprint 구분 이유
→ 아키텍처 설명
→ 로그인
→ 핵심 기능 실행
→ Kafka 기반 상태 변화
→ 추천 결과
→ 회고
```

---

# 최종 산출물 체크리스트

- [ ] 이해관계자와 Pain Point
- [ ] AI 솔루션 설명
- [ ] User Story와 Acceptance Criteria
- [ ] Product Backlog와 Sprint Backlog
- [ ] Sprint 1·2 구분 근거
- [ ] 팀 아키텍처 구성도
- [ ] API 명세
- [ ] 실행 가능한 코드
- [ ] 통합 테스트 결과표
- [ ] 화면·Eureka·Swagger·Kafka 로그 스냅샷
- [ ] 트러블슈팅 기록
- [ ] Sprint Review 결과
- [ ] Keep·Problem·Try 회고 결과

---

# 빠른 일정 요약

| 시점 | 목표 | 반드시 남길 결과 |
|---|---|---|
| 오늘 오전 | Agile·MSA 이해 | Pain Point, User Story 초안 |
| 오늘 오후 초반 | 원본 시스템 확인 | 정상 동작 확인, API 목록 |
| 오늘 오후 | Sprint 1 Planning·착수 | 역할 배분, Sprint Board, 목록·상세·신청 구현 시작 |
| 오늘 종료 전 | 진행 상태 정리 | 완료·미완료·장애물·내일 첫 작업 |
| 내일 오전 | Sprint 1 완성 | 로그인→조회→신청 전체 데모 |
| 내일 오전 후반 | Review·Retro·Sprint 2 Planning | 피드백과 Sprint 2 Backlog |
| 내일 오후 | Payment·Kafka·Recommend 확장 | 결제 이벤트와 상태 변경, 추천 결과 |
| 내일 종료 전 | 통합·발표 | 전체 데모, 발표자료, 최종 회고 |
