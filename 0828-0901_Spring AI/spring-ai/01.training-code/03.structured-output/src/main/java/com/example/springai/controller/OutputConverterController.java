package com.example.springai.controller;

import lombok.extern.slf4j.Slf4j;

import org.springframework.ai.chat.client.ChatClient;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@Slf4j
@RestController
// 모든 메서드의 공통 URL 앞부분이다. 아래 @GetMapping 값과 합쳐 최종 엔드포인트가 된다.
@RequestMapping("/ai")
public class OutputConverterController {

    /*
     * [컨버터 선택 방법]
     * - 사용하려는 변환 메서드 하나만 남기고 나머지 메서드를 주석 처리해도 된다.
     * - 다른 설정 파일에서 OutputConverter를 별도로 지정할 필요는 없다.
     * - 각 메서드 마지막의 entity(...)에 전달한 타입에 따라 변환 결과가 결정된다.
     *   예: entity(ActorsFilms.class)는 단일 객체,
     *       entity(new ParameterizedTypeReference<List<String>>() {})는 문자열 목록으로 변환한다.
     * - 여러 메서드를 모두 남겨도 한꺼번에 실행되지 않으며, 요청한 엔드포인트의 메서드 하나만 실행된다.
     *
     * [엔드포인트 요청 위치]
     * - 웹 화면에서는 static/js/chat.js의 fetch(...)가 선택한 엔드포인트를 호출한다.
     * - 메서드를 주석 처리하면 해당 엔드포인트는 없어지므로, 웹 화면에서 선택할 경우 404가 발생한다.
     * - 브라우저 주소창이나 Postman에서도 아래 예시 URL을 직접 요청할 수 있다.
     */

    /**
     * AI 응답을 변환할 목표 자료형이다.
     * record를 사용하면 actor와 films 필드를 가진 불변 데이터 객체를 간단히 만들 수 있다.
     */
    private static record ActorsFilms(String actor, List<String> films) {}
    private final ChatClient chatClient;

    // Spring Boot 자동 설정으로 생성된 ChatClient.Builder를 생성자 주입받는다.
    public OutputConverterController(ChatClient.Builder chatClientBuilder) {
        // Builder로 AI 요청에 사용할 ChatClient를 생성한다.
        this.chatClient = chatClientBuilder.build();
    }
    
    /**
     * BeanOutputConverter - 단일 Bean
     * GET /ai/bean
     *
     * AI의 텍스트 응답을 ActorsFilms 객체 하나로 변환한다.
     * 요청 예: http://localhost:8080/ai/bean?userInput=톰 행크스의 영화 5개를 알려줘
     */
    @GetMapping("/bean")
    public ActorsFilms getSingleActorFilms(@RequestParam String userInput) {
        return chatClient.prompt()       // 새로운 AI 프롬프트 요청을 만든다.
                .user(userInput)         // 사용자 질문을 프롬프트에 넣는다.
                .call()                  // AI 응답이 끝날 때까지 동기 방식으로 기다린다.
                .entity(ActorsFilms.class); // 응답을 ActorsFilms 타입으로 변환한다.
    }
    
    /**
     * BeanOutputConverter - Generic Bean Type (List<Bean>)
     * GET /ai/list-bean
     *
     * AI의 텍스트 응답을 ActorsFilms 객체 여러 개가 담긴 List로 변환한다.
     * 요청 예: http://localhost:8080/ai/list-bean?userInput=배우 3명과 대표 영화 3개씩 알려줘
     */
    @GetMapping("/list-bean")
    public List<ActorsFilms> getMultipleActorsFilms(@RequestParam String userInput) {
        List<ActorsFilms> actorsFilmsList = chatClient.prompt()
                .user(userInput)
                .call()
                // 제네릭 타입은 런타임에 타입 정보가 지워지므로
                // ParameterizedTypeReference로 List 내부 타입까지 전달한다.
                .entity(new ParameterizedTypeReference<List<ActorsFilms>>() {});

        // 변환된 결과를 서버 로그에서 확인한다. 문자열 연결 대신 자리표시자를 사용한다.
        log.info("List of ActorsFilms: {}", actorsFilmsList);

        return actorsFilmsList;
    }

    /**
     * MapOutputConverter
     * GET /ai/map
     *
     * 응답 구조가 고정된 Bean으로 표현하기 어려울 때 Map으로 변환한다.
     * 요청 예: http://localhost:8080/ai/map?userInput=과일 이름과 맛 5개를 알려줘
     */
    @GetMapping("/map")
    public Map<String, Object> getMapResult(@RequestParam String userInput) {
        return chatClient.prompt()
                .user(userInput)
                .call()
                // Map의 키는 String, 값은 여러 자료형이 가능하므로 Object로 지정한다.
                .entity(new ParameterizedTypeReference<Map<String, Object>>() {});
    }
    
    /**
     * ListOutputConverter
     * GET /ai/list
     *
     * AI의 응답을 단순 문자열 목록으로 변환한다.
     * 요청 예: http://localhost:8080/ai/list?userInput=아이스크림 맛 10개를 알려줘
     */
    @GetMapping("/list")
    public List<String> getListResult(@RequestParam String userInput) {
        return chatClient.prompt()
                .user(userInput)
                .call()
                // List<String>의 전체 제네릭 타입 정보를 변환기에 전달한다.
                .entity(new ParameterizedTypeReference<List<String>>() {});
    }
}
