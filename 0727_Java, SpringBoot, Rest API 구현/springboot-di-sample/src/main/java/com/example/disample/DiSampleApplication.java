package com.example.disample;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/*
 * @SpringBootApplication은 다음 세 가지 핵심 기능을 포함한다.
 *
 * 1. @Configuration
 *    - 이 클래스가 Spring 설정 클래스임을 의미한다.
 *
 * 2. @EnableAutoConfiguration
 *    - 클래스패스의 라이브러리를 분석해 필요한 설정을 자동으로 구성한다.
 *
 * 3. @ComponentScan
 *    - 현재 패키지(com.example.disample)와 하위 패키지에서
 *      @RestController, @Service, @Component 등을 탐색해 Bean으로 등록한다.
 *
 * 이 클래스가 controller, service, repository보다 상위 패키지에 있어야
 * 기본 컴포넌트 스캔이 정상적으로 동작한다.
 */
@SpringBootApplication
public class DiSampleApplication {

    public static void main(String[] args) {
        /*
         * SpringApplication.run()이 실행되면 Spring Container가 생성된다.
         *
         * 주요 처리 순서:
         * 1. 설정과 컴포넌트 탐색
         * 2. Repository 프록시 Bean 생성
         * 3. Service Bean 생성 및 Repository 주입
         * 4. Controller Bean 생성 및 Service 주입
         * 5. 내장 웹 서버 실행
         */
        SpringApplication.run(DiSampleApplication.class, args);
    }
}
