package com.skala.skala_shop_api.repository;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import com.skala.skala_shop_api.data.table.Customer;

// Customer 엔터티의 기본 CRUD와 페이징 기능을 제공하는 JPA 저장소
@Repository
public interface CustomerRepository extends JpaRepository<Customer, String> {
}
