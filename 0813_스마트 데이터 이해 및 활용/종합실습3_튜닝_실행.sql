-- ============================================================================
-- 종합실습 3: HR DB 느린 쿼리 튜닝
-- PostgreSQL / DBeaver
-- ============================================================================
-- 실행 방법
-- 1. 파일 전체를 한 번에 실행하지 말고 2-1, 2-2 ... 5-2 실험을 블록별로 실행한다.
-- 2. 각 실험은 BEGIN -> 튜닝 전 -> 튜닝 작업 -> 튜닝 후 -> ROLLBACK 순서다.
-- 3. 튜닝 전과 튜닝 후 EXPLAIN 결과를 각각 캡처한다.
-- 4. ROLLBACK으로 현재 실험의 인덱스를 취소하여 다음 실험에 영향을 주지 않게 한다.
-- 5. EXPLAIN에서 Scan 방식, Rows Removed by Filter, Buffers, Execution Time을 기록한다.


-- ----------------------------------------------------------------------------
-- 2번. lower(email) 이메일 검색
-- ----------------------------------------------------------------------------

-- [2-0. 대상 데이터 준비 - 처음에 한 번만 실행]
-- 환경설정의 이메일 도메인이 random()으로 생성되므로 과제의 지정 주소를 확실히 준비한다.
UPDATE hr.employees
SET email = 'user1234@corp.com'
WHERE employee_id = 1234;
ANALYZE hr.employees;


-- ----------------------------------------------------------------------------
-- 2-1. lower(email) 함수 기반 인덱스 방식
-- ----------------------------------------------------------------------------
BEGIN;

-- [2-1 튜닝 전]
-- lower(email)은 원본 email에 생성된 UNIQUE 인덱스와 표현식이 다르므로 Seq Scan이 예상된다.
EXPLAIN (ANALYZE, BUFFERS)
SELECT employee_id, first_name, last_name, email
FROM hr.employees
WHERE lower(email) = lower('USER1234@CORP.COM');

-- [2-1 튜닝 작업]
-- 조회식과 정확히 같은 lower(email) 표현식 인덱스를 생성한다.
CREATE INDEX idx_employees_lower_email
ON hr.employees (lower(email));
ANALYZE hr.employees;

-- [2-1 튜닝 후]
-- SQL은 튜닝 전과 동일하며 idx_employees_lower_email 사용 여부를 확인한다.
EXPLAIN (ANALYZE, BUFFERS)
SELECT employee_id, first_name, last_name, email
FROM hr.employees
WHERE lower(email) = lower('USER1234@CORP.COM');

ROLLBACK;


-- ----------------------------------------------------------------------------
-- 2-2. 소문자 저장 규칙을 이용한 쿼리 재작성
-- ----------------------------------------------------------------------------
BEGIN;

-- [2-2 튜닝 전]
-- 컬럼에 lower()를 적용했으므로 기존 email UNIQUE 인덱스를 직접 사용하지 못한다.
EXPLAIN (ANALYZE, BUFFERS)
SELECT employee_id, first_name, last_name, email
FROM hr.employees
WHERE lower(email) = 'user1234@corp.com';

-- [2-2 튜닝 작업]
-- 환경설정에서 email이 lower()로 저장되므로 컬럼 함수를 제거한다.
-- 추가 인덱스 없이 기존 employees_email_key UNIQUE 인덱스를 재사용한다.
-- ZIP 최종 setup과 동일하게 테이블 통계를 갱신한다.
ANALYZE hr.employees;

-- [2-2 튜닝 후]
EXPLAIN (ANALYZE, BUFFERS)
SELECT employee_id, first_name, last_name, email
FROM hr.employees
WHERE email = 'user1234@corp.com';

ROLLBACK;


-- ----------------------------------------------------------------------------
-- 3번. Gmail 접미사 검색
-- ----------------------------------------------------------------------------

-- ----------------------------------------------------------------------------
-- 3-1. pg_trgm GIN 인덱스 방식
-- ----------------------------------------------------------------------------
BEGIN;

