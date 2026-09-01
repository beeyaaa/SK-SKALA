package com.example.springai.controller;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.example.springai.agent.OrchestratorAgent;

import jakarta.servlet.http.HttpSession;

/**
 * GET /ai?request=질문 형식으로 요청을 받아 Orchestrator에게 위임하는 Controller.
 * 어떤 전문 Agent를 사용할지는 Orchestrator가 Tool-calling으로 판단한다.
 */
@RestController
public class ChatController {

    private final OrchestratorAgent orchestratorAgent;

    public ChatController(OrchestratorAgent orchestratorAgent) {
        this.orchestratorAgent = orchestratorAgent;
    }

    @GetMapping("/ai")
    public String chat(@RequestParam String request, HttpSession session) {
        return orchestratorAgent.ask(request, session.getId());
    }
}
