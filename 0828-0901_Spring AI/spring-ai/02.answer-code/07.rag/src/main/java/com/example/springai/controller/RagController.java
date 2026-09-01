package com.example.springai.controller;

import java.util.Map;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

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
@RequestMapping("/ai/rag")
public class RagController {

    private final QuestionAnswerService questionAnswerService;
    private final RetrievalAugmentService retrievalAugmentService;

    public RagController(QuestionAnswerService questionAnswerService,
            RetrievalAugmentService retrievalAugmentService) {
        this.questionAnswerService = questionAnswerService;
        this.retrievalAugmentService = retrievalAugmentService;
    }

    /**
     * 질문을 입력받아 QuestionAnswerAdvisor 기반 RAG 답변을 반환한다.
     * GET /ai/rag/qa?question=대한민국의 주권은 누구에게 있는가?
     */
    @GetMapping("/simple")
    public Map<String, Object> questionAnswer(@RequestParam String question) {
        String answer = questionAnswerService.answerQuestion(question);

        return Map.of(
                "question", question,
                "answer", answer);
    }


    /**
     * -------------------------------------------------------------------
     * RetrievalAugmentationAdvisor 기반 RAG 답변을 반환한다.
     * -------------------------------------------------------------------
     */

    /**
     * 질문을 입력받아 RetrievalAugmentationAdvisor 기반 RAG 답변을 반환한다.
     * GET /ai/rag/advanced?question=대한민국의 주권은 누구에게 있는가?
     * @param question 사용자 질문
     * @param session HttpSession 객체
     * @return Map<String, Object> 질문, 대화 ID, 답변을 포함한 Map 객체
     */
    @GetMapping("/advanced")
    public Map<String, Object> advancedQuery(@RequestParam String question,
            HttpSession session) {
        String answer = retrievalAugmentService.answer(question, session.getId());

        return Map.of(
                "question", question,
                "conversationId", session.getId(),
                "answer", answer);
    }
}
