-- 실행 위치: campus_task_db 데이터베이스

CREATE SCHEMA IF NOT EXISTS campus_task;

-- 현재 접속 세션에서 campus_task 스키마를 기본으로 사용합니다.
SET search_path TO campus_task, public;

SELECT current_database() AS database_name,
       current_schema() AS schema_name;

