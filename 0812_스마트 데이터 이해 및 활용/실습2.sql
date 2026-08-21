-- ============================================================
-- [종합실습 2 - 1번]
-- 1. 학생과 수강을 INNER JOIN하여 수강 존재 학생의 과목/성적을 조회
--
-- INNER JOIN 특징:
-- student와 enroll 양쪽에 student_id가 존재하는 행만 출력된다.
-- 따라서 수강 이력이 없는 학생과 학생 정보가 없는 고아 수강은 제외된다.
-- ============================================================

SELECT
    s.student_id AS 학생_ID,  -- 학생의 고유번호
    s.name       AS 학생명,   -- 학생 이름
    e.course     AS 과목,     -- 수강 과목명
    e.grade      AS 성적      -- 해당 과목의 성적
FROM lab.student AS s         -- student 테이블에 s라는 별칭 지정
INNER JOIN lab.enroll AS e    -- enroll 테이블에 e라는 별칭 지정
    ON s.student_id = e.student_id
    -- 두 테이블에서 student_id가 같은 행끼리 연결한다.
    -- INNER JOIN이므로 양쪽 테이블에 모두 존재하는 행만 남는다.
ORDER BY
    s.student_id ASC,         -- 학생 번호를 오름차순으로 정렬
    e.course ASC;             -- 같은 학생은 과목명을 오름차순으로 정렬
    
-- ============================================================
-- [종합실습 2 - 2번]
-- 모든 학생을 기준으로 수강 정보를 연결한다.
--
-- LEFT JOIN을 사용하므로 수강 기록이 없는 학생도 출력된다.
-- 수강 기록이 없으면 과목과 성적이 NULL로 표시된다.
-- 학생 정보가 없는 고아 수강 1001, 1010은 LEFT JOIN 결과에 포함되지 않는다.
-- ============================================================

SELECT
    s.student_id AS 학생_ID,  -- 학생 번호
    s.name       AS 학생명,   -- 학생 이름
    s.major      AS 전공,     -- 학생 전공
    e.course     AS 과목,     -- 수강 과목, 미수강이면 NULL
    e.grade      AS 성적      -- 과목 성적, 미수강이면 NULL
FROM lab.student AS s         -- 모든 학생을 기준으로 조회
LEFT JOIN lab.enroll AS e     -- 학생의 수강 정보를 연결
    ON s.student_id = e.student_id
    -- 수강 정보가 없어도 왼쪽 student 행은 유지된다.
ORDER BY
    s.student_id,             -- 학생 번호 오름차순
    e.course;                 -- 같은 학생은 과목명 오름차순
    
    -- ============================================================
-- [종합실습 2 - 3번]
-- 모든 수강 기록을 기준으로 학생 정보를 연결한다.
--
-- RIGHT JOIN을 사용하므로 student에 없는 수강 기록도 출력된다.
-- 학생 정보가 없는 수강 기록은 학생_ID, 학생명, 전공이 NULL로 표시된다.
-- ============================================================

SELECT
    s.student_id AS 학생_ID,       -- student에 존재하지 않으면 NULL
    s.name       AS 학생명,        -- student에 존재하지 않으면 NULL
    s.major      AS 전공,          -- student에 존재하지 않으면 NULL
    e.student_id AS 수강_학생_ID,  -- enroll에 기록된 학생 번호
    e.course     AS 과목,          -- 수강 과목
    e.grade      AS 성적           -- 과목 성적
FROM lab.student AS s
RIGHT JOIN lab.enroll AS e         -- 모든 enroll 행을 유지
    ON s.student_id = e.student_id
    -- student에 같은 학생 번호가 없어도 enroll 행은 출력된다.
ORDER BY
    e.student_id,
    e.course;

-- ============================================================
-- [종합실습 2 - 4번]
-- FULL OUTER JOIN으로 학생과 수강 양쪽의 모든 데이터를 조회한다.
--
-- 포함되는 데이터:
-- 1. 학생 정보와 수강 정보가 모두 있는 정상 수강 기록
-- 2. 학생 정보만 있는 미수강 학생
-- 3. 수강 정보만 있는 고아 수강 기록(1001, 1010)
-- ============================================================

SELECT
    s.student_id AS 학생_ID,       -- student의 학생 번호
    s.name       AS 학생명,        -- 학생 정보가 없으면 NULL
    s.major      AS 전공,          -- 학생 정보가 없으면 NULL
    e.student_id AS 수강_학생_ID,  -- enroll에 기록된 학생 번호
    e.course     AS 과목,          -- 미수강 학생이면 NULL
    e.grade      AS 성적           -- 미수강 학생이면 NULL
FROM lab.student AS s
FULL OUTER JOIN lab.enroll AS e
    ON s.student_id = e.student_id
