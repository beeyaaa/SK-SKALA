# 작성자: 홍은비
# 작성일자: 2026-08-21
# 변경사항: 콘텐츠 아카이브 정적 파일과 Nginx 설정 구성, Image Layer별 설명 주석 보강

# 경량 Linux 배포판 Alpine 기반의 공식 Nginx 이미지를 Base Image로 사용한다.
FROM nginx:alpine

# 정적 리소스는 Nginx Document Root에, Server 설정은 conf.d에 복사한다.
COPY index.html /usr/share/nginx/html/index.html
COPY styles.css /usr/share/nginx/html/styles.css
COPY nginx.conf /etc/nginx/conf.d/default.conf

# EXPOSE는 컨테이너가 80번 포트를 사용한다는 메타데이터이며 실제 공개는 Compose ports가 담당한다.
EXPOSE 80
