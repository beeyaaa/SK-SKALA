package com.skala.skala_shop_api.controller;

import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.validation.annotation.Validated;

import com.skala.skala_shop_api.common.Response;
import com.skala.skala_shop_api.data.dto.CustomerSession;
import com.skala.skala_shop_api.data.dto.OrderRequest;
import com.skala.skala_shop_api.data.table.Customer;
import com.skala.skala_shop_api.service.CustomerService;

import lombok.RequiredArgsConstructor;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.security.SecurityRequirement;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Positive;

@RestController // 반환값을 JSON 응답으로 전달하는 REST Controller
@RequestMapping("/api/customers") //이 컨트롤러의 기본 URL 경로를 지정
@RequiredArgsConstructor 
@Validated
@Tag(name = "고객", description = "회원·로그인·주문·취소 API")
public class CustomerController {

    private final CustomerService customerService;

    // GET /api/customers/list?offset=0&count=10
    // 전체 고객 목록 조회 API
    @GetMapping("/list")
    @Operation(summary = "고객 목록 조회")
    public Response getAllCustomers(
            @Parameter(description = "페이지 번호(0부터 시작)", example = "0")
            @RequestParam(defaultValue = "0")
            @Min(value = 0, message = "offset은 0 이상이어야 합니다.") int offset,
            @Parameter(description = "페이지 크기", example = "10")
            @RequestParam(defaultValue = "10")
            @Positive(message = "count는 1 이상이어야 합니다.") int count) {
        return customerService.getAllCustomers(offset, count);
    }

    // GET /api/customers/{customerId}
    // 단일 고객 상세 조회 API
    @GetMapping("/{customerId}")
    @Operation(summary = "고객 및 주문상품 조회")
    public Response getCustomerById(
            @Parameter(description = "고객 ID", example = "skala01")
            @PathVariable
            @NotBlank(message = "고객 ID는 필수입니다.") String customerId) {
        return customerService.getCustomerById(customerId);
    }

    // POST /api/customers
    //고객 등록
    @PostMapping
    @Operation(summary = "회원가입")
    public Response createCustomer(@Valid @RequestBody Customer customer) {
        return customerService.createCustomer(customer);
    }

    // POST /api/customers/login
    // 고객 로그인
    @PostMapping("/login")
    @Operation(summary = "로그인", description = "성공하면 bff-access JWT Cookie를 발급합니다.")
    public Response loginCustomer(@Valid @RequestBody CustomerSession customerSession) {
        return customerService.loginCustomer(customerSession);
    }

    // PUT /api/customers
    // 고객 정보 수정
    @PutMapping
    @Operation(summary = "고객 포인트 수정")
    public Response updateCustomer(@RequestBody Customer customer) {
        return customerService.updateCustomer(customer);
    }

    // DELETE /api/customers
    // 고객 삭제
    @DeleteMapping
    @Operation(summary = "고객 삭제")
    public Response deleteCustomer(@RequestBody Customer customer) {
        return customerService.deleteCustomer(customer);
    }

    // POST /api/customers/order
    // 고객 상품 주문
    @PostMapping("/order")
    @Operation(summary = "상품 주문", description = "JWT Cookie에서 현재 고객을 식별합니다.")
    @SecurityRequirement(name = "cookieAuth")
    public Response placeOrder(@Valid @RequestBody OrderRequest order) {
        return customerService.placeOrder(order);
    }

    // POST /api/customers/cancel
    // 고객 주문 취소
    @PostMapping("/cancel")
    @Operation(summary = "주문 취소", description = "주문 수량을 차감하고 포인트를 환급합니다.")
    @SecurityRequirement(name = "cookieAuth")
    public Response cancelOrder(@Valid @RequestBody OrderRequest order) {
        return customerService.cancelOrder(order);
    }
}
