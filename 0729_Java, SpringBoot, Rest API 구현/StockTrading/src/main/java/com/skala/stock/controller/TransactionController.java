package com.skala.stock.controller;

import com.skala.stock.dto.TradeRequestDto;
import com.skala.stock.dto.TransactionDto;
import com.skala.stock.service.TransactionService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/transactions")
@RequiredArgsConstructor
@Tag(name = "거래 관리", description = "주식 매수/매도 거래 API")
public class TransactionController {

    private final TransactionService transactionService;

    @PostMapping("/trade")
    @Operation(summary = "주식 거래 실행", description = "주식 매수 또는 매도를 실행합니다")
    public ResponseEntity<TransactionDto> executeTrade(@Valid @RequestBody TradeRequestDto tradeRequest) {
        TransactionDto transaction = transactionService.executeTrade(tradeRequest);
        return ResponseEntity.status(HttpStatus.CREATED).body(transaction);
    }

    @GetMapping("/user/{userId}")
    @Operation(summary = "사용자 거래 내역 조회", description = "특정 사용자의 전체 거래 내역을 조회합니다")
    public ResponseEntity<List<TransactionDto>> getUserTransactions(@PathVariable Long userId) {
        List<TransactionDto> transactions = transactionService.getUserTransactions(userId);
        return ResponseEntity.ok(transactions);
    }

    @GetMapping("/{id}")
    @Operation(summary = "거래 상세 조회", description = "거래 ID로 거래 상세 정보를 조회합니다")
    public ResponseEntity<TransactionDto> getTransactionById(@PathVariable Long id) {
        TransactionDto transaction = transactionService.getTransactionById(id);
        return ResponseEntity.ok(transaction);
    }
}
