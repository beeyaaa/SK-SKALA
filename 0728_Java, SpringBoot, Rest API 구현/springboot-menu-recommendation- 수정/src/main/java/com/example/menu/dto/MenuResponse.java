package com.example.menu.dto;

/**
 * 메뉴 추천 결과를 JSON 형태로 반환하기 위한 DTO입니다.
 */
public record MenuResponse(
        String category,
        String menu,
        String message
) {
}
