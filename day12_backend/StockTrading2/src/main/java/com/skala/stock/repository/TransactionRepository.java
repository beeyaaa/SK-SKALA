package com.skala.stock.repository;

import com.skala.stock.entity.Transaction;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.Optional;
import java.util.List;

@Repository
public interface TransactionRepository extends JpaRepository<Transaction, Long> {
    List<Transaction> findByUserIdOrderByTransactionDateDesc(Long userId);
    List<Transaction> findByUserIdAndStockIdOrderByTransactionDateDesc(Long userId, Long stockId);

    @Query(
        "SELECT t FROM Transaction t " +
        "JOIN FETCH t.user " +
        "JOIN FETCH t.stock " +
        "WHERE t.id = :id"
    )
    Optional<Transaction> findTransactionDetailById(
            @Param("id") Long id
    );

    @Query(
        "SELECT t FROM Transaction t " +
        "JOIN FETCH t.user " +
        "JOIN FETCH t.stock " +
        "WHERE t.user.id = :userId " +
        "ORDER BY t.transactionDate DESC"
    )
    List<Transaction> findTransactionsWithDetails(
            @Param("userId") Long userId
    );

    @Query(
        "SELECT t FROM Transaction t " +
        "JOIN FETCH t.user " +
        "JOIN FETCH t.stock " +
        "WHERE t.user.id = :userId " +
        "AND t.stock.id = :stockId " +
        "ORDER BY t.transactionDate DESC"
    )
    List<Transaction> findStockTransactionsWithDetails(
            @Param("userId") Long userId,
            @Param("stockId") Long stockId
    );

    @Query(
        "SELECT COALESCE(SUM(t.realizedProfit), 0) " +
        "FROM Transaction t " +
        "WHERE t.user.id = :userId " +
        "AND t.type = :type"
    )
    Long calculateRealizedProfit(
            @Param("userId") Long userId,
            @Param("type") Transaction.TransactionType type
    );

    @Query(
        "SELECT COALESCE(SUM(t.totalAmount - t.realizedProfit), 0) " +
        "FROM Transaction t " +
        "WHERE t.user.id = :userId " +
        "AND t.type = :type"
    )
    Long calculateSoldPurchaseAmount(
            @Param("userId") Long userId,
            @Param("type") Transaction.TransactionType type
    );
}
