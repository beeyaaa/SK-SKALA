package com.example.springai.rag;

import org.springframework.ai.chat.client.ChatClient;
import org.springframework.ai.chat.client.advisor.MessageChatMemoryAdvisor;
import org.springframework.ai.chat.client.advisor.SimpleLoggerAdvisor;
import org.springframework.ai.chat.memory.ChatMemory;
import org.springframework.ai.chat.model.ChatModel;
import org.springframework.ai.rag.advisor.RetrievalAugmentationAdvisor;
import org.springframework.ai.rag.preretrieval.query.expansion.MultiQueryExpander;
import org.springframework.ai.rag.preretrieval.query.transformation.CompressionQueryTransformer;
import org.springframework.ai.rag.preretrieval.query.transformation.RewriteQueryTransformer;
import org.springframework.ai.rag.retrieval.search.VectorStoreDocumentRetriever;
import org.springframework.ai.vectorstore.VectorStore;
import org.springframework.stereotype.Service;

/**
 * RetrievalAugmentationAdvisor를 이용한 Advanced RAG 초기 구성입니다.
 * 처리 흐름: Pre-Retrieval(Rewrite, Compression, MultiQuery) → Retrieval → Post-Retrieval
 */
@Service
public class RetrievalAugmentService {

    private final ChatClient chatClient;

    public RetrievalAugmentService(ChatModel chatModel, VectorStore vectorStore, ChatMemory chatMemory) {

        /**
         * ------------------------------------------------------------------
         * RetrievalAugmentationAdvisor에서 사용하기 위한 ChatClient.Builder 객체를 생성
         * 1. ChatClient.builder(chatModel) : ChatModel을 기반으로 ChatClient.Builder 객체를 생성
         * 2. .defaultAdvisors(new SimpleLoggerAdvisor()) : SimpleLoggerAdvisor를 기본 Advisor로 설정하여, ChatClient의 요청과 응답을 로깅하도록 함
         * ------------------------------------------------------------------
         */
        ChatClient.Builder transformerBuilder = ChatClient.builder(chatModel)
                .defaultAdvisors(new SimpleLoggerAdvisor());

        /**
         * ------------------------------------------------------------------
         * RetrievalAugmentationAdvisor 객체를 생성해보자
         * 1. .queryTransformers() : Pre-Retrieval 단계에서 RewriteQueryTransformer를 이용해 사용자 질문을 검색에 적합한 문장으로 재작성하는 Transformer를 설정
         * 2. .documentRetriever() : Retrieval 단계에서 재작성된 질문으로 벡터 저장소에서 관련 문서를 검색하는 DocumentRetriever를 설정
         * ------------------------------------------------------------------
         */
        RetrievalAugmentationAdvisor retrievalAdvisor = RetrievalAugmentationAdvisor.builder()
                // ** Pre-Retrieval: 사용자 질문을 검색에 적합한 문장으로 재작성 **
                .queryTransformers(
                        // 재작성된 질문을 대화 이력과 함께 압축(독립 질문화)하는 Transformer를 설정
                        CompressionQueryTransformer.builder()
                        .chatClientBuilder(transformerBuilder)
                        .build(),
                        // 사용자 질문을 검색에 적합한 문장으로 재작성하는 Transformer를 설정
                        RewriteQueryTransformer.builder()
                        .chatClientBuilder(transformerBuilder)
                        .build())
                // ** Pre-Retrieval: 사용자 질문을 여러 개의 쿼리로 확장 **
                .queryExpander(MultiQueryExpander.builder()
                        .chatClientBuilder(transformerBuilder)
                        .numberOfQueries(3)  // default=3
                        .build())
                // ** Retrieval: 재작성된 질문으로 벡터 저장소에서 관련 문서 검색 **
                .documentRetriever(VectorStoreDocumentRetriever.builder()
                        .topK(5)
                        .similarityThreshold(0.3)
                        .vectorStore(vectorStore)
                        .build())
                .build();

        /**
         * ------------------------------------------------------------------
         * ChatClient 객체를 생성해서 RetrievalAugmentationAdvisor를 .defaultAdvisors()로 설정
         * .defaultAdvisors() : RetrievalAugmentationAdvisor를 기본 Advisor로 설정하여, 사용자 질문에 대한 답변을 생성할 때 검색된 문서를 컨텍스트로 활용하도록 함
         * ------------------------------------------------------------------
         */
        this.chatClient = ChatClient.builder(chatModel)
                .defaultAdvisors(
                        MessageChatMemoryAdvisor.builder(chatMemory).build(),
                        retrievalAdvisor, 
                        new SimpleLoggerAdvisor()
                )
                .build();
    }

    /**
     * 질문에 대한 답변을 생성합니다. (쿼리 재작성 → 검색 → 답변 생성)
     *
     * @param question 사용자 질문
     * @return 생성된 답변
     */
    public String answer(String question, String conversationId) {
        return chatClient.prompt()
                .advisors(a -> a.param(ChatMemory.CONVERSATION_ID, conversationId))
                .user(question)
                .call()
                .content();
    }
}
