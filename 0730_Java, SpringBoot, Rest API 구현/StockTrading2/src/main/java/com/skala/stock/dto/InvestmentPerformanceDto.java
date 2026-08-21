package com.skala.stock.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Getter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class InvestmentPerformanceDto {

    private Long userId;
    private Long realizedProfit;
    private Long unrealizedProfit;
    private Long totalProfit;
    private Long totalInvestment;
    private Double returnRate;
}
