package com.example.springai.controller;

import org.springframework.ai.chat.client.ChatClient;
import org.springframework.ai.chat.messages.SystemMessage;
import org.springframework.ai.chat.prompt.ChatOptions;
import org.springframework.http.MediaType;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import reactor.core.publisher.Flux;

/**
 * 동기(call)와 비동기(stream) 방식을 모두 지원하는 ChatClient 예제 Controller.
 *
 * - GET /ai        : 동기 방식. 응답이 모두 생성된 후 한번에 반환한다.
 * - GET /ai/stream : 비동기(스트리밍) 방식. 토큰이 생성되는 대로 순차적으로 반환한다.
 */
@RestController
public class ChatController {

    private final ChatClient chatClient;

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

        // The Fluent API in Action (동기 방식)
        return this.chatClient.prompt()
                .options(chatOptions)
                .user(userInput)
                .call()
                .content();
    }

    @GetMapping(value = "/ai/stream", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    public Flux<String> chatStream(@RequestParam String userInput) {

        // The Fluent API in Action (비동기/스트리밍 방식)
        // ChatClientRequestSpec.system()은 String/Resource/Consumer만 받으므로
        // 이미 만들어진 SystemMessage 객체는 messages()로 등록한다.
        return this.chatClient.prompt()
                .user(userInput)
                .stream()
                .content();
    }
}
