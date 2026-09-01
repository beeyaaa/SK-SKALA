package com.example.springai.controller;

import java.util.Map;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.example.springai.rag.FullRagService;
import jakarta.servlet.http.HttpSession;

/**
 * RAG 질의응답(QuestionAnswerAdvisor) 기능을 제공하는 Controller.
 *
 * - FullRagService를 이용한 질의응답(통합 RAG 기반)
 */
@RestController
@RequestMapping("/ai/rag")
public class FullRagController {

    private final FullRagService fullRagService;

    public FullRagController(FullRagService fullRagService) {
        this.fullRagService = fullRagService;
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
    @GetMapping("/full-rag")
    public Map<String, Object> fullRagQuery(@RequestParam String question,
            HttpSession session) {
        String answer = fullRagService.answer(question, session.getId());

        return Map.of(
                "question", question,
                "conversationId", session.getId(),
                "answer", answer);
    }
}
