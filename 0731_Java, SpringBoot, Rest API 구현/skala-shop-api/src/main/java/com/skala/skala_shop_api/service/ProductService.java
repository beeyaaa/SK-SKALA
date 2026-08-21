package com.skala.skala_shop_api.service;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.stereotype.Service;

import com.skala.skala_shop_api.common.PagedList;
import com.skala.skala_shop_api.common.Response;
import com.skala.skala_shop_api.data.table.Product;
import com.skala.skala_shop_api.exception.Error;
import com.skala.skala_shop_api.exception.ParameterException;
import com.skala.skala_shop_api.exception.ResponseException;
import com.skala.skala_shop_api.repository.ProductRepository;
import com.skala.skala_shop_api.tools.StringUtil;

import lombok.RequiredArgsConstructor;

@Service 
@RequiredArgsConstructor 
public class ProductService {

    private final ProductRepository productRepository;

    // 1. 전체 상품 목록 조회
    public Response getAllProducts(int offset, int count) {
        validatePagination(offset, count);

        //Pageable 객체 생성 -> 페이징 및 정렬
        Pageable pageable = PageRequest.of(
                offset,
                count,
                Sort.by(Sort.Direction.ASC, "id"));
        
        //페이지 단위 데이터 조회
        Page<Product> productPage = productRepository.findAll(pageable);
        //결과를 PagedList 객체로 가공
        PagedList<Product> pagedList = PagedList.<Product>builder()
                .offset(productPage.getNumber())
                .count(productPage.getNumberOfElements())
                .total(productPage.getTotalElements())
                .items(productPage.getContent())
                .build();
        //Response 객체에 담아 반환
        return Response.builder()
                .body(pagedList)
                .build();
    }

    // 차별화 기능: 상품명과 가격 범위로 상품 검색
    public Response searchProducts(
            String keyword,
            Double minPrice,
            Double maxPrice,
            int offset,
            int count) {
        validatePagination(offset, count);
        validatePriceRange(minPrice, maxPrice);

        String normalizedKeyword = StringUtil.isAnyBlank(keyword)
                ? null
                : keyword.trim();
        Pageable pageable = PageRequest.of(
                offset,
                count,
                Sort.by(Sort.Direction.ASC, "id"));
        Page<Product> productPage = productRepository.searchProducts(
                normalizedKeyword,
                minPrice,
                maxPrice,
                pageable);

        PagedList<Product> pagedList = PagedList.<Product>builder()
                .offset(productPage.getNumber())
                .count(productPage.getNumberOfElements())
                .total(productPage.getTotalElements())
                .items(productPage.getContent())
                .build();

        return Response.builder()
                .body(pagedList)
                .build();
    }

    // 2. 개별 상품 상세 조회
    public Response getProductById(Long id) {
        //Id로 상품 조회
        Product product = productRepository.findById(id)
                .orElseThrow(() -> new ResponseException(Error.DATA_NOT_FOUND));
        //Response 객체에 담아 반환 
        return Response.builder()
                .body(product)
                .build();
    }

    // 3. 상품 등록(생성)
    public Response createProduct(Product product) {
        validateProduct(product);
        //입력값 검증
        if (productRepository.findByProductName(product.getProductName()).isPresent()) {
            throw new ResponseException(Error.DATA_DUPLICATED);
        }

        //신규 Product id는 0L로 세팅
        product.setId(null);
        Product savedProduct = productRepository.save(product);
        //Response 객체에 담아 반환 
        return Response.builder()
                .body(savedProduct)
                .build();
    }

    // 4. 상품 정보 수정
    public Response updateProduct(Product product) {
        validateProduct(product);

        //입력값 검증
        if (product.getId() == null) {
            throw new ParameterException("id");
        }
        
        //해당 id의 product 존재하는지 확인
        Product savedProduct = productRepository.findById(product.getId())
                .map(existingProduct -> {
                    existingProduct.setProductName(product.getProductName());
                    existingProduct.setProductPrice(product.getProductPrice());
                    return productRepository.save(existingProduct);
                })
                .orElseThrow(() -> new ResponseException(Error.DATA_NOT_FOUND));
        
        //Response 객체에 담아 반환 
        return Response.builder()
                .body(savedProduct)
                .build();
    }

    // 5. 상품 삭제
    public Response deleteProduct(Product product) {
        if (product == null || product.getId() == null) {
            throw new ParameterException("id");
        }

        // id로 조회해서 삭제
        Product savedProduct = productRepository.findById(product.getId())
                .orElseThrow(() -> new ResponseException(Error.DATA_NOT_FOUND));

        productRepository.delete(savedProduct);

        //Response 객체에 담아 반환
        return Response.builder()
                .body(savedProduct)
                .build();
    }

    // 상품명과 가격 입력값을 공통으로 검증
    private void validateProduct(Product product) {
        if (product == null
                || StringUtil.isAnyBlank(product.getProductName())
                || product.getProductPrice() == null
                || product.getProductPrice() <= 0) {
            throw new ParameterException("productName", "productPrice");
        }
    }

    private void validatePagination(int offset, int count) {
        if (offset < 0 || count <= 0) {
            throw new ParameterException("offset", "count");
        }
    }

    private void validatePriceRange(Double minPrice, Double maxPrice) {
        if ((minPrice != null && minPrice < 0)
                || (maxPrice != null && maxPrice <= 0)
                || (minPrice != null && maxPrice != null && minPrice > maxPrice)) {
            throw new ParameterException("minPrice", "maxPrice");
        }
    }
}
