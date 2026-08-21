package com.example.configsample.config;

import jakarta.validation.Valid;
import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.NotNull;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.boot.context.properties.bind.DefaultValue;
import org.springframework.boot.convert.DataSizeUnit;
import org.springframework.util.unit.DataSize;
import org.springframework.util.unit.DataUnit;
import org.springframework.validation.annotation.Validated;

import java.time.Duration;
import java.util.List;

@Validated
@ConfigurationProperties(prefix = "app")
public record AppProperties(
        @NotBlank String name,
        @NotBlank String description,
        @NotBlank String environment,
        @Valid @NotNull ExternalApi externalApi,
        @Valid @NotNull Storage storage,
        @Valid @NotNull Security security
) {

    public record ExternalApi(
            @NotBlank String baseUrl,
            @NotNull @DefaultValue("3s") Duration connectTimeout,
            @NotNull @DefaultValue("5s") Duration readTimeout,
            @NotBlank String apiKey
    ) {
    }

    public record Storage(
            @NotBlank String type,
            @NotBlank String directory,
            @NotNull
            @DefaultValue("10MB")
            @DataSizeUnit(DataUnit.MEGABYTES)
            DataSize maxFileSize
    ) {
    }

    public record Security(
            @NotEmpty List<String> allowedOrigins,
            @NotBlank @Email String adminEmail
    ) {
    }
}
