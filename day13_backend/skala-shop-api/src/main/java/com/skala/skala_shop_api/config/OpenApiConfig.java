package com.skala.skala_shop_api.config;

import org.springframework.context.annotation.Configuration;

import io.swagger.v3.oas.annotations.OpenAPIDefinition;
import io.swagger.v3.oas.annotations.enums.SecuritySchemeIn;
import io.swagger.v3.oas.annotations.enums.SecuritySchemeType;
import io.swagger.v3.oas.annotations.info.Contact;
import io.swagger.v3.oas.annotations.info.Info;
import io.swagger.v3.oas.annotations.info.License;
import io.swagger.v3.oas.annotations.security.SecurityScheme;

@Configuration
@OpenAPIDefinition(
        info = @Info(
                title = "SKALA Shop API",
                version = "1.0.0",
                description = "패션 상품·고객·주문을 관리하는 쇼핑몰 REST API",
                contact = @Contact(name = "SKALA Shop"),
                license = @License(name = "Educational Use")))
@SecurityScheme(
        name = "cookieAuth",
        type = SecuritySchemeType.APIKEY,
        in = SecuritySchemeIn.COOKIE,
        paramName = "bff-access",
        description = "로그인 API가 발급하는 JWT HttpOnly Cookie")
public class OpenApiConfig {
}
