package com.skala.skala_shop_api.exception;

import lombok.Getter;

@Getter
public class ResponseException extends RuntimeException {

    private final Error error;

    public ResponseException(Error error) {
        super(error.name());
        this.error = error;
    }

    public ResponseException(Error error, String message) {
        super(message);
        this.error = error;
    }
}
