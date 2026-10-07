import { mkdirSync, writeFileSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const scriptDir = dirname(fileURLToPath(import.meta.url))
const projectRoot = resolve(scriptDir, '..')

const domains = [
  {
    key: 'BACKEND',
    label: '백엔드',
    ids: [1, 2, ...Array.from({ length: 28 }, (_, index) => index + 4)],
    titles: [
      'Spring Boot 기초', 'Spring Boot MSA', 'Java 객체지향 실전', 'Spring Security와 JWT',
      'REST API 설계와 테스트', 'JPA와 Hibernate 성능 최적화', 'Kotlin 서버 개발', 'Spring WebFlux 리액티브 프로그래밍',
      '클린 아키텍처 실전', '도메인 주도 설계 입문', '백엔드 TDD 실전', 'Gradle 빌드 자동화',
      'Spring과 Redis 활용', 'Kafka 이벤트 기반 아키텍처', 'gRPC 서비스 개발', 'GraphQL API 구축',
      'Spring Batch 대용량 처리', 'Java 동시성 프로그래밍', 'JVM 성능 튜닝', '백엔드 로깅과 모니터링',
      'API Gateway 패턴', '분산 트랜잭션 이해', 'Saga 패턴 실전', 'CQRS와 이벤트 소싱',
      '헥사고날 아키텍처', '레거시 시스템 리팩터링', 'Spring 통합 테스트', 'Spring Cloud 실전',
      'Java 21 신기능', '대규모 트래픽 백엔드 설계'
    ]
  },
  {
    key: 'FRONTEND',
    label: '프론트엔드',
    ids: [3, ...Array.from({ length: 29 }, (_, index) => index + 32)],
    titles: [
      'Vue.js 기초', 'React 웹 개발 입문', 'HTML과 CSS 실전', 'TypeScript 실전',
      'Next.js 웹 애플리케이션', '프론트엔드 테스트 자동화', 'Vue 3 Composition API', 'React 상태 관리',
      '웹 접근성 실무', '반응형 웹 디자인', 'JavaScript 핵심 원리', '모던 CSS 레이아웃',
      'Vite 빌드 최적화', '프론트엔드 성능 개선', 'Storybook 디자인 시스템', 'React Query 데이터 패칭',
      'Nuxt 풀스택 프론트엔드', 'Svelte 입문', '웹 컴포넌트 설계', 'Micro Frontend 아키텍처',
      '브라우저 렌더링 원리', '프론트엔드 보안 기초', 'Playwright E2E 테스트', '프론트엔드 CI/CD',
      'Canvas 데이터 시각화', 'PWA 서비스 개발', '프론트엔드 코드 리뷰', 'Redux Toolkit 실전',
      'Vue Pinia 상태 관리', '대규모 프론트엔드 설계'
    ]
  },
  {
    key: 'OTHER',
    label: 'AI',
    ids: Array.from({ length: 30 }, (_, index) => index + 61),
    titles: [
      '머신러닝 입문', '생성형 AI와 프롬프트 엔지니어링', '딥러닝과 PyTorch', 'RAG 기반 AI 서비스 구축',
      'LLM 애플리케이션 평가와 운영', '자연어 처리 기초', '컴퓨터 비전 입문', 'Transformer 핵심 원리',
      'OpenAI API 서비스 개발', 'LangChain 애플리케이션', '벡터 데이터베이스 활용', 'AI Agent 설계',
      '멀티모달 AI 서비스', '파인튜닝과 모델 최적화', '추천 시스템 입문', '시계열 예측 모델',
      'MLOps 파이프라인', 'AI 모델 설명 가능성', 'Responsible AI 기초', '음성 인식 서비스 개발',
      '이미지 생성 AI 활용', '문서 분류 자동화', 'LLM 프롬프트 평가', '검색 증강 생성 심화',
      '지식 그래프와 AI', '경량 모델 배포', 'AI 서비스 비용 최적화', 'Synthetic Data 생성',
      'LLM 보안과 가드레일', '기업용 AI 아키텍처'
    ]
  },
  {
    key: 'DEVOPS',
    label: 'DevOps',
    ids: Array.from({ length: 30 }, (_, index) => index + 91),
    titles: [
      'Docker 컨테이너 실전', 'Kubernetes 운영 기초', 'GitHub Actions CI/CD', 'AWS 클라우드 아키텍처',
      'Terraform 인프라 자동화', 'Linux 서버 운영', 'Nginx 웹 서버 구성', 'Helm 차트 실전',
      'Argo CD GitOps', 'Jenkins 파이프라인', 'Prometheus 모니터링', 'Grafana 대시보드',
      'ELK 로그 분석', 'OpenTelemetry 분산 추적', 'SRE 기초', '클라우드 비용 최적화',
      'AWS EKS 운영', 'Azure DevOps 입문', 'GCP 인프라 설계', 'Ansible 구성 관리',
      '네트워크와 DNS 기초', '서비스 메시 Istio', 'Kubernetes 보안', '컨테이너 이미지 최적화',
      '무중단 배포 전략', '재해 복구 설계', 'DevSecOps 파이프라인', '플랫폼 엔지니어링',
      'MSA 관측성과 장애 대응', '대규모 클라우드 운영'
    ]
  },
  {
    key: 'DATA_SCIENCE',
    label: '데이터',
    ids: Array.from({ length: 30 }, (_, index) => index + 121),
    titles: [
      'Python 데이터 분석', 'Pandas와 SQL 데이터 처리', '데이터 시각화와 대시보드', '통계 분석 기초',
      'A/B 테스트 실무', 'Tableau 대시보드', 'Power BI 데이터 분석', '데이터 전처리 실전',
      '탐색적 데이터 분석', '비즈니스 지표 설계', '고객 세그먼트 분석', '마케팅 데이터 분석',
      '제품 분석과 퍼널', '시계열 데이터 분석', '공간 데이터 분석', '데이터 품질 관리',
      'Apache Spark 입문', 'PySpark 대용량 분석', '데이터 파이프라인 기초', 'Airflow 워크플로',
      'dbt 분석 엔지니어링', '데이터 웨어하우스 설계', 'BigQuery 데이터 분석', 'Snowflake 활용',
      '실험 설계와 인과 추론', '예측 분석 실무', '텍스트 데이터 분석', '로그 데이터 분석',
      '데이터 스토리텔링', '데이터 기반 의사결정'
    ]
  },
  {
    key: 'DATABASE',
    label: '데이터베이스',
    ids: Array.from({ length: 30 }, (_, index) => index + 151),
    titles: [
      'MySQL 성능 튜닝', 'Redis 캐시 설계', '데이터 모델링 실전', 'SQL 기초',
      'SQL 고급 쿼리', 'PostgreSQL 운영', 'Oracle 데이터베이스 기초', 'MongoDB 문서 모델링',
      'Elasticsearch 검색 설계', '인덱스 설계 원칙', '실행 계획 분석', '데이터베이스 트랜잭션',
      '동시성과 잠금 관리', 'DB 장애 복구', '백업과 복원 실전', '데이터베이스 보안',
      '샤딩과 파티셔닝', '복제와 고가용성', 'NoSQL 데이터 설계', '그래프 데이터베이스',
      '시계열 데이터베이스', '클라우드 데이터베이스', 'RDS 운영 실전', '데이터 마이그레이션',
      'CDC 데이터 동기화', '대용량 배치 쿼리', 'ORM과 데이터베이스', '쿼리 성능 모니터링',
      '분산 데이터베이스', '데이터 아키텍처 설계'
    ]
  },
  {
    key: 'SECURITY',
    label: '보안',
    ids: Array.from({ length: 30 }, (_, index) => index + 181),
    titles: [
      '웹 애플리케이션 보안', 'OAuth2와 OpenID Connect', 'OWASP Top 10 실전', '네트워크 보안 기초',
      '클라우드 보안 아키텍처', 'API 보안 설계', 'JWT 보안 실무', '침투 테스트 입문',
      '취약점 진단 자동화', '보안 로그 분석', 'SIEM 운영 기초', '제로 트러스트 아키텍처',
      'IAM 권한 관리', 'Kubernetes 보안 실전', '컨테이너 보안', 'DevSecOps 구축',
      '암호학 기초', '개인정보 보호 설계', '시큐어 코딩 Java', '시큐어 코딩 JavaScript',
      '모바일 앱 보안', '데이터베이스 보안', '랜섬웨어 대응', '인시던트 대응 실무',
      '디지털 포렌식 입문', '소프트웨어 공급망 보안', 'SAST와 DAST 활용', '보안 위협 모델링',
      'AI 서비스 보안', '기업 보안 거버넌스'
    ]
  },
  {
    key: 'MOBILE',
    label: '모바일',
    ids: Array.from({ length: 30 }, (_, index) => index + 211),
    titles: [
      'Flutter 모바일 앱 개발', 'Dart 프로그래밍 기초', 'Android Kotlin 입문', 'iOS Swift 입문',
      'React Native 앱 개발', 'Flutter 상태 관리', 'Android Jetpack Compose', 'SwiftUI 앱 개발',
      '모바일 UI/UX 구현', '모바일 REST API 연동', 'Firebase 앱 백엔드', '모바일 푸시 알림',
      '앱 결제 시스템', '모바일 인증과 보안', '모바일 데이터 저장', '오프라인 우선 앱 설계',
      '모바일 성능 최적화', '앱 크래시 분석', 'Android 테스트 자동화', 'iOS 테스트 자동화',
      '모바일 CI/CD', '앱스토어 배포 실전', '모바일 접근성', '위치 기반 서비스',
      '카메라와 미디어 처리', 'BLE IoT 앱 개발', 'Flutter 애니메이션', '모바일 아키텍처 패턴',
      '크로스플랫폼 앱 전략', '대규모 모바일 서비스 설계'
    ]
  }
]

for (const domain of domains) {
  if (domain.ids.length !== 30 || domain.titles.length !== 30) {
    throw new Error(`${domain.label} 도메인의 ID와 강의명은 각각 30개여야 합니다.`)
  }
}

const descriptionSuffix = {
  BACKEND: '서버 애플리케이션 설계와 API 구현 역량을 프로젝트로 익힙니다.',
  FRONTEND: '사용자 중심의 웹 화면과 유지보수 가능한 UI 구조를 구현합니다.',
  OTHER: 'AI 모델과 생성형 AI 기술을 실제 서비스 문제에 적용합니다.',
  DEVOPS: '자동화된 배포와 안정적인 서비스 운영 방법을 실습합니다.',
  DATA_SCIENCE: '데이터를 정제하고 분석하여 비즈니스 의사결정에 활용합니다.',
  DATABASE: '안정적이고 확장 가능한 데이터 저장 및 조회 구조를 설계합니다.',
  SECURITY: '서비스의 주요 위협을 이해하고 안전한 대응 방법을 적용합니다.',
  MOBILE: '모바일 환경에 적합한 앱 구조와 사용자 경험을 구현합니다.'
}

const sqlEscape = (value) => value.replaceAll("'", "''")
const courses = domains.flatMap((domain, domainIndex) =>
  domain.titles.map((title, index) => {
    const id = domain.ids[index]
    const price = 39000 + ((index + domainIndex * 2) % 8) * 5000
    const enrollmentCount = 180 + ((id * 73 + domainIndex * 41) % 720)
    const salesCount = enrollmentCount + 35 + ((id * 29) % 140)
    return {
      id,
      title,
      description: `${title}의 핵심 개념을 이해하고 ${descriptionSuffix[domain.key]}`,
      category: domain.key,
      categoryLabel: domain.label,
      price,
      enrollmentCount,
      salesCount
    }
  })
).sort((a, b) => a.id - b.id)

if (courses.length !== 240 || new Set(courses.map((course) => course.id)).size !== 240) {
  throw new Error('강의 데이터는 중복 없는 240개여야 합니다.')
}

const courseById = new Map(courses.map((course) => [course.id, course]))
const sqlRows = courses.map((course) =>
  `    (${course.id}, '${sqlEscape(course.title)}', '${sqlEscape(course.description)}', '${course.category}', ${course.price}, 100, ${course.enrollmentCount}, 'ACTIVE', NOW(6), NOW(6))`
)

const courseSql = `-- 데모용 강의 카탈로그: 8개 도메인 × 30개 = 총 240개
-- scripts/generate_catalog_data.mjs에서 생성합니다.

INSERT IGNORE INTO users (
    id, email, password, name, role, created_at, updated_at
) VALUES (
    100, 'catalog@lecture.local', 'DISABLED_LOGIN', '교육 콘텐츠팀', 'INSTRUCTOR', NOW(6), NOW(6)
);

INSERT INTO courses (
    id, title, description, category, price, instructor_id,
    enrollment_count, status, created_at, updated_at
) VALUES
${sqlRows.join(',\n')}
ON DUPLICATE KEY UPDATE
    title = VALUES(title),
    description = VALUES(description),
    category = VALUES(category),
    price = VALUES(price),
    enrollment_count = VALUES(enrollment_count),
    status = VALUES(status),
    updated_at = NOW(6);
`

const audienceHistories = [
  { id: 201, name: 'user1', courseIds: [3, 32] },
  { id: 202, name: 'user2', courseIds: [1, 4, 6] },
  { id: 203, name: 'user3', courseIds: [121, 61, 62] },
  { id: 204, name: 'user4', courseIds: [91, 92, 93] },
  { id: 205, name: 'user5', courseIds: [1, 3, 6, 32] },
  { id: 206, name: 'user6', courseIds: [121, 122, 151] },
  { id: 207, name: 'user7', courseIds: [5, 181, 182] },
  { id: 208, name: 'user8', courseIds: [211, 212, 3] },
  { id: 209, name: 'user9', courseIds: [1, 2, 7, 8, 15, 16] },
  { id: 210, name: 'user10', courseIds: [61, 62, 63, 64, 65] },
  { id: 211, name: 'user11', courseIds: [91, 92, 94, 95, 101] },
  { id: 212, name: 'user12', courseIds: [3, 32, 34, 35, 36] }
]

const userRows = audienceHistories.map(({ id, name }) =>
  `    (${id}, '${name}@lecture.local', 'DISABLED_LOGIN', '${name}', 'STUDENT', NOW(6), NOW(6))`
)
const enrollmentRows = audienceHistories.flatMap(({ id, courseIds }) =>
  courseIds.map((courseId) => `    (${id}, ${courseId}, 'ACTIVE', NOW(6), NOW(6))`)
)
const audienceSql = `-- 사용자별 수강 이력 데모 데이터
-- scripts/generate_catalog_data.mjs에서 생성합니다.

INSERT INTO users (id, email, password, name, role, created_at, updated_at) VALUES
${userRows.join(',\n')}
ON DUPLICATE KEY UPDATE
    email = VALUES(email),
    name = VALUES(name),
    role = VALUES(role),
    updated_at = NOW(6);

INSERT INTO enrollments (user_id, course_id, status, created_at, updated_at) VALUES
${enrollmentRows.join(',\n')}
ON DUPLICATE KEY UPDATE
    status = VALUES(status),
    updated_at = NOW(6);
`

const coPurchaseMap = new Map()
const addCoPurchase = (courseIds, count) => {
  const ids = [...new Set(courseIds)].sort((a, b) => a - b)
  const key = ids.join('-')
  const coursesForIds = ids.map((id) => courseById.get(id))
  if (coursesForIds.some((course) => !course)) throw new Error(`존재하지 않는 강의 조합: ${key}`)
  coPurchaseMap.set(key, {
    courseIds: ids,
    courseNames: coursesForIds.map((course) => course.title),
    coPurchaseCount: count
  })
}

domains.forEach((domain, domainIndex) => {
  for (let index = 0; index < domain.ids.length - 1; index += 1) {
    addCoPurchase([domain.ids[index], domain.ids[index + 1]], 70 + ((index * 17 + domainIndex * 23) % 210))
  }
  for (let index = 0; index < domain.ids.length - 2; index += 2) {
    addCoPurchase(domain.ids.slice(index, index + 3), 40 + ((index * 13 + domainIndex * 19) % 140))
  }
  for (let index = 0; index < domain.ids.length - 3; index += 4) {
    addCoPurchase(domain.ids.slice(index, index + 4), 20 + ((index * 11 + domainIndex * 17) % 90))
  }
});

[
  [[1, 2], 145], [[1, 2, 91], 164], [[2, 91, 92], 132], [[3, 32, 34], 188],
  [[32, 34, 35], 174], [[61, 62, 64], 205], [[62, 64, 71], 221],
  [[121, 122, 151], 156], [[121, 61, 62], 183], [[5, 181, 182], 149],
  [[91, 92, 94, 95], 118], [[211, 212, 3], 126], [[1, 3, 6, 32], 97]
].forEach(([courseIds, count]) => addCoPurchase(courseIds, count))

const salesData = {
  metadata: {
    description: '사용자별 강의 패키지 추천을 위한 예시 판매 데이터',
    isMockData: true,
    period: '최근 6개월'
  },
  courseSales: courses.map(({ id, title, salesCount }) => ({
    courseId: id,
    courseName: title,
    salesCount
  })),
  coPurchases: [...coPurchaseMap.values()].sort((a, b) => {
    if (a.courseIds.length !== b.courseIds.length) return a.courseIds.length - b.courseIds.length
    return a.courseIds[0] - b.courseIds[0]
  })
}

mkdirSync(resolve(projectRoot, 'init-db'), { recursive: true })
mkdirSync(resolve(projectRoot, 'recommend-service/app/data'), { recursive: true })
writeFileSync(resolve(projectRoot, 'init-db/02_seed_courses.sql'), courseSql)
writeFileSync(resolve(projectRoot, 'init-db/03_seed_audiences.sql'), audienceSql)
writeFileSync(
  resolve(projectRoot, 'recommend-service/app/data/mock_sales_data.json'),
  `${JSON.stringify(salesData, null, 2)}\n`
)

console.log(JSON.stringify({
  courses: courses.length,
  domains: domains.length,
  students: audienceHistories.length,
  enrollments: enrollmentRows.length,
  coPurchases: salesData.coPurchases.length
}, null, 2))