ORDER BY
    COALESCE(s.student_id, e.student_id) ASC,
    e.course ASC;

-- ============================================================
-- [종합실습 2 - 5번]
-- 한 번도 수강하지 않은 학생 목록을 조회한다.
--
-- 처리 방식:
-- 1. LEFT JOIN으로 모든 학생을 유지한다.
-- 2. 수강 기록이 없는 학생은 enroll 컬럼이 NULL이 된다.
-- 3. WHERE에서 enroll의 student_id가 NULL인 행만 선택한다.
--
-- 이 방식을 LEFT JOIN 기반 Anti Join이라고 한다.
-- ============================================================

SELECT
    s.student_id AS 학생_ID,  -- 학생 번호
    s.name       AS 학생명,   -- 학생 이름
    s.major      AS 전공,     -- 학생 전공
    s.gpa        AS GPA       -- 학생 GPA
FROM lab.student AS s
LEFT JOIN lab.enroll AS e
    ON s.student_id = e.student_id
WHERE e.student_id IS NULL    -- 수강 기록이 없는 학생만 선택
ORDER BY s.student_id ASC;

-- ============================================================
-- [종합실습 2 - 6번]
-- 한 과목 이상 수강한 학생 목록을 조회한다.
--
-- 처리 방식:
-- 1. INNER JOIN으로 학생과 수강 기록을 연결한다.
-- 2. 한 학생이 여러 과목을 수강하면 같은 학생이 여러 행으로 나온다.
-- 3. DISTINCT로 중복 학생을 제거해 학생당 한 행만 출력한다.
-- ============================================================

SELECT DISTINCT
    s.student_id AS 학생_ID,  -- 학생 번호
    s.name       AS 학생명,   -- 학생 이름
    s.major      AS 전공,     -- 학생 전공
    s.gpa        AS GPA       -- 학생 GPA
FROM lab.student AS s
INNER JOIN lab.enroll AS e
    ON s.student_id = e.student_id
    -- 수강 기록이 존재하는 학생만 연결된다.
ORDER BY s.student_id ASC;

-- ============================================================
-- [종합실습 2 - 7번]
-- 고객별 주문 건수와 주문 총액을 조회한다.
--
-- 처리 방식:
-- 1. customers와 orders를 customer_id로 연결한다.
-- 2. 고객별로 GROUP BY한다.
-- 3. COUNT로 주문 건수를 계산한다.
-- 4. SUM으로 주문 총액을 계산한다.
-- ============================================================

SELECT
    c.customer_id   AS 고객_ID,    -- 고객 번호
    c.customer_name AS 고객명,     -- 고객 이름
    COUNT(o.order_id) AS 주문_건수, -- 고객별 주문 개수
    SUM(o.amount)     AS 주문_총액  -- 고객별 주문금액 합계
FROM lab.customers AS c
INNER JOIN lab.orders AS o
    ON c.customer_id = o.customer_id
    -- customers와 orders의 고객 번호가 같은 행을 연결한다.
GROUP BY
    c.customer_id,
    c.customer_name
    -- 고객 한 명을 하나의 그룹으로 묶는다.
ORDER BY
    c.customer_id ASC;

-- ============================================================
-- [종합실습 2 - 8번]
-- 고객별 주문 총액을 계산하고,
-- 주문 총액이 높은 고객 상위 10명을 조회한다.
--
-- 처리 방식:
-- 1. customers와 orders를 customer_id로 연결한다.
-- 2. 고객별로 주문금액을 합산한다.
-- 3. 주문 총액을 내림차순으로 정렬한다.
-- 4. LIMIT 10으로 상위 10명만 출력한다.
-- ============================================================

SELECT
    c.customer_id     AS 고객_ID,   -- 고객 번호
    c.customer_name   AS 고객명,    -- 고객 이름
    SUM(o.amount)     AS 주문_총액  -- 고객별 주문금액 합계
FROM lab.customers AS c
INNER JOIN lab.orders AS o
    ON c.customer_id = o.customer_id
    -- 고객 번호가 같은 주문 기록을 연결한다.
GROUP BY
    c.customer_id,
    c.customer_name
    -- 고객 한 명을 하나의 그룹으로 묶는다.
ORDER BY
    주문_총액 DESC,   -- 주문 총액이 높은 고객부터 정렬
    c.customer_id ASC -- 총액이 같으면 고객 번호 오름차순
LIMIT 10;             -- 정렬된 결과 중 상위 10명만 출력

-- ============================================================
-- [종합실습 2 - 9번]
-- 모든 직원과 각 직원의 매니저 이름을 조회한다.
--
-- Self Join:
-- 하나의 emp 테이블을 직원용(e)과 매니저용(m)으로 두 번 참조한다.
--
-- LEFT JOIN을 사용하는 이유:
-- CEO는 manager_id가 NULL이지만 결과에 포함해야 하기 때문이다.
-- ============================================================

