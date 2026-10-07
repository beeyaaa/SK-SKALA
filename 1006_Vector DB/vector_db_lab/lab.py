# ============================================================
# 작성자   : Codex (홍은비 실습 보조)
# 작성일자 : 2026-10-07
# 내용     : [실습 1·2] PDF 벡터 검색과 Hybrid Search 비교
#            - PDF 로딩·청킹·BGE-M3 임베딩 후 FAISS/Qdrant 저장
#            - Dense·BM25·RRF·Reranker 검색 결과 비교
# 변경내역 :
#            - 2026-10-07  Codex  실습 코드 및 단계별 주석 작성
# ============================================================
"""SK-SKALA Vector DB labs 1 and 2. Run `python lab.py --help`."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

# - Transformers의 TensorFlow 경로를 끄고 시스템 Keras 3와의 충돌 방지
os.environ.setdefault("USE_TF", "0")

ROOT = Path(__file__).resolve().parent
PDF_DIR = ROOT.parent / "Vector DB_실습_PDF"
DATA_DIR = ROOT / "data"
COLLECTION = "skala_vector_db_1006"
DIM = 1024

# - 모델·라이브러리 캐시를 실습 폴더에 저장
# -> 실행 환경에서 사용자 홈 캐시에 쓸 수 없어도 모델 로딩 가능
for key, path in {
    "HF_HOME": DATA_DIR / "hf_cache",
    "MPLCONFIGDIR": DATA_DIR / "mpl_cache",
    "XDG_CACHE_HOME": DATA_DIR / "cache",
}.items():
    if key not in os.environ:
        path.mkdir(parents=True, exist_ok=True)
        os.environ[key] = str(path)


# 1) 실습 PDF 선택 및 텍스트 청킹
def document_paths(all_pdfs: bool) -> list[Path]:
    """유형별 PDF 5개 또는 실습 폴더의 전체 PDF 목록 반환."""
    paths = sorted(PDF_DIR.glob("*.pdf"))
    if not paths:
        raise FileNotFoundError(f"PDF 파일이 없습니다: {PDF_DIR}")
    if all_pdfs:
        return paths
    # - 강의에서 사용하는 1~5번 보고서 유형별로 한 문서씩 선택
    selected = []
    for number in range(1, 6):
        matches = [p for p in paths if p.name.startswith(f"{number}. ")]
        if not matches:
            raise FileNotFoundError(f"{number}번 실습 PDF가 없습니다")
        if number == 1:
            # - SPRi Brief: 파일명 끝의 YYYYMM으로 가장 최신 월 선택
            # -> 사전식 정렬로 8월이 12월보다 뒤에 오는 오류 방지
            matches.sort(key=lambda p: int(re.search(r"_(\d{6})\.pdf$", p.name).group(1)))
        selected.append(matches[-1])
    return selected


def make_chunks(paths: list[Path]) -> list[dict]:
    """PDF 페이지별 텍스트를 추출하고 500자 안팎의 청크로 분할."""
    import pymupdf
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    # - 청크를 50자씩 겹쳐 페이지 내 분할 경계의 문맥 보존
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500, chunk_overlap=50, separators=["\n\n", "\n", ".", " ", ""]
    )
    chunks = []
    for path in paths:
        with pymupdf.open(path) as doc:
            for page_number, page in enumerate(doc, start=1):
                for text in splitter.split_text(page.get_text()):
                    if text.strip():
                        # - 원문·문서명·페이지 번호를 함께 보관
                        # -> Qdrant 필터 검색과 결과 출처 확인에 사용
                        chunks.append({
                            "id": len(chunks), "text": text,
                            "source": path.name, "page": page_number,
                        })
        print(f"로딩: {path.name}", flush=True)
    if not chunks:
        raise ValueError("추출된 텍스트가 없습니다. 이미지 PDF라면 OCR이 필요합니다.")
    return chunks


# 2) BGE-M3 임베딩 모델 로딩 및 벡터 생성
def embedding_model():
    """BGE-M3 모델을 CPU에서도 실행할 수 있는 설정으로 로딩."""
    from FlagEmbedding import BGEM3FlagModel
    # - CPU에서 지원되지 않는 fp16 연산 방지
    return BGEM3FlagModel(model_location("BAAI/bge-m3"), use_fp16=False)


def model_location(model_id: str) -> str:
    """모델 캐시가 있으면 로컬 경로를, 없으면 다운로드용 모델 ID를 반환."""
    from huggingface_hub import snapshot_download
    try:
        return snapshot_download(model_id, local_files_only=True)
    except FileNotFoundError:
        # -> 최초 실행에서는 모델 ID를 전달해 Hugging Face에서 다운로드
        return model_id


def encode(model, texts: list[str]):
    """텍스트를 정규화된 1024차원 BGE-M3 벡터로 변환."""
    import numpy as np
    import faiss

    vectors = np.asarray(
        model.encode(texts, batch_size=8, return_dense=True,
                     return_sparse=False, return_colbert_vecs=False)["dense_vecs"],
        dtype="float32",
    )
    if vectors.ndim != 2 or vectors.shape[1] != DIM:
        raise ValueError(f"BGE-M3 벡터 크기가 예상과 다릅니다: {vectors.shape}")
    # - FAISS 내적 검색과 Qdrant 코사인 검색의 비교 기준 통일
    faiss.normalize_L2(vectors)
    return vectors


# 3) FAISS 인덱스와 Qdrant 컬렉션 구축
def client():
    """로컬 Qdrant에 연결하고 서버 응답 확인."""
    from qdrant_client import QdrantClient
    c = QdrantClient(url="http://localhost:6333", timeout=60)
    # - 컬렉션 조회: 검색 단계 이전에 서버 연결 확인
    c.get_collections()
    return c


def ingest(args):
    """PDF 청크의 임베딩을 생성해 인덱스 구축용 파일로 저장."""
    import numpy as np

    paths = document_paths(args.all_pdfs)
    print(f"대상 PDF: {len(paths)}개", flush=True)
    chunks = make_chunks(paths)
    print(f"청크: {len(chunks)}개. BGE-M3 임베딩을 시작합니다.", flush=True)
    model = embedding_model()
    vectors = []
    # - 32개씩 임베딩해 큰 문서 세트를 한 번에 처리할 때의 메모리 부담 완화
    for start in range(0, len(chunks), 32):
        vectors.append(encode(model, [c["text"] for c in chunks[start:start + 32]]))
        print(f"임베딩: {min(start + 32, len(chunks))}/{len(chunks)}", flush=True)
    vectors = np.vstack(vectors)
    print(f"임베딩 shape: {vectors.shape}", flush=True)
    DATA_DIR.mkdir(exist_ok=True)
    np.save(DATA_DIR / "embeddings.npy", vectors)
    with (DATA_DIR / "chunks.jsonl").open("w", encoding="utf-8") as out:
        for chunk in chunks:
            out.write(json.dumps(chunk, ensure_ascii=False) + "\n")
    # - macOS에서 Torch 실행 후 FAISS HNSW 구축 시 관찰된 프로세스 충돌 회피
    # -> 임베딩을 저장하고 새 Python 프로세스에서 인덱스·컬렉션 구축
    os.execv(sys.executable, [sys.executable, str(Path(__file__).resolve()), "finalize"])


def finalize(_args):
    """저장된 임베딩으로 FAISS 인덱스와 Qdrant 컬렉션 구축."""
    import faiss
    import numpy as np
    from qdrant_client.models import VectorParams, Distance, PointStruct

    chunks = [json.loads(line) for line in (DATA_DIR / "chunks.jsonl").open(encoding="utf-8")]
    vectors = np.load(DATA_DIR / "embeddings.npy")
    if vectors.shape != (len(chunks), DIM):
        raise ValueError(f"청크와 임베딩 크기가 다릅니다: {len(chunks)}, {vectors.shape}")
    # - FAISS HNSW 인덱스를 파일로 저장해 이후 검색에서 재사용
    index = faiss.IndexHNSWFlat(DIM, 32, faiss.METRIC_INNER_PRODUCT)
    index.hnsw.efConstruction = 200
    index.add(vectors)
    faiss.write_index(index, str(DATA_DIR / "faiss.index"))

    qdrant = client()
    # - 재실행 시 이 실습의 컬렉션만 교체해 오래된 포인트가 남지 않도록 처리
    if qdrant.collection_exists(COLLECTION):
        qdrant.delete_collection(COLLECTION)
    qdrant.create_collection(
        collection_name=COLLECTION,
        vectors_config=VectorParams(size=DIM, distance=Distance.COSINE),
    )
    # - 벡터와 원문·출처·페이지 정보를 64개 단위로 함께 업로드
    for start in range(0, len(chunks), 64):
        batch = [PointStruct(id=c["id"], vector=vectors[c["id"]].tolist(),
                             payload=c) for c in chunks[start:start + 64]]
        qdrant.upsert(collection_name=COLLECTION, points=batch, wait=True)
        print(f"Qdrant 저장: {min(start + 64, len(chunks))}/{len(chunks)}", flush=True)

    print(f"완료: FAISS {index.ntotal}개, Qdrant {qdrant.count(COLLECTION, exact=True).count}개")


# 4) FAISS·Qdrant 검색 및 페이지 필터
def load_data():
    """저장된 청크와 FAISS 인덱스를 읽고 개수 일치 여부 확인."""
    import faiss

    if not (DATA_DIR / "chunks.jsonl").exists():
        raise FileNotFoundError("먼저 `python lab.py ingest`를 실행하세요")
    chunks = [json.loads(line) for line in (DATA_DIR / "chunks.jsonl").open(encoding="utf-8")]
    index = faiss.read_index(str(DATA_DIR / "faiss.index"))
    if index.ntotal != len(chunks):
        raise ValueError("FAISS 인덱스와 청크 수가 다릅니다. ingest를 다시 실행하세요")
    return chunks, index


def show(title: str, ids: list[int], chunks: list[dict]):
    """검색 순위와 청크의 문서명·페이지·본문 앞부분 출력."""
    print(f"\n[{title}]")
    for rank, i in enumerate(ids, 1):
        c = chunks[i]
        excerpt = " ".join(c["text"].split())[:110]
        print(f"{rank}. #{i} {c['source']} p.{c['page']} — {excerpt}")


def dense_ids(index, vector, count: int) -> list[int]:
    """FAISS에서 질문 벡터와 유사한 청크 ID를 순위대로 반환."""
    _, found = index.search(vector, min(count, index.ntotal))
    return [int(i) for i in found[0] if i >= 0]


def search(args):
    """같은 질문으로 FAISS·Qdrant 검색과 페이지 조건 검색 실행."""
    from qdrant_client.models import Filter, FieldCondition, Range

    model = embedding_model()
    chunks, index = load_data()
    vector = encode(model, [args.query])
    show("FAISS", dense_ids(index, vector, 5), chunks)
    qdrant = client()
    hits = qdrant.query_points(
        collection_name=COLLECTION, query=vector[0].tolist(),
        limit=5, with_payload=True,
    ).points
    print("\n[Qdrant]")
    for rank, hit in enumerate(hits, 1):
        p = hit.payload
        print(f"{rank}. score={hit.score:.3f} {p['source']} p.{p['page']} — {' '.join(p['text'].split())[:110]}")
    # - Qdrant payload의 페이지 번호로 검색 범위 제한
    filtered = qdrant.query_points(
        collection_name=COLLECTION, query=vector[0].tolist(),
        query_filter=Filter(must=[FieldCondition(key="page", range=Range(gte=args.min_page))]),
        limit=5, with_payload=True,
    ).points
    print(f"\n[Qdrant 페이지 {args.min_page} 이상 필터]")
    for rank, hit in enumerate(filtered, 1):
        p = hit.payload
        print(f"{rank}. {p['source']} p.{p['page']} — {' '.join(p['text'].split())[:110]}")
    assert all(hit.payload["page"] >= args.min_page for hit in filtered)


# 5) BM25·RRF·Reranker 검색 결과 비교
def compare(args):
    """Dense·BM25·Hybrid·Reranker의 상위 검색 결과 비교."""
    import bm25s
    from FlagEmbedding import FlagReranker

    model = embedding_model()
    chunks, index = load_data()
    texts = [c["text"] for c in chunks]
    bm25 = bm25s.BM25()
    # - Dense 검색과 동일한 청크로 BM25 키워드 인덱스 구축
    bm25.index(bm25s.tokenize(texts), show_progress=False)
    reranker = FlagReranker(model_location("BAAI/bge-reranker-v2-m3"), use_fp16=False)
    evaluation_rows = []

    for query in args.queries:
        vector = encode(model, [query])
        dense = dense_ids(index, vector, 30)
        sparse_array, _ = bm25.retrieve(bm25s.tokenize(query), k=min(30, len(chunks)), show_progress=False)
        sparse = [int(i) for i in sparse_array[0] if i >= 0]
        ranks_dense = {i: rank for rank, i in enumerate(dense, 1)}
        ranks_sparse = {i: rank for rank, i in enumerate(sparse, 1)}
        # - 점수 단위가 다른 Dense와 BM25를 원점수 대신 순위로 결합
        scores = {
            i: (1 / (60 + ranks_dense[i]) if i in ranks_dense else 0)
             + (1 / (60 + ranks_sparse[i]) if i in ranks_sparse else 0)
            for i in set(dense) | set(sparse)
        }
        hybrid = sorted(scores, key=scores.get, reverse=True)[:20]
        # - RRF로 좁힌 후보 20개를 질문·청크 쌍으로 다시 채점
        rerank_scores = reranker.compute_score([[query, chunks[i]["text"]] for i in hybrid], normalize=True)
        reranked = [i for _, i in sorted(zip(rerank_scores, hybrid), reverse=True)]
        print(f"\n질문: {query}")
        show("Dense 상위 5", dense[:5], chunks)
        show("BM25 상위 5", sparse[:5], chunks)
        show("Hybrid RRF 상위 5", hybrid[:5], chunks)
        show("Hybrid + Reranker 상위 5", reranked[:5], chunks)
        # - 단계별 검색 문맥을 저장해 생성 답변을 추가한 뒤 RAGAS 평가에 활용
        for stage, ids in [("dense", dense[:5]), ("hybrid", hybrid[:5]),
                           ("reranker", reranked[:5])]:
            evaluation_rows.append({
                "stage": stage,
                "user_input": query,
                "retrieved_contexts": [chunks[i]["text"] for i in ids],
                "response": "",
            })

    if args.json_output:
        output = Path(args.json_output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(evaluation_rows, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nRAGAS 입력 초안: {output} (ragas_eval.py로 답변 생성·평가 가능)")


# 6) 터미널 실행 명령 연결
def main():
    """ingest·finalize·search·compare 명령과 입력 인자 정의."""
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p_ingest = sub.add_parser("ingest", help="PDF → 청크 → BGE-M3 → FAISS + Qdrant")
    p_ingest.add_argument("--all-pdfs", action="store_true", help="5개 대신 폴더의 PDF 전부 사용")
    p_ingest.set_defaults(func=ingest)
    p_finalize = sub.add_parser("finalize", help=argparse.SUPPRESS)
    p_finalize.set_defaults(func=finalize)
    p_search = sub.add_parser("search", help="FAISS/Qdrant 검색 및 페이지 필터")
    p_search.add_argument("query", nargs="?", default="HBM이란 무엇인가?")
    p_search.add_argument("--min-page", type=int, default=5)
    p_search.set_defaults(func=search)
    p_compare = sub.add_parser("compare", help="Dense/BM25/Hybrid/Reranker 비교")
    p_compare.add_argument("queries", nargs="*", default=["HBM", "HBM 반도체"])
    p_compare.add_argument("--json-output", help="RAGAS 입력 초안 JSON 저장")
    p_compare.set_defaults(func=compare)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
