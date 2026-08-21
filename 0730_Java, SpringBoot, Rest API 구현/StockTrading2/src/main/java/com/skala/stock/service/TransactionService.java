package com.skala.stock.service;
import com.skala.stock.dto.TradeRequestDto;
import com.skala.stock.entity.Portfolio;
import com.skala.stock.entity.Stock;
import com.skala.stock.entity.User;
import com.skala.stock.repository.PortfolioRepository;
import com.skala.stock.repository.StockRepository;
import com.skala.stock.repository.UserRepository;

import com.skala.stock.dto.TransactionDto;
import com.skala.stock.entity.Transaction;
import com.skala.stock.repository.TransactionRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Propagation;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class TransactionService {

    private final TransactionRepository transactionRepository;
    private final UserRepository userRepository;
    private final StockRepository stockRepository;
    private final PortfolioRepository portfolioRepository;

    @Transactional(readOnly = true, propagation = Propagation.SUPPORTS)
    public List<TransactionDto> getUserTransactions(Long userId) {
        List<Transaction> transactions = transactionRepository.findByUserIdOrderByTransactionDateDesc(userId);
        return transactions.stream()
                .map(this::convertToDto)
                .collect(Collectors.toList());
    }

    private TransactionDto convertToDto(Transaction transaction) {
        return TransactionDto.builder()
                .id(transaction.getId())
                .userId(transaction.getUser().getId())
                .username(transaction.getUser().getUsername())
                .stockId(transaction.getStock().getId())
                .stockCode(transaction.getStock().getCode())
                .stockName(transaction.getStock().getName())
                .type(transaction.getType())
                .quantity(transaction.getQuantity())
                .price(transaction.getPrice())
                .totalAmount(transaction.getTotalAmount())
                .realizedProfit(transaction.getRealizedProfit())
                .transactionDate(transaction.getTransactionDate())
                .createdAt(transaction.getCreatedAt())
                .build();
    }

    public TransactionDto getTransactionById(Long id) {
        Transaction transaction =
                transactionRepository.findTransactionDetailById(id)
                        .orElseThrow(() ->
                                new RuntimeException(
                                        "거래를 찾을 수 없습니다: " + id
                                )
                        );

        return convertToDto(transaction);
    }

    @Transactional
    public TransactionDto executeTrade(
            TradeRequestDto tradeRequest) {

        User user = userRepository
                .findById(tradeRequest.getUserId())
                .orElseThrow(() ->
                        new RuntimeException(
                                "사용자를 찾을 수 없습니다: "
                                        + tradeRequest.getUserId()
                        )
                );

        Stock stock = stockRepository
                .findById(tradeRequest.getStockId())
                .orElseThrow(() ->
                        new RuntimeException(
                                "주식을 찾을 수 없습니다: "
                                        + tradeRequest.getStockId()
                        )
                );

        Long currentPrice = stock.getCurrentPrice();

        Long totalAmount =
                currentPrice * tradeRequest.getQuantity();

        Long realizedProfit = 0L;

        if (tradeRequest.getType()
                == Transaction.TransactionType.BUY) {

            executeBuy(
                    user,
                    stock,
                    tradeRequest.getQuantity(),
                    currentPrice,
                    totalAmount
            );

        } else {

            realizedProfit = executeSell(
                    user,
                    stock,
                    tradeRequest.getQuantity(),
                    currentPrice,
                    totalAmount
            );
        }

        userRepository.save(user);

        Transaction transaction = Transaction.builder()
                .user(user)
                .stock(stock)
                .type(tradeRequest.getType())
                .quantity(tradeRequest.getQuantity())
                .price(currentPrice)
                .totalAmount(totalAmount)
                .realizedProfit(realizedProfit)
                .build();

        Transaction savedTransaction =
                transactionRepository.save(transaction);

        return convertToDto(savedTransaction);
    }

    private void executeBuy(
            User user,
            Stock stock,
            Long quantity,
            Long currentPrice,
            Long totalAmount) {

        if (user.getBalance() < totalAmount) {
            throw new RuntimeException(
                    "잔액이 부족합니다. 필요 금액: "
                            + totalAmount
                            + ", 보유 금액: "
                            + user.getBalance()
            );
        }

        user.setBalance(
                user.getBalance() - totalAmount
        );

        Portfolio portfolio = portfolioRepository
                .findByUserIdAndStockId(
                        user.getId(),
                        stock.getId()
                )
                .orElse(null);

        if (portfolio == null) {
            Portfolio newPortfolio = Portfolio.builder()
                    .user(user)
                    .stock(stock)
                    .quantity(quantity)
                    .averagePrice(currentPrice)
                    .build();

            portfolioRepository.save(newPortfolio);
            return;
        }

        Long oldQuantity = portfolio.getQuantity();
        Long oldAveragePrice = portfolio.getAveragePrice();

        Long newQuantity = oldQuantity + quantity;

        Long totalPurchaseAmount =
                oldQuantity * oldAveragePrice
                        + quantity * currentPrice;

        Long newAveragePrice =
                totalPurchaseAmount / newQuantity;

        portfolio.setQuantity(newQuantity);
        portfolio.setAveragePrice(newAveragePrice);

        portfolioRepository.save(portfolio);
    }

    private Long executeSell(
            User user,
            Stock stock,
            Long quantity,
            Long currentPrice,
            Long totalAmount) {

        Portfolio portfolio = portfolioRepository
                .findByUserIdAndStockId(
                        user.getId(),
                        stock.getId()
                )
                .orElseThrow(() ->
                        new RuntimeException(
                                "보유하고 있지 않은 주식입니다: "
                                        + stock.getName()
                        )
                );

        if (portfolio.getQuantity() < quantity) {
            throw new RuntimeException(
                    "보유 수량이 부족합니다. 보유 수량: "
                            + portfolio.getQuantity()
                            + ", 매도 수량: "
                            + quantity
            );
        }

        user.setBalance(
                user.getBalance() + totalAmount
        );

        Long remainingQuantity =
                portfolio.getQuantity() - quantity;

        Long realizedProfit =
                (currentPrice - portfolio.getAveragePrice()) * quantity;

        if (remainingQuantity == 0L) {
            portfolioRepository.delete(portfolio);
            return realizedProfit;
        }

        portfolio.setQuantity(remainingQuantity);
        portfolioRepository.save(portfolio);
        return realizedProfit;
    }
}