SELECT
    e.emp_id     AS 직원_ID,    -- 직원 번호
    e.name       AS 직원명,     -- 직원 이름
    e.manager_id AS 매니저_ID,  -- 직원에게 지정된 매니저 번호
    m.name       AS 매니저명    -- 같은 테이블에서 찾은 매니저 이름
FROM lab.emp AS e               -- e: 직원으로 사용한 emp 테이블
LEFT JOIN lab.emp AS m          -- m: 매니저로 사용한 동일한 emp 테이블
    ON e.manager_id = m.emp_id
    -- 직원의 manager_id와 매니저의 emp_id를 연결한다.
ORDER BY
    e.emp_id ASC;

-- ============================================================
-- [종합실습 2 - 10번]
-- 모든 학생을 기준으로 과목별 학생 수를 집계한다.
--
-- 처리 방식:
-- 1. LEFT JOIN으로 미수강 학생까지 유지한다.
-- 2. 수강 과목이 NULL이면 '미수강'으로 표시한다.
-- 3. 과목별로 GROUP BY하여 학생 수를 계산한다.
--
-- COUNT(s.student_id)를 사용하는 이유:
-- 미수강 학생도 student_id는 존재하므로 100명으로 집계된다.
-- COUNT(e.student_id)를 사용하면 미수강 그룹은 0명으로 계산된다.
-- ============================================================

SELECT
    COALESCE(e.course, '미수강') AS 과목,  -- NULL 과목은 미수강으로 표시
    COUNT(s.student_id)          AS 학생_수 -- 해당 과목에 포함된 학생 수
FROM lab.student AS s
LEFT JOIN lab.enroll AS e
    ON s.student_id = e.student_id
    -- 모든 학생을 유지하면서 수강 정보를 연결한다.
GROUP BY
    e.course
    -- 과목별로 그룹화하며 NULL도 하나의 그룹으로 집계된다.
ORDER BY
    CASE WHEN e.course IS NULL THEN 1 ELSE 0 END,
    -- 실제 과목을 먼저 표시하고 미수강은 마지막에 표시한다.
    e.course ASC;

-- ============================================================
-- [종합실습 2 - 11번]
-- DB 과목을 수강하지 않은 모든 학생을 조회한다.
--
-- NOT EXISTS:
-- 각 학생에 대해 course가 'DB'인 수강 기록이 존재하는지 확인하고,
-- 해당 기록이 존재하지 않는 학생만 결과에 포함한다.
--
-- 포함 대상:
-- 1. 다른 과목은 수강했지만 DB 과목은 수강하지 않은 학생
-- 2. 아무 과목도 수강하지 않은 학생
-- ============================================================

SELECT
    s.student_id AS 학생_ID, -- 학생 번호
    s.name       AS 학생명,  -- 학생 이름
    s.major      AS 전공,    -- 학생 전공
    s.gpa        AS GPA      -- 학생 GPA
FROM lab.student AS s
WHERE NOT EXISTS (
    SELECT 1
    FROM lab.enroll AS e
    WHERE e.student_id = s.student_id
      AND e.course = 'DB'
      -- 현재 학생에게 DB 과목 수강 기록이 있는지 확인한다.
)
ORDER BY
    s.student_id ASC;

-- ============================================================
-- [종합실습 2 - 12번 / 1단계]
-- 과목별 책임 매니저를 저장할 course_owner 테이블을 생성한다.
--
-- course:
-- 과목을 구분하는 기본키
--
-- manager_id:
-- 해당 과목을 담당하는 매니저 번호
-- emp 테이블의 emp_id를 참조하는 외래키
-- ============================================================

CREATE TABLE IF NOT EXISTS lab.course_owner (
    course     VARCHAR(50) PRIMARY KEY,
    manager_id INT NOT NULL
);

-- ============================================================
-- [종합실습 2 - 12번 / 2단계]
-- enroll에 존재하는 과목들을 Mgr_2~Mgr_11에게 순서대로 배정한다.
--
-- 과목과 매니저에 각각 순번을 부여하고,
-- MOD 연산으로 10명의 매니저에게 과목을 반복 배정한다.
--
-- ON CONFLICT:
-- 같은 과목이 이미 존재해도 오류가 발생하지 않도록
-- 기존 manager_id를 다시 갱신한다.
-- ============================================================

