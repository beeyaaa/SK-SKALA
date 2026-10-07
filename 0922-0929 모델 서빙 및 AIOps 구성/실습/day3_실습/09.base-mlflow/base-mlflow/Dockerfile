# mlflow 실습과제 전용 이미지 — mlflow 서버(mlflow-server 서비스)와
# 학습/검증 클라이언트(trainer, verify 서비스) 양쪽이 이 이미지 하나를 공유한다.
# (서버냐 클라이언트냐는 docker-compose.yml의 command로만 갈린다)
FROM python:3.11-slim

WORKDIR /app

# healthcheck에서 mlflow-server의 /health 엔드포인트를 확인하기 위해 curl 설치
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "solution.py"]
