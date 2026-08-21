# CampusTask 테이블 정의서

표기: PK는 기본키, FK는 외래키, UK는 고유키를 의미한다.

## students - 학생

| 컬럼 | 자료형 | NULL | 키·제약조건 | 기본값 | 설명 |
|---|---|:---:|---|---|---|
| `id` | `BIGINT` | 불가 | PK, IDENTITY | 자동 증가 | 학생 식별자 |
| `student_no` | `VARCHAR(20)` | 불가 | UK | 없음 | 학번 |
| `name` | `VARCHAR(50)` | 불가 |  | 없음 | 학생 이름 |
| `email` | `VARCHAR(100)` | 불가 | UK | 없음 | 이메일 |
| `phone` | `VARCHAR(20)` | 허용 |  | `NULL` | 전화번호 |
| `enrolled` | `BOOLEAN` | 불가 |  | `TRUE` | 재학 여부 |
| `created_at` | `TIMESTAMPTZ` | 불가 |  | `CURRENT_TIMESTAMP` | 학생 등록 일시 |

## courses - 강좌

| 컬럼 | 자료형 | NULL | 키·제약조건 | 기본값 | 설명 |
|---|---|:---:|---|---|---|
| `id` | `BIGINT` | 불가 | PK, IDENTITY | 자동 증가 | 강좌 식별자 |
| `course_code` | `VARCHAR(20)` | 불가 | UK | 없음 | 강좌 코드 |
| `title` | `VARCHAR(100)` | 불가 |  | 없음 | 강좌명 |

## enrollments - 수강신청

| 컬럼 | 자료형 | NULL | 키·제약조건 | 기본값 | 설명 |
|---|---|:---:|---|---|---|
| `student_id` | `BIGINT` | 불가 | PK, FK | 없음 | 학생 식별자 |
| `course_id` | `BIGINT` | 불가 | PK, FK | 없음 | 강좌 식별자 |
| `enrolled_at` | `DATE` | 불가 |  | `CURRENT_DATE` | 수강신청일 |

- 복합 PK: `(student_id, course_id)`
- FK: `student_id` → `students.id`
- FK: `course_id` → `courses.id`

## assignments - 과제

| 컬럼 | 자료형 | NULL | 키·제약조건 | 기본값 | 설명 |
|---|---|:---:|---|---|---|
| `id` | `BIGINT` | 불가 | PK, IDENTITY | 자동 증가 | 과제 식별자 |
| `course_id` | `BIGINT` | 불가 | FK | 없음 | 강좌 식별자 |
| `title` | `VARCHAR(200)` | 불가 |  | 없음 | 과제 제목 |
| `due_at` | `TIMESTAMPTZ` | 불가 |  | 없음 | 제출 마감 일시 |

- FK: `course_id` → `courses.id`

## submissions - 과제 제출

| 컬럼 | 자료형 | NULL | 키·제약조건 | 기본값 | 설명 |
|---|---|:---:|---|---|---|
| `id` | `BIGINT` | 불가 | PK, IDENTITY | 자동 증가 | 제출물 식별자 |
| `assignment_id` | `BIGINT` | 불가 | FK | 없음 | 과제 식별자 |
| `student_id` | `BIGINT` | 불가 | FK | 없음 | 학생 식별자 |
| `submitted_at` | `TIMESTAMPTZ` | 불가 |  | `CURRENT_TIMESTAMP` | 제출 일시 |
| `score` | `NUMERIC(5,2)` | 허용 | CHECK | `NULL` | 점수 |
| `feedback` | `TEXT` | 허용 |  | `NULL` | 피드백 |

- FK: `assignment_id` → `assignments.id`
- FK: `student_id` → `students.id`
- UK: `(assignment_id, student_id)`
- CHECK: `score IS NULL OR score BETWEEN 0 AND 100`

