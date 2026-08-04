package com.example.menu.controller;

import com.example.menu.dto.MenuResponse;
import com.example.menu.service.MenuService;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.bind.annotation.RequestParam;

/**
 * 브라우저의 HTTP 요청을 받아 메뉴 추천 결과를 반환한다.
 */
@RestController
@RequestMapping("/api")
public class MenuController {

    private final MenuService menuService;

    /**
     * Spring Container가 MenuService Bean을 생성자에 주입합니다.
     */
    public MenuController(MenuService menuService) {
        this.menuService = menuService;
    }

    @GetMapping("/hello/{name}")
    public String hello(@PathVariable("name") String name) {
        return name + "님, 오늘도 맛있는 하루 보내세요!";
    }

    @GetMapping("/menu")
    public String menu() {
        return "오늘의 추천 메뉴는 " + menuService.recommend() + "입니다.";
    }

    @GetMapping("/menu/random")
    public String randomMenu() {
        return "오늘은 " + menuService.randomMenu() + " 어떠세요?";
    }

    @GetMapping("/menu/{category}")
    public String menuByCategory(@PathVariable("category") String category) {
        String menu = menuService.recommendByCategory(category);
        return category + " 추천 메뉴는 " + menu + "입니다.";
    }

    @GetMapping("/menu/weather/{weather}")
    public String menuByWeather(@PathVariable("weather") String weather) {
        String menu = menuService.recommendByWeather(weather);

        if ("추천 가능한 메뉴가 없습니다".equals(menu)) {
            return "추천 가능한 메뉴가 없습니다.";
        }

        return weather + " 추천 메뉴는 " + menu + "입니다.";
    }

    @GetMapping("/menu/my/{with}")
    public String menuByWith(@PathVariable("with") String with)
    {
        String menu = menuService.recommendByWith(with);

        if ("추천 가능한 메뉴가 없습니다".equals(menu)) {
            return "추천 가능한 메뉴가 없습니다.";
        }

        return with + " 추천 메뉴는 " + menu + "입니다.";
    }

    @GetMapping("/menu/json/{category}")
    public MenuResponse menuJson(@PathVariable("category") String category) {
        String menu = menuService.recommendByCategory(category);

        return new MenuResponse(
                category,
                menu,
                "오늘은 " + menu + " 어떠세요?"
        );
    }

    @GetMapping("/menu/mood/{mood}")
    public MenuResponse menuByMood(@PathVariable("mood") String mood) {
        String menu = menuService.recommendByMood(mood);

        if ("추천 가능한 메뉴가 없습니다".equals(menu)) {
        return new MenuResponse(
                mood,
                null,
                "추천 가능한 메뉴가 없습니다."
        );
    }

        return new MenuResponse(
                mood,
                menu,
                "오늘 기분에는 " + menu + " 어떠세요?"
        );
    }

    

    @GetMapping("/menu/price/search")
    public String menuByPrice(
            @RequestParam("min") int min,
            @RequestParam("max") int max
    ) {
        if (min < 0 || max < 0) {
            return "가격은 0원 이상이어야 합니다.";
        }

        if (min > max) {
            return "최소 가격은 최대 가격보다 클 수 없습니다.";
        }

        String menu = menuService.recommendByPrice(min, max);

        return min + "원부터 " + max + "원 사이의 추천 메뉴는 " + menu + "입니다.";
    }

    
}
