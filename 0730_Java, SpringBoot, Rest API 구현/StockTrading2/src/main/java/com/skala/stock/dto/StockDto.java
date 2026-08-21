package com.skala.stock.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Size;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class StockDto {

    private Long id;

    @NotBlank(message = "종목 코드는 필수입니다")
    @Size(max = 20, message = "종목 코드는 20자 이하여야 합니다")
    private String code;

    @NotBlank(message = "종목명은 필수입니다")
    @Size(max = 100, message = "종목명은 100자 이하여야 합니다")
    private String name;

    @NotNull(message = "현재가는 필수입니다")
    private Long currentPrice;

    private Long previousPrice;
}
