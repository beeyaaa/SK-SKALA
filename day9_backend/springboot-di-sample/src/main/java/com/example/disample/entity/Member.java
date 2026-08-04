package com.example.disample.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;

/*
 * @Entity
 * - 이 클래스를 JPA가 관리하는 엔티티로 등록한다.
 * - 데이터베이스 테이블의 한 행과 매핑되는 객체다.
 *
 * Entity는 일반적인 Spring Bean이 아니다.
 * 따라서 Controller나 Service에 의존성으로 주입하는 대상이 아니다.
 */
@Entity
@Table(name = "members")
public class Member {

    /*
     * @Id
     * - 기본 키 컬럼을 지정한다.
     *
     * @GeneratedValue
     * - 기본 키 값을 데이터베이스가 자동으로 생성한다.
     */
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, length = 50)
    private String name;

    @Column(nullable = false, unique = true, length = 100)
    private String email;

    /*
     * JPA는 엔티티를 생성할 때 기본 생성자를 사용한다.
     * 외부에서 직접 사용할 필요가 없으므로 protected로 제한한다.
     */
    protected Member() {
    }

    /*
     * 신규 회원 생성 시 사용하는 생성자다.
     * id는 DB에서 자동 생성되므로 매개변수로 받지 않는다.
     */
    public Member(String name, String email) {
        this.name = name;
        this.email = email;
    }

    /*
     * 이 예제는 객체 상태를 무분별하게 변경하지 않도록
     * Setter 대신 조회용 Getter만 제공한다.
     */
    public Long getId() {
        return id;
    }

    public String getName() {
        return name;
    }

    public String getEmail() {
        return email;
    }
}
