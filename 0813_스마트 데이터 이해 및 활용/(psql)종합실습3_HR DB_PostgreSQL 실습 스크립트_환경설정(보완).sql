-- ============================================================
-- 종합실습3-1 — HR DB 느린 쿼리 성능 튜닝 실습
-- 환경설정 (PART 0) 전용  |  PostgreSQL 11+  |  psql 실행 버전 (v2)
-- ============================================================
-- ⚠️ psql 사용 안내
--  1) psql은 하나의 세션이 계속 유지되므로, 아래 SET search_path 가
--     스크립트 실행이 끝난 뒤에도 같은 세션 내에서는 유지됩니다.
--  2) 실행 방법
--     - 전체 실행: psql -U <user> -d <db> -f 종합실습3-1_환경설정_psql버전.sql
--     - 또는 psql 접속 후: \i /경로/종합실습3-1_환경설정_psql버전.sql
--  3) 이 스크립트는 환경(스키마/테이블/데이터)만 구성합니다.
--     LAB A~E(문제/실습)는 별도 파일로 제공됩니다.
--
-- [데이터 설계 포인트]
--   - hire_date: 20%는 최근 365일 이내, 80%는 그 이전으로 분산
--     → "최근 365일 입사자" 조건이 항상 결과를 반환하도록 설계
--   - email 도메인: 편향 분포 (gmail.com 약 3%)
--     corp.com 35% / example.com 30% / mail.com 20% / outlook.com 12% / gmail.com 3%
--     → 선행 와일드카드 LIKE 검색 실습에서, 힌트 없이도 플래너가
--       자연스럽게 인덱스를 선택할 수 있을 만큼 선택도를 낮춰둔 것
-- ============================================================

\timing on
\pset pager off

\echo '=== PART 0. 환경 설정 시작 ==='

DROP SCHEMA IF EXISTS hr CASCADE;
CREATE SCHEMA hr;
SET search_path = hr, public;

CREATE TABLE locations (
  location_id   SERIAL PRIMARY KEY,
  city          TEXT NOT NULL,
  country       TEXT NOT NULL,
  region        TEXT NOT NULL
);

CREATE TABLE departments (
  department_id   SERIAL PRIMARY KEY,
  department_name TEXT NOT NULL,
  location_id     INT NOT NULL REFERENCES locations(location_id)
);

CREATE TABLE jobs (
  job_id     SERIAL PRIMARY KEY,
  job_title  TEXT NOT NULL,
  min_salary INT NOT NULL,
  max_salary INT NOT NULL
);

CREATE TABLE employees (
  employee_id   BIGSERIAL PRIMARY KEY,
  first_name    TEXT NOT NULL,
  last_name     TEXT NOT NULL,
  email         TEXT UNIQUE NOT NULL,
  phone         TEXT,
  hire_date     DATE NOT NULL,
  salary        INT NOT NULL,
  manager_id    BIGINT NULL,
  department_id INT NOT NULL REFERENCES departments(department_id),
  job_id        INT NOT NULL REFERENCES jobs(job_id),
  status        TEXT NOT NULL DEFAULT 'ACTIVE'
);

CREATE TABLE job_history (
  employee_id   BIGINT NOT NULL REFERENCES employees(employee_id),
  start_date    DATE NOT NULL,
  end_date      DATE NOT NULL,
  department_id INT NOT NULL REFERENCES departments(department_id),
  job_id        INT NOT NULL REFERENCES jobs(job_id),
  PRIMARY KEY (employee_id, start_date)
);

-- 기준 데이터 적재
INSERT INTO locations(city, country, region)
SELECT
  'City_'||gs::text,
  (ARRAY['KR','US','JP','DE','FR','GB','IN','CN'])[1 + (random()*7)::int],
  (ARRAY['APAC','EMEA','AMER'])[1 + (random()*2)::int]
FROM generate_series(1, 50) gs;

INSERT INTO departments(department_name, location_id)
SELECT
  'Dept_'||gs::text,
  1 + (random() * 49)::int
FROM generate_series(1, 200) gs;

INSERT INTO jobs(job_title, min_salary, max_salary)
SELECT
  'Job_'||gs::text,
  2000 + (random()*1000)::int,
  8000 + (random()*7000)::int
FROM generate_series(1, 40) gs;

-- 대량 employees 생성 (약 50,000건) — hire_date FIXED 로직 + email 도메인 편향 분포
WITH nums AS (
  SELECT gs AS n FROM generate_series(1, 50000) gs
)
INSERT INTO employees(
  first_name, last_name, email, phone, hire_date, salary,
  manager_id, department_id, job_id, status
)
SELECT
  'First_'||n,
  'Last_'||n,
  lower(
    'user'||n||'@'||
    CASE
      WHEN dom < 0.35 THEN 'corp.com'       -- 35%
      WHEN dom < 0.65 THEN 'example.com'    -- 30%
      WHEN dom < 0.85 THEN 'mail.com'       -- 20%
      WHEN dom < 0.97 THEN 'outlook.com'    -- 12%
      ELSE 'gmail.com'                      -- 3%
    END
  ),
  '010-'||lpad(((random()*9999)::int)::text,4,'0')||'-'||lpad(((random()*9999)::int)::text,4,'0'),
  CASE
    WHEN random() < 0.20
      THEN CURRENT_DATE - ((random() * 364)::int)          -- 최근 365일 (20%)
    ELSE
      CURRENT_DATE - (365 + (random() * 3300)::int)        -- 그 이전 (약 9년) (80%)
  END AS hire_date,
  2000 + (random()*10000)::int,
  CASE WHEN random() < 0.2 THEN NULL ELSE 1 + (random()*200)::int END,
  1 + (random()*199)::int,
  1 + (random()*39)::int,
  CASE WHEN random() < 0.05 THEN 'INACTIVE' ELSE 'ACTIVE' END
FROM (
  SELECT n, random() AS dom FROM nums
) t;

-- job_history 일부 생성 (직무/부서 이동 이력)
INSERT INTO job_history(employee_id, start_date, end_date, department_id, job_id)
SELECT
  e.employee_id,
  e.hire_date,
  e.hire_date + (30 + (random()*900)::int),
  1 + (random()*199)::int,
  1 + (random()*39)::int
FROM employees e
WHERE e.employee_id % 10 = 0;  -- 10명 중 1명만 이력 생성

VACUUM ANALYZE;

\echo '=== PART 0. 환경 설정 완료 ==='
\timing off