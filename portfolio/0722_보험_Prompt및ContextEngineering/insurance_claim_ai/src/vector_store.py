from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings

PROJECT_DIR = Path(__file__).resolve().parents[1]


COLLECTIONS = {
    "case_law": "case_law_collection",
    "statute": "statute_collection",
    "terms": "terms_collection",
}

def get_embeddings() -> OpenAIEmbeddings:
    load_dotenv()
    return OpenAIEmbeddings(
        model=os.getenv(
            "EMBEDDING_MODEL",
            "text-embedding-3-small",
        )
    )


def build_store(
    document_type: str,
    documents: list[Document],
    persist_directory: Path,
) -> Chroma:
    persist_directory.mkdir(parents=True, exist_ok=True)
    ids = [
        f"{document_type}_{index:04d}"
        for index in range(1, len(documents) + 1)
    ]
    return Chroma.from_documents(
        documents=documents,
        ids=ids,
        embedding=get_embeddings(),
        collection_name=COLLECTIONS[document_type],
        persist_directory=str(persist_directory),
    )


def load_store(document_type: str) -> Chroma:
    return Chroma(
        collection_name=COLLECTIONS[document_type],
        embedding_function=get_embeddings(),
        persist_directory=str(
            PROJECT_DIR / "vector_db" / document_type
        ),
    )


def as_retriever(document_type: str, k: int = 5):
    return load_store(document_type).as_retriever(
        search_kwargs={"k": k}
    )
