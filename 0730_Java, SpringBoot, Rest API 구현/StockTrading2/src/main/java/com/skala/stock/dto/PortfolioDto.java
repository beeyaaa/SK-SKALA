package com.skala.stock.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import jakarta.validation.constraints.NotNull;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class PortfolioDto {

    private Long id;
    private Long userId;
    private String username;
    private Long stockId;
    private String stockCode;
    private String stockName;
    private Long quantity;
    private Long averagePrice;
    private Long currentPrice;
    private Long totalValue; // 현재 평가 금액
    private Long profitLoss; // 평가 손익
}
