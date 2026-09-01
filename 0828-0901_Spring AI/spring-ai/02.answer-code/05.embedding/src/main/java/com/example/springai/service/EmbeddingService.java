package com.example.springai.service;

import java.util.List;
import java.util.Map;

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

    public String save(String text, Map<String, Object> metadata) {
        Document document = new Document(text, metadata);
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
                .similarityThreshold(0.4)
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
                save(
                        "제1조 ①대한민국은 민주공화국이다. ②대한민국의 주권은 국민에게 있고, 모든 권력은 국민으로부터 나온다.",
                        Map.of("category", "constitution", "type", "law", "article", 1)),
                save(
                        "제2조 ①대한민국의 국민이 되는 요건은 법률로 정한다.②국가는 법률이 정하는 바에 의하여 재외국민을 보호할 의무를 진다.",
                        Map.of("category", "constitution", "type", "law", "article", 2)),
                save(
                        "제3조 대한민국의 영토는 한반도와 그 부속도서로 한다.",
                        Map.of("category", "constitution", "type", "law", "article", 3)),
                save(
                        "제4조 대한민국은 통일을 지향하며, 자유민주적 기본질서에 입각한 평화적 통일정책을 수립하고 이를 추진한다.",
                        Map.of("category", "constitution", "type", "law", "article", 4)),
                save(
                        "제5조 ①대한민국은 국제평화의 유지에 노력하고 침략적 전쟁을 부인한다. ②국군은 국가의 안전보장과 국토방위의 신성한 의무를 수행함을 사명으로 하며, 그 정치적 중립성은 준수된다.",
                        Map.of("category", "constitution", "type", "law", "article", 5)));
    }
}
