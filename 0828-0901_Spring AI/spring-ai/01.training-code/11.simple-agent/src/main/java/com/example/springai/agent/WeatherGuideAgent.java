package com.example.springai.agent;

import org.springframework.ai.chat.client.ChatClient;
import org.springframework.ai.chat.client.advisor.MessageChatMemoryAdvisor;
import org.springframework.ai.chat.client.advisor.SimpleLoggerAdvisor;
import org.springframework.ai.chat.memory.ChatMemory;
import org.springframework.ai.chat.model.ChatModel;
import org.springframework.stereotype.Component;

import com.example.springai.tools.DateTimeTools;
import com.example.springai.tools.WeatherTools;

/**
 * 도시별 날씨 정보를 안내하는 Agent.
 * 역할(시스템 프롬프트)과 이 Agent가 사용할 수 있는 Tool을 함께 정의한다.
 */
@Component
public class WeatherGuideAgent {

    private static final String SYSTEM_PROMPT = """
            당신은 도시별 날씨 정보를 안내하는 '날씨 안내 에이전트'입니다.
            날씨 조회 도구를 사용해 사용자가 묻는 도시의 현재 날씨를 확인하고,
            기온과 체감 날씨를 이해하기 쉽게 안내하세요.
            도구로 확인할 수 없는 내용은 추측하지 말고, 모른다고 답하세요.
            """;

    private final ChatClient chatClient;

    public WeatherGuideAgent(ChatModel chatModel, ChatMemory chatMemory,
            WeatherTools weatherTools, DateTimeTools dateTimeTools) {

        this.chatClient = ChatClient.builder(chatModel)
                .defaultSystem(SYSTEM_PROMPT)
                .defaultTools(weatherTools, dateTimeTools)
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
