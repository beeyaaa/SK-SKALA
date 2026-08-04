package com.skala.stock.mapper;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class TransactionStatisticsDto {
    private String stockCode;
    private String stockName;
    private Long totalBuyQuantity;
    private Long totalSellQuantity;
    private Long netQuantity;
    private Long totalBuyAmount;
    private Long totalSellAmount;
    private Long netAmount;
}
