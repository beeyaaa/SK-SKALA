package com.skala.skala_shop_api.service;

import java.util.List;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import com.skala.skala_shop_api.common.PagedList;
import com.skala.skala_shop_api.common.Response;
import com.skala.skala_shop_api.common.SessionHandler;
import com.skala.skala_shop_api.data.dto.CustomerSession;
import com.skala.skala_shop_api.data.dto.OrderItemDto;
import com.skala.skala_shop_api.data.dto.OrderListDto;
import com.skala.skala_shop_api.data.dto.OrderRequest;
import com.skala.skala_shop_api.data.table.Customer;
import com.skala.skala_shop_api.data.table.OrderItem;
import com.skala.skala_shop_api.data.table.Product;
import com.skala.skala_shop_api.exception.Error;
import com.skala.skala_shop_api.exception.ParameterException;
import com.skala.skala_shop_api.exception.ResponseException;
import com.skala.skala_shop_api.repository.CustomerRepository;
import com.skala.skala_shop_api.repository.OrderItemRepository;
import com.skala.skala_shop_api.repository.ProductRepository;
import com.skala.skala_shop_api.tools.StringUtil;

import lombok.RequiredArgsConstructor;

@Service
@RequiredArgsConstructor
public class CustomerService {

    private static final double INITIAL_POINT = 1_000_000.0;

    private final ProductRepository productRepository;
    private final CustomerRepository customerRepository;
    private final OrderItemRepository orderItemRepository;
    private final SessionHandler sessionHandler;

    // 1. 전체 고객 목록 조회
    public Response getAllCustomers(int offset, int count) {
        validatePagination(offset, count);

        // Pageable 객체 생성
        Pageable pageable = PageRequest.of(
                offset,
                count,
                Sort.by(Sort.Direction.ASC, "customerId"));
        //페이지 단위 조회
        Page<Customer> customerPage = customerRepository.findAll(pageable);
        List<Customer> customers = customerPage.getContent()
                .stream()
                .map(this::withoutPassword)
                .toList();
        
        PagedList<Customer> pagedList = PagedList.<Customer>builder()
                .offset(customerPage.getNumber())
                .count(customerPage.getNumberOfElements())
                .total(customerPage.getTotalElements())
                .items(customers)
                .build();
        //PagedList로 결과 변환 후 Response로 감싸 반환
        return Response.builder()
                .body(pagedList)
                .build();
    }

    // 2. 단일 고객 및 상품 목록 조회
    @Transactional(readOnly = true)
    public Response getCustomerById(String customerId) {
        Customer customer = getCustomer(customerId);
        //고객이 보유한 OrderItem 리스트 조회
        List<OrderItemDto> products = orderItemRepository
                .findByCustomerCustomerId(customerId)
                .stream()
                .map(this::toOrderItemDto)
                .toList();
        //DTO 리스트 변환
        OrderListDto orderList = OrderListDto.builder()
                .customerId(customer.getCustomerId())
                .customerPoint(customer.getCustomerPoint())
                .products(products)
                .build();
        //DTO를 Response에 세팅해 반환
        return Response.builder()
                .body(orderList)
                .build();
    }

    // 3. 고객 생성
    public Response createCustomer(Customer requestCustomer) {
        if (requestCustomer == null
                || StringUtil.isAnyBlank(
                        requestCustomer.getCustomerId(),
                        requestCustomer.getCustomerPassword())) {
            throw new ParameterException("customerId", "customerPassword");
        }

        //중복 아이디 체크
        if (customerRepository.existsById(requestCustomer.getCustomerId())) {
            throw new ResponseException(Error.DATA_DUPLICATED);
        }
        //customer 객체 생성, 초기 적립 포인트 세팅
        Customer customer = new Customer(
                requestCustomer.getCustomerId(),
                INITIAL_POINT);
        customer.setCustomerPassword(requestCustomer.getCustomerPassword());
        
        //저장 후 response 반환
        Customer savedCustomer = customerRepository.save(customer);
        return Response.builder()
                .body(withoutPassword(savedCustomer))
                .build();
    }

    // 4. 고객 로그인
    public Response loginCustomer(CustomerSession customerSession) {
        if (customerSession == null
                || StringUtil.isAnyBlank(
                        customerSession.getCustomerId(),
                        customerSession.getCustomerPassword())) {
            throw new ParameterException("customerId", "customerPassword");
        }
        //id로 조회, 비밀번호 검증
        Customer customer = customerRepository
                .findById(customerSession.getCustomerId())
                .orElseThrow(() -> new ResponseException(Error.DATA_NOT_FOUND));

        if (!customerSession.getCustomerPassword().equals(customer.getCustomerPassword())) {
            throw new ResponseException(Error.NOT_AUTHENTICATED);
        }
        //** SessionHandler: 지금 요청한 사람이 누군지 확인하는 도구 -> 로그인한 사람이 누구인지 알아야 하는 기능에서만 사용
        sessionHandler.storeAccessToken(customer.getCustomerId());

        return Response.builder()
                .body(withoutPassword(customer))
                .build();
    }

