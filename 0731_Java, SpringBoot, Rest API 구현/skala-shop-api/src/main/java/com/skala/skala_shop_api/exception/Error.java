package com.skala.skala_shop_api.exception;

import org.springframework.http.HttpStatus;

import lombok.Getter;
import lombok.RequiredArgsConstructor;

// 서비스에서 발생할 수 있는 오류 유형
@Getter
@RequiredArgsConstructor
public enum Error {
    DATA_NOT_FOUND(HttpStatus.NOT_FOUND),
    DATA_DUPLICATED(HttpStatus.CONFLICT),
    NOT_AUTHENTICATED(HttpStatus.UNAUTHORIZED),
    INSUFFICIENT_FUNDS(HttpStatus.BAD_REQUEST),
    INSUFFICIENT_QUANTITY(HttpStatus.BAD_REQUEST),
    SESSION_NOT_FOUND(HttpStatus.UNAUTHORIZED);

    private final HttpStatus status;
}
