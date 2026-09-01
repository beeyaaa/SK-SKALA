package com.example.springai.tools;

import org.springframework.ai.mcp.annotation.McpTool;
import org.springframework.ai.mcp.annotation.McpToolParam;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Mono;

import lombok.extern.slf4j.Slf4j;

/**
 * AI가 호출할 수 있는 날씨 조회 도구를 제공합니다.
 */
@Component
@Slf4j
public class WeatherTools {

    private final String weatherApiKey;
    private final String weatherApiPath;
    private final WebClient webClient;

    public WeatherTools(
            WebClient.Builder webClientBuilder,
            @Value("${weather.api.key}") String weatherApiKey,
            @Value("${weather.api.base-url}") String weatherBaseUrl,
            @Value("${weather.api.path}") String weatherApiPath) {
        
        this.weatherApiKey = weatherApiKey;
        this.weatherApiPath = weatherApiPath;
        
        log.info("WeatherTools initialized with base URL: {}", weatherBaseUrl);
        log.info("WeatherTools initialized with API path: {}", weatherApiPath);
        log.info("WeatherTools initialized with API key: {}", weatherApiKey != null ? "설정됨" : "null");
        
        this.webClient = webClientBuilder
                .baseUrl(weatherBaseUrl)
                .build();
    }

    /**
     * 도시 이름으로 현재 날씨를 조회합니다.
     *
     * @param city 도시 이름 (예: Seoul, Busan)
     * @return 날씨 정보 JSON 문자열
     */
    @McpTool(description = "도시 이름으로 현재 날씨를 조회합니다. 예: Seoul")
    public String getCurrentWeather(
            @McpToolParam(description = "도시 이름 (예: Seoul)", required = true) String city) {
        
        log.info("날씨 조회 요청 - 도시: {}", city);
        
        String result = webClient.get()
                .uri(uriBuilder -> uriBuilder
                        .path(weatherApiPath)
                        .queryParam("q", city)
                        .queryParam("appid", weatherApiKey)
                        .queryParam("units", "metric")
                        .queryParam("lang", "kr")
                        .build())
                .retrieve()
                .bodyToMono(String.class)
                .onErrorResume(ex -> {
                    log.error("날씨 조회 실패: {}", ex.getMessage());
                    return Mono.just("{\"error\": \"" + ex.getMessage() + "\"}");
                })
                .block();
        
        log.info("날씨 조회 결과: {}", result);
        return result;
    }
}
