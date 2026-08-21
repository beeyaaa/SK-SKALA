-- 실행 위치: campus_task_db 데이터베이스

SET search_path TO campus_task, public;

-- 1. 학생
CREATE TABLE students (
  id BIGINT GENERATED ALWAYS AS IDENTITY,
  student_no VARCHAR(20) NOT NULL,
  name VARCHAR(50) NOT NULL,
  email VARCHAR(100) NOT NULL,
  phone VARCHAR(20),
  enrolled BOOLEAN NOT NULL DEFAULT TRUE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

  CONSTRAINT pk_students PRIMARY KEY (id),
  CONSTRAINT uk_students_student_no UNIQUE (student_no),
  CONSTRAINT uk_students_email UNIQUE (email)
);

-- 2. 강좌
CREATE TABLE courses (
  id BIGINT GENERATED ALWAYS AS IDENTITY,
  course_code VARCHAR(20) NOT NULL,
  title VARCHAR(100) NOT NULL,

  CONSTRAINT pk_courses PRIMARY KEY (id),
  CONSTRAINT uk_courses_course_code UNIQUE (course_code)
);

-- 3. 수강신청: 학생과 강좌의 N:M 관계를 연결하는 교차 테이블
CREATE TABLE enrollments (
  student_id BIGINT NOT NULL,
  course_id BIGINT NOT NULL,
  enrolled_at DATE NOT NULL DEFAULT CURRENT_DATE,

  CONSTRAINT pk_enrollments PRIMARY KEY (student_id, course_id),
  CONSTRAINT fk_enrollments_student
    FOREIGN KEY (student_id) REFERENCES students (id) ON DELETE CASCADE,
  CONSTRAINT fk_enrollments_course
    FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE
);

-- 4. 과제
CREATE TABLE assignments (
  id BIGINT GENERATED ALWAYS AS IDENTITY,
  course_id BIGINT NOT NULL,
  title VARCHAR(200) NOT NULL,
  due_at TIMESTAMPTZ NOT NULL,

  CONSTRAINT pk_assignments PRIMARY KEY (id),
  CONSTRAINT fk_assignments_course
    FOREIGN KEY (course_id) REFERENCES courses (id) ON DELETE CASCADE
);

-- 5. 과제 제출
CREATE TABLE submissions (
  id BIGINT GENERATED ALWAYS AS IDENTITY,
  assignment_id BIGINT NOT NULL,
  student_id BIGINT NOT NULL,
  submitted_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
  score NUMERIC(5,2),
  feedback TEXT,

  CONSTRAINT pk_submissions PRIMARY KEY (id),
  CONSTRAINT uk_submissions_assignment_student
    UNIQUE (assignment_id, student_id),
  CONSTRAINT chk_submissions_score
    CHECK (score IS NULL OR score BETWEEN 0 AND 100),
  CONSTRAINT fk_submissions_assignment
    FOREIGN KEY (assignment_id) REFERENCES assignments (id) ON DELETE CASCADE,
  CONSTRAINT fk_submissions_student
    FOREIGN KEY (student_id) REFERENCES students (id) ON DELETE CASCADE
);

-- 교차 테이블을 course_id부터 조회할 때 사용할 인덱스
CREATE INDEX idx_enrollments_course_student
  ON enrollments (course_id, student_id);

-- 학생별 제출물을 빠르게 조회하기 위한 인덱스
CREATE INDEX idx_submissions_student
  ON submissions (student_id);

-- 생성된 테이블 확인
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'campus_task'
ORDER BY table_name;

