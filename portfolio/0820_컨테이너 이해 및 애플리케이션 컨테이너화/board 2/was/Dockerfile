# was/Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 5000
# 수정: 외부 5002번 포트는 실행 시 -p 5002:5000으로 연결
CMD ["python", "app.py"]
