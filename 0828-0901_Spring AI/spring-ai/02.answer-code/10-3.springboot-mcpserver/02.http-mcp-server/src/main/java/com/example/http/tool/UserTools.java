package com.example.http.tool;

import com.example.http.domain.User;
import com.example.http.service.UserService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.ai.mcp.annotation.McpTool;
import org.springframework.ai.mcp.annotation.McpToolParam;
import org.springframework.stereotype.Component;

import java.util.List;

/**
 * MCP Tools for User domain
 */
@Component
@RequiredArgsConstructor
@Slf4j
public class UserTools {

    private final UserService userService;

    @McpTool(description = "모든 사용자 정보를 조회합니다.")
    public List<User> getAllUsers() {
        log.info("MCP Tool: getAllUsers called");
        return userService.getAllUsers();
    }

    @McpTool(description = "ID로 특정 사용자를 조회합니다.")
    public User getUserById(
            @McpToolParam(description = "사용자 ID", required = true) Long id
    ) {
        log.info("MCP Tool: getUserById called with id={}", id);
        return userService.getUser(id);
    }

    @McpTool(description = "이메일로 특정 사용자를 조회합니다.")
    public User getUserByEmail(
            @McpToolParam(description = "이메일 주소", required = true) String email
    ) {
        log.info("MCP Tool: getUserByEmail called with email={}", email);
        return userService.getUserByEmail(email);
    }

    @McpTool(description = "이름으로 사용자를 검색합니다. 부분 일치를 지원합니다.")
    public List<User> searchUsersByName(
            @McpToolParam(description = "검색할 이름", required = true) String name
    ) {
        log.info("MCP Tool: searchUsersByName called with name={}", name);
        return userService.searchUsersByName(name);
    }

    @McpTool(description = "새로운 사용자를 생성합니다.")
    public User createUser(
            @McpToolParam(description = "사용자 이름", required = true) String name,
            @McpToolParam(description = "이메일 주소", required = true) String email
    ) {
        log.info("MCP Tool: createUser called with name={}, email={}", name, email);
        User user = User.builder()
                .name(name)
                .email(email)
                .build();
        return userService.createUser(user);
    }

    @McpTool(description = "사용자 정보를 수정합니다.")
    public User updateUser(
            @McpToolParam(description = "사용자 ID", required = true) Long id,
            @McpToolParam(description = "새로운 이름", required = true) String name,
            @McpToolParam(description = "새로운 이메일", required = true) String email
    ) {
        log.info("MCP Tool: updateUser called with id={}, name={}, email={}", id, name, email);
        User user = User.builder()
                .name(name)
                .email(email)
                .build();
        return userService.updateUser(id, user);
    }

    @McpTool(description = "사용자를 삭제합니다.")
    public String deleteUser(
            @McpToolParam(description = "사용자 ID", required = true) Long id
    ) {
        log.info("MCP Tool: deleteUser called with id={}", id);
        userService.deleteUser(id);
        return "User deleted successfully: id=" + id;
    }
}
