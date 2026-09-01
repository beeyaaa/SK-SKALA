package com.example.springai.rag;

import org.springframework.ai.chat.client.ChatClient;
import org.springframework.ai.chat.client.advisor.SimpleLoggerAdvisor;
import org.springframework.ai.chat.client.advisor.vectorstore.QuestionAnswerAdvisor;
import org.springframework.ai.chat.model.ChatModel;
import org.springframework.ai.vectorstore.SearchRequest;
import org.springframework.ai.vectorstore.VectorStore;
import org.springframework.stereotype.Service;

/**
 * QuestionAnswerAdvisor를 사용하는 간단한 RAG 서비스입니다.
 * QuestionAnswerAdvisor는 검색과 컨텍스트 주입을 자동으로 처리하는 고수준 Advisor입니다.
 */
@Service
public class QuestionAnswerService {

    private final ChatClient chatClient;

    /**
     * QuestionAnswerService 생성자.
     * QuestionAnswerAdvisor를 기본 Advisor로 설정하여 ChatClient를 생성합니다.
     *
     * @param chatModel ChatModel
     * @param vectorStore 벡터 저장소
     */
    public QuestionAnswerService(ChatModel chatModel, VectorStore vectorStore) {
        this.chatClient = ChatClient.builder(chatModel)
                .defaultAdvisors(QuestionAnswerAdvisor.builder(vectorStore)
                        .searchRequest(
                            SearchRequest.builder()
                                        .topK(5)  // default is 4 (청크가 세분화되며 정답 청크가 3위 밖으로 밀려나 topK를 늘림)
                                        .similarityThreshold(0.3)  // default is 0.0
                                        .build()
                        )
                        .build())
                .defaultAdvisors(new SimpleLoggerAdvisor()) // 로깅 Advisor 추가
                .build();
    }

    /**
     * 질문에 대한 답변을 생성합니다.
     *
     * @param question 사용자 질문
     * @return 생성된 답변
     */
    public String answerQuestion(String question) {
        return chatClient.prompt()
                .user(question)
                .call()
                .content();
    }
}
