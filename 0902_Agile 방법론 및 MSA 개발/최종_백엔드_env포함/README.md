# The following practice code is intended for educational purposes only. For contact :  audit@korea.ac.kr, Sungryel Lim Ph.D

# This practice code is not a completed commercial version but has been developed for educational purposes; supplementation is required depending on the deployment objective for use as a commercial service.

# 전체 백엔드 기동 순서 (depends_on 기반)
MariaDB / Kafka (인프라)
  → Eureka (서비스 등록)
    → Auth Server (인증)
      → API Gateway + 4개 서비스
        → Recommend Service

# 공통 이미지 파일 로드 (API Gateway, Auth Server)
docker load -i infra-images.tar

# msa-lecture/auth-server:1.0 등 태그 확인
docker images

## 프로젝트 루트에서 (초기 트러블슈팅/리빌드 고려, 캐시 없이 빌드, 컨테이너는 묶어서 백그라운드로 실행)
docker compose build --no-cache
docker compose up -d

## 또는 한줄로
docker compose build --no-cache && docker compose up -d

# 로그 확인
## 전체 로그 한번에 보기
docker compose logs -f

## 또는 개별 컨테이너 로그 보기
docker compose logs -f [서비스명]

docker compose logs -f mariadb
docker compose logs -f kafka
docker compose logs -f eureka-server
docker compose logs -f auth-server
docker compose logs -f api-gateway
docker compose logs -f user-service
docker compose logs -f course-service
docker compose logs -f enrollment-service
docker compose logs -f payment-service
docker compose logs -f recommend-service

# 전체 종료 (또는 컨테이너 빌드 중, 실패 시에 기존 컨테이너 정리)
docker compose down

# 서버 기동 상태 확인
http://localhost:8761/

# 프론트엔드 실행
## 로컬 실행 방법
cd vue-frontend
npm install
npm run dev

## 브라우저에서 접속
http://localhost:3000

---

# 변경 사항

### 수정, 생성 파일

| 상태 | 디렉터리/파일 | 주요 내용 |
|---|---|---|
| 수정 | `user-service/src/main/java/com/lecture/user/{controller/UserController.java,repository/UserRepository.java,service/UserService.java}` | Recommend Service가 사용할 전체 `STUDENT` 목록 내부 조회 기능 추가 |
| 수정 | `{user,course,enrollment,payment}-service/src/main/resources/application.yml` | DB 접속 계정과 비밀번호를 환경변수로 분리 |
| 수정 | `recommend-service/main.py` | 신규 패키지 추천 Router 등록 |
| 수정 | `recommend-service/app/client/course_client.py` | Course API 응답 형식 호환 및 예외 처리 보강 |
| 수정 | `recommend-service/app/config/{security.py,settings.py}` | JWT 검증, 로컬 테스트 인증, OpenAI·서비스 URL 환경설정 추가 |
| 수정 | `recommend-service/app/model/schemas.py` | 페르소나 및 패키지 추천 요청·응답 모델 추가 |
| 생성 | `recommend-service/app/client/user_client.py` | User Service의 수강생 정보를 조회하는 내부 클라이언트 |
| 생성 | `recommend-service/app/router/{prompt_recommend_router.py,audience_package_router.py}` | 단일 패키지 및 2단계 페르소나·다중 패키지 API 제공 |
| 생성 | `recommend-service/app/service/{package_draft_service.py,audience_package_service.py}` | OpenAI/규칙 기반 추천, 후보 선정, 검증 및 가격 계산 |
| 생성 | `recommend-service/app/data/mock_sales_data.json` | 강의별 판매량과 동시구매 분석용 실습 데이터 |
| 생성 | `recommend-service/tests/{test_package_draft_service.py,test_audience_package_service.py,run_persona_api_experiment.py}` | 추천 로직 단위 테스트 및 API 순차 호출 실험 |
| 수정·생성 | `init-db/{01_init.sql,02_seed_courses.sql,03_seed_audiences.sql}` | 스키마 설명 보완, 240개 강의와 50명 수강생·수강 이력 추가 |
| 생성·대체 | `{docker-compose.build.yml,docker-compose.local.yml,.env.example}` | 환경변수 기반 빌드 및 로컬 AI 연동 설정 |
| 생성 | `scripts/generate_catalog_data.mjs` | 강의·수강 이력·판매 실습 데이터를 재생성하는 도구 |
| 생성 | `open.py` | 환경파일 확인부터 변경 서비스 빌드와 Docker 기동까지 자동화 |

### 데이터 사용 기준

| 데이터 | 원천 | 사용 이유 |
|---|---|---|
| 수강생 목록 | User Service → `users` DB | 실제 `STUDENT` 계정만 분석하기 위해 사용. 구버전 서비스에서는 JSON의 ID 후보를 단건 DB API로 검증 |
| 수강 이력 | Enrollment Service → `enrollments` DB | 사용자별 수강 강의와 학습 수준을 계산하기 위해 사용 |
| 강의 정보 | Course Service → `courses` DB | 활성 강의의 제목·카테고리·가격으로 후보를 구성하기 위해 사용 |
| 판매량·동시구매 횟수 | `recommend-service/app/data/mock_sales_data.json` | 현재 DB에 판매 분석용 집계 테이블이 없어 실습용 근거 데이터로 사용 |