-- [3-1 튜닝 전]
-- 선행 와일드카드 % 때문에 일반 B-tree 인덱스를 사용하기 어려워 Seq Scan이 예상된다.
-- 주의: 실제 SQL은 Markdown 링크가 아닌 '%gmail.com'을 사용한다.
EXPLAIN (ANALYZE, BUFFERS)
SELECT employee_id, email
FROM hr.employees
WHERE email LIKE '%gmail.com';

-- [3-1 튜닝 작업]
-- pg_trgm은 문자열을 삼항으로 색인하여 부분 문자열 검색을 지원한다.
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE INDEX idx_employees_email_trgm
ON hr.employees
USING gin (email gin_trgm_ops);
ANALYZE hr.employees;

-- [3-1 튜닝 후]
-- SQL은 튜닝 전과 동일하며 GIN 인덱스 사용 여부를 확인한다.
EXPLAIN (ANALYZE, BUFFERS)
SELECT employee_id, email
FROM hr.employees
WHERE email LIKE '%gmail.com';

ROLLBACK;


-- ----------------------------------------------------------------------------
-- 3-2. right() 함수 기반 B-tree 인덱스 방식
-- ----------------------------------------------------------------------------
BEGIN;

-- [3-2 튜닝 전]
-- right(email, 10)을 모든 행에 계산해야 하므로 Seq Scan이 예상된다.
EXPLAIN (ANALYZE, BUFFERS)
SELECT employee_id, email
FROM hr.employees
WHERE right(email, 10) = '@gmail.com';

-- [3-2 튜닝 작업]
-- 쿼리와 동일한 right(email, 10) 표현식을 B-tree로 색인한다.
CREATE INDEX idx_employees_email_domain
ON hr.employees (right(email, 10));
ANALYZE hr.employees;

-- [3-2 튜닝 후]
EXPLAIN (ANALYZE, BUFFERS)
SELECT employee_id, email
FROM hr.employees
WHERE right(email, 10) = '@gmail.com';

ROLLBACK;


-- ----------------------------------------------------------------------------
-- 4번. 최근 365일 ACTIVE 직원의 연봉 상위 100명
-- ----------------------------------------------------------------------------

-- ----------------------------------------------------------------------------
-- 4-1. LIMIT + 정렬 우선 복합/커버링 인덱스
-- ----------------------------------------------------------------------------
BEGIN;

-- [4-1 튜닝 전]
-- 조건과 정렬을 지원하는 인덱스가 없으면 Seq Scan + Top-N Sort가 예상된다.
EXPLAIN (ANALYZE, BUFFERS)
SELECT employee_id, email, hire_date, salary, status
FROM hr.employees
WHERE status = 'ACTIVE'
  AND hire_date >= CURRENT_DATE - INTERVAL '365 days'
ORDER BY salary DESC, employee_id
LIMIT 100;

-- [4-1 튜닝 작업]
-- salary DESC, employee_id를 ORDER BY와 일치시키고 조회 컬럼을 INCLUDE한다.
-- 정렬된 인덱스를 읽다가 최근 ACTIVE 직원 100명을 채우면 중단할 수 있다.
CREATE INDEX idx_employees_salary_desc_cover
ON hr.employees (salary DESC, employee_id)
INCLUDE (email, hire_date, status);
ANALYZE hr.employees;

-- [4-1 튜닝 후]
-- 튜닝 전과 같은 LIMIT SQL을 실행하고 Sort 제거 및 인덱스 사용 여부를 확인한다.
EXPLAIN (ANALYZE, BUFFERS)
SELECT employee_id, email, hire_date, salary, status
FROM hr.employees
WHERE status = 'ACTIVE'
  AND hire_date >= CURRENT_DATE - INTERVAL '365 days'
ORDER BY salary DESC, employee_id
LIMIT 100;

ROLLBACK;


-- ----------------------------------------------------------------------------
-- 4-2. FETCH FIRST + ACTIVE 전용 부분 인덱스
-- ----------------------------------------------------------------------------
BEGIN;

-- [4-2 튜닝 전]
-- FETCH FIRST는 LIMIT과 논리적으로 같은 상위 100건을 요청하며 Seq Scan + Top-N Sort가 예상된다.
EXPLAIN (ANALYZE, BUFFERS)
SELECT employee_id, email, hire_date, salary, status
FROM hr.employees
WHERE hire_date >= CURRENT_DATE - INTERVAL '365 days'
  AND status = 'ACTIVE'
