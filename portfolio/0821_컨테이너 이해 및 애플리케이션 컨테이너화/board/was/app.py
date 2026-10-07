"""
작성자: 홍은비
작성일자: 2026-08-21
변경사항: 콘텐츠 아카이브 REST API와 DB 처리 구현, 함수별 입력·트랜잭션·HTTP 응답 주석 보강

Flask가 Web의 비동기 요청을 처리하고 PostgreSQL의 posts 테이블에
영화·음악·도서·전시·예능·팟캐스트 콘텐츠 기록을 저장한다.
"""

import os
import time
from contextlib import contextmanager
from decimal import Decimal

import psycopg2
from flask import Flask, jsonify, request
from psycopg2.extras import RealDictCursor

app = Flask(__name__)

# Compose가 전달한 환경변수를 우선 사용하고, 값이 없을 때만 두 번째 인자의 기본값을 사용한다.
# 컨테이너 간 접속 주소에는 localhost가 아니라 Compose 서비스명 board-db를 사용한다.
DB_CONFIG = {
    "host": os.getenv("DB_HOST", "board-db"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "dbname": os.getenv("DB_NAME", "board"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "mypassword"),
}

# 허용 목록(Allowlist)으로 카테고리와 정렬 방식을 제한한다.
# SORT_OPTIONS의 SQL 조각은 사용자 입력을 직접 넣지 않고 검증된 key로만 선택한다.
CATEGORIES = {"movie", "music", "book", "exhibition", "variety", "podcast"}
SORT_OPTIONS = {
    "latest": "created_at DESC, id DESC",
    "rating": "rating DESC, created_at DESC",
    "title": "LOWER(title) ASC, id DESC",
}


@contextmanager
def db_cursor(*, commit=False):
    """PostgreSQL Connection과 Cursor의 생명주기 및 트랜잭션을 관리한다.

    commit=True인 쓰기 작업은 정상 완료 시 Commit하고, 예외가 발생하면
    Rollback한 뒤 예외를 다시 발생시킨다. finally에서 Connection을 닫으므로
    호출부가 자원 해제를 빠뜨리지 않는다.
    """
    conn = psycopg2.connect(**DB_CONFIG)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            yield cursor
        if commit:
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """DB 시작을 기다린 뒤 posts 테이블을 생성·확장한다.

    Docker 컨테이너가 Running이어도 PostgreSQL이 즉시 접속 가능한 것은 아니므로
    OperationalError 발생 시 2초 간격으로 최대 10회 재시도한다.
    """
    for attempt in range(10):
        try:
            with db_cursor(commit=True) as cursor:
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS posts (
                        id SERIAL PRIMARY KEY,
                        title VARCHAR(200) NOT NULL,
                        creator VARCHAR(120) NOT NULL DEFAULT '',
                        category VARCHAR(20) NOT NULL DEFAULT 'movie',
                        rating NUMERIC(2, 1) NOT NULL DEFAULT 3.0,
                        content TEXT NOT NULL,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    )
                    """
                )
                # 현재 연결된 posts 테이블의 기존 행을 보존하면서 필요한 열만 추가한다.
                cursor.execute(
                    """
                    ALTER TABLE posts
                        ADD COLUMN IF NOT EXISTS creator VARCHAR(120) NOT NULL DEFAULT '',
                        ADD COLUMN IF NOT EXISTS category VARCHAR(20) NOT NULL DEFAULT 'movie',
                        ADD COLUMN IF NOT EXISTS rating NUMERIC(2, 1) NOT NULL DEFAULT 3.0,
                        ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    """
                )
            print("콘텐츠 아카이브 posts 테이블 준비 완료", flush=True)
            return
        except psycopg2.OperationalError:
            if attempt == 9:
                raise
            print(f"DB 준비 대기 중... ({attempt + 1}/10)", flush=True)
            time.sleep(2)


def serialize_post(post):
    """RealDictRow를 Flask가 JSON으로 직렬화할 수 있는 기본 자료형으로 변환한다.

    PostgreSQL NUMERIC은 Decimal, TIMESTAMPTZ는 datetime으로 반환되므로
    각각 float와 ISO 8601 문자열로 변환한다.
    """
    result = dict(post)
    if isinstance(result.get("rating"), Decimal):
        result["rating"] = float(result["rating"])
    for key in ("created_at", "updated_at"):
        if result.get(key):
            result[key] = result[key].isoformat()
    return result


def validate_post(data):
    """POST·PUT JSON Payload를 정제하고 서버 측 유효성 검사를 수행한다.

    HTML의 required/maxlength는 우회할 수 있으므로 WAS에서도 필수값, 길이,
    허용 카테고리, 평점 범위와 0.5 단위를 다시 검증한다.
    """
    if not isinstance(data, dict):
        return None, "JSON 형식의 요청이 필요합니다."

    title = str(data.get("title", "")).strip()
    creator = str(data.get("creator", "")).strip()
    category = str(data.get("category", "")).strip().lower()
    content = str(data.get("content", "")).strip()

    try:
        rating = float(data.get("rating", 0))
    except (TypeError, ValueError):
        return None, "평점은 숫자로 입력해주세요."

    if not title or not creator or not content:
        return None, "작품명, 만든 사람, 감상을 모두 입력해주세요."
    if len(title) > 200:
        return None, "작품명은 200자 이하로 입력해주세요."
    if len(creator) > 120:
        return None, "만든 사람은 120자 이하로 입력해주세요."
    if len(content) > 5000:
        return None, "감상은 5,000자 이하로 입력해주세요."
    if category not in CATEGORIES:
        return None, "지원하지 않는 카테고리입니다."
    if not 0.5 <= rating <= 5.0 or abs(rating * 2 - round(rating * 2)) > 1e-9:
        return None, "평점은 0.5부터 5.0까지 0.5 단위로 선택해주세요."

    return {
        "title": title,
        "creator": creator,
        "category": category,
        "rating": rating,
        "content": content,
    }, None


@app.get("/health")
def health():
    """WAS 프로세스뿐 아니라 PostgreSQL 연결까지 확인하는 Readiness Endpoint다."""
    try:
        with db_cursor() as cursor:
            # SELECT 1은 테이블을 변경하지 않는 최소 비용의 DB 연결 확인 Query다.
            cursor.execute("SELECT 1")
            cursor.fetchone()
        return jsonify({"status": "healthy", "database": "connected"}), 200
    except psycopg2.Error:
        return jsonify({"status": "unhealthy", "database": "disconnected"}), 503


@app.get("/api/posts")
def get_posts():
    """검색어·카테고리·정렬 Query Parameter에 맞는 기록 목록을 반환한다."""
    keyword = request.args.get("q", "").strip()
    category = request.args.get("category", "all").strip().lower()
    sort = request.args.get("sort", "latest").strip().lower()

    if category != "all" and category not in CATEGORIES:
        return jsonify({"error": "지원하지 않는 카테고리입니다."}), 400
    if sort not in SORT_OPTIONS:
        return jsonify({"error": "지원하지 않는 정렬 방식입니다."}), 400

    # WHERE 조건과 바인딩 값을 별도로 누적하여 선택적 검색 조건을 구성한다.
    conditions = []
    params = []
    if keyword:
        conditions.append("(title ILIKE %s OR creator ILIKE %s OR content ILIKE %s)")
        search_pattern = f"%{keyword}%"
        params.extend([search_pattern, search_pattern, search_pattern])
    if category != "all":
        conditions.append("category = %s")
        params.append(category)

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    # Column/ORDER BY 식별자는 일반 Parameter Binding 대상이 아니므로 Allowlist에서 선택한다.
    order_clause = SORT_OPTIONS[sort]

    with db_cursor() as cursor:
        # 검색어와 카테고리는 %s Placeholder로 바인딩하여 SQL Injection을 방지한다.
        cursor.execute(
            f"""
            SELECT id, title, creator, category, rating, content,
                   created_at, updated_at
            FROM posts
            {where_clause}
            ORDER BY {order_clause}
            """,
            params,
        )
        rows = cursor.fetchall()

    return jsonify([serialize_post(row) for row in rows])


@app.get("/api/posts/<int:post_id>")
def get_post(post_id):
    """Path Parameter의 ID와 일치하는 단일 기록을 반환한다."""
    with db_cursor() as cursor:
        cursor.execute(
            """
            SELECT id, title, creator, category, rating, content,
                   created_at, updated_at
            FROM posts
            WHERE id = %s
            """,
            (post_id,),
        )
        post = cursor.fetchone()

    if post is None:
        return jsonify({"error": "기록을 찾을 수 없습니다."}), 404
    return jsonify(serialize_post(post))


@app.post("/api/posts")
def create_post():
    """검증된 JSON Payload로 새 기록을 생성하고 HTTP 201 Created를 반환한다."""
    # silent=True는 잘못된 JSON에서 Flask 예외 대신 None을 받아 공통 검증으로 처리하게 한다.
    data, error = validate_post(request.get_json(silent=True))
    if error:
        return jsonify({"error": error}), 400

    with db_cursor(commit=True) as cursor:
        # RETURNING을 사용해 INSERT 직후 추가 SELECT 없이 생성된 행을 응답한다.
        cursor.execute(
            """
            INSERT INTO posts (title, creator, category, rating, content)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id, title, creator, category, rating, content,
                      created_at, updated_at
            """,
            (
                data["title"],
                data["creator"],
                data["category"],
                data["rating"],
                data["content"],
            ),
        )
        post = cursor.fetchone()

    return jsonify(serialize_post(post)), 201


@app.put("/api/posts/<int:post_id>")
def update_post(post_id):
    """기존 기록 전체를 교체하고 수정 시각을 갱신하는 PUT Endpoint다."""
    data, error = validate_post(request.get_json(silent=True))
    if error:
        return jsonify({"error": error}), 400

    with db_cursor(commit=True) as cursor:
        cursor.execute(
            """
            UPDATE posts
            SET title = %s,
                creator = %s,
                category = %s,
                rating = %s,
                content = %s,
                updated_at = NOW()
            WHERE id = %s
            RETURNING id, title, creator, category, rating, content,
                      created_at, updated_at
            """,
            (
                data["title"],
                data["creator"],
                data["category"],
                data["rating"],
                data["content"],
                post_id,
            ),
        )
        post = cursor.fetchone()

    if post is None:
        return jsonify({"error": "수정할 기록을 찾을 수 없습니다."}), 404
    return jsonify(serialize_post(post))


@app.delete("/api/posts/<int:post_id>")
def delete_post(post_id):
    """ID에 해당하는 기록을 삭제하고 본문 없는 HTTP 204를 반환한다."""
    with db_cursor(commit=True) as cursor:
        cursor.execute("DELETE FROM posts WHERE id = %s", (post_id,))
        deleted = cursor.rowcount

    if deleted == 0:
        return jsonify({"error": "삭제할 기록을 찾을 수 없습니다."}), 404
    return "", 204


@app.errorhandler(psycopg2.Error)
def handle_database_error(error):
    """처리되지 않은 PostgreSQL 예외를 기록하고 일관된 JSON 500 응답으로 변환한다."""
    app.logger.exception("데이터베이스 처리 중 오류가 발생했습니다.", exc_info=error)
    return jsonify({"error": "데이터베이스 처리 중 오류가 발생했습니다."}), 500


if __name__ == "__main__":
    # app.py를 직접 실행할 때만 스키마 준비 후 모든 컨테이너 인터페이스에서 요청을 받는다.
    # 0.0.0.0으로 Bind해야 컨테이너 외부의 Nginx가 5000번 포트에 접속할 수 있다.
    init_db()
    app.run(host="0.0.0.0", port=5000)
