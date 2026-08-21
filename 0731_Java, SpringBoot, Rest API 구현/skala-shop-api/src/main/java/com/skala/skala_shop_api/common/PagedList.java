package com.skala.skala_shop_api.common;

import java.util.List;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
public class PagedList<T> {

    @Schema(description = "현재 페이지 번호", example = "0")
    private int offset;

    @Schema(description = "현재 페이지 항목 수", example = "5")
    private int count;

    @Schema(description = "전체 항목 수", example = "5")
    private long total;

    @Schema(description = "현재 페이지 데이터")
    private List<T> items;

    @Builder
    public PagedList(int offset, int count, long total, List<T> items) {
        this.offset = offset;
        this.count = count;
        this.total = total;
        this.items = items;
    }
}
