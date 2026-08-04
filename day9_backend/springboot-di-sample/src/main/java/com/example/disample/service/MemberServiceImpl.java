package com.example.disample.service;

import com.example.disample.dto.MemberCreateRequest;
import com.example.disample.dto.MemberResponse;
import com.example.disample.entity.Member;
import com.example.disample.repository.MemberRepository;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

/*
 * @Service
 * - 이 클래스를 Service 계층의 Spring Bean으로 등록한다.
 * - Spring Container가 객체 생성과 생명주기를 관리한다.
 */
@Service

/*
 * 기본 트랜잭션을 읽기 전용으로 설정한다.
 * 조회 메서드가 데이터 변경을 목적으로 하지 않음을 표현한다.
 */
@Transactional(readOnly = true)
public class MemberServiceImpl implements MemberService {

    private static final Logger log =
            LoggerFactory.getLogger(MemberServiceImpl.class);

    /*
     * Service가 Repository에 의존한다.
     *
     * final 필드는 생성 시 반드시 초기화되어야 하며,
     * 생성 이후 다른 객체로 변경할 수 없다.
     */
    private final MemberRepository memberRepository;

    /*
     * 생성자 주입(Constructor Injection)
     *
     * Spring Container가 MemberServiceImpl Bean을 만들 때
     * MemberRepository 타입의 Bean을 찾아 생성자 매개변수로 전달한다.
     *
     * MemberRepository는 인터페이스지만 Spring Data JPA가 만든
     * 프록시 구현 객체가 실제로 주입된다.
     *
     * 생성자가 하나뿐이면 @Autowired는 생략할 수 있다.
     */
    public MemberServiceImpl(MemberRepository memberRepository) {
        this.memberRepository = memberRepository;

        /*
         * 실제로 주입된 객체의 클래스명을 시작 로그에서 확인한다.
         * 보통 jdk.proxy...$Proxy... 형태의 프록시 클래스가 출력된다.
         */
        log.info("[DI 확인] MemberServiceImpl 생성");
        log.info("[DI 확인] 주입된 Repository 클래스: {}",
                memberRepository.getClass().getName());
    }

    /*
     * 회원 생성은 DB 데이터를 변경하므로 읽기 전용 설정을 해제한다.
     */
    @Override
    @Transactional
    public MemberResponse createMember(MemberCreateRequest request) {

        /*
         * Service 계층은 단순 DB 호출뿐 아니라
         * 이메일 중복 검사와 같은 비즈니스 규칙을 담당한다.
         */
        if (memberRepository.existsByEmail(request.email())) {
            throw new IllegalArgumentException(
                    "이미 사용 중인 이메일이다: " + request.email()
            );
        }

        Member member = new Member(
                request.name(),
                request.email()
        );

        /*
         * save()를 호출하면 INSERT가 수행되고,
         * DB가 생성한 id가 Entity에 반영된다.
         */
        Member savedMember = memberRepository.save(member);

        return MemberResponse.from(savedMember);
    }

    @Override
    public MemberResponse getMember(Long id) {
        Member member = memberRepository.findById(id)
                .orElseThrow(() ->
                        new IllegalArgumentException(
                                "회원을 찾을 수 없다. id=" + id
                        )
                );

        return MemberResponse.from(member);
    }

    @Override
    public List<MemberResponse> getMembers() {
        return memberRepository.findAll()
                .stream()
                .map(MemberResponse::from)
                .toList();
    }
}
