package com.example.disample.config;

import io.swagger.v3.oas.annotations.OpenAPIDefinition;
import io.swagger.v3.oas.annotations.info.Info;
import org.springframework.context.annotation.Configuration;

/*
 * Swagger UI에 표시할 OpenAPI 기본 정보를 설정한다.
 *
 * springdoc-openapi 의존성만 추가해도 Swagger UI는 동작하지만,
 * 이 설정을 사용하면 문서 제목과 설명을 명확하게 표시할 수 있다.
 */
@Configuration
@OpenAPIDefinition(
        info = @Info(
                title = "Spring Boot DI Sample API",
                version = "1.0.0",
                description = "Controller → Service → Repository 의존성 주입 학습용 API"
        )
)
public class OpenApiConfig {
}
