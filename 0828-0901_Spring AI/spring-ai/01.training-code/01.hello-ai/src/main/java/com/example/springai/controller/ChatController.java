package com.example.springai.controller;

import org.springframework.ai.chat.client.ChatClient;
import org.springframework.ai.chat.prompt.ChatOptions;
import org.springframework.ai.chat.prompt.PromptTemplate;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import reactor.core.publisher.Flux;

import java.util.Map;


/**
 * 동기(call)와 비동기(stream) 방식을 모두 지원하는 ChatClient 예제 Controller.
 *
 * - GET /ai        : 동기 방식. 응답이 모두 생성된 후 한 번에 반환한다.
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

    // Spring Boot 자동 설정으로 생성된 ChatClient.Builder를 생성자 주입받는다.
    public ChatController(ChatClient.Builder chatClientBuilder) {
        // Builder를 이용해 실제 AI 호출에 사용할 ChatClient를 한 번만 생성한다.
        this.chatClient = chatClientBuilder.build();
    }

    /** ------------------------------------------------------------
     * ChatClient Fluent API를 사용하여 동기 방식으로 AI 응답을 생성한다.
     * 아래 주석 처리된 코드는 기능을 단계별로 비교하기 위한 이전 예제다.
     * ------------------------------------------------------------ */
    // @GetMapping("/ai")
    // public String chat(@RequestParam String userInput) {
    //     return chatClient.prompt()
    //             .user(userInput)
    //             .call()
    //             .content();

    // }

    // @GetMapping("/ai")
    // public String chat(@RequestParam String userInput) {

    //     ChatOptions.Builder<?> chatOptions = ChatOptions.builder()
    //             .model("gpt-4o-mini")
    //             .temperature(0.7)
    //             .topP(0.9)
    //             .maxTokens(500);

    //     return this.chatClient.prompt()
    //             .options(chatOptions)
    //             .user(userInput)
    //             .call()
    //             .content();
    // }


    // 기존 고정 System Message 방식
    // @GetMapping("/ai")
    // public String chat(@RequestParam String userInput) {
    //     ChatOptions.Builder<?> chatOptions = ChatOptions.builder()
    //             .model("gpt-4o-mini")
    //             .temperature(0.7)
    //             .topP(0.9)
    //             .maxTokens(500);
    //
    //     return this.chatClient.prompt()
    //             .options(chatOptions)
    //             .system("""
    //                     너는 SKALA Spring AI 트러블슈팅 전담 조교야.
    //                     - 수강생의 에러나 디버깅 질문을 단계별로 설명해 줘.
    //                     """)
    //             .user(userInput)
    //             .call()
    //             .content();
    // }

    // 최종 실습 코드: PromptTemplate.render()를 이용한 동적 System Message 방식
    @GetMapping("/ai")
    public String chat(@RequestParam String userInput) {
        // 요청마다 사용할 모델과 생성 옵션을 설정한다.
        ChatOptions.Builder<?> chatOptions = ChatOptions.builder()
                .model("gpt-4o-mini")
                .temperature(0.7)
                .topP(0.9)
                .maxTokens(500);

        // 템플릿의 {aiName}, {terms} 자리에 실제 값을 넣어 시스템 메시지를 완성한다.
        String systemMessage = systemPrompt.render(Map.of(
                "aiName", "스프링 동기",
                "terms", "스프링 용어"
        ));

        return this.chatClient.prompt()  // 새로운 프롬프트 요청을 만든다.
                .options(chatOptions)    // 위에서 만든 모델 옵션을 적용한다.
                .system(systemMessage)   // AI의 역할과 답변 규칙을 지정한다.
                .user(userInput)         // 쿼리 파라미터로 받은 사용자 질문을 전달한다.
                .call()                  // 동기 방식으로 AI 응답 완료까지 기다린다.
                .content();              // 응답 객체에서 답변 문자열만 꺼낸다.
    }

    /** ------------------------------------------------------------
     * ChatClient Fluent API를 사용하여 비동기(스트리밍) 방식으로 AI 응답을 생성한다.
     * 아래 주석 처리된 코드는 시스템 메시지가 없는 기본 스트리밍 예제다.
     * ------------------------------------------------------------ */
    // 기존 System Message 없이 스트리밍하는 방식
    // @GetMapping(value = "/ai/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    // public Flux<String> chatStream(@RequestParam String userInput) {
    //     return this.chatClient.prompt()
    //             .user(userInput)
    //             .stream()
    //             .content();
    // }

    // 최종 실습 코드: ChatClient 내장 바인딩을 이용한 동적 System Message 방식
    @GetMapping(value = "/ai/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public Flux<String> chatStream(@RequestParam String userInput) {
        return this.chatClient.prompt()  // 새로운 프롬프트 요청을 만든다.
                .system(s -> s.text(PROMPT_TEMPLATE)
                        // PromptTemplate을 별도로 render하지 않고 요청 안에서 값을 바인딩한다.
                        .param("aiName", "스프링 스트리밍")
                        .param("terms", "클라우드 용어"))
                .user(userInput)         // 사용자의 질문을 전달한다.
                .stream()                // 답변을 한 번에 기다리지 않고 조각 단위로 받는다.
                .content();              // Flux<String> 형태의 텍스트 조각을 반환한다.
    }
}