ORDER BY salary DESC, employee_id
FETCH FIRST 100 ROWS ONLY;

-- [4-2 튜닝 작업]
-- ACTIVE 행만 색인하는 부분 인덱스로 크기와 유지 범위를 줄인다.
-- salary DESC, employee_id를 ORDER BY와 일치시켜 별도 정렬을 줄인다.
CREATE INDEX idx_employees_active_salary_desc_cover
ON hr.employees (salary DESC, employee_id)
INCLUDE (email, hire_date, status)
WHERE status = 'ACTIVE';
ANALYZE hr.employees;

-- [4-2 튜닝 후]
EXPLAIN (ANALYZE, BUFFERS)
SELECT employee_id, email, hire_date, salary, status
FROM hr.employees
WHERE hire_date >= CURRENT_DATE - INTERVAL '365 days'
  AND status = 'ACTIVE'
ORDER BY salary DESC, employee_id
FETCH FIRST 100 ROWS ONLY;

ROLLBACK;


-- ----------------------------------------------------------------------------
-- 5번. department_id=10 또는 job_id IN (3,4,5)
-- ----------------------------------------------------------------------------

-- ----------------------------------------------------------------------------
-- 5-1. OR 유지 + 두 개의 단일 컬럼 인덱스
-- ----------------------------------------------------------------------------
BEGIN;

-- [5-1 튜닝 전]
-- OR의 두 컬럼에 인덱스가 없으면 Seq Scan이 예상된다.
EXPLAIN (ANALYZE, BUFFERS)
SELECT employee_id, department_id, job_id, email
FROM hr.employees
WHERE department_id = 10
   OR job_id IN (3, 4, 5);

-- [5-1 튜닝 작업]
-- OR의 각 컬럼에 개별 B-tree 인덱스를 생성한다.
-- PostgreSQL이 두 인덱스를 BitmapOr로 결합하는지 확인한다.
CREATE INDEX idx_employees_department_id ON hr.employees (department_id);
CREATE INDEX idx_employees_job_id        ON hr.employees (job_id);
ANALYZE hr.employees;

-- [5-1 튜닝 후]
EXPLAIN (ANALYZE, BUFFERS)
SELECT employee_id, department_id, job_id, email
FROM hr.employees
WHERE department_id = 10
   OR job_id IN (3, 4, 5);

ROLLBACK;


-- ----------------------------------------------------------------------------
-- 5-2. 부분 커버링 인덱스 + UNION ALL
-- ----------------------------------------------------------------------------
BEGIN;

-- [5-2 튜닝 전]
-- 각 분기에 인덱스가 없어 두 번의 Seq Scan이 발생하고 UNION의 HashAggregate 중복 제거 비용도 추가된다.
EXPLAIN (ANALYZE, BUFFERS)
SELECT employee_id, department_id, job_id, email
FROM hr.employees
WHERE department_id = 10

UNION

SELECT employee_id, department_id, job_id, email
FROM hr.employees
WHERE job_id IN (3, 4, 5);

-- [5-2 튜닝 작업]
-- 각 조건에 해당하는 행만 저장하는 부분 인덱스를 생성한다.
-- 반환 컬럼을 INCLUDE하여 테이블 접근 없는 Index Only Scan을 유도한다.
CREATE INDEX lab_q5_department_cover_idx
ON hr.employees (department_id)
INCLUDE (employee_id, job_id, email)
WHERE department_id = 10;

CREATE INDEX lab_q5_job_cover_idx
ON hr.employees (job_id)
INCLUDE (employee_id, department_id, email)
WHERE job_id IN (3, 4, 5);
ANALYZE hr.employees;

-- [5-2 튜닝 후]
-- UNION ALL로 HashAggregate를 제거하고, 두 번째 분기에서 부서 10을 제외해 중복을 직접 방지한다.
-- Index Only Scan 2회 + Append, Heap Fetches 0을 확인한다.
EXPLAIN (ANALYZE, BUFFERS)
SELECT employee_id, department_id, job_id, email
FROM hr.employees
WHERE department_id = 10

UNION ALL

SELECT employee_id, department_id, job_id, email
FROM hr.employees
WHERE job_id IN (3, 4, 5)
  AND department_id <> 10;

ROLLBACK;
