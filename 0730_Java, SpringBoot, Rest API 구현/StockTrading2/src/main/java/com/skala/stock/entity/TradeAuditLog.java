package com.skala.stock.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.PrePersist;
import jakarta.persistence.Table;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

import java.time.LocalDateTime;

/**
 * 거래 처리 중 남기는 감사/진단 로그 테이블이다.
 *
 * 목적:
 * - REQUIRES_NEW 트랜잭션 예제를 실제로 남길 저장소가 필요하다
 * - 거래 트랜잭션과 분리된 트랜잭션으로도 데이터를 남길 수 있다는 걸 보여준다
 *
 * 주의:
 * - 이 테이블은 교육용이다. 운영에서는 개인정보/보안/용량/정책을 고려해야 한다
 */
@Entity
@Table(name = "trade_audit_logs")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class TradeAuditLog {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "user_id", nullable = false)
    private Long userId;

    @Column(name = "stock_id", nullable = false)
    private Long stockId;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 10)
    private Transaction.TransactionType type;

    @Column(nullable = false, length = 500)
    private String message;

    @Column(name = "total_assets")
    private Long totalAssets;

    @Column(name = "total_return_rate")
    private Double totalReturnRate;

    @Column(name = "created_at")
    private LocalDateTime createdAt;

    @PrePersist
    void onCreate() {
        createdAt = LocalDateTime.now();
    }
}

