package com.example.disample.controller;

import com.example.disample.dto.MemberCreateRequest;
import com.example.disample.dto.MemberResponse;
import com.example.disample.service.MemberService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.media.Content;
import io.swagger.v3.oas.annotations.media.Schema;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

/*
 * @RestController
 * - @Controller와 @ResponseBody를 결합한 애너테이션이다.
 * - 이 클래스를 Spring MVC Controller Bean으로 등록한다.
 * - 메서드 반환값은 JSON 응답 본문으로 변환된다.
 */
@RestController
@RequestMapping("/api/members")
@Tag(name = "회원 API", description = "Controller → Service → Repository 흐름 확인")
public class MemberController {

    private static final Logger log =
            LoggerFactory.getLogger(MemberController.class);

    /*
     * Controller가 Service 인터페이스에 의존한다.
     *
     * Controller가 Repository를 직접 호출하지 않고
     * 비즈니스 처리를 Service에 위임하는 것이 핵심이다.
     *
     * 권장 구조:
     * Controller → Service → Repository
     */
    private final MemberService memberService;

    /*
     * 생성자 주입(Constructor Injection)
     *
     * Spring Container는 MemberService 타입의 Bean을 찾는다.
     * 현재 구현체는 MemberServiceImpl 하나이므로 해당 Bean을 전달한다.
     *
     * @Transactional과 같은 AOP 기능 때문에 실제 주입 객체는
     * Spring 프록시일 수 있으며 클래스명은 실행 환경에 따라 달라진다.
     *
     * 생성자가 하나뿐이면 @Autowired를 생략할 수 있다.
     */
    public MemberController(MemberService memberService) {
        this.memberService = memberService;

        log.info("[DI 확인] MemberController 생성");
        log.info("[DI 확인] 주입된 Service 클래스: {}",
                memberService.getClass().getName());
    }

    /*
     * POST /api/members
     *
     * @RequestBody:
     * JSON 요청 본문을 MemberCreateRequest 객체로 변환한다.
     *
     * @Valid:
     * DTO에 선언한 @NotBlank, @Email 등의 검증을 실행한다.
     */
    @PostMapping
    @Operation(
            summary = "회원 등록",
            description = "Controller가 요청을 받고 Service에 회원 등록 처리를 위임한다."
    )
    @ApiResponse(
            responseCode = "201",
            description = "회원 등록 성공",
            content = @Content(schema = @Schema(implementation = MemberResponse.class))
    )
    @ApiResponse(responseCode = "400", description = "입력값 오류 또는 이메일 중복")
    public ResponseEntity<MemberResponse> createMember(
            @Valid @RequestBody MemberCreateRequest request
    ) {
        MemberResponse response =
                memberService.createMember(request);

        return ResponseEntity
                .status(HttpStatus.CREATED)
                .body(response);
    }

    /*
     * GET /api/members/{id}
     *
     * @PathVariable은 URL 경로의 id 값을 메서드 매개변수로 전달한다.
     */
    @GetMapping("/{id}")
    @Operation(summary = "회원 단건 조회")
    @ApiResponse(responseCode = "200", description = "조회 성공")
    @ApiResponse(responseCode = "400", description = "존재하지 않는 회원")
    public ResponseEntity<MemberResponse> getMember(
            @PathVariable Long id
    ) {
        MemberResponse response =
                memberService.getMember(id);

        return ResponseEntity.ok(response);
    }

    /*
     * GET /api/members
     *
     * 전체 회원을 조회한다.
     */
    @GetMapping
    @Operation(summary = "전체 회원 조회")
    @ApiResponse(responseCode = "200", description = "조회 성공")
    public ResponseEntity<List<MemberResponse>> getMembers() {
        List<MemberResponse> responses =
                memberService.getMembers();

        return ResponseEntity.ok(responses);
    }
}
