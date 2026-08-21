package com.skala.skala_shop_api.exception;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.FieldError;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;
import org.springframework.web.method.annotation.HandlerMethodValidationException;

import com.skala.skala_shop_api.common.Response;

import jakarta.validation.ConstraintViolationException;

// 모든 REST Controller에서 발생한 예외를 공통 응답 형식으로 처리
@RestControllerAdvice
public class GlobalExceptionHandler {

    // 서비스에서 정의한 비즈니스 예외 처리
    @ExceptionHandler(ResponseException.class)
    public ResponseEntity<Response> handleResponseException(ResponseException exception) {
        Error error = exception.getError();

        Response response = Response.builder()
                .result(1)
                .code(error.getStatus().value())
                .message(exception.getMessage())
                .body(null)
                .build();

        return ResponseEntity
                .status(error.getStatus())
                .body(response);
    }

    // 필수 요청값이 없거나 유효하지 않은 경우 처리
    @ExceptionHandler(ParameterException.class)
    public ResponseEntity<Response> handleParameterException(ParameterException exception) {
        Response response = Response.builder()
                .result(1)
                .code(HttpStatus.BAD_REQUEST.value())
                .message(exception.getMessage())
                .body(exception.getParameters())
                .build();

        return ResponseEntity
                .status(HttpStatus.BAD_REQUEST)
                .body(response);
    }

    // @Valid가 요청 JSON의 필드 검증에 실패한 경우 처리
    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<Response> handleMethodArgumentNotValidException(
            MethodArgumentNotValidException exception) {
        Map<String, String> fieldErrors = new LinkedHashMap<>();

        for (FieldError fieldError : exception.getBindingResult().getFieldErrors()) {
            fieldErrors.putIfAbsent(
                    fieldError.getField(),
                    fieldError.getDefaultMessage());
        }

        return badRequest("VALIDATION_FAILED", fieldErrors);
    }

    // @Validated가 쿼리·경로 파라미터 검증에 실패한 경우 처리
    @ExceptionHandler(ConstraintViolationException.class)
    public ResponseEntity<Response> handleConstraintViolationException(
            ConstraintViolationException exception) {
        List<String> errors = exception.getConstraintViolations()
                .stream()
                .map(violation -> violation.getMessage())
                .toList();

        return badRequest("VALIDATION_FAILED", errors);
    }

    // Spring MVC의 메서드 파라미터 검증 실패 처리
    @ExceptionHandler(HandlerMethodValidationException.class)
    public ResponseEntity<Response> handleHandlerMethodValidationException(
            HandlerMethodValidationException exception) {
        return badRequest("VALIDATION_FAILED", null);
    }

    // 별도로 처리하지 않은 서버 오류의 응답 형식을 통일
    @ExceptionHandler(Exception.class)
    public ResponseEntity<Response> handleUnexpectedException(Exception exception) {
        Response response = Response.builder()
                .result(1)
                .code(HttpStatus.INTERNAL_SERVER_ERROR.value())
                .message("INTERNAL_SERVER_ERROR")
                .body(null)
                .build();

        return ResponseEntity
                .status(HttpStatus.INTERNAL_SERVER_ERROR)
                .body(response);
    }

    private ResponseEntity<Response> badRequest(String message, Object body) {
        Response response = Response.builder()
                .result(1)
                .code(HttpStatus.BAD_REQUEST.value())
                .message(message)
                .body(body)
                .build();

        return ResponseEntity
                .status(HttpStatus.BAD_REQUEST)
                .body(response);
    }
}
