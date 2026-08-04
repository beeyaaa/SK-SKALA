package com.example.menu.service;

import org.springframework.stereotype.Service;

import java.util.List;
import java.util.concurrent.ThreadLocalRandom;

/**
 * 메뉴 추천 비즈니스 로직을 담당하는 Spring Bean입니다.
 *
 * @Service를 사용하면 Component Scan을 통해 Spring Container에
 * 자동으로 Bean으로 등록됩니다.
 */
@Service
public class MenuService {

    private final List<String> menus = List.of(
            "김치찌개",
            "불고기",
            "짜장면",
            "돈가스",
            "떡볶이",
            "치킨",
            "피자"
    );

    public String recommend() {
        return "김치찌개";
    }

    public String recommendByCategory(String category) {
        return switch (category) {
            case "korean" -> "불고기";
            case "chinese" -> "짜장면";
            case "japanese" -> "돈가스";
            case "snack" -> "떡볶이";
            default -> "추천 가능한 메뉴가 없습니다";
        };
    }

    public String recommendByWeather(String weather) {
        return switch (weather) {
            case "sunny" -> "샌드위치";
            case "rainy" -> "파전";
            case "hot" -> "평양냉면";
            case "cold" -> "순대국";
            default -> "추천 가능한 메뉴가 없습니다";
        };
    }

    public String recommendByMood(String mood) {
        return switch (mood) {
            case "happy" -> "텐동";
            case "sad" -> "두쫀쿠";
            case "tired" -> "타코야끼";
            case "stressed" -> "마라샹궈";
            default -> "추천 가능한 메뉴가 없습니다";
        };
    }

    public String recommendByPrice(int min, int max) {

        if (max <= 6000) {
            return "김밥";
        }
        else if(max <= 12000) {
            return "잠봉뵈르";
        }
        else {
            return "스시";
        }
    }

    public String recommendByWith(String with)
    {
        return switch (with)
        {
            case "solo" -> "포케";
            case "friend" -> "훠궈";
            case "family" -> "소고기";
            default -> "추천 가능한 메뉴가 없습니다";
        };
    }


    public String randomMenu() {
        int index = ThreadLocalRandom.current().nextInt(menus.size());
        return menus.get(index);
    }
}
