
package com.skala.stock.service;
import com.skala.stock.dto.InvestmentPerformanceDto;
import com.skala.stock.dto.TransactionDto;
import com.skala.stock.entity.Transaction;
import com.skala.stock.repository.TransactionRepository;
import com.skala.stock.repository.UserRepository;
import com.skala.stock.dto.PortfolioDto;
import com.skala.stock.entity.Portfolio;
import com.skala.stock.entity.Stock;
import com.skala.stock.repository.PortfolioRepository;
import com.skala.stock.entity.User;

import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class StockAnalysisService {

    private final PortfolioRepository portfolioRepository;
    private final TransactionRepository transactionRepository;
    private final UserRepository userRepository;

    public List<PortfolioDto> getPortfolioWithProfitLoss(
            Long userId) {

        return portfolioRepository
                .findPortfolioWithProfitLoss(userId)
                .stream()
                .map(this::convertToDto)
                .toList();
    }

    private PortfolioDto convertToDto(
            Portfolio portfolio) {

        Stock stock = portfolio.getStock();

        Long currentPrice = stock.getCurrentPrice();

        Long totalValue =
                portfolio.getQuantity() * currentPrice;

        Long purchaseAmount =
                portfolio.getQuantity()
                        * portfolio.getAveragePrice();

        Long profitLoss =
                totalValue - purchaseAmount;

        return PortfolioDto.builder()
                .id(portfolio.getId())
                .userId(portfolio.getUser().getId())
                .username(
                        portfolio.getUser().getUsername()
                )
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

    public List<TransactionDto> getTransactionsWithDetails(
            Long userId) {

        return transactionRepository
                .findTransactionsWithDetails(userId)
                .stream()
                .map(this::convertTransactionToDto)
                .toList();
    }

    private TransactionDto convertTransactionToDto(
            Transaction transaction) {

        return TransactionDto.builder()
                .id(transaction.getId())
                .userId(transaction.getUser().getId())
                .username(
                        transaction.getUser().getUsername()
                )
                .stockId(transaction.getStock().getId())
                .stockCode(
                        transaction.getStock().getCode()
                )
                .stockName(
                        transaction.getStock().getName()
                )
                .type(transaction.getType())
                .quantity(transaction.getQuantity())
                .price(transaction.getPrice())
                .totalAmount(transaction.getTotalAmount())
                .realizedProfit(transaction.getRealizedProfit())
                .transactionDate(
                        transaction.getTransactionDate()
                )
                .createdAt(transaction.getCreatedAt())
                .build();
    }

    public List<TransactionDto> getStockTransactionsWithDetails(
            Long userId,
            Long stockId
    ) {
        return transactionRepository
                .findStockTransactionsWithDetails(userId, stockId)
                .stream()
                .map(this::convertTransactionToDto)
                .toList();
    }

    public Long getTotalAssets(Long userId) {
        User user = userRepository.findById(userId)
                .orElseThrow(() ->
                        new RuntimeException("사용자를 찾을 수 없습니다: " + userId)
                );

        Long stockValue = portfolioRepository.calculateStockValue(userId);

        return user.getBalance() + stockValue;
    }

    public Double getTotalReturnRate(Long userId) {
        if (!userRepository.existsById(userId)) {
            throw new RuntimeException(
                    "사용자를 찾을 수 없습니다: " + userId
            );
        }

        Long purchaseAmount =
                portfolioRepository.calculateTotalPurchaseAmount(userId);

        Long stockValue =
                portfolioRepository.calculateStockValue(userId);

        if (purchaseAmount == 0) {
            return 0.0;
        }

        return (stockValue - purchaseAmount)
                / (double) purchaseAmount
                * 100;
    }

    public InvestmentPerformanceDto getInvestmentPerformance(Long userId) {
        if (!userRepository.existsById(userId)) {
            throw new RuntimeException(
                    "사용자를 찾을 수 없습니다: " + userId
            );
        }

        Long realizedProfit = transactionRepository.calculateRealizedProfit(
                userId,
                Transaction.TransactionType.SELL
        );
        Long unrealizedProfit =
                portfolioRepository.calculateUnrealizedProfit(userId);
        Long currentPurchaseAmount =
                portfolioRepository.calculateTotalPurchaseAmount(userId);
        Long soldPurchaseAmount =
                transactionRepository.calculateSoldPurchaseAmount(
                        userId,
                        Transaction.TransactionType.SELL
                );

        Long totalProfit = realizedProfit + unrealizedProfit;
        Long totalInvestment =
                currentPurchaseAmount + soldPurchaseAmount;
        Double returnRate = totalInvestment == 0
                ? 0.0
                : totalProfit / (double) totalInvestment * 100;

        return InvestmentPerformanceDto.builder()
                .userId(userId)
                .realizedProfit(realizedProfit)
                .unrealizedProfit(unrealizedProfit)
                .totalProfit(totalProfit)
                .totalInvestment(totalInvestment)
                .returnRate(returnRate)
                .build();
    }
}
