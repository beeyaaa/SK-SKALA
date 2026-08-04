package com.skala.skala_shop_api.common;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
public class Response {

    @Schema(description = "처리 결과(0: 성공, 1: 실패)", example = "0")
    private int result;

    @Schema(description = "응답 코드", example = "0")
    private int code;

    @Schema(description = "오류 메시지", example = "DATA_NOT_FOUND", nullable = true)
    private String message;

    @Schema(description = "응답 데이터", nullable = true)
    private Object body;

    @Builder
    public Response(int result, int code, String message, Object body) {
        this.result = result;
        this.code = code;
        this.message = message;
        this.body = body;
    }
}
