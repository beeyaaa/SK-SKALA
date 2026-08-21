package com.skala.stock.dto;

import com.skala.stock.entity.Transaction;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import jakarta.validation.constraints.NotNull;
import java.time.LocalDateTime;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class TransactionDto {

    private Long id;
    private Long userId;
    private String username;
    private Long stockId;
    private String stockCode;
    private String stockName;
    
    @NotNull(message = "거래 유형은 필수입니다")
    private Transaction.TransactionType type;
    
    @NotNull(message = "거래 수량은 필수입니다")
    private Long quantity;
    
    @NotNull(message = "거래 가격은 필수입니다")
    private Long price;
    
    private Long totalAmount;
    private LocalDateTime transactionDate;
    private LocalDateTime createdAt;
}
