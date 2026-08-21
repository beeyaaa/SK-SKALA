from __future__ import annotations

import re

from src.schemas import (
    AccidentFacts,
    CaseAgentOutput,
    CustomerLookupOutput,
    PaymentEstimate,
    PaymentItem,
    TermsRetrieverOutput,
)


def _integer(value: object, default: int = 0) -> int:
    if value is None:
        return default
    return int(float(value))


def _number(value: object, default: float = 0.0) -> float:
    if value is None:
        return default
    return float(value)


def _coverage(
    customer: CustomerLookupOutput,
    coverage_codes: tuple[str, ...],
) -> dict | None:
    for item in customer.coverages:
        if (
            item.get("담보코드") in coverage_codes
            and item.get("가입여부") == "Y"
        ):
            return item
    return None


def _reference_fault(
    cases: CaseAgentOutput,
) -> tuple[object | None, int | None, int | None]:
    for finding in cases.findings:
        customer_fault = finding.customer_reference_fault_percent
        counterparty_fault = finding.counterparty_reference_fault_percent
        if customer_fault is None or counterparty_fault is None:
            continue
        if customer_fault + counterparty_fault != 100:
            continue

        # 구조화된 수치가 판례 원문 과실결과에 실제 존재하는지도 확인합니다.
        source_percentages = {
            int(value)
            for value in re.findall(r"(\d{1,3})\s*%", finding.fault_result)
        }
        if (
            customer_fault not in source_percentages
            or counterparty_fault not in source_percentages
        ):
            continue
        return finding, customer_fault, counterparty_fault

    return None, None, None


def calculate_payment_estimate(
    accident: AccidentFacts,
    cases: CaseAgentOutput,
    customer: CustomerLookupOutput,
    terms: TermsRetrieverOutput,
) -> PaymentEstimate:
    missing_inputs: list[str] = []
    assumptions = [
        "인명피해가 없는 차량 물적 손해 시나리오만 계산했습니다.",
        "판례 과실비율은 확정값이 아니라 지급액 산정을 위한 참고값입니다.",
        "잔존물·부가세·대차료·휴차료 등은 계산에서 제외했습니다.",
    ]

    finding, customer_fault, counterparty_fault = _reference_fault(cases)
    if finding is None:
        missing_inputs.append("현재 사고 당사자 역할에 대응되는 판례 참고 과실비율")
    if accident.customer_estimated_cost is None:
        missing_inputs.append("고객 차량 예상 수리비")
    if accident.counterparty_estimated_cost is None:
        missing_inputs.append("상대 차량 예상 수리비")

    property_coverage = _coverage(customer, ("COV-01", "PD"))
    own_damage_coverage = _coverage(customer, ("COV-02", "OD"))
    if property_coverage is None:
        missing_inputs.append("가입된 대물배상 담보")
    if own_damage_coverage is None:
        missing_inputs.append("가입된 자기차량손해 담보")

    rules = terms.calculation_rules
    terms_warning = (
        "보험약관 PDF가 없어 coverages.csv의 담보·가입금액·자기부담금 "
        "데이터만 사용한 시뮬레이션입니다. 실제 약관과 담당자 검토 전에는 "
        "확정 보험금으로 사용할 수 없습니다."
        if terms.status != "retrieved"
        else (
            f"{terms.terms_version} 약관 제6조·제9조·제10조·제16조와 "
            "입력 손해액을 적용한 잠정 산정액입니다. 제17조에 따라 "
            "담당자 검토 전에는 확정 보험금으로 사용할 수 없습니다."
        )
    )
    if terms.status == "retrieved" and rules is None:
        missing_inputs.append("약관 지급액 계산 규칙")
    if rules is not None and rules.subtract_counterparty_recovery:
        assumptions.append(
            "약관 제9조에 따라 자차 기초손해액에서 상대방 회수 가능액을 "
            "먼저 차감했습니다."
        )

    if missing_inputs:
        return PaymentEstimate(
            status="insufficient_data",
            basis_evidence_id=(
                finding.evidence_id if finding is not None else None
            ),
            customer_reference_fault_percent=customer_fault,
            counterparty_reference_fault_percent=counterparty_fault,
            missing_inputs=missing_inputs,
            assumptions=assumptions,
            disclaimer=terms_warning,
        )

    counterparty_loss = int(accident.counterparty_estimated_cost)
    property_limit = _integer(property_coverage.get("가입금액"))
    if rules is not None:
        property_limit = min(
            property_limit,
            rules.property_damage_limit,
        )
    property_before_limit = counterparty_loss * int(customer_fault) // 100
    property_payment = min(property_before_limit, property_limit)
    counterparty_item = PaymentItem(
        coverage_name=str(property_coverage.get("담보명")),
        estimated_loss=counterparty_loss,
        applied_fault_percent=customer_fault,
        coverage_limit=property_limit,
        estimated_payment=property_payment,
        calculation=(
            f"{counterparty_loss:,}원 × 고객 참고 과실 "
            f"{customer_fault}% = {property_before_limit:,}원"
        ),
    )

    customer_loss = int(accident.customer_estimated_cost)
    own_damage_limit = _integer(own_damage_coverage.get("가입금액"))
    deductible_rate = _number(own_damage_coverage.get("자기부담률"))
    minimum_deductible = _integer(
        own_damage_coverage.get("최소자기부담금")
    )
    maximum_deductible = _integer(
        own_damage_coverage.get("최대자기부담금")
    )
    if rules is not None:
        own_damage_limit = min(
            own_damage_limit,
            rules.own_vehicle_damage_limit,
        )
        deductible_rate = rules.deductible_rate
        minimum_deductible = rules.minimum_deductible
        maximum_deductible = rules.maximum_deductible

    base_own_damage = min(customer_loss, own_damage_limit)
    possible_recovery = (
        base_own_damage * int(counterparty_fault) // 100
        if rules is not None and rules.subtract_counterparty_recovery
        else 0
    )
    before_deductible = max(base_own_damage - possible_recovery, 0)
    calculated_deductible = int(before_deductible * deductible_rate)
    deductible = max(calculated_deductible, minimum_deductible)
    if maximum_deductible > 0:
        deductible = min(deductible, maximum_deductible)
    own_damage_payment = min(
        max(before_deductible - deductible, 0),
        own_damage_limit,
    )
    customer_item = PaymentItem(
        coverage_name=str(own_damage_coverage.get("담보명")),
        estimated_loss=customer_loss,
        deductible=deductible,
        coverage_limit=own_damage_limit,
        estimated_payment=own_damage_payment,
        calculation=(
            f"기초손해 {base_own_damage:,}원 - 회수 가능액 "
            f"{possible_recovery:,}원 - 자기부담금 {deductible:,}원 "
            f"= {own_damage_payment:,}원"
        ),
    )

    total_payment = property_payment + own_damage_payment
    if rules is not None and rules.final_rounding_unit > 1:
        total_payment = (
            total_payment // rules.final_rounding_unit
            * rules.final_rounding_unit
        )

    return PaymentEstimate(
        status="calculated",
        basis_evidence_id=finding.evidence_id,
        customer_reference_fault_percent=customer_fault,
        counterparty_reference_fault_percent=counterparty_fault,
        counterparty_property_damage=counterparty_item,
        customer_vehicle_damage=customer_item,
        estimated_initial_total_payment=total_payment,
        possible_recovery_amount=possible_recovery,
        assumptions=assumptions,
        disclaimer=terms_warning,
    )
