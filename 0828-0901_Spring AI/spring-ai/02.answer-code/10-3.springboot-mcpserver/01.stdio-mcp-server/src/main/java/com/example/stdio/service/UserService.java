package com.example.stdio.service;

import com.example.stdio.domain.User;
import com.example.stdio.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

/**
 * User 서비스
 */
@Service
@RequiredArgsConstructor
@Slf4j
public class UserService {

    private final UserRepository userRepository;

    @Transactional
    public User createUser(User user) {
        log.info("Creating user: email={}", user.getEmail());
        User savedUser = userRepository.save(user);
        log.info("User created successfully: id={}, email={}", savedUser.getId(), savedUser.getEmail());
        return savedUser;
    }

    @Transactional
    public User updateUser(Long id, User user) {
        log.info("Updating user: id={}", id);
        User existingUser = userRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("User not found: id=" + id));
        
        existingUser.setName(user.getName());
        existingUser.setEmail(user.getEmail());
        
        User updatedUser = userRepository.save(existingUser);
        log.info("User updated successfully: id={}", updatedUser.getId());
        return updatedUser;
    }

    @Transactional
    public void deleteUser(Long id) {
        log.info("Deleting user: id={}", id);
        User user = userRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("User not found: id=" + id));
        userRepository.delete(user);
        log.info("User deleted successfully: id={}", id);
    }

    @Transactional(readOnly = true)
    public User getUser(Long id) {
        return userRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("User not found: id=" + id));
    }

    @Transactional(readOnly = true)
    public List<User> getAllUsers() {
        return userRepository.findAll();
    }

    @Transactional(readOnly = true)
    public User getUserByEmail(String email) {
        return userRepository.findByEmail(email)
                .orElseThrow(() -> new RuntimeException("User not found with email: " + email));
    }

    @Transactional(readOnly = true)
    public List<User> searchUsersByName(String name) {
        return userRepository.findByNameContainingIgnoreCase(name);
    }
}
