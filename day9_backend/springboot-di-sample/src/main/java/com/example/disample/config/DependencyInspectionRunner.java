package com.example.disample.config;

import com.example.disample.controller.MemberController;
import com.example.disample.repository.MemberRepository;
import com.example.disample.service.MemberService;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.context.ApplicationContext;
import org.springframework.stereotype.Component;

/*
 * 애플리케이션 초기화가 끝난 후 Spring Container에 등록된
 * Controller, Service, Repository Bean의 실제 클래스명을 확인한다.
 *
 * 이 클래스는 학습과 DI 확인을 위한 보조 코드다.
 */
@Component
public class DependencyInspectionRunner implements ApplicationRunner {

    private static final Logger log =
            LoggerFactory.getLogger(DependencyInspectionRunner.class);

    /*
     * ApplicationContext는 Spring Container를 나타낸다.
     * 이 객체도 생성자 주입으로 전달받는다.
     */
    private final ApplicationContext applicationContext;

    public DependencyInspectionRunner(
            ApplicationContext applicationContext
    ) {
        this.applicationContext = applicationContext;
    }

    /*
     * ApplicationRunner의 run()은 애플리케이션 준비가 끝난 후 호출된다.
     */
    @Override
    public void run(ApplicationArguments args) {
        MemberController controller =
                applicationContext.getBean(MemberController.class);

        MemberService service =
                applicationContext.getBean(MemberService.class);

        MemberRepository repository =
                applicationContext.getBean(MemberRepository.class);

        log.info("==================================================");
        log.info("[Spring Bean 및 의존성 주입 확인]");
        log.info("Controller Bean : {}", controller.getClass().getName());
        log.info("Service Bean    : {}", service.getClass().getName());
        log.info("Repository Bean : {}", repository.getClass().getName());
        log.info("호출 흐름        : Controller → Service → Repository");
        log.info("==================================================");
    }
}
