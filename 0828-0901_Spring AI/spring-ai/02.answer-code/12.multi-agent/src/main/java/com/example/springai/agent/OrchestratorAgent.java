package com.example.springai.agent;

import java.util.Map;

import org.springframework.ai.chat.client.ChatClient;
import org.springframework.ai.chat.client.advisor.MessageChatMemoryAdvisor;
import org.springframework.ai.chat.client.advisor.SimpleLoggerAdvisor;
import org.springframework.ai.chat.memory.ChatMemory;
import org.springframework.ai.chat.model.ChatModel;
import org.springframework.stereotype.Component;

/**
 * 사용자의 모든 요청을 받는 단일 진입점 Agent.
 * 스스로 답하지 않고, 요청 내용에 맞는 전문 Agent(Tool로 등록된 AgentDelegationTools)에게
 * 위임할지, 여러 전문 Agent를 함께 사용해 결과를 종합할지를 LLM Tool-calling으로 판단한다.
 */
@Component
public class OrchestratorAgent {

    private static final String SYSTEM_PROMPT = """
        당신은 사용자 요청을 분석해 적절한 전문 에이전트에게 작업을 위임하는 오케스트레이터입니다.
        직접 답을 지어내지 말고, 제공된 Tool의 설명을 참고해 적절한 Tool을 호출하세요.

        - 여러 전문 에이전트가 필요하면 필요한 순서대로 Tool을 호출하고 결과를 종합하세요.
        - 각 Tool에는 전체 요청이 아니라 해당 전문 에이전트가 처리할 부분만 전달하세요.
        - 적절한 Tool이 없으면 처리할 수 없다고 안내하세요.
            """;

    private final ChatClient chatClient;

    public OrchestratorAgent(ChatModel chatModel, ChatMemory chatMemory, AgentDelegationTools agentDelegationTools) {
        this.chatClient = ChatClient.builder(chatModel)
                .defaultSystem(SYSTEM_PROMPT)
                .defaultTools(agentDelegationTools)
                .defaultAdvisors(MessageChatMemoryAdvisor.builder(chatMemory).build(), new SimpleLoggerAdvisor())
                .build();
    }

    public String ask(String request, String conversationId) {
        return chatClient.prompt()
                .advisors(a -> a.param(ChatMemory.CONVERSATION_ID, conversationId))
                .toolContext(Map.of(AgentDelegationTools.CONVERSATION_ID_KEY, conversationId))
                .user(request)
                .call()
                .content();
    }
}
