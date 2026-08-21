package com.example.disample.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

/*
 * 클라이언트가 회원 생성 API에 전달하는 요청 DTO다.
 *
 * Entity를 Controller에서 직접 받지 않는 이유:
 * 1. 외부 요청 형식과 DB 구조를 분리한다.
 * 2. 입력값 검증 규칙을 명확하게 표현한다.
 * 3. Entity의 불필요한 필드 노출을 방지한다.
 */
@Schema(description = "회원 생성 요청")
public record MemberCreateRequest(

        @Schema(description = "회원 이름", example = "홍길동")
        @NotBlank(message = "이름은 필수다.")
        @Size(max = 50, message = "이름은 50자 이하여야 한다.")
        String name,

        @Schema(description = "회원 이메일", example = "hong@example.com")
        @NotBlank(message = "이메일은 필수다.")
        @Email(message = "올바른 이메일 형식이 아니다.")
        String email
) {
}
