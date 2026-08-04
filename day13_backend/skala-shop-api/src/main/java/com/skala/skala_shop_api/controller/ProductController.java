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
import com.skala.skala_shop_api.data.table.Product;
import com.skala.skala_shop_api.service.ProductService;

import lombok.RequiredArgsConstructor;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.Positive;
import jakarta.validation.constraints.PositiveOrZero;

@RestController // 반환값을 JSON 응답으로 전달하는 REST Controller
@RequestMapping("/api/products") //이 컨트롤러의 기본 URL 경로를 /api/products로 지정
@RequiredArgsConstructor // final 필드를 받는 생성자를 자동 생성
@Validated
@Tag(name = "상품", description = "상품 조회·등록·수정·삭제 API")
public class ProductController {

    private final ProductService productService;

    // GET /api/products/list?offset=0&count=10
    // 전체 상품 목록 조회 API
    @GetMapping("/list")
    @Operation(summary = "상품 목록 조회", description = "상품을 ID 오름차순으로 페이지 조회합니다.")
    public Response getAllProducts(
            @Parameter(description = "페이지 번호(0부터 시작)", example = "0")
            @RequestParam(defaultValue = "0")
            @Min(value = 0, message = "offset은 0 이상이어야 합니다.") int offset,
            @Parameter(description = "페이지 크기", example = "10")
            @RequestParam(defaultValue = "10")
            @Positive(message = "count는 1 이상이어야 합니다.") int count) {
        return productService.getAllProducts(offset, count); //productService의 메서드 호출
    }

    // GET /api/products/search?keyword=셔츠&minPrice=50000&maxPrice=100000
    // 상품명과 가격 범위로 상품을 검색하는 차별화 API
    @GetMapping("/search")
    @Operation(
            summary = "상품 검색·가격 필터",
            description = "상품명 일부와 최소·최대 가격을 조합하여 상품을 페이지 조회합니다.")
    public Response searchProducts(
            @Parameter(description = "상품명에 포함될 검색어", example = "셔츠")
            @RequestParam(required = false) String keyword,
            @Parameter(description = "최소 가격", example = "50000")
            @RequestParam(required = false)
            @PositiveOrZero(message = "최소 가격은 0 이상이어야 합니다.") Double minPrice,
            @Parameter(description = "최대 가격", example = "100000")
            @RequestParam(required = false)
            @Positive(message = "최대 가격은 0보다 커야 합니다.") Double maxPrice,
            @Parameter(description = "페이지 번호(0부터 시작)", example = "0")
            @RequestParam(defaultValue = "0")
            @Min(value = 0, message = "offset은 0 이상이어야 합니다.") int offset,
            @Parameter(description = "페이지 크기", example = "10")
            @RequestParam(defaultValue = "10")
            @Positive(message = "count는 1 이상이어야 합니다.") int count) {
        return productService.searchProducts(
                keyword,
                minPrice,
                maxPrice,
                offset,
                count);
    }

    // GET /api/products/{id}
    // 개별 상품 상세 조회 API
    @GetMapping("/{id}")
    @Operation(summary = "상품 상세 조회")
    public Response getProductById(
            @Parameter(description = "상품 ID", example = "1")
            @PathVariable
            @Positive(message = "상품 ID는 1 이상이어야 합니다.") Long id) {
        return productService.getProductById(id);
    }

    // POST /api/products
    // 상품 등록 API
    @PostMapping
    @Operation(summary = "상품 등록")
    public Response createProduct(@Valid @RequestBody Product product) {
        return productService.createProduct(product);
    }

    // PUT /api/products
    // 상품 정보 수정 API
    @PutMapping
    @Operation(summary = "상품 수정")
    public Response updateProduct(@Valid @RequestBody Product product) {
        return productService.updateProduct(product);
    }

    // DELETE /api/products
    // 상품 삭제 API
    @DeleteMapping
    @Operation(summary = "상품 삭제")
    public Response deleteProduct(@RequestBody Product product) {
        return productService.deleteProduct(product);
    }
}
