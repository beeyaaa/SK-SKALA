package com.example.springai.rarag;

import org.springframework.ai.chat.client.ChatClient;
import org.springframework.ai.chat.client.advisor.SimpleLoggerAdvisor;
import org.springframework.ai.chat.model.ChatModel;
import org.springframework.ai.rag.advisor.RetrievalAugmentationAdvisor;
import org.springframework.ai.rag.preretrieval.query.transformation.RewriteQueryTransformer;
import org.springframework.ai.rag.retrieval.search.VectorStoreDocumentRetriever;
import org.springframework.ai.vectorstore.VectorStore;
import org.springframework.stereotype.Service;

/**
 * 검색 전(Pre-Retrieval) 단계에서 쿼리를 재작성(Rewrite)하는 Advanced RAG 서비스입니다.
 * 처리 흐름: 질문 재작성 → 벡터 검색 → 컨텍스트 주입 → 답변 생성
 */
@Service
public class RewriteQueryService {

    private static final int TOP_K = 5;
    private static final double SIMILARITY_THRESHOLD = 0.3;

    private final ChatClient chatClient;

    public RewriteQueryService(ChatModel chatModel, VectorStore vectorStore) {
        RetrievalAugmentationAdvisor retrievalAdvisor = RetrievalAugmentationAdvisor.builder()
                // 1단계: 사용자 질문을 검색에 적합한 문장으로 재작성
                .queryTransformers(RewriteQueryTransformer.builder()
                        .chatClientBuilder(ChatClient.builder(chatModel)
                                .defaultAdvisors(new SimpleLoggerAdvisor()))
                        .build())
                // 2단계: 재작성된 질문으로 벡터 저장소에서 관련 문서 검색
                .documentRetriever(VectorStoreDocumentRetriever.builder()
                        .topK(TOP_K)
                        .similarityThreshold(SIMILARITY_THRESHOLD)
                        .vectorStore(vectorStore)
                        .build())
                .build();

        this.chatClient = ChatClient.builder(chatModel)
                // 3단계: 검색 문서를 컨텍스트로 주입해 답변 생성
                .defaultAdvisors(retrievalAdvisor, new SimpleLoggerAdvisor())
                .build();
    }

    /**
     * 질문에 대한 답변을 생성합니다. (쿼리 재작성 → 검색 → 답변 생성)
     *
     * @param question 사용자 질문
     * @return 생성된 답변
     */
    public String answer(String question) {
        return chatClient.prompt()
                .user(question)
                .call()
                .content();
    }
}
