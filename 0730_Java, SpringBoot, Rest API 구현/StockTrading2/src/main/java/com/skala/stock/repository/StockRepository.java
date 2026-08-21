package com.skala.stock.repository;

import com.skala.stock.entity.Stock;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.Optional;



@Repository
public interface StockRepository extends JpaRepository<Stock, Long> {
    @Query("SELECT s FROM Stock s WHERE s.code = :code")
    Optional<Stock> findByCode(
            @Param("code") String code
    );
    boolean existsByCode(String code);
}
