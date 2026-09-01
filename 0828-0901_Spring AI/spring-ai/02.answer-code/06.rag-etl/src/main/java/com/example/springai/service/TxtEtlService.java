package com.example.springai.service;

import java.util.List;

import org.springframework.ai.document.Document;
import org.springframework.ai.document.DocumentTransformer;
import org.springframework.ai.document.DocumentWriter;
import org.springframework.ai.reader.TextReader;
import org.springframework.ai.transformer.splitter.TokenTextSplitter;
import org.springframework.ai.vectorstore.VectorStore;
import org.springframework.core.io.ResourceLoader;
import org.springframework.stereotype.Service;

import lombok.extern.slf4j.Slf4j;

/**
 * TXT 문서를 읽어(Extract) 청크로 분할하고(Transform) VectorDB에 저장(Load)하는
 * RAG ETL 학습용 서비스.
 *
 * 사용 예) txtEtlService.extract("파일명.txt").transform().load();
 */
@Service
@Slf4j
public class TxtEtlService {

	private static final String DOCUMENTS_PATH = "classpath:documents/";

	// text-embedding-3-small 기준 청크 설정 (임베딩 모델의 컨텍스트에 맞춘 토큰 단위 분할)
	// 여러 조항이 한 청크에 뭉쳐 검색 정밀도가 떨어지므로 아래와 같이 조정
	private static final int CHUNK_SIZE = 200;               // 목표 토큰 수 (조문 1~2개 수준으로 축소)
	private static final int MIN_CHUNK_SIZE_CHARS = 100;     // 최소 문자 수 (짧은 조문도 별도 청크로 유지)
	private static final int MIN_CHUNK_LENGTH_TO_EMBED = 5; // 임베딩할 최소 청크 길이 (초단문 노이즈 방지)
	private static final int MAX_NUM_CHUNKS = 10000;         // 최대 청크 수 (메모리 보호)

	private final ResourceLoader resourceLoader;
	private final DocumentWriter documentWriter;

	// extract -> transform -> load로 이어지는 동안 유지되는 현재 처리 대상 문서
	private List<Document> documents;

	public TxtEtlService(ResourceLoader resourceLoader, VectorStore vectorStore) {
		this.resourceLoader = resourceLoader;
		this.documentWriter = vectorStore;
	}

	/** Extract: documents 폴더에서 TXT 파일을 읽어 Document 목록을 만든다. */
	public TxtEtlService extract(String fileName) {
		this.documents = new TextReader(resourceLoader.getResource(DOCUMENTS_PATH + fileName)).get();

		log.info("[TXT ETL] Extract 완료 - fileName: {}, document 수: {}", fileName, documents.size());
		return this;
	}

	/** Transform: TokenTextSplitter로 문서를 임베딩 모델에 맞는 크기의 청크로 분할한다. */
	public TxtEtlService transform() {
		DocumentTransformer transformer = TokenTextSplitter.builder()
				.withChunkSize(CHUNK_SIZE)
				.withMinChunkSizeChars(MIN_CHUNK_SIZE_CHARS)
				.withMinChunkLengthToEmbed(MIN_CHUNK_LENGTH_TO_EMBED)
				.withMaxNumChunks(MAX_NUM_CHUNKS)
				.withKeepSeparator(true)
				.build();

		this.documents = transformer.apply(documents);

		log.info("[TXT ETL] Transform 완료 - 청크 수: {}", documents.size());
		return this;
	}

	/** Load: 분할된 문서를 임베딩하여 VectorDB에 저장한다. */
	public List<Document> load() {
		documentWriter.write(documents);

		log.info("[TXT ETL] Load 완료 - VectorDB 저장 건수: {}", documents.size());
		return documents;
	}
}
