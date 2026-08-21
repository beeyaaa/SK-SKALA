"""
미니 게시판의 WAS(Web Application Server).

Web에서 받은 HTTP 요청을 Flask가 처리하고,
psycopg2를 사용해 PostgreSQL의 posts 테이블을 저장·조회한다.
"""

import os
import time

# psycopg2: Python과 PostgreSQL을 연결하는 DB 드라이버
import psycopg2
# Flask: API 서버, request: 요청 데이터, jsonify: JSON 응답 생성
from flask import Flask, jsonify, request

# Flask 애플리케이션 객체 생성
app = Flask(__name__)

# WAS가 board-db 컨테이너에 접속할 때 사용할 DB 설정
# os.getenv("이름", "기본값"): Docker -e로 전달한 환경변수를 우선 사용
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "board-db"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "dbname": os.getenv("DB_NAME", "board"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "mypassword"),
}


# WAS 시작 시 posts 테이블이 없으면 자동 생성
def init_db():
    """DB 준비가 늦을 수 있으므로 최대 10번 연결을 재시도한다."""
    for attempt in range(10):
        try:
            # **DB_CONFIG는 딕셔너리의 값을 이름이 있는 인자로 풀어서 전달
            conn = psycopg2.connect(**DB_CONFIG)
            try:
                # cursor는 SQL을 DB에 전달하고 결과를 받는 객체
                with conn.cursor() as cursor:
                    cursor.execute("""
                        -- IF NOT EXISTS: 테이블이 이미 있으면 오류 없이 넘어감
                        CREATE TABLE IF NOT EXISTS posts (
                            id SERIAL PRIMARY KEY,
                            title VARCHAR(200) NOT NULL,
                            content TEXT NOT NULL,
                            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                        )
                    """)
                # CREATE TABLE 결과를 DB에 최종 반영
                conn.commit()
                print("posts 테이블 준비 완료")
                return
            finally:
                # 성공·실패와 관계없이 DB 연결을 반드시 정리
                conn.close()
        except psycopg2.OperationalError:
            if attempt == 9:
                raise
            print("DB 준비 대기 중...")
            # PostgreSQL 컨테이너가 준비될 시간을 주고 다시 시도
            time.sleep(2)


# Web(localhost:8080)과 WAS(localhost:5001)는 포트가 다르므로
# 브라우저가 WAS API 요청을 허용하도록 CORS 헤더를 추가한다.
@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return response


# GET /api/message: WAS가 정상 응답하는지 간단히 확인하는 API
@app.get("/api/message")
def message():
    return jsonify({
        "message": "WAS에서 처리한 결과입니다."
    })


# POST /api/posts: Web의 글쓰기 요청을 posts 테이블에 저장
@app.post("/api/posts")
def create_post():
    # JSON 본문을 Python 딕셔너리로 변환; JSON이 없거나 잘못되면 {}
    data = request.get_json(silent=True) or {}
    # strip()으로 제목·내용 앞뒤의 불필요한 공백 제거
    title = str(data.get("title", "")).strip()
    content = str(data.get("content", "")).strip()

    # 필수값이 비어 있으면 DB에 저장하지 않고 400 Bad Request 반환
    if not title or not content:
        return jsonify({"error": "제목과 내용을 모두 입력해주세요."}), 400

    conn = psycopg2.connect(**DB_CONFIG)
    try:
        with conn.cursor() as cursor:
            # %s와 값을 분리해 전달하는 파라미터 바인딩으로 SQL Injection 방지
            cursor.execute(
                """
                INSERT INTO posts (title, content)
                VALUES (%s, %s)
                RETURNING id, created_at
                """,
                (title, content),
            )
            # RETURNING으로 DB가 생성한 id와 작성 시각을 한 행 가져옴
            post_id, created_at = cursor.fetchone()
        # INSERT 결과를 DB에 최종 저장
        conn.commit()
    finally:
        conn.close()

    # 201 Created: 새 데이터가 성공적으로 생성됐다는 HTTP 상태 코드
    return jsonify({
        "id": post_id,
        "title": title,
        "content": content,
        "created_at": created_at.isoformat(),
    }), 201


# GET /api/posts: DB에 저장된 게시글 목록 조회
@app.get("/api/posts")
def get_posts():
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT id, title, content, created_at
                FROM posts
                -- id가 큰 최신 게시글부터 조회
                ORDER BY id DESC
            """)
            # SELECT 결과의 모든 행을 리스트로 가져옴
            rows = cursor.fetchall()
    finally:
        conn.close()

    # DB 튜플 목록을 Web이 사용할 수 있는 JSON 배열로 변환
    return jsonify([
        {
            "id": row[0],
            "title": row[1],
            "content": row[2],
            "created_at": row[3].isoformat(),
        }
        for row in rows
    ])


# 이 파일을 `python app.py`로 직접 실행했을 때만 아래 코드 실행
if __name__ == "__main__":
    # Flask를 실행하기 전에 DB와 posts 테이블부터 준비
    init_db()
    # 0.0.0.0: 컨테이너 밖의 요청 허용
    # 5000: 컨테이너 내부 포트 (호스트 5001과 -p 5001:5000으로 연결)
    app.run(host="0.0.0.0", port=5000)
