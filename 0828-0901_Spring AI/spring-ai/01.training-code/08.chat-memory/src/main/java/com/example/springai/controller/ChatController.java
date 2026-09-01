package com.example.springai.controller;

import com.example.springai.advisor.AdvisorA;
import com.example.springai.advisor.AdvisorB;
import com.example.springai.advisor.AdvisorC;
import java.util.List;
import org.springframework.ai.chat.client.ChatClient;
import org.springframework.ai.chat.client.advisor.SafeGuardAdvisor;
import org.springframework.ai.chat.client.advisor.SimpleLoggerAdvisor;
import org.springframework.ai.chat.prompt.ChatOptions;
import org.springframework.ai.chat.prompt.PromptTemplate;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.core.Ordered;
import reactor.core.publisher.Flux;

import java.util.Map;

/**
 * 동기(call)와 비동기(stream) 방식을 모두 지원하는 ChatClient 예제 Controller.
 *
 * - GET /ai        : 동기 방식. 응답이 모두 생성된 후 한번에 반환한다.
 * - GET /ai/stream : 비동기(스트리밍) 방식. 토큰이 생성되는 대로 순차적으로 반환한다.
 */
@RestController
public class ChatController {

    private static final String PROMPT_TEMPLATE = """
            너는 SKALA Spring AI 교육 과정의 친절하고 열정적인 보조교사 {aiName}입니다.
                - 수강생의 질문에 따뜻하고 격려하는 어조로 답변해 주세요.
                - {terms}는 초보자도 이해하기 쉽게 비유를 들어서 설명해 주세요.
                - 답변 끝에는 항상 실습을 응원하는 따뜻한 한 마디를 덧붙여 주세요.
            """;
    private final PromptTemplate systemPrompt = new PromptTemplate(PROMPT_TEMPLATE);

    private final ChatClient chatClient;

    private final SafeGuardAdvisor safeGuardAdvisor = new SafeGuardAdvisor(
                List.of("욕설", "계좌번호", "폭력", "폭탄", "외설", "소개"),
                "해당 질문은 민감한 콘텐츠 요청이므로 응답할 수 없습니다.",
                Ordered.HIGHEST_PRECEDENCE
            );

    // Autoconfigured ChatClient.Builder is injected
    public ChatController(ChatClient.Builder chatClientBuilder) {
        this.chatClient = chatClientBuilder.build();
    }

    @GetMapping("/ai")
    public String chat(@RequestParam String userInput) {
        // 2번 ChatOptions 적용 실습
        ChatOptions.Builder<?> chatOptions = ChatOptions.builder()
            .model("gpt-4o-mini")
            .temperature(0.7)
            .topP(0.9)
            .maxTokens(500);

        String systemMessage = systemPrompt.render(Map.of(
                "aiName", "스프링동기",
                "terms", "스프링 용어"
        ));

        // The Fluent API in Action (동기 방식)
        return this.chatClient.prompt()
                .options(chatOptions)
                .system(systemMessage)
                .user(userInput)
                .advisors(new AdvisorA(), new AdvisorB(), new AdvisorC())
                .advisors(new SimpleLoggerAdvisor(Ordered.LOWEST_PRECEDENCE))
                .advisors(safeGuardAdvisor)
                .call()
                .content();
    }

    @GetMapping(value = "/ai/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public Flux<String> chatStream(@RequestParam String userInput) {

        return this.chatClient.prompt()
                .system(u -> u.text(PROMPT_TEMPLATE)
                        .param("aiName", "스프링스트리밍")
                        .param("terms", "클라우드 용어"))
                .user(userInput)
                .advisors(new SimpleLoggerAdvisor(Ordered.LOWEST_PRECEDENCE))
                .stream()
                .content();
    }
}
