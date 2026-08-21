package com.skala.skala_shop_api.repository;

import java.util.Optional;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import com.skala.skala_shop_api.data.table.Product;

// Product 엔터티의 기본 CRUD와 페이징 기능을 제공하는 JPA 저장소
@Repository
public interface ProductRepository extends JpaRepository<Product, Long> {

    // 상품 이름이 일치하는 데이터를 조회하며, 결과가 없을 수 있으므로 Optional로 반환
    Optional<Product> findByProductName(String productName);

    // 입력된 상품명과 가격 범위에 맞는 상품을 페이지 단위로 검색
    @Query("""
            SELECT product
            FROM Product product
            WHERE (:keyword IS NULL
                   OR LOWER(product.productName) LIKE LOWER(CONCAT('%', :keyword, '%')))
              AND (:minPrice IS NULL OR product.productPrice >= :minPrice)
              AND (:maxPrice IS NULL OR product.productPrice <= :maxPrice)
            """)
    Page<Product> searchProducts(
            @Param("keyword") String keyword,
            @Param("minPrice") Double minPrice,
            @Param("maxPrice") Double maxPrice,
            Pageable pageable);
}
