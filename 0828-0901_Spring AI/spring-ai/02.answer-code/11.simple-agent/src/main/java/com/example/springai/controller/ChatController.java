package com.example.springai.controller;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.example.springai.agent.FileManagerAgent;
import com.example.springai.agent.WeatherGuideAgent;

import jakarta.servlet.http.HttpSession;

/**
 * GET /ai?agent=file|weather&request=질문 형식으로 선택된 Agent의 응답을 제공하는 Controller.
 */
@RestController
public class ChatController {

    private final FileManagerAgent fileManagerAgent;
    private final WeatherGuideAgent weatherGuideAgent;

    public ChatController(FileManagerAgent fileManagerAgent, WeatherGuideAgent weatherGuideAgent) {
        this.fileManagerAgent = fileManagerAgent;
        this.weatherGuideAgent = weatherGuideAgent;
    }

    @GetMapping("/ai")
    public String chat(
            @RequestParam String request,
            @RequestParam(defaultValue = "file") String agent,
            HttpSession session) {

        String conversationId = session.getId();

        return switch (agent) {
            case "weather" -> weatherGuideAgent.ask(request, conversationId);
            default -> fileManagerAgent.ask(request, conversationId);
        };
    }
}
