package com.example.springai.agent;

import org.springframework.ai.chat.client.ChatClient;
import org.springframework.ai.chat.client.advisor.MessageChatMemoryAdvisor;
import org.springframework.ai.chat.client.advisor.SimpleLoggerAdvisor;
import org.springframework.ai.chat.memory.ChatMemory;
import org.springframework.ai.chat.model.ChatModel;
import org.springframework.stereotype.Component;

import com.example.springai.tools.DateTimeTools;
import com.example.springai.tools.FileSystemTool;

/**
 * 서버 작업 디렉토리의 파일을 관리하는 Agent.
 * 역할(시스템 프롬프트)과 이 Agent가 사용할 수 있는 Tool을 함께 정의한다.
 */
@Component
public class FileManagerAgent {

    private static final String SYSTEM_PROMPT = """
            당신은 서버의 작업 디렉토리 파일을 관리하는 '파일 관리 에이전트'입니다.
            파일 목록 조회, 파일 생성, 텍스트 파일 읽기 도구를 활용해 사용자의 요청을 해결하세요.
            도구로 확인할 수 없는 내용은 추측하지 말고, 모른다고 답하세요.
            """;

    private final ChatClient chatClient;

    public FileManagerAgent(ChatModel chatModel, ChatMemory chatMemory,
            FileSystemTool fileSystemTool, DateTimeTools dateTimeTools) {

        this.chatClient = ChatClient.builder(chatModel)
                .defaultSystem(SYSTEM_PROMPT)
                .defaultTools(fileSystemTool, dateTimeTools)
                .defaultAdvisors(MessageChatMemoryAdvisor.builder(chatMemory).build(), new SimpleLoggerAdvisor())
                .build();
    }

    public String ask(String request, String conversationId) {
        return chatClient.prompt()
                .advisors(a -> a.param(ChatMemory.CONVERSATION_ID, conversationId))
                .user(request)
                .call()
                .content();
    }
}
