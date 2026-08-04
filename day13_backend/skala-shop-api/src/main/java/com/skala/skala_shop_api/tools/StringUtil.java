package com.skala.skala_shop_api.tools;

import java.util.Arrays;

// 문자열 입력값 검증에 사용하는 공통 유틸리티
public class StringUtil {

    private StringUtil() {
    }

    // 전달된 문자열 중 null, 빈 문자열 또는 공백 문자열이 하나라도 있는지 확인
    public static boolean isAnyBlank(String... values) {
        return values == null
                || values.length == 0
                || Arrays.stream(values).anyMatch(
                        value -> value == null || value.isBlank());
    }
}
