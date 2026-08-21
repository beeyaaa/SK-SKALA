package com.example.disample.repository;

import com.example.disample.entity.Member;
import org.springframework.data.jpa.repository.JpaRepository;

/*
 * Repository 계층의 역할:
 * - 데이터 저장, 조회, 수정, 삭제
 * - DB와 직접 상호작용하는 영속성 계층
 *
 * JpaRepository<Member, Long>
 * - Member: 관리할 Entity 타입
 * - Long: Member 기본 키 타입
 *
 * 이 인터페이스에는 @Repository가 없어도 된다.
 * Spring Data JPA가 실행 시점에 구현 프록시 객체를 자동 생성하고
 * Spring Container에 Bean으로 등록한다.
 */
public interface MemberRepository extends JpaRepository<Member, Long> {

    /*
     * 메서드 이름을 분석해 이메일 존재 여부를 확인하는 쿼리를 자동 생성한다.
     *
     * 개념적인 SQL:
     * SELECT COUNT(*) FROM members WHERE email = ?
     */
    boolean existsByEmail(String email);
}
