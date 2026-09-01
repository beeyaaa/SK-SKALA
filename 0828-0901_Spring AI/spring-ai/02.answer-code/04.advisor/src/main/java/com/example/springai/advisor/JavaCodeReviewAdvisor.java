package com.example.springai.advisor;

import org.springframework.ai.chat.client.ChatClientRequest;
import org.springframework.ai.chat.client.ChatClientResponse;
import org.springframework.ai.chat.client.advisor.api.CallAdvisor;
import org.springframework.ai.chat.client.advisor.api.CallAdvisorChain;

public class JavaCodeReviewAdvisor implements CallAdvisor {

    @Override
    public String getName() {
        return "JavaCodeReviewAdvisor";
    }

    @Override
    public int getOrder() {
        return 0;
    }

    @Override
    public ChatClientResponse adviseCall(
            ChatClientRequest request,
            CallAdvisorChain chain) {

        // 1. 사용자가 입력한 Prompt 확인
        String userText =
                request.prompt()
                       .getUserMessage()
                       .getText();

        // 2. Agent 역할 및 업무 규칙 추가
        String agentPrompt = """
            당신은 Java/Spring 코드 리뷰 전문 Agent입니다.

            다음 규칙을 따르세요.
            1. 코드의 문제점을 찾습니다.
            2. 문제의 원인을 설명합니다.
            3. 개선 방법을 제시합니다.
            4. 가능하면 개선된 코드를 제공합니다.

            [사용자 요청]
            %s
            """.formatted(userText);

        // 3. 기존 ChatClientRequest를 기반으로
        //    새로운 Prompt를 가진 Request 생성
        ChatClientRequest newRequest =
                request.mutate()
                       .prompt(
                           request.prompt()
                                  .augmentUserMessage(agentPrompt)
                       )
                       .build();

        // 4. 다음 Advisor 또는 ChatModel 호출
        return chain.nextCall(newRequest);
    }
}
