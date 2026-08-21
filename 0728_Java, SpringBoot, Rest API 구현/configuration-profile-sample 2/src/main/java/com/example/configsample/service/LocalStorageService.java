package com.example.configsample.service;

import com.example.configsample.config.AppProperties;
import org.springframework.context.annotation.Profile;
import org.springframework.stereotype.Service;

@Service
@Profile("local | dev")
public class LocalStorageService implements StorageService {

    private final AppProperties appProperties;

    public LocalStorageService(AppProperties appProperties) {
        this.appProperties = appProperties;
    }

    @Override
    public String save(String filename) {
        String directory = appProperties.storage().directory();
        return "로컬 저장 완료: %s/%s".formatted(directory, filename);
    }
}
