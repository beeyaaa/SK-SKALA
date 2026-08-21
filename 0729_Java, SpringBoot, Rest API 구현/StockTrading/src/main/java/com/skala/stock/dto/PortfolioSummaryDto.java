//추가기능ㅌ
package com.skala.stock.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;

@Getter
@NoArgsConstructor
@AllArgsConstructor
@Builder
@Schema(description = "사용자의 전체 투자 현황 요약")
public class PortfolioSummaryDto {

    @Schema(description = "사용자 ID", example = "1")
    private Long userId;

    @Schema(description = "사용자명", example = "user1")
    private String username;

    @Schema(description = "현재 보유 현금", example = "500000")
    private Long cashBalance;

    @Schema(description = "보유 주식의 현재 평가금액 합계", example = "1200000")
    private Long stockValue;

    @Schema(description = "현금과 주식 평가금액을 합한 총자산", example = "1700000")
    private Long totalAsset;

    @Schema(description = "보유 주식의 전체 평가손익", example = "150000")
    private Long totalProfitLoss;

    @Schema(description = "전체 투자수익률(%)", example = "14.28")
    private Double profitRate;
}
