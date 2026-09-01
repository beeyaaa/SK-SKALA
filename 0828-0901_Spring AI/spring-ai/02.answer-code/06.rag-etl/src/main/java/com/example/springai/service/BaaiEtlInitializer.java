package com.example.springai.service;

import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.context.annotation.Profile;
import org.springframework.stereotype.Component;

import lombok.extern.slf4j.Slf4j;

@Component
@Profile("baai")
@Slf4j
public class BaaiEtlInitializer implements ApplicationRunner {

    private static final String DOCUMENT_FILE_NAME = "대한민국헌법(19880225).txt";

    private final TxtEtlService txtEtlService;

    public BaaiEtlInitializer(TxtEtlService txtEtlService) {
        this.txtEtlService = txtEtlService;
    }

    @Override
    public void run(ApplicationArguments args) {
        int chunkCount = txtEtlService.extract(DOCUMENT_FILE_NAME)
                .transform()
                .load()
                .size();

        log.info("[BAAI ETL] VectorDB 초기화 및 문서 재적재 완료 - 청크 수: {}", chunkCount);
    }
}