WITH course_list AS (
    SELECT
        e.course,
        ROW_NUMBER() OVER (
            ORDER BY e.course
        ) AS course_order
    FROM lab.enroll AS e
    GROUP BY e.course
),
manager_list AS (
    SELECT
        e.emp_id,
        ROW_NUMBER() OVER (
            ORDER BY e.emp_id
        ) AS manager_order
    FROM lab.emp AS e
    WHERE LEFT(e.name, 4) = 'Mgr_'
)
INSERT INTO lab.course_owner (
    course,
    manager_id
)
SELECT
    c.course,
    m.emp_id
FROM course_list AS c
INNER JOIN manager_list AS m
    ON m.manager_order = MOD(c.course_order - 1, 10) + 1
ON CONFLICT (course)
DO UPDATE SET
    manager_id = EXCLUDED.manager_id;

-- ============================================================
-- [종합실습 2 - 12번 / 3단계]
-- 과목별 수강 인원과 책임 매니저를 조회한다.
--
-- course_owner와 enroll을 과목명으로 연결하고,
-- course_owner와 emp를 manager_id로 연결한다.
--
-- COUNT(DISTINCT e.student_id):
-- 같은 학생이 중복 집계되지 않도록 학생 번호를 기준으로 계산한다.
-- ============================================================

SELECT
    co.course                   AS 과목,          -- 과목명
    COUNT(DISTINCT e.student_id) AS 수강_인원,    -- 과목별 수강 인원
    m.emp_id                    AS 책임_매니저_ID, -- 책임 매니저 번호
    m.name                      AS 책임_매니저명   -- 책임 매니저 이름
FROM lab.course_owner AS co
LEFT JOIN lab.enroll AS e
    ON co.course = e.course
INNER JOIN lab.emp AS m
    ON co.manager_id = m.emp_id
GROUP BY
    co.course, 
    m.emp_id,
    m.name
ORDER BY
    co.course ASC;

-- ============================================================
-- [종합실습 2 - 13번]
-- 학생과 과목의 전체 조합을 생성하여
-- 학생별 과목 추천 후보를 만든다.
--
-- CROSS JOIN:
-- 모든 학생을 모든 과목과 한 번씩 조합한다.
--
-- student는 1,000명이고 과목은 23개이므로
-- 전체 조합은 1,000 × 23 = 23,000행이다.
-- 문제 요구사항에 따라 그중 100행만 조회한다.
-- ============================================================

SELECT
    s.student_id AS 학생_ID, -- 학생 번호
    s.name       AS 학생명,  -- 학생 이름
    s.major      AS 전공,    -- 학생 전공
    c.course     AS 추천_과목 -- 학생과 조합된 과목
FROM lab.student AS s
CROSS JOIN (
    -- 별도의 과목 테이블이 없으므로
    -- enroll에서 중복되지 않은 과목 목록을 만든다.
    SELECT DISTINCT
        e.course
    FROM lab.enroll AS e
) AS c
ORDER BY
    s.student_id ASC,
    c.course ASC
LIMIT 100;

-- ============================================================
-- [종합실습 2 - 14번]
-- SELECT 절의 스칼라 서브쿼리를 사용하여
-- 각 학생에게 소속 학과명을 붙인다.
--
-- 스칼라 서브쿼리:
-- 실행 결과로 하나의 값만 반환하는 서브쿼리이다.
--
-- 현재 실습 DB에는 별도의 학과 테이블이 없으므로
-- student 테이블에서 현재 학생의 major를 다시 조회한다.
-- student_id는 기본키이므로 서브쿼리는 정확히 한 행만 반환한다.
-- ============================================================

SELECT
    s.student_id AS 학생_ID, -- 학생 번호
    s.name       AS 학생명,  -- 학생 이름
    s.gpa        AS GPA,     -- 학생 GPA

    (
        SELECT
            s2.major
        FROM lab.student AS s2
        WHERE s2.student_id = s.student_id
        -- 바깥쪽 현재 학생과 같은 학생 번호의 major를 가져온다.
    ) AS 소속_학과명

FROM lab.student AS s
ORDER BY
    s.student_id ASC;

-- ============================================================
-- [종합실습 2 - 15번]
-- 전체 학생의 평균 GPA보다 GPA가 높은 학생을 조회한다.
--
-- WHERE 절의 서브쿼리에서 전체 평균 GPA를 먼저 계산한다.
-- 바깥쪽 쿼리는 각 학생의 GPA를 전체 평균과 비교한다.
-- ============================================================

SELECT
    s.student_id AS 학생_ID, -- 학생 번호
    s.name       AS 학생명,  -- 학생 이름
    s.major      AS 전공,    -- 학생 전공
    s.gpa        AS GPA      -- 학생 GPA
FROM lab.student AS s
WHERE s.gpa > (
    SELECT
        AVG(s2.gpa)
    FROM lab.student AS s2
    -- 전체 학생의 평균 GPA 하나를 반환한다.
)
ORDER BY
    s.gpa DESC,         -- GPA가 높은 학생부터 정렬
    s.student_id ASC;   -- GPA가 같으면 학생 번호 오름차순
    
    -- ============================================================
