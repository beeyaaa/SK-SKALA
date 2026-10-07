package com.lecture.user.repository;

import com.lecture.user.entity.User;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;
import java.util.List;

public interface UserRepository extends JpaRepository<User, Long> {
    Optional<User> findByEmail(String email);
    boolean existsByEmail(String email);

    // [페르소나 분석] 추천 서비스가 전체 수강생만 조회할 수 있도록 역할 기준으로 필터링한다.
    List<User> findByRoleOrderByIdAsc(User.Role role);
}
