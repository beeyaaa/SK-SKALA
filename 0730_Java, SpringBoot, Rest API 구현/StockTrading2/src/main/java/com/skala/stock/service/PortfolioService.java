package com.skala.stock.service;

import com.skala.stock.dto.PortfolioDto;
import com.skala.stock.entity.Portfolio;
import com.skala.stock.entity.Stock;
import com.skala.stock.repository.PortfolioRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class PortfolioService {

    private final PortfolioRepository portfolioRepository;

    public List<PortfolioDto> getUserPortfolio(Long userId) {
        List<Portfolio> portfolios = portfolioRepository.findByUserId(userId);
        return portfolios.stream()
                .map(this::convertToDto)
                .collect(Collectors.toList());
    }

    // addToPortfolio, updatePortfolio, removeFromPortfolio 메서드는 
    // executeTrade() 제거로 인해 더 이상 사용되지 않습니다.
    // 교육생 실습을 위해 제거되었습니다.

    private PortfolioDto convertToDto(Portfolio portfolio) {
        Stock stock = portfolio.getStock();
        Long currentPrice = stock.getCurrentPrice();
        Long totalValue = portfolio.getQuantity() * currentPrice;
        Long profitLoss = totalValue - (portfolio.getQuantity() * portfolio.getAveragePrice());

        return PortfolioDto.builder()
                .id(portfolio.getId())
                .userId(portfolio.getUser().getId())
                .username(portfolio.getUser().getUsername())
                .stockId(stock.getId())
                .stockCode(stock.getCode())
                .stockName(stock.getName())
                .quantity(portfolio.getQuantity())
                .averagePrice(portfolio.getAveragePrice())
                .currentPrice(currentPrice)
                .totalValue(totalValue)
                .profitLoss(profitLoss)
                .build();
    }

    public PortfolioDto getPortfolio(Long userId, Long stockId) {

        Portfolio portfolio = portfolioRepository
                .findByUserIdAndStockId(
                        userId,
                        stockId
                )
                .orElseThrow(() ->
                        new RuntimeException(
                                "포트폴리오를 찾을 수 없습니다. "
                                        + "사용자 ID: "
                                        + userId
                                        + ", 주식 ID: "
                                        + stockId
                        )
                );

        return convertToDto(portfolio);
    }
}
