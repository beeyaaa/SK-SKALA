package com.example.disample.dto;

import com.example.disample.entity.Member;
import io.swagger.v3.oas.annotations.media.Schema;

/*
 * API가 클라이언트에 반환하는 회원 응답 DTO다.
 *
 * Entity 자체를 응답으로 반환하지 않고 DTO로 변환하면
 * API 응답 구조와 DB 구조를 서로 독립적으로 관리할 수 있다.
 */
@Schema(description = "회원 응답")
public record MemberResponse(
        @Schema(example = "1")
        Long id,

        @Schema(example = "홍길동")
        String name,

        @Schema(example = "hong@example.com")
        String email
) {

    /*
     * Member Entity를 MemberResponse DTO로 변환한다.
     */
    public static MemberResponse from(Member member) {
        return new MemberResponse(
                member.getId(),
                member.getName(),
                member.getEmail()
        );
    }
}
