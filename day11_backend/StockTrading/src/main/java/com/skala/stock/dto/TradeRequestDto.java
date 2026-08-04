package com.skala.stock.dto;

import com.skala.stock.entity.Transaction;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import jakarta.validation.constraints.NotNull;

@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class TradeRequestDto {

    @NotNull(message = "사용자 ID는 필수입니다")
    private Long userId;
    
    @NotNull(message = "주식 ID는 필수입니다")
    private Long stockId;
    
    @NotNull(message = "거래 유형은 필수입니다")
    private Transaction.TransactionType type;
    
    @NotNull(message = "거래 수량은 필수입니다")
    private Long quantity;
}
