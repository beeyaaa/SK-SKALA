package com.example.springai.rarag;

import org.springframework.ai.chat.client.ChatClient;
import org.springframework.ai.chat.client.advisor.MessageChatMemoryAdvisor;
import org.springframework.ai.chat.client.advisor.SimpleLoggerAdvisor;
import org.springframework.ai.chat.memory.ChatMemory;
import org.springframework.ai.chat.model.ChatModel;
import org.springframework.ai.chat.prompt.PromptTemplate;
import org.springframework.ai.rag.advisor.RetrievalAugmentationAdvisor;
import org.springframework.ai.rag.preretrieval.query.transformation.CompressionQueryTransformer;
import org.springframework.ai.rag.preretrieval.query.transformation.RewriteQueryTransformer;
import org.springframework.ai.rag.retrieval.search.VectorStoreDocumentRetriever;
import org.springframework.ai.vectorstore.VectorStore;
import org.springframework.core.Ordered;
import org.springframework.stereotype.Service;

/**
 * 검색 전(Pre-Retrieval) 단계에서 대화 이력을 압축(Compression)하는 Advanced RAG 서비스입니다.
 * 처리 흐름: 대화 이력 압축(독립 질문화) → 질문 재작성(검색 최적화) → 벡터 검색 → 컨텍스트 주입 → 답변 생성
 * 여러 turn에 걸친 대화에서 후속 질문(예: "그럼 그건 언제야?")을 검색 가능한 독립 질문으로 만들 때 효과적입니다.
 */
@Service
public class CompressionQueryService {

    private static final int TOP_K = 3;
    private static final double SIMILARITY_THRESHOLD = 0.3;

    private static final String COMPRESSION_PROMPT = """
            당신은 대화 이력과 후속 질문을 바탕으로 검색에 최적화된 독립적인 질문을 생성하는 전문가입니다.

            대화 이력:
            {history}

            후속 질문:
            {query}

            위 내용을 바탕으로, 이전 대화의 문맥을 포함하여 명확하고 구체적인 하나의 독립된 질문으로 다시 작성해주세요.
            답변은 질문 내용만 포함해야 합니다.
            """;

    private final ChatClient chatClient;

    public CompressionQueryService(ChatModel chatModel, VectorStore vectorStore, ChatMemory chatMemory) {
        RetrievalAugmentationAdvisor retrievalAdvisor = RetrievalAugmentationAdvisor.builder()
                // 1~2단계: 대화 문맥을 독립 질문으로 압축한 뒤 검색에 적합하게 재작성
                .queryTransformers(
                        CompressionQueryTransformer.builder()
                                .chatClientBuilder(ChatClient.builder(chatModel)
                                        .defaultAdvisors(new SimpleLoggerAdvisor()))
                                .promptTemplate(new PromptTemplate(COMPRESSION_PROMPT))
                                .build(),
                        RewriteQueryTransformer.builder()
                                .chatClientBuilder(ChatClient.builder(chatModel)
                                        .defaultAdvisors(new SimpleLoggerAdvisor()))
                                .build()
                )
                // 3단계: 변환된 질문으로 벡터 저장소에서 관련 문서 검색
                .documentRetriever(VectorStoreDocumentRetriever.builder()
                        .topK(TOP_K)
                        .similarityThreshold(SIMILARITY_THRESHOLD)
                        .vectorStore(vectorStore)
                        .build())
                .build();

        this.chatClient = ChatClient.builder(chatModel)
                // 4단계: 대화 이력과 검색 문서를 적용해 답변 생성
                .defaultAdvisors(
                        MessageChatMemoryAdvisor.builder(chatMemory).build(),
                        retrievalAdvisor,
                        new SimpleLoggerAdvisor(Ordered.LOWEST_PRECEDENCE - 1))
                .build();
    }

    /**
     * 질문에 대한 답변을 생성합니다. (대화 이력 압축 → 질문 재작성 → 검색 → 답변 생성)
     *
     * @param question 사용자 질문
     * @param conversationId 대화 ID (세션 ID 등)
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
