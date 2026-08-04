package com.skala.skala_shop_api.repository;

import java.util.List;
import java.util.Optional;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import com.skala.skala_shop_api.data.table.Customer;
import com.skala.skala_shop_api.data.table.OrderItem;
import com.skala.skala_shop_api.data.table.Product;

// OrderItem 엔터티의 기본 CRUD 기능을 제공하는 JPA 저장소
@Repository
public interface OrderItemRepository extends JpaRepository<OrderItem, Long> {

    // OrderItem의 customer를 거쳐 customerId가 일치하는 주문 상품 목록 조회
    List<OrderItem> findByCustomerCustomerId(String customerId);

    // 특정 고객이 특정 상품을 주문했는지 조회
    Optional<OrderItem> findByCustomerAndProduct(Customer customer, Product product);
}
