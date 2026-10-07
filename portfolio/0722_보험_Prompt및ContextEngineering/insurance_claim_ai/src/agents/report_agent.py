from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable

from src.schemas import (
    AccidentFacts,
    CaseAgentOutput,
    CustomerLookupOutput,
    EvidenceDetail,
    FinalAssessment,
    FinalAssessmentDraft,
    LawAgentOutput,
    PaymentEstimate,
    TermsRetrieverOutput,
)


class ReportAgent:
    def __init__(self, llm: Runnable) -> None:
        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                "당신은 보험사 담당자를 위한 사고검토 보고서 Agent다. "
                "제공된 Agent 결과만 사용한다. 과실비율과 보험금을 확정하지 않는다. "
                "모든 핵심 결론은 검색 결과의 evidence_id와 연결한다. "
                "약관이 없으면 보상 여부를 확정할 수 없다고 명시한다. "
                "고객 사고이력을 현재 사고 과실 산정에 사용하지 않는다. "
                "case_analysis에는 판례 Agent가 찾은 사건번호, 법원, 선고일, "
                "판례상 과실비율, 유사점과 차이점을 포함한다. "
                "law_analysis에는 Law Agent의 law_name, article, article_title을 "
                "그대로 사용하며 서로 다른 법률명과 조문을 결합하지 않는다. "
                "customer_checks에는 유효 계약번호, 가입담보, 미종결 사고와 "
                "파손 중첩 플래그를 반드시 포함한다. "
                "evidence_ids에는 실제 분석 문장에서 인용한 ID만 넣고, "
                "입력 Agent 결과에 존재하지 않는 ID는 만들지 않는다.",
            ),
            (
                "human",
                "사고={accident}\n판례={cases}\n법률={laws}\n"
                "고객={customer}\n약관={terms}",
            ),
        ])
        # evidence_details는 아래에서 검색 결과로 확정적으로 조립합니다.
        # 자유 형식 dict를 OpenAI 구조화 출력 스키마에 포함하지 않습니다.
        self.chain = prompt | llm.with_structured_output(FinalAssessmentDraft)

    def run(
        self,
        accident: AccidentFacts,
        cases: CaseAgentOutput,
        laws: LawAgentOutput,
        customer: CustomerLookupOutput,
        terms: TermsRetrieverOutput,
        payment: PaymentEstimate,
    ) -> FinalAssessment:
        draft = self.chain.invoke({
            "accident": accident.model_dump_json(ensure_ascii=False),
            "cases": cases.model_dump_json(ensure_ascii=False),
            "laws": laws.model_dump_json(ensure_ascii=False),
            "customer": customer.model_dump_json(ensure_ascii=False),
            "terms": terms.model_dump_json(ensure_ascii=False),
        })

        # 사건번호·법률명·조문·고객정보는 LLM이 다시 쓰지 않고
        # 각 Agent의 구조화 결과를 그대로 사용해 근거 혼합을 방지합니다.
        case_analysis = [
            (
                f"[{finding.evidence_id}] {finding.court} "
                f"{finding.decision_date} 선고 {finding.case_no} "
                f"({finding.accident_type}) / 판례상 과실: "
                f"{finding.fault_result} / 유사점: "
                f"{', '.join(finding.similarities)} / 차이점: "
                f"{', '.join(finding.differences)} / 출처: "
                f"{finding.source_file} p.{finding.pdf_page}"
            )
            for finding in cases.findings
        ]

        law_analysis = [
            (
                f"[{finding.evidence_id}] {finding.law_name} "
                f"{finding.article}"
                f"{' ' + finding.paragraph if finding.paragraph else ''} "
                f"({finding.article_title or '조문명 없음'}): "
                f"{finding.applicability} — {finding.violation_status} "
                f"({finding.source_file} p.{finding.pdf_page})"
            )
            for finding in laws.findings
        ]

        policy = customer.policy
        coverage_names = [
            str(item.get("담보명"))
            for item in customer.coverages
            if item.get("가입여부") == "Y"
        ]
        customer_checks = [
            (
                f"사고일 기준 유효계약: {policy.get('policy_id')} / "
                f"상품: {policy.get('product_code')} / "
                f"약관버전: {policy.get('약관버전')}"
            ),
            f"가입담보: {', '.join(coverage_names)}",
        ]
        customer_checks.extend(customer.overlap_flags)
        customer_checks.append(customer.history_use_limitation)

        evidence_ids = [
            finding.evidence_id
            for finding in cases.findings
        ] + [
            finding.evidence_id
            for finding in laws.findings
        ] + [
            finding.evidence_id
            for finding in terms.findings
        ]

        evidence_details = [
            EvidenceDetail(
                evidence_id=finding.evidence_id,
                type="case_law",
                case_no=finding.case_no,
                court=finding.court,
                decision_date=finding.decision_date,
                source_file=finding.source_file,
                pdf_page=finding.pdf_page,
                relevance=finding.relevance,
            )
            for finding in cases.findings
        ] + [
            EvidenceDetail(
                evidence_id=finding.evidence_id,
                type="law",
                law_name=finding.law_name,
                article=finding.article,
                paragraph=finding.paragraph,
                article_title=finding.article_title,
                source_file=finding.source_file,
                pdf_page=finding.pdf_page,
            )
            for finding in laws.findings
        ] + [
            EvidenceDetail(
                evidence_id=finding.evidence_id,
                type="terms",
                article=finding.article,
                article_title=finding.article_title,
                terms_version=terms.terms_version,
                source_file=finding.source_file,
                pdf_page=finding.pdf_page,
            )
            for finding in terms.findings
        ]

        damage_parts = []
        if accident.customer_damage:
            damage_parts.append(f"고객 차량 {accident.customer_damage}")
        if accident.customer_estimated_cost is not None:
            damage_parts.append(
                f"고객 예상 수리비 {accident.customer_estimated_cost:,}원"
            )
        if accident.counterparty_estimated_cost is not None:
            damage_parts.append(
                f"상대 예상 수리비 "
                f"{accident.counterparty_estimated_cost:,}원"
            )
        accident_summary = (
            f"{accident.accident_date} {accident.location or '장소 미상'}에서 "
            f"고객({accident.customer_action})과 "
            f"상대방({accident.counterparty_action})이 "
            f"{accident.accident_type}한 사고입니다."
        )
        if damage_parts:
            accident_summary += " " + ", ".join(damage_parts) + "."

        return FinalAssessment.model_validate({
            **draft.model_dump(),
            "accident_summary": accident_summary,
            "case_analysis": case_analysis,
            "law_analysis": law_analysis,
            "customer_checks": customer_checks,
            "terms_analysis": [terms.message],
            "evidence_ids": evidence_ids,
            "evidence_details": evidence_details,
            "payment_estimate": payment,
        })
