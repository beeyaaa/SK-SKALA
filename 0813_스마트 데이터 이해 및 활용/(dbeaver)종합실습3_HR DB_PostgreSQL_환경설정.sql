-- ============================================================
-- 종합실습3-1 — HR DB 느린 쿼리 성능 튜닝 실습
-- 환경설정 전용 (PART 0)  |  PostgreSQL 11+  |  DBeaver 실행 버전
-- ============================================================
-- ⚠️ DBeaver 사용 안내
--  1) 이 스크립트는 "환경(스키마/테이블/데이터)만" 구성합니다.
--     실습 문항(성능 튜닝 LAB)은 별도 파일로 진행합니다.
--  2) DBeaver는 커넥션 풀 특성상 SET search_path가 다음 쿼리 실행 시
--     끊길 수 있습니다. 그래서 이 스크립트는 SET search_path 대신
--     모든 테이블 참조에 hr. 스키마를 명시적으로 붙였습니다.
--  3) 실행 방법: 전체 실행(▶▶ Execute SQL Script, Alt+X / Cmd+Shift+Enter)
--     한 번으로 충분합니다. 위→아래 순서대로 한 세션(탭)에서 실행하세요.
--  4) 실습 문항을 풀 때도 테이블을 참조할 때 반드시 hr. 접두사를
--     붙여서 사용하세요 (예: hr.employees).
--
-- [데이터 설계 포인트]
--   - hire_date: 20%는 최근 365일 이내, 80%는 그 이전으로 분산
--     → "최근 365일 입사자" 조건이 항상 결과를 반환하도록 설계
--   - email 도메인: 편향 분포 (gmail.com 약 3%)
--     corp.com 35% / example.com 30% / mail.com 20% / outlook.com 12% / gmail.com 3%
--     → 선행 와일드카드 LIKE 검색 실습에서, 힌트 없이도 플래너가
--       자연스럽게 인덱스를 선택할 수 있을 만큼 선택도를 낮춰둔 것
-- ============================================================

-- ================================================================
-- PART 0. 환경 설정 (스키마 / 테이블 / 데이터)
-- ================================================================

DROP SCHEMA IF EXISTS hr CASCADE;
CREATE SCHEMA hr;

CREATE TABLE hr.locations (
  location_id   SERIAL PRIMARY KEY,
  city          TEXT NOT NULL,
  country       TEXT NOT NULL,
  region        TEXT NOT NULL
);

CREATE TABLE hr.departments (
  department_id   SERIAL PRIMARY KEY,
  department_name TEXT NOT NULL,
  location_id     INT NOT NULL REFERENCES hr.locations(location_id)
);

CREATE TABLE hr.jobs (
  job_id     SERIAL PRIMARY KEY,
  job_title  TEXT NOT NULL,
  min_salary INT NOT NULL,
  max_salary INT NOT NULL
);

CREATE TABLE hr.employees (
  employee_id   BIGSERIAL PRIMARY KEY,
  first_name    TEXT NOT NULL,
  last_name     TEXT NOT NULL,
  email         TEXT UNIQUE NOT NULL,
  phone         TEXT,
  hire_date     DATE NOT NULL,
  salary        INT NOT NULL,
  manager_id    BIGINT NULL,
  department_id INT NOT NULL REFERENCES hr.departments(department_id),
  job_id        INT NOT NULL REFERENCES hr.jobs(job_id),
  status        TEXT NOT NULL DEFAULT 'ACTIVE'
);

CREATE TABLE hr.job_history (
  employee_id   BIGINT NOT NULL REFERENCES hr.employees(employee_id),
  start_date    DATE NOT NULL,
  end_date      DATE NOT NULL,
  department_id INT NOT NULL REFERENCES hr.departments(department_id),
  job_id        INT NOT NULL REFERENCES hr.jobs(job_id),
  PRIMARY KEY (employee_id, start_date)
);

-- 기준 데이터 적재
INSERT INTO hr.locations(city, country, region)
SELECT
  'City_'||gs::text,
  (ARRAY['KR','US','JP','DE','FR','GB','IN','CN'])[1 + (random()*7)::int],
  (ARRAY['APAC','EMEA','AMER'])[1 + (random()*2)::int]
FROM generate_series(1, 50) gs;

INSERT INTO hr.departments(department_name, location_id)
SELECT
  'Dept_'||gs::text,
  1 + (random() * 49)::int
FROM generate_series(1, 200) gs;

INSERT INTO hr.jobs(job_title, min_salary, max_salary)
SELECT
  'Job_'||gs::text,
  2000 + (random()*1000)::int,
  8000 + (random()*7000)::int
FROM generate_series(1, 40) gs;

-- 대량 employees 생성 (약 50,000건) — hire_date FIXED 로직 + email 도메인 편향 분포
WITH nums AS (
  SELECT gs AS n FROM generate_series(1, 50000) gs
)
INSERT INTO hr.employees(
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
INSERT INTO hr.job_history(employee_id, start_date, end_date, department_id, job_id)
SELECT
  e.employee_id,
  e.hire_date,
  e.hire_date + (30 + (random()*900)::int),
  1 + (random()*199)::int,
  1 + (random()*39)::int
FROM hr.employees e
WHERE e.employee_id % 10 = 0;  -- 10명 중 1명만 이력 생성

-- DBeaver/JDBC 일괄 실행의 pipeline mode에서 VACUUM은 실행할 수 없으므로
-- 환경 구성 스크립트에서는 ANALYZE만 수행한다.
ANALYZE hr.locations;
ANALYZE hr.departments;
ANALYZE hr.jobs;
ANALYZE hr.employees;
ANALYZE hr.job_history;
