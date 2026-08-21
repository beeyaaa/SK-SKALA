-- 실행 위치: campus_task_db 데이터베이스

SET search_path TO campus_task, public;

-- Q1. 재학 중인 학생을 학번 오름차순으로 조회하시오.
-- 사용 문법: SELECT, WHERE, ORDER BY
SELECT
  student_no,
  name,
  email
FROM students
WHERE enrolled = TRUE
ORDER BY student_no ASC;

-- Q2. 학생 전화번호가 NULL이면 '미등록'으로 표시하시오.
-- 사용 함수: COALESCE
SELECT
  student_no,
  name,
  COALESCE(phone, '미등록') AS phone_display
FROM students
ORDER BY student_no ASC;

-- Q3. 제출 시간과 마감 시간을 비교하여 정상 제출과 지각 제출을 표시하시오.
-- 사용 문법: CASE WHEN, JOIN
SELECT
  s.student_no,
  s.name AS student_name,
  a.title AS assignment_title,
  a.due_at,
  sb.submitted_at,
  CASE
    WHEN sb.submitted_at <= a.due_at THEN '정상 제출'
    ELSE '지각 제출'
  END AS submission_status
FROM submissions AS sb
JOIN students AS s
  ON s.id = sb.student_id
JOIN assignments AS a
  ON a.id = sb.assignment_id
ORDER BY a.due_at ASC, s.student_no ASC;

-- Q4. 과제 마감 일시에서 연도, 월, 일을 추출하시오.
-- 사용 함수: EXTRACT, TO_CHAR
SELECT
  title,
  due_at,
  EXTRACT(YEAR FROM due_at) AS due_year,
  EXTRACT(MONTH FROM due_at) AS due_month,
  EXTRACT(DAY FROM due_at) AS due_day,
  TO_CHAR(due_at, 'YYYY-MM-DD HH24:MI') AS due_display
FROM assignments
ORDER BY due_at ASC;

-- Q5. 수강신청 교차 테이블을 이용하여 학생별 수강 강좌를 조회하시오.
-- 사용 문법: students → enrollments → courses JOIN
SELECT
  s.student_no,
  s.name AS student_name,
  c.course_code,
  c.title AS course_title,
  e.enrolled_at
FROM students AS s
JOIN enrollments AS e
  ON e.student_id = s.id
JOIN courses AS c
  ON c.id = e.course_id
ORDER BY s.student_no ASC, c.course_code ASC;

-- Q6. 과제 제출 결과와 점수·피드백을 조회하시오.
-- 점수와 피드백이 NULL이면 각각 '미채점', '피드백 없음'으로 표시합니다.
SELECT
  c.title AS course_title,
  a.title AS assignment_title,
  s.student_no,
  s.name AS student_name,
  sb.submitted_at,
  COALESCE(sb.score::TEXT, '미채점') AS score_display,
  COALESCE(sb.feedback, '피드백 없음') AS feedback_display
FROM submissions AS sb
JOIN students AS s
  ON s.id = sb.student_id
JOIN assignments AS a
  ON a.id = sb.assignment_id
JOIN courses AS c
  ON c.id = a.course_id
ORDER BY c.course_code ASC, a.id ASC, s.student_no ASC;

