package com.skala.skala_shop_api.exception;

import java.util.List;

import lombok.Getter;

@Getter
public class ParameterException extends RuntimeException {

    private final List<String> parameters;

    public ParameterException(String... parameters) {
        super("Invalid parameters: " + String.join(", ", parameters));
        this.parameters = List.of(parameters);
    }
}
