package com.example.springai.config;

import org.springframework.ai.embedding.EmbeddingModel;
import org.springframework.ai.vectorstore.VectorStore;
import org.springframework.ai.vectorstore.pgvector.PgVectorStore;
import org.springframework.beans.factory.annotation.Qualifier;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.jdbc.core.JdbcTemplate;


/**
 * ChatMemory 전용 VectorStore Bean을 생성하는 Configuration 클래스
 * VectorStoreConfig
 */
@Configuration
public class VectorStoreConfig {
    @Bean
    @Qualifier("chatMemoryVectorStore")
    public VectorStore chatMemoryVectorStore(JdbcTemplate jdbcTemplate, EmbeddingModel embeddingModel) {
        return PgVectorStore.builder(jdbcTemplate, embeddingModel)
                .schemaName("public")
                .vectorTableName("chat_memory_vector_store")  // ChatMemory 전용 테이블
                .initializeSchema(true)
                .removeExistingVectorStoreTable(true)  // 기존 테이블을 제거
                .build();
    }
}
