# CampusTask

학생의 강좌 수강정보와 강좌별 과제 및 제출 결과를 관리하는 PostgreSQL 학사관리 실습 프로젝트입니다.

## 프로젝트 범위

- 학생과 강좌 관리
- 수강신청 교차 테이블 관리
- 강좌별 과제 관리
- 학생별 과제 제출 및 채점 결과 관리
- `WHERE`, `ORDER BY`, `COALESCE`, `CASE WHEN`, 날짜 함수, `JOIN` 실습

로그인, 파일 업로드, 알림, 재제출 이력은 1일차 범위에서 제외합니다.

## 디렉터리

```text
CampusTask/
├─ README.md
├─ docs/
│  ├─ requirements.md
│  └─ table-definition.md
├─ erd/
│  └─ campus-task-erd.mmd
└─ sql/
   ├─ 01-create-database.sql
   ├─ 02-create-schema.sql
   ├─ 03-create-tables.sql
   ├─ 04-insert-sample-data.sql
   └─ 05-practice-queries.sql
```

## SQL 실행 순서

1. 기본 `postgres` 데이터베이스에 접속합니다.
2. `01-create-database.sql`을 실행합니다.
3. 새로 생성된 `campus_task_db` 데이터베이스에 다시 접속합니다.
4. `02-create-schema.sql`부터 `05-practice-queries.sql`까지 번호순으로 실행합니다.

`04-insert-sample-data.sql`은 비어 있는 테이블에서 한 번 실행하는 것을 기준으로 작성했습니다.

## 샘플 데이터 수

| 테이블 | 데이터 수 |
|---|---:|
| `students` | 12건 |
| `courses` | 10건 |
| `enrollments` | 24건 |
| `assignments` | 10건 |
| `submissions` | 12건 |

