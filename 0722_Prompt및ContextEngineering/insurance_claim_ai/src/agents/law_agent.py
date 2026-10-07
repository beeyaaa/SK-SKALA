from __future__ import annotations

from datetime import date
import re

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable

from src.vector_store import as_retriever
from src.schemas import AccidentFacts, LawAgentOutput


def _effective_on(document: Document, accident_date: str) -> bool:
    effective_date = document.metadata.get("effective_date")
    if not effective_date:
        return True
    return date.fromisoformat(effective_date) <= date.fromisoformat(accident_date)


def _context(documents: list[Document]) -> str:
    blocks = []
    for index, document in enumerate(documents, start=1):
        metadata = document.metadata
        blocks.append(
            f"[검색조문 {index}]\n"
            f"법률: {metadata.get('law_name')}\n"
            f"시행일: {metadata.get('effective_date')}\n"
            f"조문: {metadata.get('article')} {metadata.get('article_title')}\n"
            f"원본 파일: {metadata.get('source_file')}\n"
            f"PDF 페이지: {metadata.get('pdf_page')}\n"
            f"원문:\n{document.page_content}"
        )
    return "\n\n".join(blocks)


class LawAgent:
    def __init__(self, llm: Runnable) -> None:
        self.retriever = as_retriever("statute", k=8)
        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                "당신은 자동차 사고 관련 법률 검색 보조 Agent다. "
                "검색된 조문만 사용하고 조문을 만들지 않는다. "
                "law_name, article, article_title, source_file, pdf_page는 "
                "검색조문의 메타데이터를 그대로 복사하고 서로 다른 법률의 "
                "법률명과 조문을 결합하지 않는다. "
                "사고 사실만으로 위반을 확정하지 말고 적용 가능, 위반 가능성, "
                "추가 사실 확인 필요 중 하나로 표현한다. "
                "evidence_id는 L-01부터 순서대로 부여한다.",
            ),
            (
                "human",
                "검색질의: {query}\n현재 사고:\n{accident}\n\n"
                "사고일에 유효한 검색 조문:\n{context}",
            ),
        ])
        self.chain = prompt | llm.with_structured_output(LawAgentOutput)

    def run(self, accident: AccidentFacts) -> LawAgentOutput:
        query = (
            f"{accident.accident_type} {accident.customer_action} "
            f"{accident.counterparty_action} 과속 진로변경 안전운전 "
            "과실상계 손해배상"
        )
        documents = [
            document
            for document in self.retriever.invoke(query)
            if _effective_on(document, accident.accident_date)
        ]
        result = self.chain.invoke({
            "query": query,
            "accident": accident.model_dump_json(ensure_ascii=False),
            "context": _context(documents),
        })

        documents_by_article = {
            (
                str(document.metadata.get("law_name")),
                str(document.metadata.get("article")),
            ): document
            for document in documents
        }
        accident_text = (
            f"{accident.accident_type} {accident.location or ''} "
            f"{accident.customer_action} {accident.counterparty_action}"
        )
        verified_findings = []
        for finding in result.findings:
            matched = re.search(
                r"제\s*(\d+)\s*조(?:의\s*(\d+))?",
                finding.article,
            )
            if not matched:
                continue
            article = f"제{matched.group(1)}조"
            if matched.group(2):
                article += f"의{matched.group(2)}"

            # 교차로라는 사실이 없으면 교차로 전용 조문을 적용하지 않습니다.
            if "교차로" not in accident_text and article in {
                "제25조",
                "제26조",
                "제31조",
            }:
                continue

            document = documents_by_article.get((finding.law_name, article))
            if document is None:
                continue
            metadata = document.metadata
            verified_findings.append(finding.model_copy(update={
                "law_name": str(metadata.get("law_name")),
                "effective_date": str(metadata.get("effective_date") or "") or None,
                "article": str(metadata.get("article")),
                "article_title": str(metadata.get("article_title")),
                "source_file": str(metadata.get("source_file")),
                "pdf_page": int(metadata.get("pdf_page")),
            }))
        return result.model_copy(update={"findings": verified_findings})