-- [종합실습 2 - 16번]
-- 각 학생의 GPA를 자신이 속한 학과의 평균 GPA와 비교하여
-- 학과 평균보다 GPA가 높은 학생을 조회한다.
--
-- 상관 서브쿼리(Correlated Subquery):
-- 안쪽 서브쿼리에서 바깥 쿼리의 s.major를 참조한다.
-- 따라서 학생마다 해당 학생의 학과 평균을 다시 계산하여 비교한다.
-- ============================================================

SELECT
    s.student_id AS 학생_ID, -- 학생 번호
    s.name       AS 학생명,  -- 학생 이름
    s.major      AS 전공,    -- 학생이 속한 학과
    s.gpa        AS GPA      -- 학생 GPA
FROM lab.student AS s
WHERE s.gpa > (
    SELECT
        AVG(s2.gpa)
    FROM lab.student AS s2
    WHERE s2.major = s.major
    -- 현재 학생과 같은 학과의 학생들만 평균 계산
)
ORDER BY
    s.major ASC,       -- 학과명 오름차순
    s.gpa DESC,        -- 학과 안에서 GPA 내림차순
    s.student_id ASC;  -- GPA가 같으면 학생 번호 오름차순
    
    -- ============================================================
-- [종합실습 2 - 17번]
-- 수강(enroll) 기록이 하나 이상 존재하는 학생만 조회한다.
--
-- EXISTS:
-- 현재 학생과 일치하는 수강 기록이 한 행이라도 존재하면 TRUE가 된다.
-- EXISTS는 존재 여부만 확인하므로 학생이 여러 과목을 수강해도
-- 학생 한 명당 결과는 한 행만 출력된다.
-- ============================================================

SELECT
    s.student_id AS 학생_ID, -- 학생 번호
    s.name       AS 학생명,  -- 학생 이름
    s.major      AS 전공,    -- 학생 전공
    s.gpa        AS GPA      -- 학생 GPA
FROM lab.student AS s
WHERE EXISTS (
    SELECT 1
    FROM lab.enroll AS e
    WHERE e.student_id = s.student_id
    -- 현재 학생의 수강 기록이 존재하는지 확인한다.
)
ORDER BY
    s.student_id ASC;

-- ============================================================
-- [종합실습 2 - 18번]
-- 수강 기록이 한 건도 없는 학생을 조회한다.
--
-- NOT EXISTS:
-- 현재 학생과 일치하는 수강 기록이 존재하지 않을 때 TRUE가 된다.
-- 따라서 enroll에 기록이 없는 학생만 결과에 포함된다.
-- ============================================================

SELECT
    s.student_id AS 학생_ID, -- 학생 번호
    s.name       AS 학생명,  -- 학생 이름
    s.major      AS 전공,    -- 학생 전공
    s.gpa        AS GPA      -- 학생 GPA
FROM lab.student AS s
WHERE NOT EXISTS (
    SELECT 1
    FROM lab.enroll AS e
    WHERE e.student_id = s.student_id
    -- 현재 학생의 수강 기록이 존재하는지 확인한다.
)
ORDER BY
    s.student_id ASC;

-- ============================================================
-- [종합실습 2 - 19번]
-- HR 전공 학생 981, 985, 990번과 다른 전공 학생의 GPA를 비교한다.
--
-- Self Join:
-- student 테이블을 HR 학생용(hr)과 비교 학생용(other_s)으로
-- 두 번 참조한다.
--
-- 조인 조건:
-- 1. 서로 같은 학생은 제외한다.
-- 2. 두 학생의 GPA 차이가 0.1 미만인 경우만 연결한다.
--
-- 필터 조건:
-- 1. hr은 HR 전공 학생만 선택한다.
-- 2. other_s는 HR이 아닌 학생만 선택한다.
-- 3. HR 학생은 981, 985, 990번으로 제한한다.
-- ============================================================

SELECT
    hr.name        AS HR_학생,    -- 비교 기준이 되는 HR 학생
    hr.gpa         AS HR_GPA,     -- HR 학생의 GPA
    other_s.name   AS 비교_학생,  -- GPA가 비슷한 타 전공 학생
    other_s.gpa    AS 비교_GPA,   -- 타 전공 학생의 GPA
    other_s.major  AS 전공        -- 비교 학생의 전공
FROM lab.student AS hr
INNER JOIN lab.student AS other_s
    ON hr.student_id <> other_s.student_id
    -- 같은 학생끼리 연결되지 않도록 제외한다.

   AND ABS(hr.gpa - other_s.gpa) < 0.1
    -- 두 학생의 GPA 차이가 0.1 미만인 경우만 연결한다.

