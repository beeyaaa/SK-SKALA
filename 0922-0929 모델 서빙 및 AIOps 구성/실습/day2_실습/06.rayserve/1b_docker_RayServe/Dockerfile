# 공식 Ray 이미지(ray[serve] 사전 설치) 위에 실습 앱만 얹는다.
# 온프레미스 실습(1_onprem_Rayserve)이 검증한 ray 2.56.1과 동일 버전으로 고정.
FROM rayproject/ray:2.56.1-py311

WORKDIR /serve
COPY app.py serve_config.yaml ./
