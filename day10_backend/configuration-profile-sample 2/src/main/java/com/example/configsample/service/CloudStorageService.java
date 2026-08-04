package com.example.configsample.service;

import org.springframework.context.annotation.Profile;
import org.springframework.stereotype.Service;

@Service
@Profile("prod")
public class CloudStorageService implements StorageService {

    @Override
    public String save(String filename) {
        return "클라우드 스토리지 저장 완료: " + filename;
    }
}
