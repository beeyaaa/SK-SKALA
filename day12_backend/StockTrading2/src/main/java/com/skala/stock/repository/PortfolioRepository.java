package com.skala.stock.repository;

import com.skala.stock.entity.Portfolio;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;
import java.util.Optional;

@Repository
public interface PortfolioRepository extends JpaRepository<Portfolio, Long> {
    List<Portfolio> findByUserId(Long userId);
    @Query(
        "SELECT p FROM Portfolio p " +
        "JOIN FETCH p.user " +
        "JOIN FETCH p.stock " +
        "WHERE p.user.id = :userId " +
        "AND p.stock.id = :stockId"
    )
    Optional<Portfolio> findByUserIdAndStockId(
            @Param("userId") Long userId,
            @Param("stockId") Long stockId
    );
    boolean existsByUserIdAndStockId(Long userId, Long stockId);

    @Query(
        "SELECT p FROM Portfolio p " +
        "JOIN FETCH p.user " +
        "JOIN FETCH p.stock " +
        "WHERE p.user.id = :userId " +
        "ORDER BY p.id ASC"
    )
    List<Portfolio> findPortfolioWithProfitLoss(
            @Param("userId") Long userId
    );

    @Query(
        "SELECT COALESCE(SUM(p.quantity * p.stock.currentPrice), 0) " +
        "FROM Portfolio p " +
        "WHERE p.user.id = :userId"
    )
    Long calculateStockValue(@Param("userId") Long userId);

    @Query(
        "SELECT COALESCE(SUM(p.quantity * p.averagePrice), 0) " +
        "FROM Portfolio p " +
        "WHERE p.user.id = :userId"
    )
    Long calculateTotalPurchaseAmount(@Param("userId") Long userId);

    @Query(
        "SELECT COALESCE(SUM(p.quantity * " +
        "(p.stock.currentPrice - p.averagePrice)), 0) " +
        "FROM Portfolio p " +
        "WHERE p.user.id = :userId"
    )
    Long calculateUnrealizedProfit(@Param("userId") Long userId);
}
