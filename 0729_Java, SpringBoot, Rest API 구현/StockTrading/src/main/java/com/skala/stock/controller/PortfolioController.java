package com.skala.stock.controller;

import com.skala.stock.dto.PortfolioDto;
import com.skala.stock.dto.PortfolioSummaryDto;
import com.skala.stock.service.PortfolioService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/portfolios")
@RequiredArgsConstructor
@Tag(name = "포트폴리오 관리", description = "포트폴리오 조회 API")
public class PortfolioController {

    private final PortfolioService portfolioService;

    @GetMapping("/user/{userId}")
    @Operation(summary = "사용자 포트폴리오 조회", description = "특정 사용자의 전체 포트폴리오를 조회합니다")
    public ResponseEntity<List<PortfolioDto>> getUserPortfolio(@PathVariable Long userId) {
        List<PortfolioDto> portfolios = portfolioService.getUserPortfolio(userId);
        return ResponseEntity.ok(portfolios);
    }

    //추가기능 엔드포인트 추가
    @GetMapping("/user/{userId}/summary")
    @Operation(summary = "사용자 투자 현황 요약", description = "사용자의 현금, 주식 평가금액, 총자산, 평가손익과 수익률을 조회합니다")
    public ResponseEntity<PortfolioSummaryDto> getUserPortfolioSummary(@PathVariable Long userId) {
        PortfolioSummaryDto summary = portfolioService.getUserPortfolioSummary(userId);
        return ResponseEntity.ok(summary);
    }

    @GetMapping("/user/{userId}/stock/{stockId}")
    @Operation(summary = "특정 주식 포트폴리오 조회", description = "사용자의 특정 주식 포트폴리오를 조회합니다")
    public ResponseEntity<PortfolioDto> getPortfolio(
            @PathVariable Long userId,
            @PathVariable Long stockId) {
        PortfolioDto portfolio = portfolioService.getPortfolio(userId, stockId);
        return ResponseEntity.ok(portfolio);
    }
}
