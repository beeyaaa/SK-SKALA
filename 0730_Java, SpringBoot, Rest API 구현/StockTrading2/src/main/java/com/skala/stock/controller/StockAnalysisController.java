
package com.skala.stock.controller;

import com.skala.stock.dto.InvestmentPerformanceDto;
import com.skala.stock.dto.PortfolioDto;
import com.skala.stock.service.StockAnalysisService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import com.skala.stock.dto.TransactionDto;

import java.util.List;
import java.util.Map;

@RestController
@RequestMapping("/api/analysis")
@RequiredArgsConstructor
@Tag(
    name = "주식 분석",
    description = "JPA를 활용한 주식 분석 API"
)
public class StockAnalysisController {

    private final StockAnalysisService stockAnalysisService;

    @GetMapping("/portfolio/{userId}")
    @Operation(
        summary = "포트폴리오 평가손익 조회",
        description = "사용자의 포트폴리오와 종목별 평가손익을 조회합니다"
    )
    public ResponseEntity<List<PortfolioDto>>
            getPortfolioWithProfitLoss(
                    @PathVariable Long userId) {

        List<PortfolioDto> portfolios =
                stockAnalysisService
                        .getPortfolioWithProfitLoss(userId);

        return ResponseEntity.ok(portfolios);
    }

    @GetMapping("/transactions/{userId}")
    @Operation(
            summary = "거래 내역 상세 조회",
            description = "사용자의 전체 거래내역을 사용자 및 주식 정보와 함께 조회합니다"
    )
    public ResponseEntity<List<TransactionDto>>
            getTransactionsWithDetails(
                    @PathVariable Long userId) {

        List<TransactionDto> transactions =
                stockAnalysisService
                        .getTransactionsWithDetails(userId);

        return ResponseEntity.ok(transactions);
    }

    @GetMapping("/transactions/{userId}/stock/{stockId}")
    @Operation(
            summary = "특정 주식 거래 내역 조회",
            description = "사용자의 특정 주식 매수·매도 내역을 조회합니다"
    )
    public ResponseEntity<List<TransactionDto>> getStockTransactionsWithDetails(
            @PathVariable Long userId,
            @PathVariable Long stockId
    ) {
        return ResponseEntity.ok(
                stockAnalysisService.getStockTransactionsWithDetails(
                        userId,
                        stockId
                )
        );
    }

    @GetMapping("/assets/{userId}")
    @Operation(
            summary = "총 자산 조회",
            description = "사용자의 현금과 보유 주식 평가금액을 합산하여 조회합니다"
    )
    public ResponseEntity<Map<String, Object>> getTotalAssets(
            @PathVariable Long userId
    ) {
        Long totalAssets = stockAnalysisService.getTotalAssets(userId);

        return ResponseEntity.ok(
                Map.of(
                        "userId", userId,
                        "totalAssets", totalAssets
                )
        );
    }

    @GetMapping("/return-rate/{userId}")
    @Operation(
            summary = "총 수익률 조회",
            description = "사용자가 보유한 전체 주식의 총수익률을 조회합니다"
    )
    public ResponseEntity<Map<String, Object>> getTotalReturnRate(
            @PathVariable Long userId
    ) {
        Double returnRate =
                stockAnalysisService.getTotalReturnRate(userId);

        return ResponseEntity.ok(
                Map.of(
                        "userId", userId,
                        "totalReturnRate", returnRate
                )
        );
    }

    @GetMapping("/performance/{userId}")
    @Operation(
            summary = "투자 성과 통합 조회",
            description = "실현손익, 평가손익, 총손익과 전체 수익률을 조회합니다"
    )
    public ResponseEntity<InvestmentPerformanceDto> getInvestmentPerformance(
            @PathVariable Long userId
    ) {
        return ResponseEntity.ok(
                stockAnalysisService.getInvestmentPerformance(userId)
        );
    }
}