WHERE hr.major = 'HR'
  -- 왼쪽은 HR 전공 학생만 선택한다.

  AND other_s.major <> 'HR'
  -- 오른쪽은 HR이 아닌 학생만 선택한다.

  AND hr.student_id IN (981, 985, 990)
  -- 지정된 HR 학생 세 명만 비교한다.

ORDER BY
    HR_학생 ASC,
    비교_GPA DESC;

-- ============================================================
-- [종합실습 2 - 20번]
-- 다음 조건 중 하나 이상을 만족하는 학생을 조회한다.
--
-- 조건 1: 전공이 CS인 학생
-- 조건 2: DB 과목을 수강한 학생
--
-- OR:
-- 두 조건 중 하나만 만족해도 결과에 포함한다.
--
-- EXISTS:
-- 현재 학생에게 DB 과목 수강 기록이 존재하는지 확인한다.
-- 여러 수강 기록이 있어도 학생은 한 행만 출력된다.
-- ============================================================

SELECT
    s.student_id AS 학생_ID, -- 학생 번호
    s.name       AS 학생명,  -- 학생 이름
    s.major      AS 전공,    -- 학생 전공
    s.gpa        AS GPA      -- 학생 GPA
FROM lab.student AS s
WHERE s.major = 'CS'
   OR EXISTS (
       SELECT 1
       FROM lab.enroll AS e
       WHERE e.student_id = s.student_id
         AND e.course = 'DB'
       -- 현재 학생에게 DB 과목 수강 기록이 있는지 확인한다.
   )
ORDER BY
    s.student_id ASC;

-- ============================================================
-- [종합실습 2 - 21번]
-- 학과별·GPA 구간별 학생 수를 집계하고,
-- 학과별 소계와 전체 총계를 함께 출력한다.
--
-- GPA 구간:
-- 1. 3.0 미만
-- 2. 3.0 이상 3.5 이하
-- 3. 3.5 초과
--
-- ROLLUP(major, gpa_tier):
-- 학과·GPA 구간별 상세 → 학과별 소계 → 전체 총계를 생성한다.
--
-- GROUPING():
-- ROLLUP이 만든 NULL과 실제 데이터의 NULL을 구분한다.
-- ============================================================

WITH student_gpa_tier AS (
    -- 학생마다 GPA 구간을 계산한다.
    SELECT
        s.major,
        CASE
            WHEN s.gpa < 3.0  THEN '3.0 미만'
            WHEN s.gpa <= 3.5 THEN '3.0~3.5'
            ELSE                   '3.5 초과'
        END AS gpa_tier
    FROM lab.student AS s
)

SELECT
    CASE
        WHEN GROUPING(major) = 1 THEN '전체' -- GROUPING(major) 함수로 소계 행에 '전체' 라벨을 붙일 것
        ELSE major
    END AS 전공,

    CASE
        WHEN GROUPING(major) = 1
         AND GROUPING(gpa_tier) = 1 THEN '총계'
        WHEN GROUPING(gpa_tier) = 1 THEN '소계'
        ELSE gpa_tier
    END AS GPA_구간,

    COUNT(*) AS 학생_수

FROM student_gpa_tier

-- GROUP BY ROLLUP(major, gpa_tier)로 학과별, 전체 소계를 동시에 조회
GROUP BY
    ROLLUP(major, gpa_tier)

ORDER BY
    GROUPING(major) ASC,    -- 전체 총계를 가장 마지막에 표시
    major ASC,              -- 학과명 오름차순
    GROUPING(gpa_tier) ASC, -- 학과별 소계를 상세 행 아래에 표시
    CASE gpa_tier
        WHEN '3.0 미만'  THEN 1
        WHEN '3.0~3.5'  THEN 2
        WHEN '3.5 초과' THEN 3
        ELSE 4
    END;

-- ============================================================
-- [종합실습 2 - 22번 / 1단계]
-- WITH RECURSIVE를 사용하여 CEO부터 시작하는 조직도를 탐색한다.
--
-- depth:
-- CEO는 0, CEO의 부하는 1, 그 아래 직원은 2로 표시한다.
--
-- path:
-- CEO부터 현재 직원까지의 조직 경로를 문자열로 표시한다.
-- ============================================================

WITH RECURSIVE org_tree AS (

    -- 시작 행(Anchor): 상위 관리자가 없는 CEO를 선택한다.
    SELECT
        e.emp_id,
        e.name,
        e.manager_id,
        0           AS depth,
        e.name::TEXT AS path
    FROM lab.emp AS e
    WHERE e.manager_id IS null --CEO찾기
    

    UNION ALL

    -- 재귀 단계: 현재 직원의 직속 부하를 계속 연결한다.
    SELECT
        child.emp_id,
        child.name,
        child.manager_id,
        parent.depth + 1,
        parent.path || ' > ' || child.name
    FROM lab.emp AS child
    INNER JOIN org_tree AS parent
        ON child.manager_id = parent.emp_id
)

