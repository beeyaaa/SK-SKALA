package com.example.disample.service;

import com.example.disample.dto.MemberCreateRequest;
import com.example.disample.dto.MemberResponse;

import java.util.List;

/*
 * Service 인터페이스는 비즈니스 기능의 명세를 정의한다.
 *
 * Controller가 구체 클래스인 MemberServiceImpl이 아니라
 * MemberService 인터페이스에 의존하도록 만들어 결합도를 낮춘다.
 */
public interface MemberService {

    MemberResponse createMember(MemberCreateRequest request);

    MemberResponse getMember(Long id);

    List<MemberResponse> getMembers();
}
