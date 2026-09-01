package com.example.springai.service;

import java.util.List;

import org.springframework.ai.document.Document;
import org.springframework.ai.vectorstore.SearchRequest;
import org.springframework.ai.vectorstore.VectorStore;
import org.springframework.stereotype.Service;

/**
 * Vector DB의 가장 기본적인 세 가지 동작을 보여 주는 교육용 서비스.
 *
 * <pre>
 * 저장: 문장 -> 임베딩 벡터 -> Vector DB
 * 검색: 질문 -> 임베딩 벡터 -> 가까운 문서
 * 삭제: 문서 ID -> Vector DB에서 삭제
 * </pre>
 */
@Service
public class EmbeddingService {

    private final VectorStore vectorStore;

    public EmbeddingService(VectorStore vectorStore) {
        this.vectorStore = vectorStore;
    }

    /**
     * 문장을 저장하고, 나중에 삭제할 때 사용할 문서 ID를 반환한다.
     * 임베딩 생성과 DB 저장은 VectorStore가 내부에서 처리한다.
     */
    public String save(String text) {
        Document document = new Document(text);
        vectorStore.add(List.of(document));
        return document.getId();
    }

    /**
     * 질문과 의미가 가장 비슷한 문서를 최대 3개 찾는다.
     * 질문의 임베딩 생성과 벡터 비교는 VectorStore가 내부에서 처리한다.
     */
    public List<Document> search(String query) {
        SearchRequest request = SearchRequest.builder()
                .query(query)
                .topK(3)
                .build();

        return vectorStore.similaritySearch(request);
    }

    /** 문서 ID로 한 건을 삭제한다. */
    public void delete(String documentId) {
        vectorStore.delete(List.of(documentId));
    }

    /** 검색 실습에 사용할 예제 문서를 저장한다. */
    public List<String> saveSamples() {
        return List.of(
                save("대한민국은 민주공화국이다."),
                save("대한민국의 영토는 한반도와 그 부속도서로 한다."),
                save("대한민국은 국제평화의 유지에 노력한다."));
    }
}
