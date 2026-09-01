# 🔎 Spring AI 2일차 — RAG · ChatMemory · Tool Calling 완전 정리

> 💡 **한 줄 요약**
> LLM은 **지식 단절 · 환각 · 컨텍스트 부재**라는 3가지 한계를 갖는다. 이를 **외부 세계와의 연결** 3가지로 푼다 —
> **Retrieval(RAG)** 로 사내 지식을 붙이고, **Memory** 로 대화 맥락을 유지하고, **Tool Calling** 으로 실제 행동을 하게 만든다.

**출처**: `SPRING AI 이해_v1.4.pdf` (총 349p) · SK C&C
**범위**: PDF p158 ~ p279 (2일차 전체)
**실습 코드**: `01.training code/06.rag-etl`, `07.rag`, `08.chat-memory`, `09.tool`

> ℹ️ 이 문서의 `p번호`는 **PDF 뷰어 기준 물리 페이지**입니다. 슬라이드 우하단 인쇄 번호보다 **1 큽니다**.

---

## 📑 목차

| # | 챕터 | 핵심 질문 | 슬라이드 |
|---|---|---|---|
| 1 | [LLM의 한계와 외부 세계 연결](#1-llm의-한계와-외부-세계-연결) | LLM은 왜 사내 데이터를 모르나? | p158~p163 |
| 2 | [RAG ETL (Offline)](#2-rag-etl--offline-파이프라인) | 문서를 어떻게 Vector DB에 넣나? | p164~p182 |
| 3 | [RAG Runtime](#3-rag-runtime) | 검색 품질을 어떻게 끌어올리나? | p183~p225 |
| 4 | [ChatMemory](#4-chatmemory) | LLM이 대화를 기억하게 하려면? | p226~p252 |
| 5 | [Tool Calling](#5-tool-calling) | LLM이 실제로 일을 하게 하려면? | p253~p279 |
| ★ | [전체 흐름 한 장 요약](#-전체-흐름-한-장-요약) | — | — |
| ★ | [시험/면접 대비 핵심 문답](#-시험면접-대비-핵심-문답) | — | — |
| ⚠️ | [원문 용어 검증 노트](#️-원문-용어-검증-노트) | — | — |

---

# 1. LLM의 한계와 외부 세계 연결

> 📍 **p158~p163** | 왜 RAG가 필요한가

## 1-1. LLM의 3가지 한계 (p159)

| 한계 | 설명 |
|---|---|
| **지식 단절 (Knowledge Cutoff)** | 훈련 데이터 **이후의 최신 이벤트는 알지 못함** |
| **환각 (Hallucination)** | 사실이 아닌 내용을 **그럴듯하게 생성** |
| **컨텍스트 부재 (Lack of Context)** | 사용자의 특정 도메인이나 **비공개 문서에 접근할 수 없음** |

> ❓ **핵심 질문**: 어떻게 AI가 **우리의 데이터**를 기반으로 정확하게 답변하게 할 수 있을까?

## 1-2. 외부 세계와의 연결 — 3가지 축 (p160) ⭐⭐

이 슬라이드는 2일차 전체의 **지도**다. p228, p255에서 반복해서 등장한다.

| 축 | 영문 | 해결하는 것 | 구체적 수단 |
|---|---|---|---|
| **① Retrieval** | External Knowledge Search | 지식 단절 + 환각 | · Vector Store 검색 (pgvector 등)<br>· 최신/사내외 데이터 연결<br>· Prompt에 **근거 문서** 포함 |
| **② Tool** | Function Calling / API Integration | 행동 불가 | · LLM이 외부 API·DB를 호출하여 **작업 수행**<br>· DB 조회, 시스템 자동화 |
| **③ Memory** | Conversation Context Management | 대화 맥락 상실 | · 대화 맥락 유지 및 상태 관리 |

```plain text
                        ┌─── ① Retrieval (RAG) ─── Vector Store / 사내 문서
                        │
  LLM  ─── 외부 연결 ────┼─── ② Tool Calling  ───── 외부 API / DB / K8s
                        │
                        └─── ③ Memory        ───── 대화 이력 / 세션
```

## 1-3. RAG란 (p161)

| | 설명 |
|---|---|
| **비유로 말하면** | 오픈북 시험. 문제를 받으면 **먼저 교과서에서 관련 페이지를 찾아** 펼쳐놓고, 그걸 보면서 답을 쓴다. |
| **정확히 말하면** | Vector DB로부터 **검색(Retrieval)** 해서 사용자 질문을 **보강(Augment)** 하고 LLM을 통해 답을 **생성(Generation)** 하는 패턴. |

**4단계 흐름**

| # | 단계 | 설명 |
|---|---|---|
| 1 | **사용자 질문** | 사용자가 질문을 입력 (예: "spring AI는 무엇인가?") |
| 2 | **검색 (Retrieve)** | Vector Store에서 질문과 관련된 문서를 검색 |
| 3 | **증강 (Augment)** | 검색된 Document 내용을 Prompt에 **Context로 추가** |
| 4 | **생성 (Generate)** | 증강된 Prompt를 기반으로 LLM이 정확하고 **사실에 근거한** 답변을 생성 |

## 1-4. RAG 파이프라인 — 2개의 시간대 (p162~p163) ⭐

```plain text
[ p162 — RAG 파이프라인 전체 그림 ]

 ETL ┃  ┌─────────────┐   ┌──────────────┐    ┌──────────────┐
     ┃  │             │──►│Chunk of Text │───►│  Embeddings  │──┐
     ┃  │ Data Source │──►│Chunk of Text │───►│  Embeddings  │──┤
     ┃  │             │──►│Chunk of Text │───►│  Embeddings  │──┤
     ┃  └─────────────┘──►│Chunk of Text │───►│  Embeddings  │──┤
━━━━━┻━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┿━━━━
 RAG ┃                                                          ▼
     ┃  ┌─────────┐   Find relevant data    ┌──────────────────────┐
     ┃  │ Prompt  │───────────────────────► │      Vector DB       │
     ┃  └────┬────┘                         └───────────┬──────────┘
     ┃       │        ┌──────────────────────┐          │
     ┃       └───────►│ LLM context and      │◄─────────┘
     ┃                │ relevant data        │
     ┃                └──────────┬───────────┘
     ┃                           ▼
     ┃                        ┌─────┐      ┌───────────┐
     ┃                        │ LLM │─────►│ Response  │
     ┃                        └─────┘      └───────────┘
```

**Offline vs Runtime (p163)**

```plain text
Offline (미리 해두는 일 — ETL)
 text, pdf,   ┌──────────┐   ┌─────────────┐   ┌──────────┐
 docx, html,──►│<<Read>>  │──►│  <<Split>>  │──►│<<Write>> │──► Vector DB
 json …       │ Document │   │  Document   │   │ Document │
              │  Reader  │   │ Transformer │   │  Writer  │
              └──────────┘   └─────────────┘   └──────────┘

RunTime (질문이 들어올 때마다)
              ┌──────────────┐   ┌─────────────┐   ┌──────────────┐
   질문   ────►│ <<Retrieve>> │──►│ <<Augment>> │──►│ <<Generate>> │──► 답변
              └──────────────┘   └─────────────┘   └──────────────┘
```

> ⭐ **시험 포인트**: **ETL은 Offline(사전 적재), RAG는 Runtime(질의 시점)** 이다. 두 개를 헷갈리면 안 된다.

---

# 2. RAG ETL — Offline 파이프라인

> 📍 **p164~p182** | 외부 소스로부터 텍스트를 추출하고, Document로 변환하고, 벡터 저장소에 적재하는 과정

## 2-1. ETL 3단계 (p165)

| 단계 | 컴포넌트 | 역할 |
|---|---|---|
| **Extract** | `DocumentReader` | 다양한 소스(PDF, JSON, HTML 등)에서 원시 데이터를 읽어 `Document` 객체로 **추출** |
| **Transform** | `DocumentTransformer` | 추출된 데이터를 AI 모델에 최적화된 형태로 **분할하고 정제하여 변환** |
| **Load** | `DocumentWriter` | 변환된 데이터를 Vector Store 같은 최종 목적지에 **적재** |

## 2-2. Functional Interface 3종 세트 (p166~p167) ⭐⭐

Spring AI의 ETL은 **Java 표준 함수형 인터페이스**를 그대로 상속했다. 이게 설계의 핵심이다.

```plain text
[ p166 — ETL 구현체 개요 ]

              Document Reader      Document Transformer       Document Writer
              ┌──────────────┐     ┌──────────────────┐      ┌────────────────┐
 (Source) ───►│  Supplier    │────►│    Function      │─────►│   Consumer     │───► (Store)
              │<List<Document>>    │<List<Document>,  │      │<List<Document>>│
              └──────────────┘     │ List<Document>>  │      └────────────────┘
                     │             └──────────────────┘              │
                     ▼                      │                        ▼
              List<Document>                ▼                  Vector Store
                                     List<Document>
```

| 단계 | Spring AI 인터페이스 | 상속한 Java 함수형 인터페이스 | 메서드 |
|---|---|---|---|
| Extract | `DocumentReader` | `Supplier<List<Document>>` | `get()` → `read()` |
| Transform | `DocumentTransformer` | `Function<List<Document>, List<Document>>` | `apply()` → `transform()` |
| Load | `DocumentWriter` | `Consumer<List<Document>>` | `accept()` → `write()` |

**전체 클래스 계층 (p167)**

```plain text
 Supplier<List<Document>>      Function<List<..>,List<..>>      Consumer<List<Document>>
          ▲                              ▲                              ▲
          │                              │                              │
 ┌────────┴─────────┐          ┌─────────┴──────────┐        ┌──────────┴──────────┐
 │  DocumentReader  │          │DocumentTransformer │        │   DocumentWriter    │
 │      get()       │          │ apply(List<Doc>):  │        │ accept(List<Doc>)   │
 └────────▲─────────┘          │      List<Doc>     │        └──────────▲──────────┘
          │                    └─────────▲──────────┘                   │
          │                              │                   ┌──────────┴──────────┐
 ┌────────┴────────────┐      ┌──────────┴──────────┐        │    VectorStore      │
 │ PagePdfDocumentReader│      │    TextSplitter     │        │ add(List<Document>) │
 │ TikaDocumentReader   │      │       ▲             │        │ similaritySearch()  │
 │ ParagraphPdfDocReader│      │ TokenTextSplitter   │        └──────────▲──────────┘
 │ TextReader           │      │                     │                   │
 │ JsonReader           │      │ContentFormatTransformer      ┌──────────┴───────────────┐
 └─────────────────────┘      │KeywordMetadataEnricher│       │ PgVectorStore            │
                              │SummaryMetadataEnricher│       │ MilvusVectorStore        │
                              └─────────────────────┘        │ QdrantVectorStore        │
                                                             │ ChromaVectorStore        │
                                          FileDocumentWriter │ WeaviateVectorStore      │
                                          (별도 구현체)        │ Neo4j / Pinecone / Redis │
                                                             │ Azure / SimpleVectorStore│
                                                             └──────────────────────────┘
```

## 2-3. Extract — DocumentReader (p168~p171)

```java
public interface DocumentReader extends Supplier<List<Document>> {
    default List<Document> read() {
        return get();
    }
}

@FunctionalInterface
public interface Supplier<T> {
    T get();
}
```

**대표 구현체**

| 구현체 | 설명 |
|---|---|
| `TextReader` | Resource(inputStream으로 오픈)에서 단순 텍스트 읽기 (UTF-8로 전환) |
| `JsonReader` | JSON → Document 리스트로 변환 |
| `TikaDocumentReader` | Apache Tika 기반. **PDF / Word / PPT / HTML** 등 다양한 포맷 지원 |
| `JsoupDocumentReader` | HTML 파싱 |
| `PagePdfDocumentReader` | PDF를 **페이지 단위**로 Document 생성 |
| `ParagraphPdfDocumentReader` | PDF를 **문단(목차) 단위**로 Document 생성 |

**TextReader 사용 예 (p169)**

```java
private static final String DOCUMENTS_PATH = "classpath:documents/";
private List<Document> documents;
private final ResourceLoader resourceLoader;

public TxtEtlService(ResourceLoader resourceLoader, VectorStore vectorStore) {
    this.resourceLoader = resourceLoader;
    this.vectorStore = vectorStore;
}

/** Extract: documents 폴더에서 TXT 파일을 읽어 Document 목록을 만든다. */
public TxtEtlService extract(String fileName) {
    this.documents = new TextReader(
            resourceLoader.getResource(DOCUMENTS_PATH + fileName)).get();
    log.info("[TXT ETL] Extract 완료 - fileName: {}, document 수: {}", fileName, documents.size());
    return this;   // ← Fluent 체이닝을 위해 this 반환
}
```

## 2-4. ⚠️ Extract 직후 Document 개수와 Big Document 문제 (p171) ⭐

**Extract 후 `List<Document>`의 개수는?**

| Reader | 결과 개수 |
|---|---|
| `TextReader` | **1개** (파일 전체가 Document 하나) |
| `PagePdfDocumentReader` | **페이지 수만큼** |

**Big Document의 문제점**

| 문제 | 설명 |
|---|---|
| **임베딩 벡터의 의미 희석** | 다양한 주제가 섞여 **전체적인 정보의 특징이 뭉개짐** |
| **질문과 관련 없는 노이즈 포함** | 관련 없는 정보로 인한 **유사도 품질 저하 + 토큰 사용량 증가** |

> ⭐ **그래서 Transform(Split)이 필요하다.** Extract만 하면 문서 1개짜리 거대한 벡터가 되어 검색이 무의미해진다.

## 2-5. Transform — DocumentTransformer (p172~p175)

```java
public interface DocumentTransformer extends Function<List<Document>, List<Document>> {
    default List<Document> transform(List<Document> transform) {
        return apply(transform);
    }
}
```

**대표 구현체**

| 구현체 | 설명 |
|---|---|
| **`TokenTextSplitter`** | AI 모델의 **Token 기준**으로 문서를 일정 크기(Chunk)로 분할 — **기본 구현체** |
| `TextSplitter` | 텍스트 기반 분할기의 **추상 클래스**. 문단·구분자 등 커스텀 분할 규칙 구현 시 확장 |
| `MarkdownTextSplitter` | 마크다운 헤더(`#`, `##`) 구조를 인식하여 **장/절 단위로 논리적 분할** |
| `KeywordMetadataEnricher` | **LLM을 활용해** 문서에서 주요 키워드를 추출하여 metadata에 추가 |
| `SummaryMetadataEnricher` | **LLM을 활용해** 문서의 요약문(Summary)을 생성하여 metadata에 추가 |
| `ContentFormatTransformer` | Document의 포맷터 지정 |

> 💡 `KeywordMetadataEnricher` / `SummaryMetadataEnricher`는 **내부에서 LLM을 호출**한다. 문서가 많으면 비용이 크게 늘어나니 주의.

**TokenTextSplitter 설정 (p173)**

```java
// CL100K_BASE 인코딩(OpenAI 모델 호환)을 사용하여 문장 경계를 고려한 의미 있는 청크 생성
DocumentTransformer transformer = TokenTextSplitter.builder()
        .withChunkSize(200)              // defaultChunkSize: 목표 토큰 수 (200 토큰)
        .withMinChunkSizeChars(100)      // minChunkSizeChars: 최소 문자 수 (100 문자)
        .withMinChunkLengthToEmbed(10)   // 10 문자보다 작으면 청크 제외
        .withMaxNumChunks(10000)         // maxNumChunks: 최대 청크 수 (메모리 보호)
        .withKeepSeparator(true)         // 줄바꿈/문장 구분 기호 유지
        .build();
```

> 💡 **Chunk 단위란?** 질문에 답할 수 있는 **가장 최소한의 유의미한 정보 덩어리**.

**TokenTextSplitter 매개변수 5개 (p174)** ⭐ 시험 단골

| 매개변수 | 설명 | 프레임워크 기본값 |
|---|---|---|
| `chunkSize` | 1차 분할 시 기준이 되는 **목표 토큰 수**. 구분자를 고려하여 자연스러운 문장 경계에서 분할 | **800 토큰** |
| `minChunkSizeChars` | chunkSize를 구분자로 자를 때 **최소 350자 이후**에서 분할하도록 지시 | **350 문자** |
| `minChunkLengthToEmbed` | 임베딩을 수행할 **최소 문자 수**. 이 값보다 짧은 의미 없는 조각은 버림 | **5 문자** |
| `maxNumChunks` | 최종 생성을 허용할 **최대 Chunk 개수 제한**. 메모리 폭주 방지 및 비용 절감 | **10,000 개** |
| `keepSeparator` | 줄바꿈(`\n`)이나 문장 구분 기호를 삭제하지 않고 유지할지 여부 | **true** |

**분할 알고리즘 (p174)**

```plain text
1. chunkSize 기준 1차 청크 분할
   예) chunkSize = 800 설정 시, 2,000 토큰 → 약 800 / 800 / 400 토큰으로 분할
   단, 토큰 범위 내의 구분자('.', '?', '!', '\n' 등)를 탐색하여
   자연스러운 문장 경계에서 자름

2. minChunkSizeChars 적용
   구분자를 찾더라도 최소 350자는 확보한 뒤에 자름

3. minChunkLengthToEmbed 적용
   5자 미만의 조각은 임베딩하지 않고 버림

4. maxNumChunks 적용
   10,000개를 넘으면 중단
```

**왜 Chunk로 나누나? — 5가지 이유 (p175)** ⭐

| 이유 | 설명 | 기대 효과 |
|---|---|---|
| **프롬프트 최대 토큰 한계 대응** | LLM이 한 번에 처리할 수 있는 컨텍스트 길이에 제한 | 입력 초과 오류 방지, 안정적 응답 |
| **검색 정확도 향상** | 문서 전체보다 관련 구간을 더 정밀하게 찾기 쉬움 | 답변 근거의 적합도 상승, 오답/헛소리 감소 |
| **비용 및 지연 감소** | 필요한 청크만 프롬프트에 넣어 토큰 사용을 줄임 | 호출 비용 절감, 응답 속도 개선 |
| **노이즈 감소** | 관련 없는 내용까지 같이 들어가는 것을 줄임 | 답변 집중도/일관성 향상 |
| **재적재/업데이트 용이** | 변경된 부분만 다시 임베딩/저장하면 됨 | 운영·유지보수 효율 증가, 동기화 부담 감소 |

## 2-6. Load — DocumentWriter (p176~p177)

```java
public interface DocumentWriter extends Consumer<List<Document>> {
    default void write(List<Document> documents) {
        accept(documents);
    }
}
```

**핵심 상속 관계** ⭐

```plain text
 DocumentWriter (Interface)
      └── write(List<Document>)
                ▲
                │ (상속)
 VectorStore (Interface)
      └── add(List<Document>)
```

> ⭐ **`VectorStore`가 곧 `DocumentWriter`다.** 그래서 `vectorStore`를 `DocumentWriter` 타입 필드에 그대로 주입할 수 있다.

```java
private final DocumentWriter documentWriter;

public TxtEtlService(ResourceLoader resourceLoader, VectorStore vectorStore) {
    this.resourceLoader = resourceLoader;
    this.documentWriter = vectorStore;   // ← VectorStore가 DocumentWriter를 구현하므로 가능
}

/** Load: 분할된 문서를 임베딩하여 VectorDB에 저장한다. */
public List<Document> load() {
    documentWriter.write(documents);
    log.info("[TXT ETL] Load 완료 - VectorDB 저장 건수: {}", documents.size());
    return documents;
}
```

## 2-7. 🧪 실습 — RAG ETL 코드 리뷰 및 PDF 확장 (p178~p182)

**① 코드 리뷰** — `01.training code/06.rag-etl`의 `RagEtlController.java`, `TxtEtlService.java`
- [ ] Spring Boot 실행 → `localhost:8080` 접속 → UI에서 ETL 실행
- [ ] DBeaver로 pgvector 접속 후 저장된 정보 확인

**② PDF 처리 추가 — `PdfEtlService.java` (p180)**
대상 파일: `resources/documents/대한민국형법(20250318).pdf`

```java
/** Extract: documents 폴더에서 PDF 파일을 페이지 단위로 읽어 Document 목록을 만든다. */
public PdfEtlService extract(String fileName) {
    PdfDocumentReaderConfig config = PdfDocumentReaderConfig.builder()
            .withPagesPerDocument(1)      // 페이지 1장 = Document 1건
            .build();

    this.documents = new PagePdfDocumentReader(
            resourceLoader.getResource(DOCUMENTS_PATH + fileName), config)
            .get();
    return this;
}
```

**③ Controller에 엔드포인트 추가 (p181)**

```java
@PostMapping("/pdf")
public Map<String, Object> executePdfETL(@RequestParam String fileName) {
    List<Document> loaded = pdfEtlService.extract(fileName)
            .transform()
            .load();

    return Map.of(
            "fileName", fileName,
            "chunkCount", loaded.size());
}
```

> ⭐ `.extract().transform().load()` — ETL 3단계가 **Fluent 체이닝**으로 이어진다. 각 메서드가 `this`를 반환하기 때문.

- [ ] 참고 문서: `https://docs.spring.io/spring-ai/reference/api/etl-pipeline.html`

---

# 3. RAG Runtime

> 📍 **p183~p225** | 질문이 들어올 때마다 실행되는 검색·증강·생성

## 3-1. Runtime RAG 3단계 (p184)

| 단계 | 설명 |
|---|---|
| **[Retrieval]** | 질문이 들어오면 Vector DB에서 **유사도 높은 문서 조각(Chunk) 검색** |
| **[Augment]** | 검색된 문서 조각을 프롬프트 내에 **참고 자료로 추가** |
| **[Generation]** | 문맥(Context) 기반으로 **환각 없이 정확한 답변 생성** |

## 3-2. RAG Advisor 2종 비교 (p185) ⭐⭐

| | **QuestionAnswerAdvisor** (기본) | **RetrievalAugmentationAdvisor** (고급) |
|---|---|---|
| **목적** | 기본 VectorStore 기반 RAG를 **빠르게** 구현 | 멀티 커스텀 컴포넌트 **조합 및 파이프라인 제어** |
| **적합** | 단순 Q&A, Rapid Prototyping | Hybrid Search, Query Rewrite, Reranking 등 **고도화 RAG** |
| **구성** | VectorStore + SearchRequest 간단 결합 | `DocumentRetriever`, `QueryTransformer` 등 **모듈화** |
| **의존성** | `spring-ai-vector-store-advisor` | `spring-ai-rag` (추가) |

**의존성 (p186, p192)**

```xml
<!-- QuestionAnswerAdvisor / VectorStoreChatMemoryAdvisor 용 -->
<dependency>
   <groupId>org.springframework.ai</groupId>
   <artifactId>spring-ai-vector-store-advisor</artifactId>
</dependency>

<!-- RetrievalAugmentationAdvisor 용 -->
<dependency>
   <groupId>org.springframework.ai</groupId>
   <artifactId>spring-ai-rag</artifactId>
</dependency>
```

## 3-3. QuestionAnswerAdvisor (p187~p190)

`QuestionAnswerAdvisor`는 사용자 질문을 받아 Vector Store에서 관련 문서를 검색하고, 검색된 문서(Context)를 **원래 질문에 자동으로 추가**하여 LLM에게 전달한다.

```java
// [Code Snippet: Simple RAG with QuestionAnswerAdvisor]
VectorStore vectorStore = ...;
ChatModel   chatModel   = ...;

ChatClient chatClient = ChatClient.builder(chatModel).build();

ChatResponse response = chatClient.prompt()
        .user("사용자 질문...")
        // 핵심: Advisor를 통해 RAG 기능 추가
        .advisors(new QuestionAnswerAdvisor(vectorStore))   // ← 이 한 줄로 RAG 활성화
        .call()
        .chatResponse();
```

```plain text
[ p187 — 동작 4단계 ]

 ① [사용자 질문] ──►┌── QuestionAnswerAdvisor ──┐──► ④[LLM] ──► [최종 답변]
                    │  ② 🔍 검색                │
                    │      ↑                    │
                    │   [Vector Store]          │
                    │  ③ 📄 + ➕ (증강)          │
                    └───────────────────────────┘

 1) 사용자 질문: 사용자가 질문을 입력 (spring AI는 무엇인가?)
 2) 검색(Retrieve): Vector Store에서 질문과 관련된 문서를 검색
 3) 증강(Augment): 검색된 Document 내용을 Prompt에 Context로 추가
 4) 생성(Generate): 증강된 Prompt를 기반으로 LLM이 정확하고 사실에 근거한 답변을 생성
```

**검색/필터 세밀 제어 (p188)**

```java
// 1. QuestionAnswerAdvisor 생성 (정적 검색 조건 설정)
var qaAdvisor = QuestionAnswerAdvisor.builder(vectorStore)
    .searchRequest(SearchRequest.builder()
        .similarityThreshold(0.3)   // 유사도 임계값
        .topK(5)                    // 상위 5개 검색
        .build())
    .build();

// 2. ChatClient에 Advisor 등록 + 런타임 동적 필터 적용
chatClient.prompt()
     .user("Please answer my question")
     .advisors(a -> a
         .advisor(qaAdvisor)                                        // 생성한 Advisor 등록
         .param(QuestionAnswerAdvisor.FILTER_EXPRESSION,            // 런타임 동적 필터
                "category == 'spring'"))
     .call()
     .content();
```

> ⭐ **`FILTER_EXPRESSION`** — Vector 유사도와 **별개로** metadata 기반 필터를 런타임에 걸 수 있다. 예: 로그인한 사용자의 부서 문서만 검색.

**🧪 실습 (p189~p190)** — `01.training code/07.rag`
- [ ] 코드 리뷰 → Spring Boot 실행 → UI에서 질문
- [ ] Console 로그에서 **Vector Query 결과**와 **추가된 Prompt**(Vector 정보만 활용)를 확인

## 3-4. RetrievalAugmentationAdvisor — 4단계 파이프라인 (p191)

검색, 질의 변환, 필터링, 문서 결합 등 **RAG 전체 흐름을 유연하게 구성**할 수 있도록 지원하는 확장성 Advisor.
각 단계를 **독립적 구성요소로 분리**, 런타임 시점에 **모듈 조합** 가능.

```plain text
┌────────────────┬──────────────┬──────────────────┬──────────────────┐
│ ① Pre-Retrieval│ ② Retrieval  │ ③ Post-Retrieval │ ④ Generation     │
│   (사전 검색)    │   (검색)      │   (사후 검색)      │   (생성)          │
├────────────────┼──────────────┼──────────────────┼──────────────────┤
│ 사용자 쿼리를    │ Vector Store │ 검색된 문서를      │ 검색 결과를        │
│ 변환하여 검색    │ 에서 문서를   │ 재정렬하거나       │ prompt에 증강하고  │
│ 품질을 극대화    │ 가져옴        │ 필터링하여 노이즈  │ LLM을 호출하여     │
│                │              │ 를 줄임           │ 답변 생성          │
├────────────────┼──────────────┼──────────────────┼──────────────────┤
│ queryTransformers│documentRetriever│documentPostProcessors│ queryAugmenter │
│ queryExpander  │              │                  │                  │
└────────────────┴──────────────┴──────────────────┴──────────────────┘
        필수             필수            Optional           Optional
```

```java
RetrievalAugmentationAdvisor advisor = RetrievalAugmentationAdvisor.builder()
        .queryTransformers(...)         // ① Pre-Retrieval
        .queryExpander(...)             // ① Pre-Retrieval
        .documentRetriever(...)         // ② Retrieval
        .documentPostProcessors(...)    // ③ Post-Retrieval (Optional)
        .queryAugmenter(...)            // ④ Generation (Optional)
        .build();
```

## 3-5. ① Pre-Retrieval — 4가지 모듈 (p193, p195)

사용자 쿼리를 검색에 더 효과적인 형태로 가공하여 **검색 정확도를 향상**시킨다.

| 모듈 | 역할 | 예시 |
|---|---|---|
| **`RewriteQueryTransformer`** | 사용자 질문에 검색 품질에 영향을 줄 수 있는 **불필요한 내용이 포함된 경우**, LLM을 이용해 질문을 **재작성** | "혹시 오늘 날씨도 좋은데 Spring AI에서 RAG 검색 속도를 올리는 방법을 알 수 있나요? 부탁드립니다"<br>→ **"Spring AI RAG 검색 속도 최적화 방법"** |
| **`CompressionQueryTransformer`** | **대화 기억과 관련 있는 모호한 질문**을 LLM을 이용해 **완전한 독립 질문으로 변환** | 이전 대화: "spring AI의 TokenTextSplitter 설정법을 알려줘"<br>현재: "그럼 그거 기본 토큰 크기(chunk size)는 얼마야"<br>→ **"Spring AI TokenTextSplitter의 기본 chunk size 설정값은 얼마인가?"** |
| **`MultiQueryExpander`** | 단일 질문을 **의미적으로 다양한 여러 질문으로 확장**하여 더 많은 관련 문서를 검색할 기회를 높임 | "Spring AI RAG 성능 개선"<br>→ ① "Spring AI RAG 성능 향상 및 속도 최적화 기법"<br>② "Spring AI VectorStore 검색 정확도 및 임베딩 개선" ③ … |
| **`TranslationQueryTransformer`** | 질문을 **Embedding Model이 학습한 언어로 번역** | 한국어 질문 → 영어 문서 검색 시 유용 |

> ⚠️ **Pre-Retrieval 모듈은 전부 LLM을 추가로 호출한다.** 즉 질문 1건당 LLM 호출이 2~4회로 늘어난다. 비용·지연을 반드시 고려할 것.

**RewriteQueryTransformer 구현 (p196~p197)**

```java
public RewriteQueryService(ChatModel chatModel, VectorStore vectorStore) {

    // 사용자 질문을 정제하기 위해 "별도의" ChatClient가 필요하다
    ChatClient.Builder transformerBuilder = ChatClient.builder(chatModel)
            .defaultAdvisors(new SimpleLoggerAdvisor());

    RetrievalAugmentationAdvisor advisor = RetrievalAugmentationAdvisor.builder()
            // LLM을 통해 장황한 질문을 정제된 메시지로 전환
            .queryTransformers(RewriteQueryTransformer.builder()
                    .chatClientBuilder(transformerBuilder)
                    .build())
            .documentRetriever(VectorStoreDocumentRetriever.builder()
                    .vectorStore(vectorStore)
                    .similarityThreshold(0.5)
                    .topK(3)
                    .build())
            .build();

    // 나의 질문을 위한 ChatClient
    this.chatClient = ChatClient.builder(chatModel)
            .defaultAdvisors(advisor, new SimpleLoggerAdvisor())
            .build();
}
```

> ⭐ **왜 ChatClient가 2개인가?** QueryTransformer가 쓰는 ChatClient에 RAG Advisor를 붙이면 **무한 재귀**가 발생한다. 반드시 분리해야 한다.

**RewriteQueryTransformer가 실제로 쓰는 프롬프트 (p199)**

```plain text
사용자의 질문을 벡터 데이터베이스(Vector DB) 검색에 최적화된 형태로 재작성하세요.
불필요한 표현은 제거하고, 핵심 의미를 유지하면서 간결하고 명확한 검색 질문으로 다시 작성해주세요.
답변은 질문 내용만 포함해야 합니다.

Original query:
국회의원이 하라는 일은 하지 않고, 자기 개인 이익만 챙기고 있고 이게 국회의원이 할 일이냐?

Rewritten query:
```

```plain text
LLM 결과:
"국회의원의 직무와 의무는 무엇이며, 개인의 이익을 우선하는 행위가 국회의원의 직무에 부합하는가?"
```

**동작 결과 (p198)**

```plain text
질문           : 국회의원이 하라는 일은 하지 않고, 자기 개인 이익만 챙기고 있고 이게 국회의원이 할 일이냐?
queryTransformer 후 : 국회의원의 역할과 개인 이익 추구에 대한 비판
Response       : 국회의원은 청렴의 의무가 있으며, 국가이익을 우선하여 직무를 행해야 한다고 명시되어 있다.
                 개인 이익을 추구하는 것은 국회의원의 의무에 반하는 행동이다.
```

## 3-6. ② Retrieval — VectorStoreDocumentRetriever (p194)

1단계에서 생성된 Query를 이용해 VectorStore에서 **유사도가 높은 문서 검색**을 담당하는 모듈.

- `VectorStore`를 사용하여 유사도 기반 문서 검색
- RAG 파이프라인 내에서 **자동으로 검색 결과를 프롬프트에 주입**
- 내부적으로 `VectorStore.similaritySearch()`를 사용

```java
.documentRetriever(VectorStoreDocumentRetriever.builder()
        .vectorStore(vectorStore)
        .similarityThreshold(0.5)
        .topK(3)
        .build())
```

## 3-7. 🧪 실습 1 — RewriteQueryTransformer (p200~p203)

`01.training code/06.rag` — `RetrievalAugmentService.java`와 `RagController.java`의 빈칸 채우기

**A. QueryTransformer용 `ChatClient.Builder` 생성**

```java
ChatClient.Builder transformerBuilder = ChatClient.builder(chatModel)
        .defaultAdvisors(new SimpleLoggerAdvisor());
```

**B. `RetrievalAugmentationAdvisor` 객체 생성**

```java
RetrievalAugmentationAdvisor retrievalAdvisor = RetrievalAugmentationAdvisor.builder()
        .queryTransformers(
                // 사용자 질문을 검색에 적합한 문장으로 재작성
                RewriteQueryTransformer.builder()
                        .chatClientBuilder(transformerBuilder)
                        .build())
        .documentRetriever(VectorStoreDocumentRetriever.builder()
                .vectorStore(vectorStore)
                .build())
        .build();
```

**C. 나의 질문을 위한 ChatClient 생성**

```java
this.chatClient = ChatClient.builder(chatModel)
        .defaultAdvisors(retrievalAdvisor, new SimpleLoggerAdvisor())
        .build();
```

**D. `RagController.java`에서 호출 (p201)**

```java
@GetMapping("/advanced")
public Map<String, Object> advancedQuery(@RequestParam String question,
                                         HttpSession session) {
    String answer = retrievalAugmentService.answer(question, session.getId());
    return Map.of("question", question, "answer", answer);
}
```

- [ ] Spring Boot 실행 → UI 확인 → **Console 로그**에서 재작성된 질문 확인

## 3-8. CompressionQueryTransformer (p205~p211)

**구현 (p205~p206)**

```java
public RewriteQueryService(ChatModel chatModel, VectorStore vectorStore, ChatMemory chatMemory) {

    ChatClient.Builder transformerBuilder = ChatClient.builder(chatModel)
            .defaultAdvisors(new SimpleLoggerAdvisor());

    RetrievalAugmentationAdvisor advisor = RetrievalAugmentationAdvisor.builder()
            .queryTransformers(
                    CompressionQueryTransformer.builder()
                            .chatClientBuilder(transformerBuilder)
                            .build())
            .documentRetriever(VectorStoreDocumentRetriever.builder()
                    .vectorStore(vectorStore)
                    .build())
            .build();
    // ...
}

public String answer(String question, String conversationId) {
    return chatClient.prompt()
            // HTTP Session 정보를 ChatMemory Advisor에 전달
            // Session ID를 기반으로 Prompt 이력 저장·관리
            .advisors(a -> a.param(ChatMemory.CONVERSATION_ID, conversationId))
            .user(question)
            .call()
            .content();
}
```

> ⚠️ **CompressionQueryTransformer는 `ChatMemory`가 필수다.** 대화 이력이 없으면 "그거", "대통령은?" 같은 모호한 질문을 복원할 수 없다.

**실제 프롬프트 (p207)**

```plain text
당신은 대화 이력과 후속 질문을 바탕으로 검색에 최적화된 독립적인 질문을 생성하는 전문가입니다.

대화 이력:
USER: 국회의원이 하라는 일은 하지 않고, 자기 개인 이익만 챙기고 있고 이게 국회의원이 할 일이냐?
ASSISTANT: 국회의원은 청렴의 의무가 있으며, 국가이익을 우선하여 양심에 따라 직무를 행해야 한다.
           따라서 개인 이익만을 챙기는 것은 국회의원의 직무에 맞지 않다.

Original query:
대통령은?

위 내용을 바탕으로, 이전 대화의 사용자 질문 문맥을 포함하여
명확하고 구체적인 하나의 독립된 질문으로 다시 작성해주세요.
답변은 질문 내용만 포함해야 합니다.
```

```plain text
LLM 결과:
"국회의원과 마찬가지로 대통령도 개인의 이익만을 추구하는 것이 대통령의 직무에 부합하는가?"
```

**🧪 실습 (p208~p209)**

```java
// A. queryTransformers에 추가 — 순서가 중요하다
RetrievalAugmentationAdvisor retrievalAdvisor = RetrievalAugmentationAdvisor.builder()
        .queryTransformers(
                // ① 재작성된 질문을 대화 이력과 함께 압축(독립 질문화)
                CompressionQueryTransformer.builder()
                        .chatClientBuilder(transformerBuilder)
                        .build(),
                // ② 사용자 질문을 검색에 적합한 문장으로 재작성
                RewriteQueryTransformer.builder()
                        .chatClientBuilder(transformerBuilder)
                        .build())
        .documentRetriever(...)
        .build();
```

```java
// B. chatMemory 적용
this.chatClient = ChatClient.builder(chatModel)
        // 4단계: 대화 이력과 검색 문서를 적용해 답변 생성
        .defaultAdvisors(
                MessageChatMemoryAdvisor.builder(chatMemory).build(),
                retrievalAdvisor,
                new SimpleLoggerAdvisor(Ordered.LOWEST_PRECEDENCE - 1))
        .build();
```

- [ ] UI에서 모호한 질문 **"대통령은?"** 을 넣고 어떻게 답하는지 확인
- [ ] Console 로그에서 압축된 질문 확인

## 3-9. MultiQueryExpander (p213~p217)

**구현 (p213, p215)**

```java
public MultiQueryExpanderService(ChatModel chatModel, VectorStore vectorStore) {
    ChatClient.Builder expanderBuilder = ChatClient.builder(chatModel)
            .defaultAdvisors(new SimpleLoggerAdvisor());

    RetrievalAugmentationAdvisor advisor = RetrievalAugmentationAdvisor.builder()
            .queryTransformers(/* ... */)
            // Pre-Retrieval: 사용자 질문을 여러 개의 쿼리로 확장
            .queryExpander(MultiQueryExpander.builder()
                    .chatClientBuilder(expanderBuilder)
                    .numberOfQueries(3)     // default = 3
                    .build())
            .documentRetriever(/* ... */)
            .build();
}
```

> ⭐ **호출 순서: `queryTransformers` → `queryExpander`.** Transformer로 질문을 정제한 뒤 Expander로 여러 갈래로 퍼뜨린다.

**실제 프롬프트 (p214)**

```plain text
정보 검색 및 검색 최적화 전문가로서, 주어진 쿼리에 대해 3개의 서로 다른 버전의 변형 쿼리를 생성하는 것이 너의 임무입니다.
각 변형은 원래 쿼리의 핵심 의도를 유지하면서도 주제의 다양한 관점이나 측면을 다루어야 합니다.
목표는 검색 범위를 넓히고 관련 정보를 찾을 가능성을 높이는 것입니다.
선택 이유를 설명하거나 다른 텍스트를 추가하지 마세요.
줄바꿈으로 구분된 변형 쿼리만 제공하세요.

Original query:
대통령의 임기는 어떻게 되나요?

Query variants:
```

```plain text
LLM 결과:
대한민국 대통령의 임기는 몇 년이며 연임이 가능한가?
대한민국 대통령의 임기와 중임 제한은 어떻게 규정되어 있는가?
대한민국 헌법에서 대통령의 임기와 임기 제한에 대해 어떻게 규정하고 있는가?
```

- [ ] UI에서 실행 후 Console 로그에서 3개의 확장 쿼리 확인

## 3-10. Custom QueryTransformer / QueryExpander (p218)

```java
public interface QueryTransformer extends Function<Query, Query> {
    Query transform(Query query);

    default Query apply(Query query) {
        return transform(query);
    }
}

public interface QueryExpander extends Function<Query, List<Query>> {
    List<Query> expand(Query query);

    default List<Query> apply(Query query) {
        return expand(query);
    }
}
```

> ⭐ **Transformer는 1→1**, **Expander는 1→N**. 반환 타입만 봐도 구분된다.

## 3-11. ③④ Post-Retrieval & Generation (p219~p222)

> 💡 **둘 다 Optional이다.** 설정하지 않으면
> · Post-Retrieval은 **Skip**
> · Generation은 Documents를 **하나의 String으로 자동 변환**하는 기능이 자동 지원된다.

| 단계 | 인터페이스 | 역할 |
|---|---|---|
| **Post-Retrieval** | `DocumentPostProcessor` | · **재정렬**: 쿼리와의 관련성을 기준으로 문서 순위 재조정<br>· **필터링**: 관련 없거나 중복된 문서를 제거<br>· **압축**: 문서 내용을 요약하여 노이즈를 줄이고 "lost in the middle" 문제 완화 |
| **Generation** | `ContextualQueryAugmenter` | · 사용자 쿼리와 정제된 문서 Context를 **최종 Prompt Template에 결합**<br>· `allowEmptyContext` 옵션으로 **컨텍스트가 비어 있을 경우의 동작**도 제어 |

> 💡 **"Lost in the Middle" 문제란?** LLM은 긴 컨텍스트의 **처음과 끝**은 잘 보지만 **가운데**에 있는 정보는 놓치는 경향이 있다. 그래서 문서를 재정렬·압축한다.

**DocumentPostProcessor 구현 (p220)**

```java
// DocumentPostProcessor는 검색 후 문서를 처리하는 단계
DocumentPostProcessor documentPostProcessor =
    (Query query, List<Document> documents) -> {
        // 예시: 유사도 점수(Score)가 0.5 이상인 문서만 필터링
        return documents.stream()
                .filter(doc -> doc.getScore() >= 0.5)
                .toList();
    };
```

**ContextualQueryAugmenter 프롬프트 (p221)**

```java
String contextPrompt = """
        아래는 관련 컨텍스트 정보입니다.
        ---------------------
        {context}
        ---------------------
        주어진 컨텍스트 정보만을 사용하여 질문에 답변하세요.
        다음 규칙을 따르세요:
        1. 컨텍스트에 답변이 없으면 "제공된 정보에서 답변을 찾을 수 없습니다"라고 말하세요.
        2. "컨텍스트에 따르면..." 또는 "제공된 정보에 의하면..."과 같은 표현은 피하세요.

        질문: {query}
        답변:
        """;

String emptyContextPrompt = """
        사용자의 질문이 제공된 지식 범위를 벗어났습니다.
        정중하게 답변할 수 없다고 안내해주세요.
        """;
```

**최종 조립 (p222)**

```java
// 검색된 문서를 LLM에 전달할 최종 프롬프트로 변환하는 Contextual Query Augmenter 설정
ContextualQueryAugmenter queryAugmenter = ContextualQueryAugmenter.builder()
        .promptTemplate(new PromptTemplate(contextPrompt))
        .emptyContextPromptTemplate(new PromptTemplate(emptyContextPrompt))
        .allowEmptyContext(false)    // 기본값 false
        .build();

RetrievalAugmentationAdvisor advisor = RetrievalAugmentationAdvisor.builder()
        .queryTransformers(queryTransformer, compressionTransformer)
        .queryExpander(multiQueryExpander)
        .documentRetriever(documentRetriever)
        .documentPostProcessors(documentPostProcessor)
        .queryAugmenter(queryAugmenter)
        .build();
```

> ⚠️ **`allowEmptyContext`의 의미** — `false`(기본)면 검색 결과가 없을 때 **LLM에게 물어보지 않고** emptyContextPrompt로 거절한다. `true`면 컨텍스트 없이도 LLM이 자기 지식으로 답한다 → **환각 위험**.

**🧪 실습 (p223~p225)**

```java
RetrievalAugmentationAdvisor advisor = RetrievalAugmentationAdvisor.builder()
        .queryTransformers(…)          // ① Pre-Retrieval
        .queryExpander(…)              // ① Pre-Retrieval
        .documentRetriever(…)          // ② Retrieval
        .documentPostProcessors(…)     // ③ Post-Retrieval  ← 추가
        .queryAugmenter(…)             // ④ Generation      ← 추가
        .build();
```

- [ ] `01.training code/07.rag` — 4단계가 모두 동작하는 RAG 코드 확인
- [ ] Console 로그에서 각 단계가 순서대로 찍히는지 확인

---

# 4. ChatMemory

> 📍 **p226~p252** | 다양한 유형의 스토리지를 활용한 대화 기록 관리

## 4-1. 왜 필요한가 (p227~p228)

> ⭐ **핵심 전제: LLM은 대화를 기억하지 못한다.**
> LLM API는 **stateless**다. 매 요청이 완전히 독립적이다. "기억"처럼 보이는 것은 전부 **애플리케이션이 이전 대화를 다시 보내주기 때문**이다.

## 4-2. ChatMemory 정의와 3가지 역할 (p229)

| | 설명 |
|---|---|
| **정의** | 사용자와 LLM 간에 주고받은 **대화 이력(System, User, Assistant 메시지 목록)** 을 일관된 방식으로 **저장·관리·재구성**하여 지속적인 대화 맥락(Context)을 유지해 주는 메모리 관리 컴포넌트 |

| 역할 | 설명 |
|---|---|
| **① 대화 저장 및 조회** | `conversationId`(사용자/세션별 식별자)를 기반으로 이전 메시지들을 저장 |
| **② 토큰/메시지 수 제한 (Memory Windowing)** | 대화가 길어지면 LLM의 **토큰 한계(Context Window)를 초과하고 비용이 증가**하므로, 최근 N개의 대화만 유지하거나(Sliding Window) 요약하여 관리 |
| **③ 영속화(Persistence) 지원** | 애플리케이션이 재시작되어도 대화가 유지되도록 In-Memory 외에 **Redis, DB** 등에 저장 |

## 4-3. ChatMemory 인터페이스 (p230)

```java
public interface ChatMemory {

    default void add(String conversationId, Message message) {
        Assert.hasText(conversationId, "conversationId cannot be null or empty");
        Assert.notNull(message, "message cannot be null");
        this.add(conversationId, List.of(message));
    }

    void add(String conversationId, List<Message> messages);   // 추가
    List<Message> get(String conversationId);                  // 검색
    void clear(String conversationId);                         // 삭제
}
```

> ⭐ **`add` / `get` / `clear`** 3개만 기억하면 된다.

## 4-4. 기본 구현체 — MessageWindowChatMemory (p231~p234)

**계층 구조 (p233)**

```plain text
ChatMemory                          ← 인터페이스
    │
    └── MessageWindowChatMemory     ← 기본 구현체
              │
              └── ChatMemoryRepository
                       │
                       └── InMemoryChatMemoryRepository   ← 기본 저장소
```

```java
// 아무것도 설정하지 않는 경우          │  개념적으로 이것과 동일
@Autowired                          │  MessageWindowChatMemory.builder()
ChatMemory chatMemory;              │      .chatMemoryRepository(
                                    │          new InMemoryChatMemoryRepository())
                                    │      .maxMessages(20)
                                    │      .build();
```

**기본 사용법 (p231)**

```java
// ① 일반적인 사용법: 일반 Bean처럼 자동 주입 (default 윈도우 크기 = 20)
public MessageChatMemoryService(ChatMemory chatMemory, ChatClient.Builder chatClientBuilder) {
    this.chatClient = chatClientBuilder
        .defaultAdvisors(
            MessageChatMemoryAdvisor.builder(chatMemory).build(),
            new SimpleLoggerAdvisor()
        )
        .build();
}
```

```java
// ② 윈도우 크기 변경 시 수동 생성
ChatMemory chatMemory = MessageWindowChatMemory.builder()
        .maxMessages(10)
        .build();
```

> 💡 **`maxMessages`는 "메시지 개수"다.** UserMessage + AssistantMessage가 각각 1개로 센다. 즉 `maxMessages(10)`은 **대화 5턴**이다.

**Redis 적용 (p232)**

```xml
<dependency>
    <groupId>org.springframework.ai</groupId>
    <artifactId>spring-ai-starter-model-chat-memory-repository-redis</artifactId>
</dependency>
```

```java
@Autowired
RedisChatMemoryRepository chatMemoryRepository;

ChatMemory chatMemory = MessageWindowChatMemory.builder()
        .chatMemoryRepository(chatMemoryRepository)
        .maxMessages(10)
        .build();
```

**Repository 종류와 선택 기준 (p234)** ⭐

| 저장소 구현체 | 권장 사용 상황 / 적합한 시나리오 |
|---|---|
| **`InMemoryChatMemoryRepository`** | · 로컬 개발 및 단위 테스트 환경<br>· 로그인/세션 저장이 필요 없는 단발성 챗봇 |
| **`RedisChatMemoryRepository`** | · **MSA 및 Multi-Node 분산 서버 환경**<br>· 실시간 빠른 세션 처리 및 자동 만료(TTL) 필요 시 |
| **`JdbcChatMemoryRepository`** | · RDB(MySQL, PostgreSQL 등) 기반의 서비스<br>· 대화 이력을 **서비스 영속 데이터로 엄격히 관리**할 때 |
| **`MongoDbChatMemoryRepository`** | · JSON Document 형태 데이터 저장이 편한 환경 |

## 4-5. ChatMemoryAdvisor (p235~p236)

`ChatMemory` 기능을 `ChatClient` 호출 과정에 적용하여 **이전 대화를 Prompt에 자동 주입**해서 LLM에 전달한다.

**MessageChatMemoryAdvisor**
- `ChatMemory`에서 받은 대화 기억을 **UserMessage와 AssistantMessage로 구분 생성**하여 프롬프트에 추가
- 저장된 UserMessage/AssistantMessage를 **그대로 꺼내서** 다음 요청의 Message 리스트에 추가 (역할 유지)
- 따라서 LLM은 **역할(Role) 기반 추론**이 가능하다

```java
ChatMemory chatMemory = MessageWindowChatMemory.builder()
                                .maxMessages(10)
                                .build();

MessageChatMemoryAdvisor advisor = MessageChatMemoryAdvisor.builder(chatMemory).build();

ChatClient chatClient = chatClientBuilder.defaultAdvisors(advisor).build();
```

**실제로 나가는 JSON (p236)**

```json
{
    "messages": [
      { "role": "system",    "content": "..." },
      { "role": "user",      "content": "Spring AI가 뭐야?" },      // ← 과거 User
      { "role": "assistant", "content": "Spring AI는 ..." },        // ← 과거 Assistant
      { "role": "user",      "content": "그럼 RAG는?" },            // ← 과거 User
      { "role": "assistant", "content": "RAG는 ..." },              // ← 과거 Assistant
      { "role": "user",      "content": "chunk size는?" }           // ← 현재 요청
    ]
}
```

- OpenAI GPT, Claude, Gemini 등 **대부분의 최신 Chat Model이 이 방식(Messages Array)을 표준으로 지원**
- 모델은 **순서가 있는 대화 목록에서 가장 아래 것을 현재**로 인식

## 4-6. Session별 대화 기억 Index 관리 (p237~p238)

대화 내용을 ChatMemory에 저장/추출할 때 **고유 Index가 필요**하다. 서블릿 컨테이너(내장 Tomcat)에서 발급한 **세션 식별자**를 활용한다. (사용자 ID, Token 등도 활용 가능)

```java
@GetMapping("/default")
public Map<String, Object> chatMemory(@RequestParam String question, HttpSession session) {

    String answer = chatClient.prompt()
            .user(question)
            .advisors(advisorSpec ->
                    advisorSpec.param(ChatMemory.CONVERSATION_ID, session.getId()))
            .call()
            .content();

    return Map.of(
            "question", question,
            "conversationId", session.getId(),
            "answer", answer);
}
```

> ⭐ **`ChatMemory.CONVERSATION_ID`** 는 Advisor Context에 넘기는 **키 상수**다. Advisor는 이 값으로 어떤 대화인지 식별한다.

## 4-7. VectorStoreChatMemory — 장기 기억 (p243~p252)

| | 설명 |
|---|---|
| **비유로 말하면** | 일기장 대신 **주제별 스크랩북**. 시간 순서가 아니라 "이 주제와 관련된 기억"만 꺼내온다. |
| **정확히 말하면** | 대화 내용을 **벡터 임베딩으로 변환**하여 Vector Store에 저장하고, 시간 순서가 아닌 **의미적으로 가장 관련성 높은 과거 대화**를 검색하여 컨텍스트에 포함하는 방식. |

**언제 쓰나**
- 현재 대화와 **관련된 기억만 선택적으로** 활용하고자 할 때
- **장기 기억(Long-term Memory)** 이나 특정 주제에 대한 심층적인 대화에 매우 효과적

**의존성 (p244)**

```xml
<dependency>
    <groupId>org.springframework.ai</groupId>
    <artifactId>spring-ai-starter-vector-store-pgvector</artifactId>
</dependency>
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-jdbc</artifactId>
</dependency>
<dependency>
    <groupId>org.springframework.ai</groupId>
    <artifactId>spring-ai-vector-store-advisor</artifactId>
</dependency>
<dependency>
    <groupId>org.springframework.ai</groupId>
    <artifactId>spring-ai-rag</artifactId>
</dependency>
```

**전용 VectorStore Bean 분리 (p245, p249)** ⭐

RAG용 문서 벡터와 ChatMemory용 대화 벡터가 **같은 테이블에 섞이면 안 되므로** 별도 Bean으로 분리한다.

```java
import org.springframework.ai.embedding.EmbeddingModel;
import org.springframework.ai.vectorstore.VectorStore;
import org.springframework.ai.vectorstore.pgvector.PgVectorStore;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.jdbc.core.JdbcTemplate;

/**
 * ChatMemory 전용 VectorStore Bean을 생성하는 Configuration 클래스
 */
@Configuration
public class VectorStoreConfig {

    @Bean
    @Qualifier("chatMemoryVectorStore")
    public VectorStore chatMemoryVectorStore(JdbcTemplate jdbcTemplate,
                                             EmbeddingModel embeddingModel) {
        return PgVectorStore.builder(jdbcTemplate, embeddingModel)
                .schemaName("public")
                .vectorTableName("chat_memory_vector_store")   // ← 테이블 분리
                .initializeSchema(true)
                .build();
    }
}
```

**VectorStoreChatMemoryAdvisor 적용 (p246, p250)**

```java
@Service
public class VectorStoreChatMemoryService {

    private ChatClient chatClient;

    public VectorStoreChatMemoryService(
            @Qualifier("chatMemoryVectorStore") VectorStore vectorStore,
            ChatClient.Builder chatClientBuilder) {

        this.chatClient = chatClientBuilder
            .defaultAdvisors(
                    VectorStoreChatMemoryAdvisor.builder(vectorStore).build(),
                    new SimpleLoggerAdvisor())
            .build();
    }

    public String chat(String userText, String conversationId) {
        return chatClient.prompt()
                .user(userText)
                .advisors(a -> a.param(ChatMemory.CONVERSATION_ID, conversationId))
                .call()
                .content();
    }
}
```

**Controller 등록 (p251)**

```java
private final VectorStoreChatMemoryService vectorStoreChatMemoryService;   // 생성자 주입

/**
 * VectorStoreChatMemoryAdvisor 기반 ChatMemory 답변을 반환한다.
 */
@GetMapping("/vector")
public Map<String, Object> vectorStoreChatMemory(@RequestParam String question,
                                                 HttpSession session) {
    String answer = vectorStoreChatMemoryService.chat(question, session.getId());
    return Map.of("question", question, "answer", answer);
}
```

## 4-8. MessageChatMemory vs VectorStoreChatMemory (p247~p248) ⭐⭐ 시험 단골

| 항목 | **MessageChatMemoryAdvisor** | **VectorStoreChatMemoryAdvisor** |
|---|---|---|
| **기억 형태** | 단기 기억 (Working Memory) | 장기 기억 (Semantic Memory) |
| **저장 위치** | 다양한 `ChatMemoryRepository` | Vector Store (PGVector, Weaviate 등) |
| **LLM 전달 방식** | 대화 **원문 전체/일부**를 Prompt에 삽입 | **의미 기반으로 검색된 메시지만** 삽입 |
| **회상 능력** | **정확한 문장 회상 매우 강함** | 의미 매칭만 가능, 정교한 회상 불가 |
| **토큰 소비** | 많음 (대화가 길어짐) | 적음 (필요한 메시지만 전달) |
| **저장 한계** | 토큰 제한 → 오래된 내용 삭제 | 사실상 무제한 |
| **적합한 질문** | "내가 뭐라고 했지?" | "이전 주제 다시 설명해줘" |
| **Assistant 메시지 포함** | 원문 저장 | embedding 저장 |
| **활용 목적** | 대화 흐름 이어가기 | 주제 기반 회상 |

**처리 속도 및 비용 (p248)**

| 구분 | MessageChatMemoryAdvisor | VectorStoreChatMemoryAdvisor |
|---|---|---|
| **LLM 호출 시 처리 속도** | **빠름** — 검색 과정 없이 단순 메모리 접근 | 상대적으로 **느림** — 검색(Top-K Retrieval) + embedding 비교 필요 |
| **Embedding 생성 비용** | **없음** | 메시지당 1회 embedding 필요 → LLM embedding token 비용 발생 + CPU 비용 증가 |
| **Embedding 저장 비용** | **없음** | 저장 공간 필요 (PGVector, Qdrant 등) |
| **Vector Store 검색 비용** | **없음** | 벡터 유사도 검색 비용 발생 (cosine similarity, HNSW 등) |
| **최적화 포인트** | 최근 N개 윈도우 크기 조절 | topK / threshold 조절 |

> ✅ **실무 결론**: 짧은 세션이면 **MessageChatMemory**, 며칠~몇 달에 걸친 개인화 대화가 필요하면 **VectorStoreChatMemory**. 둘을 **함께** 쓰기도 한다.

**🧪 실습 체크리스트 (p239~p242, p249~p252)**
- [ ] `01.training code/08.chat-memory` — Auto Configuration 되는 기본 ChatMemory 코드 리뷰
- [ ] Console에서 Spring AI 로그 확인 → **Request Prompt에 UserMessage/AssistantMessage 기억이 포함**되는지
- [ ] `MessageWindowChatMemory`를 직접 생성하고 `maxMessages(3)`으로 적용 → 3개 넘으면 오래된 게 사라지는지 확인
  ```java
  public MessageChatMemoryService(ChatClient.Builder chatClientBuilder, ChatMemory chatMemory) {
      // 최근 3개의 메시지만 유지하는 윈도우 방식 채팅 메모리
      MessageWindowChatMemory windowMemory = MessageWindowChatMemory.builder()
          .maxMessages(3)
          .build();

      this.chatClient = chatClientBuilder
          .defaultAdvisors(MessageChatMemoryAdvisor.builder(windowMemory).build())
          .build();
  }
  ```
- [ ] `VectorStoreChatMemoryService.java`를 직접 만들어 `VectorStoreChatMemoryAdvisor` 적용
- [ ] DBeaver에서 `chat_memory_vector_store` 테이블 확인

---

# 5. Tool Calling

> 📍 **p253~p279** | 외부 시스템의 기능을 호출하기 위한 패턴

## 5-1. Tool Calling이란 (p254)

| | 설명 |
|---|---|
| **비유로 말하면** | LLM에게 **리모컨 목록**을 주는 것. LLM은 버튼을 직접 누르지 않고 "3번 리모컨의 '켜기' 버튼을 눌러줘"라고 말할 뿐이고, **실제로 누르는 건 Spring AI**다. |
| **정확히 말하면** | AI 모델이 외부 시스템의 기능(Tool)을 호출해서 자신의 능력을 확장하기 위한 기술/패턴. **Function Call**이라고도 불림. |

> ⭐ **가장 중요한 오해 정정**: **LLM은 Tool을 실행하지 않는다.** LLM은 "어떤 Tool을 어떤 인자로 부를지"만 **JSON으로 알려주고**, 실제 메서드 실행은 **Spring AI(애플리케이션)** 가 한다.

## 5-2. 역할 분담 (p256) ⭐⭐

```plain text
[ p256 — Tool Calling 동작 흐름 ]

              ┌────────┐
              │  Tool  │  ← 실제 Java 메서드
              └───▲─┬──┘
              ③  │ │ ④
   ┌──────────────┼─┼─────────────┐
   │  Spring AI   │ ▼             │        ⑥   ┌───────────────┐
   │        ┌─────┴──────────┐    ├───────────►│ Chat Response │
┌──┴────────┤ Dispatch Tool  │    │            └───────────────┘
│Chat Request│ Call Requests │    │
│┌──────────┐└──▲─────┬──────┘    │
││Tool Def. │   │     │           │
│└──────────┘ ② │     │ ⑤         │
│ ·name      ┌──┴─────▼───────────┤
│ ·description│      AI Model     │
│ ·input schema└──────────────────┘
└────────────┘
       ①
```

| 주체 | 하는 일 |
|---|---|
| **LLM** | · 특정 작업을 수행하기 위해 **도구 호출을 요청**하고<br>· 필요한 **매개 변수만을 추론**해서 Spring AI에 제공 (Tool Definition 기반) |
| **애플리케이션 (Spring AI)** | · **도구를 정의**하고, 도구 목록을 LLM에게 전달<br>· LLM 도구 호출 요청을 처리하는 데 유용한 API 제공<br>· 도구 호출을 위한 인터페이스와 어노테이션 제공<br>· LLM이 도구 호출을 요청하면 **해당 요청을 메서드로 매핑**한 뒤 결과를 다시 LLM에 전달하는 흐름도 **자동 처리** |

## 5-3. Tool Calling 3요소 (p257)

모델이 Tool을 사용할 수 있도록, 채팅 요청에 **Tool 정의**를 포함한다. 각 Tool 정의는 3가지로 구성된다.

| 요소 | 설명 |
|---|---|
| **Name** | 모델이 호출할 Tool을 식별하기 위한 **고유 이름** |
| **description** | 어떤 작업을 수행하는 Tool인지 **설명** |
| **Input Param Schema** | Tool 호출 시 필요한 입력 값의 구조 (**JSON Schema**) |

> ⚠️ **description이 곧 성능이다.** LLM은 오직 description만 읽고 Tool을 고른다. 애매하게 쓰면 엉뚱한 Tool을 부른다.

## 5-4. 5단계 흐름 (p258) ⭐ 시험 단골

| 단계 | 주체 | 내용 |
|---|---|---|
| **①** | 사용자 | 사용자 요청: "오늘 부산 날씨는 어때?" |
| **②** | LLM | 모델은 **스스로 답할 수 없음을 인지**하고, 전달받은 tool/list의 `getCurrentWeather` Tool 호출을 요청 |
| **③** | Spring AI | Spring AI가 `getCurrentWeather` 메서드를 **실행** |
| **④** | Spring AI → LLM | Tool의 실행 결과를 다시 모델에게 전달 |
| **⑤** | LLM | 전달받은 날씨 정보를 바탕으로 **최종 답변 생성**: "오늘 날씨가 14도로 추워요" |

## 5-5. Tool 정의 — @Tool 어노테이션 (p259~p261)

```java
@Tool(description = "도시 이름으로 현재 날씨를 조회합니다. 예: Seoul")
public String getCurrentWeather(
        @ToolParam(description = "도시 이름 (예: Seoul)", required = true) String city) {
    // ...
}
```

이것이 자동으로 아래 JSON Schema로 변환되어 LLM에게 전달된다:

```json
{
  "name": "getCurrentWeather",
  "description": "도시 이름으로 현재 날씨를 조회합니다. 예: Seoul",
  "parameters": {
    "type": "object",
    "properties": {
      "city": {
        "type": "string",
        "description": "도시 이름 (예: Seoul)"
      }
    },
    "required": ["city"]
  }
}
```

**간단한 Tool 만들기 — 시간 정보 검색 (p260)**

```java
@Component
@Slf4j
public class DateTimeTools {

    @Tool(description = "사용자의 시간대에 맞는 현재 날짜와 시간 정보를 제공합니다.")
    public String getCurrentDateTime(
            @ToolParam(description = "지역명", required = true) String regionName) {

        String nowTime = LocalDateTime.now()
                .atZone(LocaleContextHolder.getTimeZone().toZoneId())
                .toString();
        log.info("현재 시간: {}", nowTime);
        return nowTime;
    }
}
```

> 💡 `@Tool`의 description은 **이 메소드가 어떤 기능을 제공하는지 설명**하며, 이 정보는 **LLM에 `ToolDefinition`으로 Prompt에 포함되어** 전달된다.

**ChatClient에 Tool 등록 (p261)**

```java
@Autowired
private final DateTimeTools dateTimeTools;

return this.chatClient.prompt()
        .advisors(a -> a.param(ChatMemory.CONVERSATION_ID, session.getId()))
        .user(request)
        .tools(dateTimeTools, fileSystemTool, weatherTools)   // ← 여러 Tool 객체를 한 번에
        .call()
        .content();
```

## 5-6. 프로토콜 상세 — 3개의 JSON (p262~p267) ⭐⭐

**Step 1. Spring AI → LLM: 사용자 질문 + Tool Definitions (p264)**

```java
// Tool 정의 정보 (LLM에게 사전에 전달)
public final class ToolDefinition {
    private final String name;          // LLM에게 알려주는 메소드 이름
    private final String description;   // LLM이 이해할 수 있는 메소드 설명
    private final String inputSchema;   // 입력 파라미터의 JSON Schema
}
```

```json
{
  "model": "gpt-4o",
  "messages": [
    { "role": "system", "content": "필요하면 도구를 사용해." },
    { "role": "user",   "content": "부산 현재 기온 알려줘" }
  ],
  "tools": [
    {
      "type": "function",
      "function": {
        "name": "getCurrentWeather",
        "description": "도시 이름으로 현재 날씨를 조회합니다. 예: Seoul",
        "parameters": { "type": "object", "properties": { "city": { "type": "string" } } }
      }
    }
  ]
}
```

**Step 2. LLM → Spring AI: Tool Request (AssistantMessage) (p265, p293)**

```json
{
    "role": "assistant",
    "content": null,
    "tool_calls": [
      {
        "id": "call_1",
        "type": "function",
        "function": {
          "name": "getCurrentWeather",
          "arguments": "{\"city\":\"Busan\"}"
        }
      }
    ]
}
```

> ⭐ `content`가 **null**이고 `tool_calls`가 채워져 있으면 "도구를 써 달라"는 뜻이다.

**Step 3. Spring AI 내부에서 Tool 메서드 호출 (p266)**

```java
@Tool(description = "도시 이름으로 현재 날씨를 조회합니다. 예: Seoul")
public String getCurrentWeather(
        @ToolParam(description = "도시 이름 (예: Seoul)", required = true) String city) {

    log.info("날씨 조회 요청 - 도시: {}", city);

    String result = webClient.get()
            .uri(uriBuilder -> uriBuilder
                    .path(weatherApiPath)
                    .queryParam("q", city)
                    .queryParam("appid", weatherApiKey)     // ← 환경변수/설정에서 주입
                    .queryParam("units", "metric")
                    .queryParam("lang", "kr")
                    .build())
            .retrieve()
            .bodyToMono(String.class)
            .block();

    return result;
}
```

**Step 4. Spring AI → LLM: ToolResponseMessage (p267)**

```json
{
    "role": "tool",
    "tool_call_id": "call_1",
    "name": "getWeather",
    "content": "{\"temp\":14}"
}
```

> ⚠️ **`tool_call_id`는 LLM의 Tool Request `tool_calls[].id`와 반드시 매칭되어야 한다.** 여러 Tool을 병렬 호출했을 때 어떤 응답이 어떤 요청의 답인지 구분하는 유일한 수단이다.

**Step 5. LLM → Spring AI: 최종 자연어 답변 (p267)**

```json
{
    "role": "assistant",
    "content": "부산의 현재 기온은 14°C 입니다."
}
```

> ⭐ **총 LLM 호출은 2회다.** ① Tool 선택을 위한 호출 ② Tool 결과를 받아 자연어로 정리하는 호출. 이 때문에 Tool Calling은 일반 대화보다 느리고 비싸다.

## 5-7. 🧪 실습 — DateTimeTool 코드 리뷰 (p268)

`01.training code/09.tool`
- [ ] 현재 날짜/시간 검색과 알람 설정 기능 Tools 코드 실행 및 동작 원리 검토
- [ ] Spring Boot 실행 → 접속
- [ ] 새로운 파일 만들어보기
- [ ] UI에서 질문 후 **어떤 도구가 호출되는지 Console 로그로 확인**

## 5-8. 🧪 실습 — OpenWeatherMap을 도구화하기 (p269~p279)

**① API Key 발급 (p270~p272)**
`https://home.openweathermap.org/` — 분당 최대 60회, 월 최대 1,000,000회 무료

제공 API:
- 현재 날씨 (Current Weather API)
- 3시간 단위 / 5일 일기예보 (5 day / 3 hour Forecast)
- 대기 오염 정보 (Air Pollution API)
- 기본 날씨 지도 레이어 (Weather Maps 1.0)
- 위치 좌표 변환 (Geocoding API)

발급 절차:
1. 접속 후 계정 생성 및 로그인
2. 계정 생성 시 회사는 SK, 목적은 Other 선택
3. 등록한 메일로 승인 메일 확인 (스팸 메일함도 확인)
4. Weather APIs → Get API Key → API Keys 메뉴에서 Key 복사

**② curl로 먼저 확인 (p273~p274)**

```bash
#!/bin/bash
# weather.sh
PATH_URI="/data/2.5/weather"
QUERY="q=Seoul&units=metric&lang=kr"
API_KEY="${OPENWEATHER_API_KEY}"     # ← 환경변수로 주입 (하드코딩 금지)

curl -s -X GET "https://api.openweathermap.org${PATH_URI}?${QUERY}&appid=${API_KEY}" | jq
```

```bash
export OPENWEATHER_API_KEY=발급받은_본인_키 && chmod +x weather.sh && ./weather.sh
```

> ⚠️ **보안 주의**: 원문 p273의 `weather.sh`에는 **API Key 문자열이 그대로 하드코딩**되어 있습니다.
> 그 키를 **그대로 사용하거나 커밋하지 마세요.** 위처럼 환경변수(`${OPENWEATHER_API_KEY}`)로 바꿔서 쓰세요.
> Spring 쪽도 `application.yaml`에 `weather.api-key: ${OPENWEATHER_API_KEY}` 형태로 주입할 것.

**③ 응답 필드 해석 (p275)**

| 필드 경로 | 값 (예시) | 의미 |
|---|---|---|
| `weather[0]` | — | 날씨 상태 요약 |
| `weather[0].main` | `"Clouds"` | Group 단위의 날씨 상태 (Clear, Rain, Clouds, Snow) |
| `weather[0].description` | `"온흐림"` | 상세 날씨 설명 (`lang=kr` 옵션이 적용된 결과) |
| `weather[0].icon` | `"04d"` | 날씨 아이콘 ID (OpenWeatherMap 이미지 URL 생성용) |
| `main.temp` | `14.2` | 현재 기온 (`units=metric`이므로 섭씨) |
| `main.feels_like` | `13.1` | 체감 온도 |
| `coord.lon` / `coord.lat` | `126.9778` / `37.5683` | 좌표 |

**④ WeatherTools.java 만들기 (p276)**

```java
@Component
@Slf4j
public class WeatherTools {

    @Value("${weather.api-key}")
    private String weatherApiKey;          // application.yaml → ${OPENWEATHER_API_KEY}

    private final WebClient webClient = WebClient.create("https://api.openweathermap.org");

    /**
     * 도시 이름으로 현재 날씨를 조회합니다.
     * @param city 도시 이름 (예: Seoul, Busan)
     * @return 날씨 정보 JSON 문자열
     */
    @Tool(description = "도시 이름으로 현재 날씨를 조회합니다. 예: Seoul")
    public String getCurrentWeather(
            @ToolParam(description = "도시 이름 (예: Seoul)", required = true) String city) {

        return webClient.get()
                .uri(uriBuilder -> uriBuilder
                        .path("/data/2.5/weather")
                        .queryParam("q", city)
                        .queryParam("appid", weatherApiKey)
                        .queryParam("units", "metric")
                        .queryParam("lang", "kr")
                        .build())
                .retrieve()
                .bodyToMono(String.class)
                .block();
    }
}
```

**⑤ ChatController에 등록 (p277)**

```java
@Autowired
private WeatherTools weatherTools;

@GetMapping("/ai")
public String chat(@RequestParam String request, HttpSession session) {
    return this.chatClient.prompt()
            .advisors(a -> a.param(ChatMemory.CONVERSATION_ID, session.getId()))
            .user(request)
            .tools(dateTimeTools, fileSystemTool, weatherTools)
            .call()
            .content();
}
```

**⑥ 검증 체크리스트 (p278~p279)**
- [ ] Spring Boot 실행 → `localhost:8080` 접속
- [ ] UI에서 질문 → **어떤 도구가 호출되는지 Console 로그 확인**
- [ ] **두 가지 도구를 복합적으로 사용하는 질문** 실행
  - 사전 조건: `weather.txt` 파일을 만들고 "캐나다 토론토 날씨와 서울 날씨를 알려줘"라는 내용을 넣어두기
  - → `FileSystemTool`(파일 읽기) + `WeatherTool`(날씨 조회) 두 개가 **순차 호출**되는지 확인
- [ ] 자신만의 새로운 도구를 하나 추가해보기 (p279)

---

## ★ 전체 흐름 한 장 요약

```plain text
╔══════════════════════════════════════════════════════════════════════════════╗
║              Spring AI 2일차 — LLM을 외부 세계와 연결하는 3가지 축              ║
╚══════════════════════════════════════════════════════════════════════════════╝

              LLM의 3대 한계: 지식 단절 · 환각 · 컨텍스트 부재
                                  │
        ┌─────────────────────────┼─────────────────────────┐
        ▼                         ▼                         ▼
  ① Retrieval (RAG)         ③ Memory                  ② Tool Calling
  "사내 지식을 붙인다"        "대화를 기억한다"           "실제로 일을 한다"


═══ ① RAG ═══════════════════════════════════════════════════════════════════

 [Offline — ETL, 미리 1번]
   Source ──► DocumentReader ──► DocumentTransformer ──► DocumentWriter ──► pgVector
             (Supplier)          (Function)              (Consumer)
              TextReader          TokenTextSplitter       VectorStore.add()
              PagePdfReader       chunkSize=800

 [Runtime — 질문마다]
   질문 ──► ① Pre-Retrieval ──► ② Retrieval ──► ③ Post-Retrieval ──► ④ Generation
            RewriteQuery         VectorStore      DocumentPost         Contextual
            CompressionQuery     Document         Processors           QueryAugmenter
            MultiQueryExpander   Retriever        (Optional)           (Optional)
              ↑LLM 추가 호출!

   간단히 쓰려면 → QuestionAnswerAdvisor 한 줄
   정교하게 → RetrievalAugmentationAdvisor 4단계 조립


═══ ③ ChatMemory ════════════════════════════════════════════════════════════

  ChatMemory (add/get/clear)
     └─ MessageWindowChatMemory (maxMessages 기본 20)
             └─ ChatMemoryRepository
                    ├─ InMemory  (로컬/테스트)
                    ├─ Redis     (MSA/분산, TTL)
                    ├─ Jdbc      (영속 관리)
                    └─ MongoDB   (JSON Doc)

  MessageChatMemoryAdvisor       vs    VectorStoreChatMemoryAdvisor
  단기·원문·정확한 회상·토큰↑            장기·의미검색·토큰↓·회상 부정확


═══ ② Tool Calling ══════════════════════════════════════════════════════════

  ① Spring AI → LLM : 질문 + tools[] (name/description/inputSchema)
  ② LLM → Spring AI : assistant { content:null, tool_calls:[{id, name, arguments}] }
  ③ Spring AI       : @Tool 붙은 Java 메서드를 실제로 실행
  ④ Spring AI → LLM : tool { tool_call_id, name, content }
  ⑤ LLM → Spring AI : assistant { content: "부산의 현재 기온은 14°C 입니다." }

  ⚠ LLM은 실행하지 않는다. "무엇을 어떤 인자로 부를지"만 말한다.
  ⚠ LLM 호출은 총 2회 (선택 + 정리)
```

---

## ★ 시험/면접 대비 핵심 문답

| # | 질문 | 답 |
|---|---|---|
| 1 | LLM의 3가지 한계는? | **지식 단절(Knowledge Cutoff)** · **환각(Hallucination)** · **컨텍스트 부재(Lack of Context)** |
| 2 | 외부 세계 연결의 3가지 축은? | **Retrieval(RAG)** — 지식 / **Tool Calling** — 행동 / **Memory** — 맥락 |
| 3 | RAG 4단계는? | 질문 → **Retrieve**(Vector DB 검색) → **Augment**(Prompt에 Context 추가) → **Generate**(LLM 답변) |
| 4 | ETL과 RAG는 각각 언제 실행되나? | **ETL은 Offline(사전 적재)**, **RAG는 Runtime(질의 시점)** |
| 5 | ETL 3단계와 대응하는 Java 함수형 인터페이스는? | `DocumentReader` = **`Supplier<List<Document>>`** / `DocumentTransformer` = **`Function<List<Document>,List<Document>>`** / `DocumentWriter` = **`Consumer<List<Document>>`** |
| 6 | `TextReader`로 읽으면 Document가 몇 개 생기나? | **1개.** `PagePdfDocumentReader`는 **페이지 수만큼** |
| 7 | Big Document의 2가지 문제는? | **임베딩 벡터의 의미 희석** / **관련 없는 노이즈 포함 → 유사도 품질 저하 + 토큰 사용량 증가** |
| 8 | `TokenTextSplitter`의 `chunkSize` 기본값은? | **800 토큰**. `minChunkSizeChars`=350, `minChunkLengthToEmbed`=5, `maxNumChunks`=10,000, `keepSeparator`=true |
| 9 | Chunk로 나누는 이유 5가지는? | 프롬프트 토큰 한계 대응 / 검색 정확도 향상 / 비용·지연 감소 / 노이즈 감소 / 재적재·업데이트 용이 |
| 10 | `VectorStore`와 `DocumentWriter`의 관계는? | **`VectorStore`가 `DocumentWriter`를 상속한다.** `write(List<Document>)` ↔ `add(List<Document>)` |
| 11 | `QuestionAnswerAdvisor`와 `RetrievalAugmentationAdvisor`의 차이는? | 전자는 **VectorStore+SearchRequest 간단 결합**(빠른 프로토타입), 후자는 **4단계 파이프라인 모듈 조립**(Hybrid Search, Query Rewrite, Reranking 등 고도화) |
| 12 | RetrievalAugmentationAdvisor의 4단계와 필수 여부는? | ① **Pre-Retrieval**(필수 아님, 품질↑) ② **Retrieval**(필수) ③ **Post-Retrieval**(Optional) ④ **Generation**(Optional) |
| 13 | Pre-Retrieval 4가지 모듈과 각각의 역할은? | `RewriteQueryTransformer`(장황→간결) / `CompressionQueryTransformer`(모호→독립 질문, **ChatMemory 필수**) / `MultiQueryExpander`(1→N개 확장) / `TranslationQueryTransformer`(언어 변환) |
| 14 | `QueryTransformer`와 `QueryExpander`의 시그니처 차이는? | `QueryTransformer extends Function<Query, Query>` (**1→1**) / `QueryExpander extends Function<Query, List<Query>>` (**1→N**) |
| 15 | QueryTransformer용 ChatClient를 왜 따로 만드나? | RAG Advisor가 붙은 ChatClient를 그대로 쓰면 **무한 재귀**가 발생하기 때문 |
| 16 | `allowEmptyContext(false)`의 의미는? | 검색 결과가 **없으면 LLM에 묻지 않고** `emptyContextPromptTemplate`으로 거절한다. `true`면 컨텍스트 없이 답하므로 **환각 위험** |
| 17 | "Lost in the Middle" 문제란? | LLM이 긴 컨텍스트의 **처음과 끝은 잘 보지만 가운데를 놓치는** 현상. Post-Retrieval의 재정렬·압축으로 완화 |
| 18 | LLM이 대화를 기억하는 원리는? | **기억하지 못한다.** LLM API는 stateless이며, 애플리케이션이 **이전 메시지를 매번 다시 보내주는 것** |
| 19 | `ChatMemory` 인터페이스의 3개 메서드는? | `add(conversationId, messages)` / `get(conversationId)` / `clear(conversationId)` |
| 20 | 기본 ChatMemory 구현체와 기본 저장소, 기본 윈도우 크기는? | `MessageWindowChatMemory` + `InMemoryChatMemoryRepository`, **maxMessages = 20** |
| 21 | `ChatMemoryRepository` 4종과 선택 기준은? | `InMemory`(로컬/테스트) / `Redis`(**MSA·Multi-Node·TTL**) / `Jdbc`(영속 데이터 엄격 관리) / `MongoDB`(JSON Document) |
| 22 | MessageChatMemory vs VectorStoreChatMemory 핵심 차이 3가지는? | ① 단기(Working) vs 장기(Semantic) ② 원문 전체 삽입 vs 의미 검색된 것만 삽입 ③ 정확한 문장 회상 강함 vs 의미 매칭만 가능 |
| 23 | VectorStoreChatMemory가 느리고 비싼 이유는? | 메시지마다 **embedding 생성**(토큰 비용 + CPU) → **저장 공간** → **벡터 유사도 검색**(cosine/HNSW) 비용까지 발생 |
| 24 | ChatMemory용 VectorStore Bean을 왜 별도로 만드나? | RAG 문서 벡터와 대화 벡터가 **같은 테이블에 섞이면 안 되므로** `@Qualifier`로 분리하고 `vectorTableName`을 다르게 지정 |
| 25 | `ChatMemory.CONVERSATION_ID`는 무엇인가? | Advisor Context에 넘기는 **키 상수**. 보통 `HttpSession.getId()`를 값으로 넘겨 세션별 대화를 구분한다 |
| 26 | Tool Calling에서 LLM이 실제로 하는 일은? | **Tool을 실행하지 않는다.** "어떤 Tool을 어떤 인자로 부를지"를 JSON(`tool_calls`)으로 알려줄 뿐이고, **실행은 Spring AI**가 한다 |
| 27 | Tool 정의의 3요소는? | **Name**(고유 이름) · **description**(무슨 일을 하는지) · **Input Param Schema**(JSON Schema) |
| 28 | Tool Calling 5단계는? | ① 사용자 요청 ② LLM이 Tool 호출 요청 ③ Spring AI가 메서드 실행 ④ 결과를 LLM에 전달 ⑤ LLM이 최종 자연어 답변 생성 |
| 29 | `tool_call_id`는 왜 필요한가? | LLM의 `tool_calls[].id`와 매칭되어야 **어떤 응답이 어떤 요청의 답인지** 구분할 수 있다. 병렬 Tool 호출 시 필수 |
| 30 | Tool Calling 1회에 LLM은 몇 번 호출되나? | **2회.** ① Tool 선택을 위한 호출 ② Tool 결과를 자연어로 정리하는 호출 |
| 31 | Tool 성능을 좌우하는 것은? | **`description`.** LLM은 오직 description만 읽고 Tool을 고르므로, 애매하면 엉뚱한 Tool을 호출한다 |
| 32 | `AssistantMessage`의 `content`가 null이면? | **Tool 호출 요청**이라는 뜻. `tool_calls` 배열에 호출할 Tool 정보가 들어 있다 |

**🧩 Quiz**

<details>
<summary>Q1. `TextReader`로 200페이지 PDF 텍스트 파일을 읽고 Transform 없이 바로 `load()` 하면?</summary>

- [x] **Document 1건**이 통째로 임베딩된다.
- [x] 다양한 주제가 하나의 벡터로 뭉개져 **의미가 희석**되고, 검색해도 항상 그 1건만 나온다.
- [x] 게다가 Embedding Model의 **최대 토큰(예: 8,192)을 초과**해 에러가 날 수 있다.
- 반드시 `TokenTextSplitter`로 `transform()` 해야 한다.
</details>

<details>
<summary>Q2. `CompressionQueryTransformer`만 넣고 `ChatMemory`를 안 붙이면?</summary>

- [x] **동작하지 않는다.** 압축의 재료가 되는 **대화 이력이 없기** 때문이다.
- [x] "대통령은?" 같은 모호한 질문이 그대로 Vector DB에 던져져 엉뚱한 문서가 나온다.
- `MessageChatMemoryAdvisor`를 함께 등록하고 `ChatMemory.CONVERSATION_ID`를 넘겨야 한다.
</details>

<details>
<summary>Q3. 아래 코드에서 무한 재귀가 발생하는 이유는?</summary>

```java
ChatClient.Builder b = ChatClient.builder(chatModel)
        .defaultAdvisors(retrievalAdvisor);          // RAG Advisor

RetrievalAugmentationAdvisor retrievalAdvisor = RetrievalAugmentationAdvisor.builder()
        .queryTransformers(RewriteQueryTransformer.builder()
                .chatClientBuilder(b)                // ← 같은 builder를 재사용
                .build())
        .build();
```

- [x] QueryTransformer가 쓰는 ChatClient에 **RAG Advisor가 붙어 있어서**, 질문을 재작성하려고 LLM을 부르면 그 호출이 다시 RAG를 타고 다시 재작성을 시도한다.
- 수정: transformer 전용 `ChatClient.Builder`를 **따로** 만들고 `SimpleLoggerAdvisor` 정도만 붙인다.
</details>

<details>
<summary>Q4. `MessageWindowChatMemory.builder().maxMessages(3)` 로 설정하면 몇 턴이 유지되나?</summary>

- [x] **약 1.5턴.** User + Assistant가 각각 1 메시지로 세므로, 3개면 User/Assistant/User 정도만 남는다.
- 실습에서 이 값을 3으로 두면 "직전 질문도 잊어버리는" 현상을 눈으로 확인할 수 있다.
</details>

---

## ⚠️ 원문 용어 검증 노트

### 정정 (원문 오기)

| # | 슬라이드 | 원문 | 정정 | 비고 |
|---|---|---|---|---|
| 1 | p159 | "환각 Halluccination" | **Hallucination** | `c` 중복 |
| 2 | p173 | `.withKeepSeparator(ture)` | `.withKeepSeparator(true)` | **컴파일 실패** |
| 3 | p174 | "chunkSize를 구분자로 자를때 최소 350자 문자이후에서" | "최소 350자 이후에서" | "자 문자" 중복 |
| 4 | p175 | "재적재/업데이트 용이 … 동기화 부담 감소" | (정상) | — |
| 5 | p178~p182 | 실습 경로 `01.training code/06.rag etl` | 슬라이드마다 `06.rag-etl` / `06.rag` / `07.rag`로 혼재 | 실제 리포지토리 폴더명 확인 필요 |
| 6 | p186 | `<artifactId>pring-ai-vector-store-advisor` | `spring-ai-vector-store-advisor` | **`s` 누락 — 빌드 실패** |
| 7 | p193, p195 | "TranslationQuery**Transfo**" (문장 잘림) | `TranslationQueryTransformer` | 슬라이드 텍스트 박스 잘림 |
| 8 | p198 | "국회의원이 청렴의 의무가 있으며" | "국회의원**은** 청렴의 의무가 있으며" | 조사 오류 |
| 9 | p200 | "1. RetrievalAugmentService.java 에 RewriteQueryTransformer를 적용" — 경로 `06.rag` | p208은 같은 파일을 `07.rag`로 표기 | 경로 불일치 |
| 10 | p205 | 메서드명이 `RewriteQueryService` 인데 내용은 Compression | `CompressionQueryService` 가 적절 | 이전 슬라이드 복사 흔적 |
| 11 | p219 | "관련 없거나 **중북**된 문서를 제거" | "**중복**된" | 오타 |
| 12 | p219 | "lost in the middle 문제 **완료**" | "문제 **완화**" | 오타 (해결이 아니라 완화) |
| 13 | p225 | "Pre Retrieval과 Retrieval만 적용되**더** 있는" | "적용되**어** 있는" | 오타 |
| 14 | p231 | `.maxMessage(10)` | `.maxMessages(10)` | **복수형 — 컴파일 실패** |
| 15 | p235 | `.maxMessage(10)` | `.maxMessages(10)` | 위와 동일 |
| 16 | p237 | `advisorSpec.param(ChatMemory.CONVERSATION_ID, session.get())` | `session.getId()` | **`get()` → `getId()`** |
| 17 | p237 | `chatClient.prompt().user(userText)` 인데 파라미터는 `question` | 변수명 불일치 | **컴파일 실패** |
| 18 | p246, p250 | 클래스명 `VectorStoreService` / 파일명 `VectorStoreChatMemoryAdvisor.java` | 클래스·파일명이 서로 다름. p249/p251의 지시는 `VectorStoreChatMemoryService` | **파일명과 클래스명 불일치 — 컴파일 실패** |
| 19 | p251 | `@Autowired;` 뒤 세미콜론 + `private final` 조합 | `@Autowired`는 세미콜론 없음. `final` 필드는 **생성자 주입**만 가능 | 슬라이드 주석대로 생성자 주입으로 바꿔야 함 |
| 20 | p252 | 제목은 "VectorStoreChatMemory 적용하기"인데 본문은 MultiQueryExpander 설명 | 본문이 p215의 복사본 | 슬라이드 복사 실수 |
| 21 | p254, p256 | "특정 작업을 수행하기 **휘애**" | "**위해**" | 오타 |
| 22 | p258 | "getCurrentWeather 메서드를 실행 e.g. 2024-10-20…" | 날짜 예시는 DateTimeTool 것 | Weather 예시와 혼재 |
| 23 | p262 | "spring AI" / "sprin AI" | `Spring AI` | p264, p292에서도 "sprin AI" 반복 |
| 24 | p269, p270 | "home.weahtermap" / "OpenWeahterMap" | `openweathermap` | 오타 |
| 25 | p273 | `API_KEY="e23e2d3fd2df53fb845e"` **하드코딩** | `API_KEY="${OPENWEATHER_API_KEY}"` | **⚠️ 보안 — 아래 보완 항목 참조** |
| 26 | p276 | 파일명 `tools/WeatherTool.java`, 클래스명 `WeatherTools` | 클래스명 = 파일명이어야 함 | **컴파일 실패** |
| 27 | p312 | "WeattherTools.java" | `WeatherTools.java` | 오타 (3일차 범위) |

### 보완 (원문에 없어 추가한 설명)

| # | 항목 | 보완 내용 |
|---|---|---|
| 1 | **⚠️ API Key 하드코딩 (p273)** | 원문 `weather.sh`에 OpenWeatherMap API Key가 평문으로 박혀 있습니다. **그 키를 그대로 사용하거나 저장소에 커밋하지 마세요.** 본인 키를 발급받아 `export OPENWEATHER_API_KEY=...` 환경변수로 주입하고, Spring 쪽은 `application.yaml`에 `weather.api-key: ${OPENWEATHER_API_KEY}`로 참조하세요. 정리본의 예제 코드는 모두 환경변수 방식으로 다시 썼습니다. |
| 2 | Tool Calling의 LLM 호출 횟수 | 원문에 명시되지 않았으나 **총 2회**(선택 + 정리)다. 응답 지연과 비용이 2배가 되는 이유 |
| 3 | `TokenTextSplitter` 빌더 메서드명 | Spring AI 2.x에서는 `.withXxx()` 대신 **`.chunkSize()` / `.minChunkSizeChars()`** 형태도 지원한다. 버전에 따라 다르니 IDE 자동완성으로 확인할 것 |
| 4 | `maxMessages`의 단위 | 원문은 "메시지 수"라고만 함. **User 1개 + Assistant 1개 = 2 메시지**이므로, 20이면 약 10턴이다 |
| 5 | `FILTER_EXPRESSION` 문법 | p188의 필터 표현식은 **Spring AI의 Filter Expression DSL**이다. `category == 'spring' && year >= 2020` 같은 형태를 지원 |
| 6 | `doc.getScore()` | p220의 `do.getScore()`는 오타로 보이며, `Document`의 유사도 점수 접근자다. 버전에 따라 `getScore()` 또는 metadata의 `distance` 키로 접근한다 |
| 7 | Pre-Retrieval의 비용 | 원문에 언급 없음. **모듈 1개당 LLM 호출 1회가 추가**된다. Rewrite + Compression + MultiQuery를 모두 켜면 질문 1건당 LLM 호출이 5회(3+1선택+1정리)까지 늘어날 수 있다 |
| 8 | `VectorStoreDocumentRetriever` 필터 | `filterExpression()` 으로 metadata 필터를 걸 수 있다. 원문에는 `vectorStore`, `similarityThreshold`, `topK`만 나옴 |
| 9 | Redis TTL | p234에서 "자동 만료(TTL) 필요 시"라고만 언급. 실제 설정은 `spring.ai.chat.memory.repository.redis.time-to-live` 프로퍼티로 한다 |

---

> 📌 **이전 문서**: [1일차 — Spring AI 기초](./01_SpringAI_Day1_기초_정리.md)
> 📌 **다음 문서**: [3일차 — MCP · Agent](./03_SpringAI_Day3_MCP와_Agent_정리.md)
