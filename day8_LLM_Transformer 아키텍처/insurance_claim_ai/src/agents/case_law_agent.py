from __future__ import annotations

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable

from src.vector_store import as_retriever
from src.schemas import AccidentFacts, CaseAgentOutput


def _context(documents: list[Document]) -> str:
    blocks = []
    for index, document in enumerate(documents, start=1):
        metadata = document.metadata
        blocks.append(
            f"[검색문서 {index}]\n"
            f"사건번호: {metadata.get('case_no')}\n"
            f"법원: {metadata.get('court')}\n"
            f"선고일: {metadata.get('decision_date')}\n"
            f"원본 파일: {metadata.get('source_file')}\n"
            f"PDF 페이지: {metadata.get('pdf_page')}\n"
            f"원문:\n{document.page_content}"
        )
    return "\n\n".join(blocks)


class CaseLawAgent:
    def __init__(self, llm: Runnable) -> None:
        self.retriever = as_retriever("case_law", k=4)
        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                "당신은 보험사 담당자의 판례 검색 보조 Agent다. "
                "제공된 검색문서 밖의 사건번호나 과실비율을 만들지 않는다. "
                "유사점과 차이점을 모두 적고 완전 일치가 아니면 직접 일치로 표시하지 않는다. "
                "판례 당사자와 현재 사고의 고객·상대방 역할이 명확히 대응할 때만 "
                "판례의 과실비율을 customer_reference_fault_percent와 "
                "counterparty_reference_fault_percent에 현재 사고 기준으로 변환한다. "
                "두 값은 fault_result 원문에 실제로 존재하는 숫자여야 하고 합계가 "
                "100이어야 한다. 역할 대응이 불명확하면 두 값 모두 null로 둔다. "
                "evidence_id는 P-01부터 순서대로 부여한다.",
            ),
            (
                "human",
                "검색질의: {query}\n현재 사고:\n{accident}\n\n"
                "검색된 판례:\n{context}",
            ),
        ])
        self.chain = prompt | llm.with_structured_output(CaseAgentOutput)

    def run(self, accident: AccidentFacts) -> CaseAgentOutput:
        query = (
            f"{accident.accident_type}. 고객 행동: {accident.customer_action}. "
            f"상대 행동: {accident.counterparty_action}. "
            f"속도제한 {accident.road_speed_limit_kmh}, "
            f"상대속도 {accident.counterparty_speed_kmh}"
        )
        documents = self.retriever.invoke(query)
        result = self.chain.invoke({
            "query": query,
            "accident": accident.model_dump_json(ensure_ascii=False),
            "context": _context(documents),
        })
        documents_by_case = {
            str(document.metadata.get("case_no")): document
            for document in documents
        }
        verified_findings = []
        for finding in result.findings:
            document = documents_by_case.get(finding.case_no)
            if document is None:
                continue
            metadata = document.metadata
            verified_findings.append(finding.model_copy(update={
                "court": str(metadata.get("court")),
                "decision_date": str(metadata.get("decision_date")),
                "accident_type": str(metadata.get("accident_type")),
                "source_file": str(metadata.get("source_file")),
                "pdf_page": int(metadata.get("pdf_page")),
            }))
        return result.model_copy(update={"findings": verified_findings})
