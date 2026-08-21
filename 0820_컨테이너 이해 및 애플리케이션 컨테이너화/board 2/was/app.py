"""
미니 게시판 WAS (Web Application Server)
- Web(nginx)에서 넘어온 요청을 처리하고 PostgreSQL에 게시글을 저장/조회한다.
- DB 접속 정보는 환경변수로 주입받는다. (DB_HOST 에는 PostgreSQL 컨테이너 이름을 넣는다)
"""

import os
import time

import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, jsonify, request

app = Flask(__name__)

# ---------------------------------------------------------------------------
# DB 설정 (환경변수로 주입)
# ---------------------------------------------------------------------------
DB_HOST = os.environ.get("DB_HOST", "localhost") # docker run 명령어를 쓸 때 DB_HOST에 localhost를 쓰면 안 된다.
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME", "board")
DB_USER = os.environ.get("DB_USER", "boarduser")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "mypassword")


def get_connection():
    """PostgreSQL 커넥션을 생성한다."""
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        connect_timeout=5,
    )


def init_db(max_retry=30, delay=2):
    """
    앱 기동 시 posts 테이블을 자동으로 생성한다.
    - postgres 이미지는 DB(board)만 만들어줄 뿐 테이블은 만들어주지 않으므로,
      WAS가 시작될 때 직접 CREATE TABLE IF NOT EXISTS로 테이블을 준비한다.
    - docker-compose 등으로 여러 컨테이너를 동시에 띄우면 DB 컨테이너가
      아직 완전히 기동되지 않은 상태일 수 있어, 접속 실패 시 delay(초) 간격으로
      최대 max_retry번 재시도한다. (depends_on은 순서만 보장할 뿐 "DB 준비 완료"는 보장하지 않기 때문)
    """
    for attempt in range(1, max_retry + 1):
        try:
            conn = get_connection()
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        CREATE TABLE IF NOT EXISTS posts (
                            id         SERIAL PRIMARY KEY,
                            title      VARCHAR(200) NOT NULL,
                            content    TEXT NOT NULL,
                            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP
                        )
                        """
                    )
                    # 이전 버전으로 이미 만들어진 테이블에도 수정 시각 컬럼을 붙인다.
                    cur.execute(
                        "ALTER TABLE posts ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP"
                    )
            conn.close()
            print(f"[WAS] DB 초기화 완료 (host={DB_HOST}, db={DB_NAME})", flush=True)
            return True
        except Exception as e:  # DB 미기동 / 네트워크 지연 등
            print(
                f"[WAS] DB 연결 대기 중... ({attempt}/{max_retry}) - {e}",
                flush=True,
            )
            time.sleep(delay)

    print("[WAS] DB 초기화 실패. 이후 요청 시 재시도합니다.", flush=True)
    return False


@app.after_request
def add_cors_headers(response):
    """Web(nginx) 컨테이너에서 직접 호출할 수 있도록 CORS 허용."""
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = (
        "GET, POST, PUT, PATCH, DELETE, OPTIONS"
    )
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------
@app.route("/health", methods=["GET"])
def health():
    """WAS <-> DB 상태 확인용."""
    try:
        conn = get_connection()
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
            cur.fetchone()
        conn.close()
        return jsonify({"status": "ok", "db": "connected", "db_host": DB_HOST})
    except Exception as e:
        return jsonify({"status": "error", "db": "disconnected", "message": str(e)}), 500


@app.route("/api/posts", methods=["GET", "OPTIONS"])
def list_posts():
    """게시글 목록 조회 (최신순)."""
    if request.method == "OPTIONS":
        return "", 204

    try:
        conn = get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT id, title, content,
                       TO_CHAR(created_at, 'YYYY-MM-DD HH24:MI') AS created_at,
                       TO_CHAR(updated_at, 'YYYY-MM-DD HH24:MI') AS updated_at
                  FROM posts
                 ORDER BY id DESC
                """
            )
            rows = cur.fetchall()
        conn.close()
        return jsonify({"posts": [dict(r) for r in rows], "count": len(rows)})
    except Exception as e:
        return jsonify({"error": "게시글 목록을 불러오지 못했습니다.", "detail": str(e)}), 500


