# from flask import Flask

# app = Flask(__name__)

# @app.route('/')
# def hello():
#     message = "was image is running"
#     print(message, flush=True)
#     return f"<h1>{message}</h1>"

# if __name__ == '__main__':
#     app.run(host='0.0.0.0', port=5000)

import os

import psycopg2
from flask import Flask, jsonify

app = Flask(__name__)


def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "board-db"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME", "board"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "mypassword"),
    )


@app.get("/api/message")
def message():
    with get_db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT NOW();")
            db_time = cursor.fetchone()[0]

    response = jsonify({
        "message": "WAS와 PostgreSQL 연결 성공",
        "db_time": str(db_time),
    })
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)