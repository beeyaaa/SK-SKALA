package com.skala.stock.service;

import com.skala.stock.dto.UserDto;
import com.skala.stock.entity.User;
import com.skala.stock.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class UserService {

    private final UserRepository userRepository;

    @Transactional
    public UserDto createUser(UserDto userDto) {
        if (userRepository.existsByUsername(userDto.getUsername())) {
            throw new RuntimeException("이미 존재하는 사용자명입니다: " + userDto.getUsername());
        }
        if (userRepository.existsByEmail(userDto.getEmail())) {
            throw new RuntimeException("이미 존재하는 이메일입니다: " + userDto.getEmail());
        }

        User user = User.builder()
                .username(userDto.getUsername())
                .password(userDto.getPassword())
                .email(userDto.getEmail())
                .balance(userDto.getBalance())
                .build();

        User savedUser = userRepository.save(user);
        return convertToDto(savedUser);
    }

    public UserDto getUserById(Long id) {
        User user = userRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("사용자를 찾을 수 없습니다: " + id));
        return convertToDto(user);
    }

    public List<UserDto> getAllUsers() {
        return userRepository.findAll().stream()
                .map(this::convertToDto)
                .collect(Collectors.toList());
    }

    private UserDto convertToDto(User user) {
        return UserDto.builder()
                .id(user.getId())
                .username(user.getUsername())
                .password(user.getPassword())
                .email(user.getEmail())
                .balance(user.getBalance())
                .build();
    }

    @Transactional
    public UserDto updateUser(Long id, UserDto userDto)
    {
        User user = userRepository.findById(id)
        .orElseThrow(() -> new RuntimeException("사용자를 찾을 수 없습니다: " + id));

        if (!user.getUsername().equals(userDto.getUsername())
            && userRepository.existsByUsername(userDto.getUsername()))
        {
            throw new RuntimeException("이미 존재하는 사용자명입니다: " + userDto.getUsername());
        }

        if (!user.getEmail().equals(userDto.getEmail())
            && userRepository.existsByEmail(userDto.getEmail()))
        {
            throw new RuntimeException("이미 존재하는 이메일입니다: " + userDto.getEmail());
        }

        user.setUsername(userDto.getUsername());
        user.setPassword(userDto.getPassword());
        user.setEmail(userDto.getEmail());
        user.setBalance(userDto.getBalance());

        User updateUser = userRepository.save(user);
        return convertToDto(updateUser);
    }

    @Transactional
    public void deleteUser(Long id)
    {
        User user = userRepository.findById(id)
            .orElseThrow(() -> new RuntimeException("사용자를 찾을 수 없습니다: " + id));

        userRepository.delete(user);
    }
}