SELECT
    o.emp_id     AS 직원_ID,
    o.name       AS 직원명,
    o.manager_id AS 매니저_ID,
    o.depth      AS 계층_깊이,
    o.path       AS 조직_경로
FROM org_tree AS o
ORDER BY
    o.path ASC;

-- ============================================================
-- [종합실습 2 - 22번 / 2단계]
-- 이름이 Mgr_로 시작하는 매니저별 직속 부하 수를 계산한다.
--
-- LEFT JOIN:
-- 직속 부하가 없는 매니저도 결과에 포함한다.
--
-- COUNT(child.emp_id):
-- 실제로 연결된 부하 직원만 계산한다.
-- ============================================================

SELECT
    manager.emp_id              AS 매니저_ID,
    manager.name                AS 매니저명,
    COUNT(child.emp_id)         AS direct_reports
FROM lab.emp AS manager
LEFT JOIN lab.emp AS child
    ON child.manager_id = manager.emp_id
WHERE manager.name LIKE 'Mgr_%'
GROUP BY
    manager.emp_id,
    manager.name
ORDER BY
    manager.emp_id ASC;

-- ============================================================
-- [종합실습 2 - 23.1]
-- 서브쿼리와 Window Function을 사용하여
-- 각 학과별 GPA 상위 3명을 조회한다.
--
-- ROW_NUMBER:
-- GPA 내림차순으로 번호를 부여하고,
-- GPA가 같으면 student_id가 작은 학생을 먼저 배치한다.
--
-- RANK / DENSE_RANK:
-- GPA 동점자에게 같은 순위를 부여하고
-- 다음 순위의 처리 방식 차이를 확인한다.
-- ============================================================

SELECT
    ranked.student_id      AS 학생_ID,
    ranked.name            AS 학생명,
    ranked.major           AS 전공,
    ranked.gpa             AS GPA,
    ranked.row_num         AS 행_순번,
    ranked.rank_num        AS 일반_순위,
    ranked.dense_rank_num  AS 연속_순위,
    ranked.total_in_major  AS 학과_전체_학생_수
FROM (
    SELECT
        s.student_id,
        s.name,
        s.major,
        s.gpa,

        ROW_NUMBER() OVER (
            PARTITION BY s.major
            ORDER BY s.gpa DESC, s.student_id ASC
        ) AS row_num,

        RANK() OVER (
            PARTITION BY s.major
            ORDER BY s.gpa DESC
        ) AS rank_num,

        DENSE_RANK() OVER (
            PARTITION BY s.major
            ORDER BY s.gpa DESC
        ) AS dense_rank_num,

        COUNT(s.student_id) OVER (
            PARTITION BY s.major
        ) AS total_in_major

    FROM lab.student AS s
) AS ranked
WHERE ranked.row_num <= 3
ORDER BY
    ranked.major ASC,
    ranked.row_num ASC;

-- ============================================================
-- [종합실습 2 - 23.2]
-- CTE와 Window Function을 사용하여
-- 각 학과별 GPA 상위 3명을 조회한다.
--
-- 1. ranked_students CTE에서 순위와 학과 인원을 계산한다.
-- 2. 바깥쪽 쿼리에서 row_num이 3 이하인 학생만 선택한다.
-- ============================================================

WITH ranked_students AS (
    SELECT
        s.student_id,
        s.name,
        s.major,
        s.gpa,

        ROW_NUMBER() OVER (
            PARTITION BY s.major
            ORDER BY s.gpa DESC, s.student_id ASC
        ) AS row_num,

        RANK() OVER (
            PARTITION BY s.major
            ORDER BY s.gpa DESC
        ) AS rank_num,

        DENSE_RANK() OVER (
            PARTITION BY s.major
            ORDER BY s.gpa DESC
        ) AS dense_rank_num,

        COUNT(s.student_id) OVER (
            PARTITION BY s.major
        ) AS total_in_major

    FROM lab.student AS s
)

SELECT
    r.student_id      AS 학생_ID,
    r.name            AS 학생명,
    r.major           AS 전공,
    r.gpa             AS GPA,
    r.row_num         AS 행_순번,
    r.rank_num        AS 일반_순위,
    r.dense_rank_num  AS 연속_순위,
    r.total_in_major  AS 학과_전체_학생_수
FROM ranked_students AS r
WHERE r.row_num <= 3
ORDER BY
    r.major ASC,
    r.row_num ASC;

