from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class AccidentFacts(BaseModel):
    claim_id: str
    customer_id: str
    accident_date: str
    location: str | None = None
    accident_type: str
    customer_action: str
    counterparty_action: str
    road_speed_limit_kmh: int | None = None
    counterparty_speed_kmh: int | None = None
    customer_damage: str | None = None
    counterparty_damage: str | None = None
    evidence: list[str] = Field(default_factory=list)
    customer_estimated_cost: int | None = None
    counterparty_estimated_cost: int | None = None
    missing_facts: list[str] = Field(default_factory=list)


class CaseFinding(BaseModel):
    evidence_id: str
    case_no: str
    court: str
    decision_date: str
    accident_type: str
    fault_result: str
    similarities: list[str]
    differences: list[str]
    source_file: str
    pdf_page: int
    relevance: Literal["high", "medium", "low"]
    customer_reference_fault_percent: int | None = None
    counterparty_reference_fault_percent: int | None = None


class CaseAgentOutput(BaseModel):
    query: str
    findings: list[CaseFinding]
    directly_matching_case_found: bool
    caveat: str


class LawFinding(BaseModel):
    evidence_id: str
    law_name: str
    effective_date: str | None = None
    article: str
    paragraph: str | None = None
    article_title: str | None = None
    applicability: str
    violation_status: Literal["적용 가능", "위반 가능성", "추가 사실 확인 필요"]
    source_file: str
    pdf_page: int


class LawAgentOutput(BaseModel):
    query: str
    findings: list[LawFinding]
    missing_evidence: list[str]
    caveat: str


class CustomerLookupOutput(BaseModel):
    customer_id: str
    customer_name: str
    policy: dict
    coverages: list[dict]
    prior_accidents: list[dict]
    open_claims: list[dict]
    overlap_flags: list[str]
    history_use_limitation: str


class TermsFinding(BaseModel):
    evidence_id: str
    article: str
    article_title: str
    applicability: str
    source_file: str
    pdf_page: int


class TermsCalculationRules(BaseModel):
    property_damage_limit: int
    own_vehicle_damage_limit: int
    deductible_rate: float
    minimum_deductible: int
    maximum_deductible: int
    subtract_counterparty_recovery: bool
    final_rounding_unit: int
    property_formula_article: str
    own_damage_formula_article: str
    deductible_article: str
    rounding_article: str


class TermsRetrieverOutput(BaseModel):
    status: Literal["retrieved", "missing_source", "not_found"]
    product_code: str | None = None
    terms_version: str | None = None
    findings: list[TermsFinding] = Field(default_factory=list)
    calculation_rules: TermsCalculationRules | None = None
    message: str


class FinalAssessmentDraft(BaseModel):
    accident_summary: str
    case_analysis: list[str]
    law_analysis: list[str]
    customer_checks: list[str]
    terms_analysis: list[str]
    provisional_fault_guidance: str
    required_human_checks: list[str]
    evidence_ids: list[str]
    disclaimer: str


class EvidenceDetail(BaseModel):
    evidence_id: str
    type: Literal["case_law", "law", "terms"]
    case_no: str | None = None
    court: str | None = None
    decision_date: str | None = None
    law_name: str | None = None
    article: str | None = None
    paragraph: str | None = None
    article_title: str | None = None
    terms_version: str | None = None
    source_file: str
    pdf_page: int
    relevance: str | None = None


class PaymentItem(BaseModel):
    coverage_name: str
    estimated_loss: int
    applied_fault_percent: int | None = None
    deductible: int = 0
    coverage_limit: int
    estimated_payment: int
    calculation: str


class PaymentEstimate(BaseModel):
    status: Literal["calculated", "insufficient_data"]
    basis_evidence_id: str | None = None
    customer_reference_fault_percent: int | None = None
    counterparty_reference_fault_percent: int | None = None
    counterparty_property_damage: PaymentItem | None = None
    customer_vehicle_damage: PaymentItem | None = None
    estimated_initial_total_payment: int | None = None
    possible_recovery_amount: int | None = None
    missing_inputs: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    disclaimer: str


class FinalAssessment(FinalAssessmentDraft):
    evidence_details: list[EvidenceDetail] = Field(default_factory=list)
    payment_estimate: PaymentEstimate
