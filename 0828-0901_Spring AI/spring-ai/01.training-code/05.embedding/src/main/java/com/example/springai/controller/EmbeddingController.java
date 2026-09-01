package com.example.springai.controller;

import java.util.List;
import java.util.Map;

import org.springframework.ai.document.Document;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.example.springai.service.EmbeddingService;

import jakarta.annotation.PostConstruct;

/** Vector DB의 저장, 검색, 삭제 API를 제공한다. */
@RestController
@RequestMapping("/ai")
public class EmbeddingController {

    private final EmbeddingService embeddingService;

    public EmbeddingController(EmbeddingService embeddingService) {
        this.embeddingService = embeddingService;
    }

    /** Controller Bean이 생성되면 검색 실습용 문서를 Vector DB에 저장한다. */
    @PostConstruct
    void saveSamples() {
        embeddingService.saveSamples();
    }

    /** 문장을 임베딩 벡터로 변환하여 Vector DB에 저장한다. */
    @PostMapping("/embedding/save")
    public Map<String, String> save(@RequestParam String text) {
        String documentId = embeddingService.save(text.trim());

        return Map.of(
                "id", documentId,
                "text", text.trim());
    }

    /** 질문과 의미가 가장 가까운 문서를 검색한다. */
    @GetMapping("/embedding/search")
    public List<Document> search(@RequestParam String query) {
        return embeddingService.search(query.trim());
    }

    /** 저장할 때 반환된 문서 ID로 데이터를 삭제한다. */
    @DeleteMapping("/embedding/delete/{documentId}")
    public ResponseEntity<Void> delete(@PathVariable String documentId) {
        embeddingService.delete(documentId);
        return ResponseEntity.noContent().build();
    }
}