-- ============================================================
-- [종합실습 2 - 24번]
-- LAG와 Window Function을 사용하여 학생별 이전 과목 대비
-- 성적 변화를 계산한다.
--
-- 처리 흐름:
-- 24.1 문자 성적을 숫자 점수로 변환
-- 24.2 학생별 이전 과목 점수와 점수 범위를 계산
-- 24.3 현재 점수와 이전 점수의 차이 및 변화 상태 출력
-- ============================================================

WITH scored_enrollments AS (

    -- 24.1 문자 성적을 숫자 점수로 변환
    SELECT
        e.student_id,
        e.course,
        e.grade,
        CASE e.grade
            WHEN 'A' THEN 4
            WHEN 'B' THEN 3
            WHEN 'C' THEN 2
            WHEN 'D' THEN 1
            ELSE NULL
        END AS score
    FROM lab.enroll AS e
),

analyzed_enrollments AS (

    -- 24.2 학생별 이전 과목 점수와 최고점-최저점 차이를 계산
    SELECT
        se.student_id,
        se.course,
        se.grade,
        se.score,

        LAG(se.score) OVER (
            PARTITION BY se.student_id
            ORDER BY se.course ASC
        ) AS prev_score,

        MAX(se.score) OVER (
            PARTITION BY se.student_id
        )
        -
        MIN(se.score) OVER (
            PARTITION BY se.student_id
        ) AS score_range

    FROM scored_enrollments AS se
)

-- 24.3 이전 과목 대비 점수 차이와 성적 변화 상태 출력
SELECT
    ae.student_id                    AS 학생_ID,
    ae.course                        AS 과목,
    ae.grade                         AS 문자_성적,
    ae.score                         AS 현재_점수,
    ae.prev_score                    AS 이전_점수,
    ae.score - ae.prev_score         AS 점수_차이,
    CASE
        WHEN ae.prev_score IS NULL
            THEN '비교 없음'
        WHEN ae.score > ae.prev_score
            THEN '상승'
        WHEN ae.score = ae.prev_score
            THEN '유지'
        ELSE '하락'
    END                              AS 성적_변화,
    ae.score_range                   AS 학생별_점수_범위
FROM analyzed_enrollments AS ae
ORDER BY
    ae.student_id ASC,
    ae.course ASC;

-- ============================================================
-- [종합실습 2 - 25.1]
-- 주문을 order_id 순으로 정렬하여 다음 값을 계산한다.
--
-- 1. 전체 주문 누적금액
-- 2. 현재 주문을 포함한 최근 3개 주문의 이동평균
-- 3. 고객별 누적 구매금액
-- ============================================================

SELECT
    o.order_id    AS 주문_ID,
    o.customer_id AS 고객_ID,
    o.amount      AS 주문_금액,

    -- 첫 번째 주문부터 현재 주문까지의 전체 누적금액
    SUM(o.amount) OVER (
        ORDER BY o.order_id
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS 전체_누적_금액,

    -- 현재 주문과 바로 앞의 2개 주문을 포함한 이동평균
    ROUND(
        AVG(o.amount) OVER (
            ORDER BY o.order_id
            ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
        ),
        2
    ) AS 최근_3개_이동평균,

    -- 같은 고객의 첫 주문부터 현재 주문까지의 누적 구매금액
    SUM(o.amount) OVER (
        PARTITION BY o.customer_id
        ORDER BY o.order_id
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS 고객별_누적_금액

FROM lab.orders AS o
ORDER BY
    o.order_id ASC;

-- ============================================================
-- [종합실습 2 - 25.2]
-- 전체 주문금액과 주문별 누적금액을 계산한 뒤,
-- 누적금액이 전체 금액의 50%를 처음 초과한 주문을 조회한다.
--
-- 문제에서 '초과'를 요구하므로 >=가 아니라 >를 사용한다.
-- ============================================================

WITH order_amounts AS (
    SELECT
        o.order_id,
        o.customer_id,
        o.amount,

        SUM(o.amount) OVER (
            ORDER BY o.order_id
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS cumulative_amount,

        SUM(o.amount) OVER () AS total_amount

    FROM lab.orders AS o
)

SELECT
    oa.order_id          AS 최초_초과_주문_ID,
    oa.customer_id       AS 고객_ID,
    oa.amount            AS 해당_주문_금액,
    oa.cumulative_amount AS 당시_누적_금액,
    oa.total_amount      AS 전체_주문_금액,
    ROUND(
        oa.cumulative_amount / oa.total_amount * 100,
        2
    )                    AS 누적_비율
FROM order_amounts AS oa
WHERE oa.cumulative_amount > oa.total_amount * 0.5
ORDER BY
    oa.order_id ASC
LIMIT 1;