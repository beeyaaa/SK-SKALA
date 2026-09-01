package com.example.springai.controller;

import java.util.Map;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.example.springai.chatmemory.MessageChatMemoryService;
import com.example.springai.chatmemory.MessageWindowChatMemoryService;
import com.example.springai.chatmemory.VectorStoreChatMemoryService;
import com.example.springai.config.VectorStoreConfig;
import com.example.springai.rag.QuestionAnswerService;
import com.example.springai.rag.RetrievalAugmentService;
import jakarta.servlet.http.HttpSession;

/**
 * RAG 질의응답(QuestionAnswerAdvisor) 기능을 제공하는 Controller.
 *
 * - QuestionAnswerService를 이용한 질의응답
 * - RewriteQueryService를 이용한 질의응답(질문 재작성 기반)
 * - CompressionQueryService를 이용한 질의응답(대화 이력 압축 기반)
 */
@RestController
@RequestMapping("/ai/chat-memory")
public class ChatMemoryController {

    //private final MessageChatMemoryService messageChatMemoryService;
    private final MessageWindowChatMemoryService messageChatMemoryService;
    private final VectorStoreChatMemoryService vectorStoreChatMemoryService;

    public ChatMemoryController(MessageWindowChatMemoryService messageChatMemoryService,
                                VectorStoreChatMemoryService vectorStoreChatMemoryService) {
        this.messageChatMemoryService = messageChatMemoryService;
        this.vectorStoreChatMemoryService = vectorStoreChatMemoryService;
    }


    /**
     * -------------------------------------------------------------------
     * MessageChatMemoryAdvisor 기반 ChatMemory 답변을 반환한다.
     * -------------------------------------------------------------------
     */
    @GetMapping("/in-memory")
    public Map<String, Object> messageChatMemory(@RequestParam String question, HttpSession session) {
        String answer = messageChatMemoryService.chat(question, session.getId());

        return Map.of(
                "question", question,
                "conversationId", session.getId(),
                "answer", answer);
    }

    /**
     * -------------------------------------------------------------------
     * VectorStoreChatMemoryAdvisor 기반 ChatMemory 답변을 반환한다.
     * -------------------------------------------------------------------
     */
    @GetMapping("/vector-store")
    public Map<String, Object> vectorStoreChatMemory(@RequestParam String question, HttpSession session) {
        String answer = vectorStoreChatMemoryService.chat(question, session.getId());

        return Map.of(
                "question", question,
                "conversationId", session.getId(),
                "answer", answer);
    }

}