    // 5. 고객 정보 업데이트
    public Response updateCustomer(Customer requestCustomer) {
        if (requestCustomer == null
                || StringUtil.isAnyBlank(requestCustomer.getCustomerId())
                || requestCustomer.getCustomerPoint() == null
                || requestCustomer.getCustomerPoint() < 0) {
            throw new ParameterException("customerId", "customerPoint");
        }
        //존재 확인 후 포인트 업데이트
        Customer customer = getCustomer(requestCustomer.getCustomerId());
        customer.setCustomerPoint(requestCustomer.getCustomerPoint());

        Customer savedCustomer = customerRepository.save(customer);
        return Response.builder()
                .body(withoutPassword(savedCustomer))
                .build();
    }

    // 6. 고객 삭제
    @Transactional
    public Response deleteCustomer(Customer requestCustomer) {
        if (requestCustomer == null
                || StringUtil.isAnyBlank(requestCustomer.getCustomerId())) {
            throw new ParameterException("customerId");
        }
        //customerid로 존재 확인 후 삭제
        Customer customer = getCustomer(requestCustomer.getCustomerId());
        List<OrderItem> orderItems = orderItemRepository
                .findByCustomerCustomerId(customer.getCustomerId());

        orderItemRepository.deleteAll(orderItems);
        customerRepository.delete(customer);

        return Response.builder()
                .body(withoutPassword(customer))
                .build();
    }

    // 7. 상품 주문
    @Transactional
    public Response placeOrder(OrderRequest order) {
        validateOrder(order);

        //현재 로그인된 customerid rkwudhrl
        Customer customer = getCustomer(sessionHandler.getCustomerId());
        Product product = getProduct(order.getProductId());
        double orderPrice = product.getProductPrice() * order.getQuantity();

        if (customer.getCustomerPoint() < orderPrice) {
            throw new ResponseException(Error.INSUFFICIENT_FUNDS);
        }
        //포인트 충분성 체크 및 차감
        customer.setCustomerPoint(customer.getCustomerPoint() - orderPrice);

        //orderitem에 이미 주문한 상품이면 수량 추가, 없으면 생성
        OrderItem orderItem = orderItemRepository
                .findByCustomerAndProduct(customer, product)
                .orElseGet(() -> new OrderItem(customer, product, 0));
        orderItem.setQuantity(orderItem.getQuantity() + order.getQuantity());

        customerRepository.save(customer);
        orderItemRepository.save(orderItem);

        return Response.builder()
                .body(withoutPassword(customer))
                .build();
    }

    // 8. 주문 취소
    @Transactional
    public Response cancelOrder(OrderRequest order) {
        validateOrder(order);
        //취소할 customer, product 엔터티 조회
        Customer customer = getCustomer(sessionHandler.getCustomerId());
        Product product = getProduct(order.getProductId());
        OrderItem orderItem = orderItemRepository
                .findByCustomerAndProduct(customer, product)
                .orElseThrow(() -> new ResponseException(Error.INSUFFICIENT_QUANTITY));
        //orderitem 보유수량 검증
        if (orderItem.getQuantity() < order.getQuantity()) {
            throw new ResponseException(Error.INSUFFICIENT_QUANTITY);
        }
        //수량 감소/삭제 처리
        int remainingQuantity = orderItem.getQuantity() - order.getQuantity();
        if (remainingQuantity == 0) {
            orderItemRepository.delete(orderItem);
        } else {
            orderItem.setQuantity(remainingQuantity);
            orderItemRepository.save(orderItem);
        }
        //취소 금액만큼 고객 포인트 증가
        double refund = product.getProductPrice() * order.getQuantity();
        customer.setCustomerPoint(customer.getCustomerPoint() + refund);
        customerRepository.save(customer);

        return Response.builder()
                .body(withoutPassword(customer))
                .build();
    }

    private Customer getCustomer(String customerId) {
        return customerRepository.findById(customerId)
                .orElseThrow(() -> new ResponseException(
                        Error.DATA_NOT_FOUND,
                        "Customer not found"));
    }

    private Product getProduct(Long productId) {
        return productRepository.findById(productId)
                .orElseThrow(() -> new ResponseException(
                        Error.DATA_NOT_FOUND,
                        "Product not found"));
    }

    private OrderItemDto toOrderItemDto(OrderItem orderItem) {
        Product product = orderItem.getProduct();
        return OrderItemDto.builder()
                .productId(product.getId())
                .productName(product.getProductName())
                .productPrice(product.getProductPrice())
                .quantity(orderItem.getQuantity())
                .build();
    }

    private Customer withoutPassword(Customer customer) {
        Customer responseCustomer = new Customer(
                customer.getCustomerId(),
                customer.getCustomerPoint());
        responseCustomer.setCustomerPassword(null);
        return responseCustomer;
    }

    private void validateOrder(OrderRequest order) {
        if (order == null
                || order.getProductId() == null
                || order.getQuantity() == null
                || order.getQuantity() <= 0) {
            throw new ParameterException("productId", "quantity");
        }
    }

    private void validatePagination(int offset, int count) {
        if (offset < 0 || count <= 0) {
            throw new ParameterException("offset", "count");
        }
    }
}
