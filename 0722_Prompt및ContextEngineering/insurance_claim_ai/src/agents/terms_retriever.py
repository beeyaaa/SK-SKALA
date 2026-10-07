from __future__ import annotations

from pathlib import Path

from langchain_core.documents import Document

from src.pdf_parsers import parse_terms_pdf
from src.schemas import (
    AccidentFacts,
    CustomerLookupOutput,
    TermsRetrieverOutput,
    TermsCalculationRules,
    TermsFinding,
)
from src.vector_store import as_retriever


TERMS_FILENAME = "Sample_Automobile_Insurance_Policy_Terms.pdf"
MANDATORY_ARTICLES = ("제6조", "제9조", "제10조", "제16조", "제17조")
ARTICLE_PURPOSES = {
    "제6조": "상대방 인정손해액에 고객 과실비율과 대물 한도를 적용",
    "제9조": "자차 기초손해액에서 상대방 회수 가능액을 차감",
    "제10조": "공제 전 보상액에 자기부담률과 최소·최대 금액 적용",
    "제12조": "기존 손상·노후·사고와 무관한 손해 등 면책 여부 확인",
    "제13조": "음주·무면허 운전 시 자기차량손해 면책 여부 확인",
    "제14조": "사실관계가 불명확하면 지급액 확정 보류",
    "제15조": "블랙박스·견적서 등 필수 제출자료 확인",
    "제16조": "담보별 원 단위 계산값 보존 및 최종 합계 1,000원 절사",
    "제17조": "AI 산출액은 담당자 검토 전 잠정값",
}


def _document_map(documents: list[Document]) -> dict[str, Document]:
    return {
        str(document.metadata.get("article")): document
        for document in documents
    }


class TermsRetriever:
    def __init__(self) -> None:
        self.retriever = as_retriever("terms", k=8)
        project_dir = Path(__file__).resolve().parents[2]
        self.pdf_path = project_dir / "data" / TERMS_FILENAME

    def run(
        self,
        accident: AccidentFacts,
        customer: CustomerLookupOutput,
    ) -> TermsRetrieverOutput:
        policy = customer.policy
        if not self.pdf_path.exists():
            return TermsRetrieverOutput(
                status="missing_source",
                product_code=str(policy.get("product_code", "")),
                terms_version=str(policy.get("약관버전", "")),
                message=(
                    "보험약관 PDF가 제공되지 않아 담보 적용, 면책, "
                    "자기부담금 및 필요서류를 확정할 수 없습니다."
                ),
            )

        all_documents, profile = parse_terms_pdf(self.pdf_path)
        product_matches = (
            str(policy.get("product_code")) == profile["product_code"]
        )
        version_matches = (
            str(policy.get("약관버전")) == profile["terms_version"]
        )
        if not product_matches or not version_matches:
            return TermsRetrieverOutput(
                status="not_found",
                product_code=str(policy.get("product_code", "")),
                terms_version=str(policy.get("약관버전", "")),
                message=(
                    "고객 계약의 상품·약관버전과 제공된 PDF가 일치하지 "
                    f"않습니다. 계약={policy.get('product_code')} / "
                    f"{policy.get('약관버전')}, PDF="
                    f"{profile['product_code']} / {profile['terms_version']}"
                ),
            )

        query = (
            f"대물배상 자기차량손해 자기부담금 지급액 계산 "
            f"고객손해 {accident.customer_estimated_cost} "
            f"상대손해 {accident.counterparty_estimated_cost} "
            f"누락정보 {' '.join(accident.missing_facts)}"
        )
        retrieved = self.retriever.invoke(query)
        retrieved_articles = {
            str(document.metadata.get("article"))
            for document in retrieved
        }
        selected_articles = list(MANDATORY_ARTICLES)
        for article in ("제12조", "제14조", "제15조"):
            if article in retrieved_articles:
                selected_articles.append(article)
        if any(
            word in f"{accident.customer_action} {accident.counterparty_action}"
            for word in ("음주", "무면허")
        ):
            selected_articles.append("제13조")

        documents_by_article = _document_map(all_documents)
        findings = []
        for index, article in enumerate(selected_articles, start=1):
            document = documents_by_article.get(article)
            if document is None:
                continue
            metadata = document.metadata
            findings.append(TermsFinding(
                evidence_id=f"T-{index:02d}",
                article=article,
                article_title=str(metadata.get("article_title", "")),
                applicability=ARTICLE_PURPOSES[article],
                source_file=str(metadata.get("source_file")),
                pdf_page=int(metadata.get("pdf_page")),
            ))

        rules = TermsCalculationRules(
            property_damage_limit=profile["property_damage_limit"],
            own_vehicle_damage_limit=profile["own_vehicle_damage_limit"],
            deductible_rate=profile["deductible_rate"],
            minimum_deductible=profile["minimum_deductible"],
            maximum_deductible=profile["maximum_deductible"],
            subtract_counterparty_recovery=(
                profile["subtract_counterparty_recovery"]
            ),
            final_rounding_unit=profile["final_rounding_unit"],
            property_formula_article="제6조",
            own_damage_formula_article="제9조",
            deductible_article="제10조",
            rounding_article="제16조",
        )
        cited = ", ".join(
            f"{finding.evidence_id} {finding.article}"
            for finding in findings
        )
        return TermsRetrieverOutput(
            status="retrieved",
            product_code=profile["product_code"],
            terms_version=profile["terms_version"],
            findings=findings,
            calculation_rules=rules,
            message=(
                f"{profile['product_name']} "
                f"({profile['terms_version']}) 적용: {cited}"
            ),
        )
