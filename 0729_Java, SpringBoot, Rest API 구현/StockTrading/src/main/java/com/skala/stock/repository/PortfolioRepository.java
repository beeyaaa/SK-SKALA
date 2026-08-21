package com.skala.stock.repository;

import com.skala.stock.entity.Portfolio;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

@Repository
public interface PortfolioRepository extends JpaRepository<Portfolio, Long> {
    List<Portfolio> findByUserId(Long userId);
    Optional<Portfolio> findByUserIdAndStockId(Long userId, Long stockId);
    boolean existsByUserIdAndStockId(Long userId, Long stockId);
}