`init-db/03_seed_audiences.sql`은 `user1~user50`과 수강 이력 169건을 추가

### 추가 API Endpoint

| Method | Endpoint | 담당 서비스 | 설명 |
|---|---|---|---|
| `GET` | `/api/users/internal/students` | User Service | DB의 전체 `STUDENT` 목록 조회(서비스 간 내부 호출) |
| `GET` | `/api/recommend/audiences` | Recommend Service | 수강생별 현재 수강 강의와 판매 지표 조회 |
| `POST` | `/api/recommend/personas/generate` | Recommend Service | 전체 수강 이력을 분석해 3~5개 페르소나 초안 생성 |
| `POST` | `/api/recommend/persona-bundles/generate` | Recommend Service | 검토된 페르소나마다 패키지 1개 생성 |

### 전체 디렉터리 구조와 변경 파일

```text
msa-lecture/
├── README.md                                      // 수정(원본 readme.md의 안내 복원 + AI API·구조·변경 내역 문서화)
├── open.py                                        // 생성(환경설정 검증·변경 서비스 빌드·Docker 실행 자동화)
├── .gitignore                                     // 생성(비밀키, 빌드 결과, Docker 이미지, 로컬 파일 제외)
├── .dockerignore                                  // 생성(Docker 빌드 컨텍스트에서 불필요·민감 파일 제외)
├── .env.example                                   // 생성(DB·OpenAI 환경변수의 안전한 예시; 실제 키 없음)
├── .github/
│   └── workflows/deploy-pages.yml                 // 생성(Vue 정적 데모를 GitHub Pages에 빌드·배포)
├── docker-compose.build.yml                       // 생성/대체(원본 docker-compose.yml의 빌드 역할 + 비밀번호·AI 환경변수화)
├── docker-compose.local.yml                       // 생성(기존 이미지에 최신 Recommend 소스를 마운트하는 로컬 AI 테스트 override)
│
├── user-service/                                  // 수정(전체 수강생 내부 조회 기능 추가)
│   └── src/main/
│       ├── java/com/lecture/user/
│       │   ├── controller/UserController.java     // 수정(GET /api/users/internal/students 추가)
│       │   ├── repository/UserRepository.java     // 수정(STUDENT 역할 목록 조회 쿼리 추가)
│       │   └── service/UserService.java           // 수정(수강생 목록을 응답 DTO로 변환)
│       └── resources/application.yml              // 수정(DB 계정 값을 환경변수로 분리)
│
├── course-service/
│   └── src/main/resources/application.yml         // 수정(DB 계정 값을 환경변수로 분리)
│
├── enrollment-service/
│   └── src/main/resources/application.yml         // 수정(DB 계정 값을 환경변수로 분리)
│
├── payment-service/
│   └── src/main/resources/application.yml         // 수정(DB 계정 값을 환경변수로 분리)
│
├── init-db/
│   ├── 01_init.sql                                // 수정(OTHER 카테고리를 AI로 사용하는 설명 보완; 기존 테이블 구조 유지)
│   ├── 02_seed_courses.sql                        // 생성(8개 도메인 × 30개, 총 240개 강의 Seed)
│   └── 03_seed_audiences.sql                      // 생성(user1~user50과 수강 이력 169건 Seed)
│
├── recommend-service/                             // 수정(AI 패키지 추천 도메인 확장)
│   ├── .dockerignore                              // 생성(Python 캐시·환경파일 등을 이미지에서 제외)
│   ├── .env.example                               // 생성(OpenAI·연동 서비스 환경변수 예시)
│   ├── main.py                                    // 수정(패키지 초안·페르소나 번들 Router 등록, 라우트 순서 정리)
│   ├── app/
│   │   ├── client/
│   │   │   ├── course_client.py                   // 수정(강의 API의 배열/래퍼 응답을 모두 처리하고 오류 방어)
│   │   │   └── user_client.py                     // 생성(User Service의 사용자·STUDENT 목록 조회)
│   │   ├── config/
│   │   │   ├── security.py                        // 수정(JWT 검증 유지 + 명시적인 로컬 전용 인증 우회 지원)
│   │   │   └── settings.py                        // 수정(OpenAI, User Service, 로컬 인증 설정 및 .env fallback 추가)
│   │   ├── data/
│   │   │   └── mock_sales_data.json               // 생성(240개 강의 판매량과 412개 동시구매 집계)
│   │   ├── model/
│   │   │   └── schemas.py                         // 수정(패키지 초안·페르소나·번들 요청/응답 모델 추가)
│   │   ├── router/
│   │   │   ├── prompt_recommend_router.py         // 생성(자연어 조건 기반 단일 패키지 초안 API)
│   │   │   └── audience_package_router.py         // 생성(수강생 조회·페르소나 생성·다중 패키지 API)
│   │   └── service/
│   │       ├── package_draft_service.py            // 생성(프롬프트·판매 데이터 기반 단일 패키지 추천)
│   │       └── audience_package_service.py         // 생성(팀원 로직 기반 2단계 페르소나·패키지 추천 핵심)
│   └── tests/
│       ├── test_package_draft_service.py           // 생성(단일 패키지 AI/규칙 fallback·가격 검증)
│       ├── test_audience_package_service.py        // 생성(페르소나 분할·번들 생성·검증 단위 테스트)
│       └── run_persona_api_experiment.py           // 생성(두 추천 API를 순서대로 호출하고 결과 저장)
│
├── scripts/
│   └── generate_catalog_data.mjs                  // 생성(강의 Seed·수강생 이력·판매 JSON 재생성 도구)
│
└── vue-frontend/                                  // 수정(팀원 프론트 및 정적 Pages 데모 포함)
    ├── Dockerfile                                 // 수정(npm install 대신 lockfile 기반 npm ci 사용)
    ├── .dockerignore                              // 생성(Node 빌드 컨텍스트 정리)
    ├── .env.example                               // 생성(API/mock 모드와 Pages base path 예시)
    ├── public/data/
    │   ├── demo-db.json                           // 생성(Pages용 사용자·강의·수강·결제 축약 데이터)
    │   ├── mock_sales_data.json                   // 생성(Pages용 판매량·동시구매 축약 데이터)
    │   └── recommend-bundles.json                 // 생성(Pages용 추천 결과 정적 응답)
    ├── src/
    │   ├── api/
    │   │   ├── index.js                           // 수정(파일 형식 정리; 공통 Axios 동작은 유지)
    │   │   ├── auth.js                            // 수정(OAuth/API 인증을 Pages 데모 인증으로 전환)
    │   │   ├── course.js                          // 수정(강의 API를 정적 JSON/localStorage 저장소에 연결)
    │   │   ├── enrollment.js                      // 수정(수강 API와 인기 추천을 정적 데이터에 연결)
    │   │   ├── mockRepository.js                  // 생성(Pages JSON 조회 및 localStorage CRUD 어댑터)
    │   │   ├── aiRecommend.js                     // 생성(mock/direct/api 모드와 2단계 추천 API 호출·화면 모델 변환)
    │   │   └── promotion.js                       // 생성(추천 번들 중 메인 프로모션 데이터 선택)
    │   ├── components/
    │   │   ├── AppHeader.vue                      // 수정(주요 메뉴를 패키지 기획으로 변경)
    │   │   ├── CourseCard.vue                     // 수정(데이터베이스·보안·모바일 카테고리 표시 추가)
    │   │   ├── PromotionBanner.vue                // 생성(메인 추천 패키지 배너)
    │   │   ├── PromotionPopup.vue                 // 생성(프로모션 팝업과 하루 숨김 UI)
    │   │   └── planner/
    │   │       ├── BundleCompositionPanel.vue     // 생성(추천 패키지·가격·강의·근거 카드)
    │   │       ├── PersonaListPanel.vue           // 생성(수강생 페르소나와 연결 패키지 카드)
    │   │       └── PlannerPager.vue                // 생성(패키지·페르소나 목록 공용 페이지 이동)
    │   ├── composables/
    │   │   └── usePagination.js                   // 생성(받아온 배열의 프론트 전용 페이징)
    │   ├── router/index.js                        // 수정(Pages용 Hash Router와 /package-planner 경로 추가)
    │   ├── store/
    │   │   ├── auth.js                            // 수정(Pages 데모 계정·토큰·세션 처리)
    │   │   └── course.js                          // 수정(8개 강의 도메인 분류·표시 지원)
    │   └── views/
    │       ├── PackagePlannerView.vue             // 생성(버튼 실행형 AI 패키지 기획 메인 화면)
    │       ├── LandingView.vue                    // 수정(추천 패키지 배너·팝업 추가)
    │       ├── LoginView.vue                      // 수정(백엔드 없는 Pages 데모 로그인 화면)
    │       ├── CallbackView.vue                   // 수정(로그인 후 패키지 기획 화면으로 이동)
    │       └── MyPageView.vue                     // 수정(사이드 메뉴를 패키지 기획 중심으로 변경)
    └── vite.config.js                             // 수정(Pages base path와 Recommend direct 프록시 추가)
```

### 삭제·대체된 원본 파일

```text
docker-compose.yml                                 // 삭제/대체 → docker-compose.build.yml
readme.md                                          // 삭제/대체 → README.md(대소문자 통일 및 내용 확장)
vue-frontend/src/views/CourseCreateView.vue        // 삭제/대체(현재 프론트 범위를 패키지 기획 데모로 축소)
vue-frontend/src/views/CourseDetailView.vue        // 삭제/대체(현재 프론트 라우터에서 강의 상세 제거)
vue-frontend/src/views/CourseListView.vue          // 삭제/대체 → PackagePlannerView.vue
vue-frontend/src/views/EnrollmentView.vue          // 삭제/대체(현재 프론트 라우터에서 수강 관리 제거)
```
