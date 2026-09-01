package com.example.springai.controller;

import lombok.extern.slf4j.Slf4j;

import org.springframework.ai.chat.client.ChatClient;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

@Slf4j
@RestController
@RequestMapping("/ai")
public class OutputConverterController {

    private static record ActorsFilms (String actor, List<String> films) {}
    private final ChatClient chatClient;

    // Autoconfigured ChatClient.Builder is injected
    public OutputConverterController(ChatClient.Builder chatClientBuilder) {
        this.chatClient = chatClientBuilder.build();
    }
    
    /**
     * BeanOutputConverter - 단일 Bean
     * GET /ai/bean
     */
    @GetMapping("/bean")
    public ActorsFilms getSingleActorFilms(@RequestParam String userInput) {
        return chatClient.prompt()
                .user(userInput)
                .call()
                .entity(ActorsFilms.class);
    }
    
    /**
     * BeanOutputConverter - Generic Bean Type (List<Bean>)
     * GET /ai/list-bean
     */
    @GetMapping("/list-bean")
    public List<ActorsFilms> getMultipleActorsFilms(@RequestParam String userInput) {
        List<ActorsFilms> actorsFilmsList = chatClient.prompt()
                .user(userInput)
                .call()
                .entity(new ParameterizedTypeReference<List<ActorsFilms>>() {});

        log.info("List of ActorsFilms: {}", actorsFilmsList.toString());
        
        return actorsFilmsList;
    }
    
    /**
     * MapOutputConverter
     * GET /ai/map
     */
    @GetMapping("/map")
    public Map<String, Object> getMapResult(@RequestParam String userInput) {
         return chatClient.prompt()
                .user(userInput)
                .call()
                .entity(new ParameterizedTypeReference<Map<String, Object>>() {});       
    }
    
    /**
     * ListOutputConverter
     * GET /ai/list
     */
    @GetMapping("/list")
    public List<String> getListResult(@RequestParam String userInput) {
        return chatClient.prompt()
                .user(userInput)
                .call()
                .entity(new ParameterizedTypeReference<List<String>>() {});
    }
}
