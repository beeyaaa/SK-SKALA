package com.example.springai.agent;

import org.springframework.ai.chat.model.ToolContext;
import org.springframework.ai.tool.annotation.Tool;
import org.springframework.ai.tool.annotation.ToolParam;
import org.springframework.stereotype.Component;

/**
 * 전문 Agent(FileManagerAgent, WeatherGuideAgent)를 Orchestrator가 호출할 수 있는
 * Tool 형태로 감싼다. Multi-Agent에서는 "Agent가 곧 다른 Agent의 Tool"이 된다.
 */
@Component
public class AgentDelegationTools {

    static final String CONVERSATION_ID_KEY = "conversationId";

    private final FileManagerAgent fileManagerAgent;
    private final WeatherGuideAgent weatherGuideAgent;

    public AgentDelegationTools(FileManagerAgent fileManagerAgent, WeatherGuideAgent weatherGuideAgent) {
        this.fileManagerAgent = fileManagerAgent;
        this.weatherGuideAgent = weatherGuideAgent;
    }

    @Tool(description = "파일 목록 조회, 파일 생성, 텍스트 파일 읽기 등 파일 관련 작업이 필요할 때 파일 관리 에이전트에게 위임합니다.")
    public String delegateToFileManager(
            @ToolParam(description = "파일 관리 에이전트에게 전달할 요청 내용") String request,
            ToolContext toolContext) {

        return fileManagerAgent.ask(request, conversationId(toolContext));
    }

    @Tool(description = "도시의 현재 날씨 정보가 필요할 때 날씨 안내 에이전트에게 위임합니다.")
    public String delegateToWeatherGuide(
            @ToolParam(description = "날씨 안내 에이전트에게 전달할 요청 내용") String request,
            ToolContext toolContext) {

        return weatherGuideAgent.ask(request, conversationId(toolContext));
    }

    private String conversationId(ToolContext toolContext) {
        return (String) toolContext.getContext().get(CONVERSATION_ID_KEY);
    }
}
