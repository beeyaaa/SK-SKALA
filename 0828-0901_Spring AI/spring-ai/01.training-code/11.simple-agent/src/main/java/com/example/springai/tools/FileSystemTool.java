package com.example.springai.tools;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.List;
import java.util.Locale;

import org.springframework.ai.tool.annotation.Tool;
import org.springframework.ai.tool.annotation.ToolParam;
import org.springframework.stereotype.Component;

/**
 * Java 애플리케이션이 실행된 디렉터리의 파일을 다루는 AI 도구입니다.
 */
@Component
public class FileSystemTool {

    private final Path workingDirectory;

    public FileSystemTool() {
        // user.dir은 Java 애플리케이션을 실행한 디렉터리를 의미합니다.
        this.workingDirectory = Path.of(System.getProperty("user.dir"))
                .toAbsolutePath()
                .normalize();
    }

    /**
     * 실행 디렉터리에 있는 파일과 디렉터리 목록을 반환합니다.
     */
    @Tool(description = "현재 Java 애플리케이션 실행 디렉터리의 파일과 디렉터리 목록을 조회합니다.")
    public List<String> listFiles() throws IOException {
        try (var paths = Files.list(workingDirectory)) {
            return paths
                    .filter(path -> Files.isRegularFile(path) || Files.isDirectory(path))
                    .sorted((left, right) -> left.getFileName().toString()
                            .compareToIgnoreCase(right.getFileName().toString()))
                    .map(path -> formatDirectoryEntry(path))
                    .toList();
        }
    }

    /**
     * 실행 디렉터리에 새로운 파일을 생성합니다.
     */
    @Tool(description = "현재 Java 애플리케이션 실행 중인 디렉터리에 새 파일을 생성합니다.")
    public String createFile(
            @ToolParam(description = "생성할 파일명", required = true) String fileName,
            @ToolParam(description = "파일에 저장할 내용", required = true) String content)
            throws IOException {

        Path filePath = resolveFilePath(fileName);

        Files.writeString(
                filePath,
                content,
                StandardCharsets.UTF_8,
                StandardOpenOption.CREATE_NEW);

        return "파일을 생성했습니다.\n파일 경로: " + filePath + "\n파일 내용:\n" + content;
    }

    /**
     * 실행 디렉터리에 있는 텍스트 파일의 내용을 반환합니다.
     */
    @Tool(description = "현재 Java 애플리케이션 실행 디렉터리 내의 txt, md, xml 파일 내용을 반환합니다.")
    public String readTextFile(
            @ToolParam(description = "내용을 읽을 txt, md, xml 파일명", required = true) String fileName)
            throws IOException {

        Path filePath = resolveFilePath(fileName);
        String lowerCaseFileName = fileName.toLowerCase(Locale.ROOT);

        if (!lowerCaseFileName.endsWith(".txt") && !lowerCaseFileName.endsWith(".md") && !lowerCaseFileName.endsWith(".xml")) {
            throw new IllegalArgumentException("txt, md, xml 파일만 읽을 수 있습니다.");
        }

        if (!Files.isRegularFile(filePath)) {
            throw new IllegalArgumentException("파일을 찾을 수 없습니다: " + fileName);
        }

        return Files.readString(filePath, StandardCharsets.UTF_8);
    }

    /**
     * 파일과 디렉터리를 쉽게 구분할 수 있는 문자열로 변환합니다.
     */
    private String formatDirectoryEntry(Path path) {
        String type = Files.isDirectory(path) ? "[디렉터리]" : "[파일]";
        return type + " " + path.getFileName();
    }

    /**
     * 파일명이 실행 디렉터리 밖을 가리키지 않는지 확인합니다.
     */
    private Path resolveFilePath(String fileName) {
        if (fileName == null || fileName.isBlank()) {
            throw new IllegalArgumentException("파일명을 입력해야 합니다.");
        }

        Path filePath = workingDirectory.resolve(fileName).normalize();

        // 학습 예제에서는 실행 디렉터리 바로 아래의 파일만 다룹니다.
        if (!workingDirectory.equals(filePath.getParent())) {
            throw new IllegalArgumentException("실행 디렉터리 바로 아래의 파일만 사용할 수 있습니다.");
        }

        return filePath;
    }
}

