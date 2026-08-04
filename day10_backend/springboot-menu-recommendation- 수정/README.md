# 오늘 뭐 먹지? Spring Boot 실습 프로젝트

초보자가 다음 내용을 학습하기 위한 예제입니다.

- Component Scan과 Bean 등록
- Spring Container
- 생성자 기반 의존성 주입(DI)
- `@RestController`
- `@GetMapping`
- `@PathVariable`
- 문자열 및 JSON 응답
- Controller와 Service 역할 분리

## 실행 환경

- JDK 21
- Gradle
- VSCode

## 실행 방법

프로젝트 폴더에서 다음 명령을 실행합니다.

```bash
gradle bootRun
```

VSCode의 Spring Boot Dashboard를 사용할 경우 `MenuApplication`을 실행해도 됩니다.

## 접속 주소

시작 화면:

```text
http://localhost:8080
```

API:

```text
GET http://localhost:8080/api/hello/홍길동
GET http://localhost:8080/api/menu
GET http://localhost:8080/api/menu/random
GET http://localhost:8080/api/menu/한식
GET http://localhost:8080/api/menu/중식
GET http://localhost:8080/api/menu/일식
GET http://localhost:8080/api/menu/json/한식
```

## 학습 포인트

`MenuService`에는 `@Service`가 붙어 있습니다. Spring은 Component Scan을 통해 이 클래스를 찾아 Bean으로 등록합니다.

`MenuController`는 `new MenuService()`를 사용하지 않습니다. Spring Container가 생성해 둔 `MenuService` Bean을 생성자를 통해 전달합니다.

```java
public MenuController(MenuService menuService) {
    this.menuService = menuService;
}
```

이 방식이 생성자 기반 의존성 주입입니다.
