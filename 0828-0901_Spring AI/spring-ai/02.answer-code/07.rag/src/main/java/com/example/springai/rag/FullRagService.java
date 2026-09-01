package com.example.springai.rag;

import org.springframework.ai.chat.client.ChatClient;
import org.springframework.ai.chat.client.advisor.MessageChatMemoryAdvisor;
import org.springframework.ai.chat.client.advisor.SimpleLoggerAdvisor;
import org.springframework.ai.chat.memory.ChatMemory;
import org.springframework.ai.chat.model.ChatModel;
import org.springframework.ai.chat.prompt.PromptTemplate;
import org.springframework.ai.document.Document;
import org.springframework.ai.rag.Query;
import org.springframework.ai.rag.advisor.RetrievalAugmentationAdvisor;
import org.springframework.ai.rag.generation.augmentation.ContextualQueryAugmenter;
import org.springframework.ai.rag.postretrieval.document.DocumentPostProcessor;
import org.springframework.ai.rag.preretrieval.query.expansion.MultiQueryExpander;
import org.springframework.ai.rag.preretrieval.query.transformation.QueryTransformer;
import org.springframework.ai.rag.preretrieval.query.transformation.RewriteQueryTransformer;
import org.springframework.ai.rag.preretrieval.query.transformation.CompressionQueryTransformer;
import org.springframework.ai.rag.retrieval.search.VectorStoreDocumentRetriever;
import org.springframework.ai.vectorstore.VectorStore;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.stream.Collectors;

/**
 * Pre-Retrieval(Rewrite, Compression, MultiQuery) → Retrieval → Post-Retrieval → Generation(증강 프롬프트) 기반 RAG 초기 구성입니다.
 * 처리 흐름: Pre-Retrieval(Rewrite, Compression, MultiQuery) → Retrieval
 */
@Service
public class FullRagService {

    private final ChatClient chatClient;
    public FullRagService(ChatModel chatModel, VectorStore vectorStore, ChatMemory chatMemory) {

        // 1. Pre-Retrieval를 위한 ChatClient Builder 생성
        ChatClient.Builder transformerBuilder = ChatClient.builder(chatModel)
                .defaultAdvisors(new SimpleLoggerAdvisor());

        // 2-1. Pre-Retrival: Rewrite Query Transformer
        QueryTransformer queryTransformer = RewriteQueryTransformer.builder()
                .chatClientBuilder(transformerBuilder)
                .build();
        
        // 2-2. Pre-Retrieval: Comppression Query Transformer
        QueryTransformer compressionTransformer = CompressionQueryTransformer.builder()
                .chatClientBuilder(transformerBuilder)
                .build();

        // 2-3. Pre-Retrieval: Query Expander
        MultiQueryExpander queryExpander = MultiQueryExpander.builder()
                .chatClientBuilder(transformerBuilder)
                .build();

        // 3. Retrieval: Document Retriever
        VectorStoreDocumentRetriever documentRetriever = VectorStoreDocumentRetriever.builder()
                .similarityThreshold(0.3)
                .vectorStore(vectorStore)
                .build();

        // 4. Post-Retrieval: Document Post-Processor
        // 현재 구현: 점수 기반 필터링만 적용
        DocumentPostProcessor documentPostProcessor = (Query query, List<Document> documents) -> {
            // 예시: 유사도 점수(Score)가 0.5 이상인 문서만 필터링
            return documents.stream()
                    .filter(doc -> doc.getScore() != null && doc.getScore() >= 0.5)
                    .collect(Collectors.toList());
        };

        // 5. Generation: 한글 프롬프트로 컨텍스트 증강
        String contextPrompt = """
                아래는 관련 컨텍스트 정보입니다.
                
                ---------------------
                {context}
                ---------------------
                
                주어진 컨텍스트 정보만을 사용하여 질문에 답변하세요.
                
                다음 규칙을 따르세요:
                
                1. 컨텍스트에 답변이 없으면 "제공된 정보에서 답변을 찾을 수 없습니다"라고 말하세요.
                2. "컨텍스트에 따르면..." 또는 "제공된 정보에 의하면..."과 같은 표현은 피하세요.
                
                질문: {query}
                
                답변:
                """;
        
        String emptyContextPrompt = """
                사용자의 질문이 제공된 지식 범위를 벗어났습니다.
                정중하게 답변할 수 없다고 안내해주세요.
                """;
        
        // 6. 검색된 문서를 LLM에 전달할 최종 프롬프트로 변환하는 Contextual Query Augmenter 설정
        ContextualQueryAugmenter queryAugmenter = ContextualQueryAugmenter.builder()
                .promptTemplate(new PromptTemplate(contextPrompt))
                .emptyContextPromptTemplate(new PromptTemplate(emptyContextPrompt))
                .allowEmptyContext(false)
                .build();

        /** 7. Retrieval Augmentation Advisor 생성
         * ------------------------------------------------------------------
         * RetrievalAugmentationAdvisor에서 사용하기 위한 ChatClient.Builder 객체를 생성
         * ------------------------------------------------------------------
         */
        RetrievalAugmentationAdvisor advisor = RetrievalAugmentationAdvisor.builder()
                .queryTransformers(queryTransformer, compressionTransformer)
                .queryExpander(queryExpander)
                .documentRetriever(documentRetriever)
                .documentPostProcessors(documentPostProcessor)
                .queryAugmenter(queryAugmenter)
                .build();

        // 8. ChatClient 생성
        this.chatClient = ChatClient.builder(chatModel)
                .defaultAdvisors(
                        MessageChatMemoryAdvisor.builder(chatMemory).build(),
                        advisor, 
                        new SimpleLoggerAdvisor()
                )
                .build();
    
    }

    /**
     * 질문에 대한 답변을 생성합니다. (검색 -> 컨텍스트 증강 -> 답변 생성)
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
