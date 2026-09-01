package com.example.springai.controller;

import org.springframework.ai.chat.client.ChatClient;
import org.springframework.ai.chat.client.advisor.MessageChatMemoryAdvisor;
import org.springframework.ai.chat.client.advisor.SimpleLoggerAdvisor;
import org.springframework.ai.chat.memory.ChatMemory;

import org.springframework.ai.chat.model.ChatModel;
import org.springframework.ai.tool.ToolCallbackProvider;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import jakarta.servlet.http.HttpSession;

/**
 * -------------------------------------------------------------------------
 * Spring AI ChatController
 * GET /ai?request=질문 형식으로 AI 응답을 제공하는 Controller.
 * 원격에 있는 MCP Server Tool 목록을 검색하기 위해 SyncMcpToolCallbackProvider(ToolCallbackProvider)를 사용한다.
 * -------------------------------------------------------------------------
 */
@RestController
public class ChatController {

    private final ChatClient chatClient;

    // Autoconfigured ChatClient.Builder is injected
    public ChatController(ChatModel chatModel, ChatMemory chatMemory) {
        this.chatClient = ChatClient.builder(chatModel)
                .defaultAdvisors(MessageChatMemoryAdvisor.builder(chatMemory).build(), new SimpleLoggerAdvisor())
                .build();
    }

    @GetMapping("/ai")
    public String chat(@RequestParam String request, HttpSession session) {

        return this.chatClient.prompt()
                .advisors(a -> a.param(ChatMemory.CONVERSATION_ID, session.getId()))
                .user(request)
                .call()
                .content();
    }
}
