package com.skala.stock.service;

import com.skala.stock.dto.TradeRequestDto;
import com.skala.stock.dto.TransactionDto;
import com.skala.stock.entity.Stock;
import com.skala.stock.entity.Transaction;
import com.skala.stock.entity.User;
import com.skala.stock.repository.StockRepository;
import com.skala.stock.repository.TransactionRepository;
import com.skala.stock.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
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
    private final PortfolioService portfolioService;

    @Transactional
    public TransactionDto executeTrade(TradeRequestDto tradeRequest) {
        User user = userRepository.findById(tradeRequest.getUserId())
                .orElseThrow(() -> new RuntimeException("사용자를 찾을 수 없습니다: " + tradeRequest.getUserId()));
        Stock stock = stockRepository.findById(tradeRequest.getStockId())
                .orElseThrow(() -> new RuntimeException("주식을 찾을 수 없습니다: " + tradeRequest.getStockId()));

        Long currentPrice = stock.getCurrentPrice();
        Long totalAmount = currentPrice * tradeRequest.getQuantity();

        if (tradeRequest.getType() == Transaction.TransactionType.BUY) {
            // 매수: 잔액 확인
            if (user.getBalance() < totalAmount) {
                throw new RuntimeException("잔액이 부족합니다. 필요 금액: " + totalAmount + ", 보유 금액: " + user.getBalance());
            }
            // 잔액 차감
            user.setBalance(user.getBalance() - totalAmount);
            // 포트폴리오에 추가
            portfolioService.addToPortfolio(user.getId(), stock.getId(), tradeRequest.getQuantity(), currentPrice);
        } else {
            // 매도: 보유 수량 확인
            var portfolio = portfolioService.getPortfolio(user.getId(), stock.getId());
            if (portfolio == null || portfolio.getQuantity() < tradeRequest.getQuantity()) {
                throw new RuntimeException("보유 수량이 부족합니다. 보유 수량: " + (portfolio != null ? portfolio.getQuantity() : 0) + ", 매도 수량: " + tradeRequest.getQuantity());
            }
            // 잔액 증가
            user.setBalance(user.getBalance() + totalAmount);
            // 포트폴리오에서 차감
            Long remainingQuantity = portfolio.getQuantity() - tradeRequest.getQuantity();
            if (remainingQuantity > 0) {
                portfolioService.updatePortfolio(user.getId(), stock.getId(), remainingQuantity);
            } else {
                portfolioService.removeFromPortfolio(user.getId(), stock.getId());
            }
        }

        userRepository.save(user);

        // 거래 기록 생성
        Transaction transaction = Transaction.builder()
                .user(user)
                .stock(stock)
                .type(tradeRequest.getType())
                .quantity(tradeRequest.getQuantity())
                .price(currentPrice)
                .totalAmount(totalAmount)
                .build();

        Transaction savedTransaction = transactionRepository.save(transaction);
        return convertToDto(savedTransaction);
    }

    public List<TransactionDto> getUserTransactions(Long userId) {
        List<Transaction> transactions = transactionRepository.findByUserIdOrderByTransactionDateDesc(userId);
        return transactions.stream()
                .map(this::convertToDto)
                .collect(Collectors.toList());
    }

    public TransactionDto getTransactionById(Long id) {
        Transaction transaction = transactionRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("거래를 찾을 수 없습니다: " + id));
        return convertToDto(transaction);
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
                .transactionDate(transaction.getTransactionDate())
                .createdAt(transaction.getCreatedAt())
                .build();
    }
}
