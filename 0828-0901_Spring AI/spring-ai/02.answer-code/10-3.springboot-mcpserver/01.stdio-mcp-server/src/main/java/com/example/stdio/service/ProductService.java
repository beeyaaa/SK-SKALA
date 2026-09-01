package com.example.stdio.service;

import com.example.stdio.domain.Product;
import com.example.stdio.repository.ProductRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

/**
 * Product 서비스
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class ProductService {

    private final ProductRepository productRepository;

    @Transactional
    public Product createProduct(Product product) {
        log.info("Creating product: name={}", product.getName());
        Product savedProduct = productRepository.save(product);
        log.info("Product created successfully: id={}, name={}", savedProduct.getId(), savedProduct.getName());
        return savedProduct;
    }

    @Transactional
    public Product updateProduct(Long id, Product product) {
        log.info("Updating product: id={}", id);
        Product existingProduct = productRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Product not found: id=" + id));
        
        existingProduct.setName(product.getName());
        existingProduct.setDescription(product.getDescription());
        existingProduct.setPrice(product.getPrice());
        existingProduct.setStock(product.getStock());
        
        Product updatedProduct = productRepository.save(existingProduct);
        log.info("Product updated successfully: id={}", updatedProduct.getId());
        return updatedProduct;
    }

    @Transactional
    public void deleteProduct(Long id) {
        log.info("Deleting product: id={}", id);
        Product product = productRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Product not found: id=" + id));
        productRepository.delete(product);
        log.info("Product deleted successfully: id={}", id);
    }

    @Transactional(readOnly = true)
    public Product getProduct(Long id) {
        return productRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Product not found: id=" + id));
    }

    @Transactional(readOnly = true)
    public List<Product> getAllProducts() {
        return productRepository.findAll();
    }

    @Transactional(readOnly = true)
    public List<Product> searchProductsByName(String name) {
        return productRepository.findByNameContainingIgnoreCase(name);
    }
}
