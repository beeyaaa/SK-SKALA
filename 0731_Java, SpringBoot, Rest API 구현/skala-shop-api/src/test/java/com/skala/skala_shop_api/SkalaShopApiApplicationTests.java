package com.skala.skala_shop_api;

import static org.hamcrest.Matchers.hasSize;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.webmvc.test.autoconfigure.AutoConfigureMockMvc;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.MvcResult;
import org.springframework.transaction.annotation.Transactional;

import com.skala.skala_shop_api.data.table.Product;
import com.skala.skala_shop_api.repository.ProductRepository;

import jakarta.servlet.http.Cookie;

@SpringBootTest
@AutoConfigureMockMvc
@Transactional
class SkalaShopApiApplicationTests {

	@Autowired
	private MockMvc mockMvc;

	@Autowired
	private ProductRepository productRepository;

	@Test
	void contextLoads() {
	}

	@Test
	void fashionSeedProductsAreLoaded() throws Exception {
		mockMvc.perform(get("/api/products/list")
						.param("offset", "0")
						.param("count", "10"))
				.andExpect(status().isOk())
				.andExpect(jsonPath("$.result").value(0))
				.andExpect(jsonPath("$.body.total").value(5))
				.andExpect(jsonPath("$.body.items", hasSize(5)));
	}

	@Test
	void productsCanBeFilteredByKeywordAndPriceRange() throws Exception {
		mockMvc.perform(get("/api/products/search")
						.param("keyword", "셔츠")
						.param("minPrice", "50000")
						.param("maxPrice", "100000")
						.param("offset", "0")
						.param("count", "10"))
				.andExpect(status().isOk())
				.andExpect(jsonPath("$.result").value(0))
				.andExpect(jsonPath("$.body.total").value(1))
				.andExpect(jsonPath("$.body.items", hasSize(1)))
				.andExpect(jsonPath("$.body.items[0].productName")
						.value("클래식 코튼 셔츠"));

		mockMvc.perform(get("/api/products/search")
						.param("minPrice", "100000")
						.param("maxPrice", "50000"))
				.andExpect(status().isBadRequest())
				.andExpect(jsonPath("$.result").value(1))
				.andExpect(jsonPath("$.code").value(400));
	}

	@Test
	void invalidPaginationReturnsBadRequest() throws Exception {
		mockMvc.perform(get("/api/products/list")
						.param("offset", "-1")
						.param("count", "10"))
				.andExpect(status().isBadRequest())
				.andExpect(jsonPath("$.result").value(1))
				.andExpect(jsonPath("$.code").value(400));

		mockMvc.perform(get("/api/customers/list")
						.param("offset", "0")
						.param("count", "0"))
				.andExpect(status().isBadRequest())
				.andExpect(jsonPath("$.result").value(1))
				.andExpect(jsonPath("$.code").value(400));
	}

	@Test
	void invalidRequestBodyIsHandledByGlobalExceptionHandler() throws Exception {
		mockMvc.perform(post("/api/products")
						.contentType(MediaType.APPLICATION_JSON)
						.content("""
								{
								  "productName": " ",
								  "productPrice": 0
								}
								"""))
				.andExpect(status().isBadRequest())
				.andExpect(jsonPath("$.result").value(1))
				.andExpect(jsonPath("$.code").value(400))
				.andExpect(jsonPath("$.message").value("VALIDATION_FAILED"))
				.andExpect(jsonPath("$.body.productName").exists())
				.andExpect(jsonPath("$.body.productPrice").exists());
	}

	@Test
	void openApiDocumentIsGenerated() throws Exception {
		mockMvc.perform(get("/v3/api-docs"))
				.andExpect(status().isOk())
				.andExpect(jsonPath("$.openapi").exists())
				.andExpect(jsonPath("$.info.title").value("SKALA Shop API"))
				.andExpect(jsonPath("$.paths['/api/products/list']").exists())
				.andExpect(jsonPath("$.paths['/api/products/search']").exists())
				.andExpect(jsonPath("$.paths['/api/customers/order']").exists())
				.andExpect(jsonPath("$.components.securitySchemes.cookieAuth").exists());
	}

	@Test
	void orderWithoutLoginReturnsUnauthorized() throws Exception {
		mockMvc.perform(post("/api/customers/order")
						.contentType(MediaType.APPLICATION_JSON)
						.content("""
								{
								  "productId": 1,
								  "quantity": 1
								}
								"""))
				.andExpect(status().isUnauthorized())
				.andExpect(jsonPath("$.message").value("SESSION_NOT_FOUND"));
	}

	@Test
	void customerCanJoinLoginOrderAndCancel() throws Exception {
		String customerId = "integration-customer";
		Product product = productRepository
				.findByProductName("클래식 코튼 셔츠")
				.orElseThrow();

		mockMvc.perform(post("/api/customers")
						.contentType(MediaType.APPLICATION_JSON)
						.content("""
								{
								  "customerId": "%s",
								  "customerPassword": "pw1234"
								}
								""".formatted(customerId)))
				.andExpect(status().isOk())
				.andExpect(jsonPath("$.body.customerPoint").value(1000000.0))
				.andExpect(jsonPath("$.body.customerPassword").isEmpty());

		MvcResult loginResult = mockMvc.perform(post("/api/customers/login")
						.contentType(MediaType.APPLICATION_JSON)
						.content("""
								{
								  "customerId": "%s",
								  "customerPassword": "pw1234"
								}
								""".formatted(customerId)))
				.andExpect(status().isOk())
				.andReturn();

		Cookie accessToken = loginResult.getResponse().getCookie("bff-access");
		if (accessToken == null) {
			throw new AssertionError("로그인 응답에 bff-access Cookie가 없습니다.");
		}

		mockMvc.perform(post("/api/customers/order")
						.cookie(accessToken)
						.contentType(MediaType.APPLICATION_JSON)
						.content("""
								{
								  "productId": %d,
								  "quantity": 2
								}
								""".formatted(product.getId())))
				.andExpect(status().isOk())
				.andExpect(jsonPath("$.body.customerPoint").value(882000.0));

		mockMvc.perform(get("/api/customers/{customerId}", customerId))
				.andExpect(status().isOk())
				.andExpect(jsonPath("$.body.products[0].productName")
						.value("클래식 코튼 셔츠"))
				.andExpect(jsonPath("$.body.products[0].quantity").value(2));

		mockMvc.perform(post("/api/customers/cancel")
						.cookie(accessToken)
						.contentType(MediaType.APPLICATION_JSON)
						.content("""
								{
								  "productId": %d,
								  "quantity": 1
								}
								""".formatted(product.getId())))
				.andExpect(status().isOk())
				.andExpect(jsonPath("$.body.customerPoint").value(941000.0));
	}
}
