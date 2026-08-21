package com.example.configsample.controller;

import com.example.configsample.config.AppProperties;
import com.example.configsample.service.StorageService;
import org.springframework.core.env.Environment;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.Map;

@RestController
@RequestMapping("/config")
public class ConfigController {

    private final AppProperties appProperties;
    private final StorageService storageService;
    private final Environment environment;

    public ConfigController(
            AppProperties appProperties,
            StorageService storageService,
            Environment environment
    ) {
        this.appProperties = appProperties;
        this.storageService = storageService;
        this.environment = environment;
    }

    @GetMapping
    public Map<String, Object> getConfiguration() {
        Map<String, Object> result = new LinkedHashMap<>();

        result.put("activeProfiles", Arrays.asList(environment.getActiveProfiles()));
        result.put("defaultProfiles", Arrays.asList(environment.getDefaultProfiles()));
        result.put("applicationName", appProperties.name());
        result.put("description", appProperties.description());
        result.put("environment", appProperties.environment());

        result.put("externalApi", Map.of(
                "baseUrl", appProperties.externalApi().baseUrl(),
                "connectTimeout", appProperties.externalApi().connectTimeout().toString(),
                "readTimeout", appProperties.externalApi().readTimeout().toString()
        ));

        result.put("storage", Map.of(
                "type", appProperties.storage().type(),
                "directory", appProperties.storage().directory(),
                "maxFileSize", appProperties.storage().maxFileSize().toString()
        ));

        result.put("allowedOrigins", appProperties.security().allowedOrigins());

        // API Key는 응답에 노출하지 않는다.
        return result;
    }

    @GetMapping("/storage/{filename}")
    public Map<String, String> testStorage(@PathVariable String filename) {
        return Map.of(
                "environment", appProperties.environment(),
                "result", storageService.save(filename)
        );
    }
}
