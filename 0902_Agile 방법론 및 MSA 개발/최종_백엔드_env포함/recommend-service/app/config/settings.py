# /docker-compose.yml : 교수자 제공 컨테이너 환경
# /docker-compose.local.yml : 로컬 AI 테스트용 override
# /recommend-service/.env : 로컬 OpenAI 설정

from pathlib import Path

from dotenv import dotenv_values
from pydantic import SecretStr
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # 서버 설정
    app_port: int = 8085
    app_name: str = "recommend-service"

    # Eureka 설정
    eureka_server_url: str = "http://localhost:8761/eureka"
    eureka_instance_host: str = "localhost"

    # Auth Server
    jwt_issuer_uri: str = "http://localhost:8080"
    jwk_set_uri: str = "http://auth-server:9000/oauth2/jwks"

    # 로컬에서만 Recommend API의 JWT 검증을 우회한다.
    local_dev_bypass_auth: bool = False

    # 서비스 URL
    enrollment_service_url: str = "http://localhost:8083"
    course_service_url: str = "http://localhost:8082"
    user_service_url: str = "http://localhost:8081"

    # Kafka
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_consumer_group_id: str = "recommend-service"
    kafka_topic_enrollment_completed: str = "enrollment.completed"

    # OpenAI API
    openai_api_key: SecretStr = SecretStr("")
    openai_model: str = "gpt-5-nano"
    openai_base_url: str = "https://api.openai.com/v1"
    openai_timeout_seconds: float = 60.0

    class Config:
        env_file = (".env", ".env.local")


settings = Settings()

# 일부 교수자 compose 파일은 OPENAI_API_KEY=""를 컨테이너 환경변수로 주입한다.
# 환경변수의 빈 문자열이 dotenv보다 우선하면 recommend-service/.env의 실제 키가
# 가려질 수 있으므로, 키가 비어 있을 때만 /app/.env를 명시적으로 한 번 더 확인한다.
if not settings.openai_api_key.get_secret_value():
    for env_path in (Path("/app/.env"), Path(".env"), Path(".env.local")):
        if not env_path.is_file():
            continue
        value = dotenv_values(env_path).get("OPENAI_API_KEY")
        if value:
            settings.openai_api_key = SecretStr(str(value))
            break
