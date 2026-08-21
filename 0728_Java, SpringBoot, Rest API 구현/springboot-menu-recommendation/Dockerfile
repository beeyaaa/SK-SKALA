# Java 21 실행 환경
FROM eclipse-temurin:21-jre

# 컨테이너 내부 작업 폴더
WORKDIR /app

# Gradle로 만든 실행용 JAR 파일 복사
COPY build/libs/springboot-menu-recommendation-0.0.1-SNAPSHOT.jar app.jar

# Spring Boot가 사용하는 포트
EXPOSE 8080

# 컨테이너가 시작될 때 서버 실행
ENTRYPOINT ["java", "-jar", "app.jar"]