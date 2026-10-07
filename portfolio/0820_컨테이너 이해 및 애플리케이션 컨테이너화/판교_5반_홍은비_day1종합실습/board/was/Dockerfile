FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# 수정: Flask가 컨테이너 내부에서 실제로 사용하는 포트 -> 5000
EXPOSE 5000
CMD ["python", "app.py"]
