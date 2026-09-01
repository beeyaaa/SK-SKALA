package com.example.springai.controller;

import org.springframework.ai.chat.client.ChatClient;
import org.springframework.ai.chat.client.advisor.MessageChatMemoryAdvisor;
import org.springframework.ai.chat.client.advisor.SimpleLoggerAdvisor;
import org.springframework.ai.chat.memory.ChatMemory;

import org.springframework.ai.chat.model.ChatModel;
import org.springframework.ai.mcp.SyncMcpToolCallbackProvider;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import jakarta.servlet.http.HttpSession;

/**
 * GET /ai?request=질문 형식으로 AI 응답을 제공하는 Controller.
 * MCP Client가 10-2.mcp-server(Streamable HTTP)에 접속해 원격으로 조회한 
 * 도구 목록(SyncMcpToolCallbackProvider)을 사용한다.
 */
@RestController
public class ChatController {

    private final ChatClient chatClient;
    private final SyncMcpToolCallbackProvider mcpToolCallbackProvider;

    // Autoconfigured ChatClient.Builder is injected
    public ChatController(ChatModel chatModel, ChatMemory chatMemory,
            SyncMcpToolCallbackProvider mcpToolCallbackProvider) {
        this.chatClient = ChatClient.builder(chatModel)
                .defaultAdvisors(MessageChatMemoryAdvisor.builder(chatMemory).build(), new SimpleLoggerAdvisor())
                .build();
        this.mcpToolCallbackProvider = mcpToolCallbackProvider;
    }

    @GetMapping("/ai")
    public String chat(@RequestParam String request, HttpSession session) {

        return this.chatClient.prompt()
                .advisors(a -> a.param(ChatMemory.CONVERSATION_ID, session.getId()))
                .user(request)
                .tools(this.mcpToolCallbackProvider)
                .call()
                .content();
    }
}
