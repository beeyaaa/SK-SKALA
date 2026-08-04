package com.skala.stock.dto;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;

/**
 * 거래 직후(트랜잭션 내부/외부) 상태를 비교하거나
 * 집계 쿼리 결과를 묶어서 다룰 때 쓰는 DTO다.
 *
 * - MyBatis 집계 쿼리 결과를 담는 용도로 두는 게 목적이다
 * - 엔티티로 만들지 않는다(영속성 컨텍스트에 얽히지 않게)
 */
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class TradeSnapshotDto {
    private Long userId;
    private Long totalAssets;
    private Double totalReturnRate;
}

