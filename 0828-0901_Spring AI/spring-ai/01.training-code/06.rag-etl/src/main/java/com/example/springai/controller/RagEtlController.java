package com.example.springai.controller;

import java.io.IOException;
import java.util.Comparator;
import java.util.List;
import java.util.Map;

import org.springframework.ai.document.Document;
import org.springframework.core.io.Resource;
import org.springframework.core.io.support.PathMatchingResourcePatternResolver;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.example.springai.service.EmbeddingService;
import com.example.springai.service.TxtEtlService;

/**
 * RAG-ETL 화면에서 사용하는 기능을 모아둔 Controller.
 *
 * - 문서 목록 조회
 * - TXT/PDF ETL 실행 (TxtEtlService, PdfEtlService의 fluent API 호출)
 * - Vector DB 검색 (EmbeddingService 재사용)
 */
@RestController
@RequestMapping("/ai/etl")
public class RagEtlController {

    private static final String DOCUMENTS_LOCATION = "classpath:documents/*";

    private final TxtEtlService txtEtlService;
    private final EmbeddingService embeddingService;

    public RagEtlController(
            TxtEtlService txtEtlService,
            EmbeddingService embeddingService
    ) {
        this.txtEtlService = txtEtlService;
        this.embeddingService = embeddingService;
    }

    /** 파일명(확장자 제외), 확장자, 원본 파일명을 담는 응답용 record. */
    public record EtlFile(String name, String extension, String fileName) {
    }

    /** GET /ai/etl/files : documents 폴더의 파일명과 확장자 목록을 반환한다. */
    @GetMapping("/files")
    public List<EtlFile> listFiles() throws IOException {
        Resource[] resources = new PathMatchingResourcePatternResolver().getResources(DOCUMENTS_LOCATION);

        return List.of(resources).stream()
                .map(Resource::getFilename)
                .filter(fileName -> fileName != null && fileName.contains("."))
                .map(fileName -> {
                    int dotIndex = fileName.lastIndexOf('.');
                    String name = fileName.substring(0, dotIndex);
                    String extension = fileName.substring(dotIndex + 1).toLowerCase();
                    return new EtlFile(name, extension, fileName);
                })
                .sorted(Comparator.comparing(EtlFile::fileName))
                .toList();
    }

    /**
     * TXT 파일명을 입력받아 Extract -> Transform -> Load를 순서대로 실행한다.
     * POST /ai/etl/txt?fileName=대한민국헌법(19880225).txt
     */
    @PostMapping("/txt")
    public Map<String, Object> executeTxtETL(@RequestParam String fileName) {
        List<Document> loaded = txtEtlService.extract(fileName)
                .transform()
                .load();

        return Map.of(
                "fileName", fileName,
                "chunkCount", loaded.size());
    }

    /* ---------------------------------------------------
     * 여기 아래에 executePdfETL()을 구현하세요.
     * @PostMapping("/pdf")를 사용하고 PdfEtlService를 호출하면 됩니다.
     * ---------------------------------------------------
     */


    /** GET /ai/etl/search : ETL로 저장한 문서를 대상으로 의미 기반 검색을 수행한다. */
    @GetMapping("/search")
    public List<Document> search(@RequestParam String query) {
        return embeddingService.search(query.trim());
    }
}