@app.route("/api/posts", methods=["POST"])
def create_post():
    """게시글 작성 (제목, 내용)."""
    data = request.get_json(silent=True) or request.form
    title = (data.get("title") or "").strip()
    content = (data.get("content") or "").strip()

    if not title or not content:
        return jsonify({"error": "제목과 내용을 모두 입력해 주세요."}), 400
    if len(title) > 200:
        return jsonify({"error": "제목은 200자 이내로 입력해 주세요."}), 400

    try:
        conn = get_connection()
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    INSERT INTO posts (title, content)
                    VALUES (%s, %s)
                    RETURNING id, title, content,
                              TO_CHAR(created_at, 'YYYY-MM-DD HH24:MI') AS created_at,
                              TO_CHAR(updated_at, 'YYYY-MM-DD HH24:MI') AS updated_at
                    """,
                    (title, content),
                )
                row = cur.fetchone()
        conn.close()
        return jsonify({"message": "게시글이 등록되었습니다.", "post": dict(row)}), 201
    except Exception as e:
        return jsonify({"error": "게시글 저장에 실패했습니다.", "detail": str(e)}), 500


@app.route("/api/posts/<int:post_id>", methods=["GET", "OPTIONS"])
def get_post(post_id):
    """게시글 단건 조회."""
    if request.method == "OPTIONS":
        return "", 204

    try:
        conn = get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT id, title, content,
                       TO_CHAR(created_at, 'YYYY-MM-DD HH24:MI') AS created_at,
                       TO_CHAR(updated_at, 'YYYY-MM-DD HH24:MI') AS updated_at
                  FROM posts
                 WHERE id = %s
                """,
                (post_id,),
            )
            row = cur.fetchone()
        conn.close()

        if row is None:
            return jsonify({"error": "게시글을 찾을 수 없습니다."}), 404
        return jsonify({"post": dict(row)})
    except Exception as e:
        return jsonify({"error": "게시글 조회에 실패했습니다.", "detail": str(e)}), 500


@app.route("/api/posts/<int:post_id>", methods=["PUT", "PATCH"])
def update_post(post_id):
    """게시글 수정 (제목, 내용). 보낸 항목만 바꾸고 나머지는 그대로 둔다."""
    data = request.get_json(silent=True) or request.form
    new_title = data.get("title")
    new_content = data.get("content")

    if new_title is None and new_content is None:
        return jsonify({"error": "수정할 제목 또는 내용을 보내주세요."}), 400

    try:
        conn = get_connection()
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                # 기존 값을 먼저 읽어 와서, 보내지 않은 항목은 그대로 유지한다.
                cur.execute("SELECT title, content FROM posts WHERE id = %s", (post_id,))
                current = cur.fetchone()
                if current is None:
                    conn.close()
                    return jsonify({"error": "게시글을 찾을 수 없습니다."}), 404

                title = (new_title if new_title is not None else current["title"]).strip()
                content = (
                    new_content if new_content is not None else current["content"]
                ).strip()

                if not title or not content:
                    conn.close()
                    return jsonify({"error": "제목과 내용을 모두 입력해 주세요."}), 400
                if len(title) > 200:
                    conn.close()
                    return jsonify({"error": "제목은 200자 이내로 입력해 주세요."}), 400

                cur.execute(
                    """
                    UPDATE posts
                       SET title = %s,
                           content = %s,
                           updated_at = CURRENT_TIMESTAMP
                     WHERE id = %s
                    RETURNING id, title, content,
                              TO_CHAR(created_at, 'YYYY-MM-DD HH24:MI') AS created_at,
                              TO_CHAR(updated_at, 'YYYY-MM-DD HH24:MI') AS updated_at
                    """,
                    (title, content, post_id),
                )
                row = cur.fetchone()
        conn.close()
        return jsonify({"message": "게시글이 수정되었습니다.", "post": dict(row)})
    except Exception as e:
        return jsonify({"error": "게시글 수정에 실패했습니다.", "detail": str(e)}), 500


@app.route("/api/posts/<int:post_id>", methods=["DELETE"])
def delete_post(post_id):
    """게시글 삭제 (칠판 지우개)."""
    try:
        conn = get_connection()
        with conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM posts WHERE id = %s", (post_id,))
                deleted = cur.rowcount
        conn.close()

        if deleted == 0:
            return jsonify({"error": "게시글을 찾을 수 없습니다."}), 404
        return jsonify({"message": "게시글이 지워졌습니다.", "id": post_id})
    except Exception as e:
        return jsonify({"error": "게시글 삭제에 실패했습니다.", "detail": str(e)}), 500


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)
