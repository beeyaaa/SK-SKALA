package com.example.menu;

import com.example.menu.controller.MenuController;
import com.example.menu.service.MenuService;
import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;

class MenuPriceTests {

    private final MenuService menuService = new MenuService();
    private final MenuController menuController = new MenuController(menuService);

    @Test
    void recommendsMenuForMaximumPriceRange() {
        assertThat(menuService.recommendByPrice(0, 6000)).isEqualTo("김밥");
        assertThat(menuService.recommendByPrice(6000, 12000)).isEqualTo("잠봉뵈르");
        assertThat(menuService.recommendByPrice(12000, 30000)).isEqualTo("스시");
    }

    @Test
    void validatesInvalidPriceRanges() {
        assertThat(menuController.menuByPrice(-1, 5000))
                .isEqualTo("가격은 0원 이상이어야 합니다.");
        assertThat(menuController.menuByPrice(20000, 5000))
                .isEqualTo("최소 가격은 최대 가격보다 클 수 없습니다.");
    }
}
