# 작성자: 홍은비
# 작성일자: 2026-08-21
# 변경사항: Flask 실행 이미지 구성, 환경변수·Layer Cache·시작 명령 설명 주석 보강

# 일반 Python 이미지보다 용량이 작은 Debian slim 기반 공식 이미지를 사용한다.
FROM python:3.11-slim

# .pyc 생성을 막고 로그 Buffering을 해제하여 Docker Logs에서 즉시 확인한다.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 이후 COPY, RUN, CMD가 기준으로 사용할 컨테이너 내부 작업 디렉터리
WORKDIR /app

# 의존성 파일을 소스보다 먼저 복사하면 소스만 바뀔 때 pip install Layer Cache를 재사용할 수 있다.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 실행에 필요한 애플리케이션 소스만 이미지에 포함한다.
COPY app.py .

# Flask가 수신하는 컨테이너 내부 포트를 이미지 메타데이터로 문서화한다.
EXPOSE 5000

# 컨테이너가 시작될 때 PID 1로 실행할 기본 명령
CMD ["python", "app.py"]
