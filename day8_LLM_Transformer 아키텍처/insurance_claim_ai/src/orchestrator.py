from __future__ import annotations

import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from src.agents.case_law_agent import CaseLawAgent
from src.agents.customer_lookup import CustomerLookup
from src.agents.law_agent import LawAgent
from src.agents.normalizer import InputNormalizer
from src.agents.report_agent import ReportAgent
from src.agents.terms_retriever import TermsRetriever
from src.payment_calculator import calculate_payment_estimate


def _verbose_results() -> bool:
    return os.getenv("VERBOSE_RESULTS", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _won(value: int | None) -> str:
    return "계산 전" if value is None else f"{value:,}원"


def _print_result(name: str, result: Any) -> None:
    payload = (
        result.model_dump()
        if hasattr(result, "model_dump")
        else result
    )
    print(f"\n[{name} 핵심 결과]", flush=True)

    if _verbose_results():
        print(
            json.dumps(payload, ensure_ascii=False, indent=2, default=str),
            flush=True,
        )
        return

    if name == "입력 구조화 Agent":
        print(
            f"- 사고: {payload['accident_date']} / "
            f"{payload.get('location') or '장소 미상'} / "
            f"{payload['accident_type']}",
            flush=True,
        )
        print(
            f"- 행동: 고객 {payload['customer_action']} / "
            f"상대 {payload['counterparty_action']}",
            flush=True,
        )
        print(
            f"- 속도: 제한 {payload.get('road_speed_limit_kmh')}km/h / "
            f"상대 {payload.get('counterparty_speed_kmh')}km/h",
            flush=True,
        )
        print(
            f"- 예상 손해: 고객 {_won(payload.get('customer_estimated_cost'))} / "
            f"상대 {_won(payload.get('counterparty_estimated_cost'))}",
            flush=True,
        )
        if payload.get("missing_facts"):
            print(
                f"- 미확인: {', '.join(payload['missing_facts'])}",
                flush=True,
            )

    elif name == "판례 Agent":
        findings = payload.get("findings", [])
        if not findings:
            print("- 관련 판례를 찾지 못했습니다.", flush=True)
        else:
            top = findings[0]
            print(
                f"- 최우선 [{top['evidence_id']}] {top['court']} "
                f"{top['case_no']} / {top['fault_result']}",
                flush=True,
            )
            print(
                f"- 관련성: {top['relevance']} / 검색 결과 {len(findings)}건",
                flush=True,
            )

    elif name == "법률 Agent":
        findings = payload.get("findings", [])
        laws = [
            f"[{item['evidence_id']}] {item['law_name']} {item['article']}"
            for item in findings
        ]
        print(
            f"- 검토 조문: {', '.join(laws) if laws else '없음'}",
            flush=True,
        )

    elif name == "고객정보 조회":
        policy = payload.get("policy", {})
        coverages = [
            str(item.get("담보명"))
            for item in payload.get("coverages", [])
            if item.get("가입여부") == "Y"
        ]
        print(
            f"- 계약: {policy.get('policy_id')} / "
            f"{policy.get('product_code')} / {policy.get('약관버전')}",
            flush=True,
        )
        print(f"- 가입담보: {', '.join(coverages)}", flush=True)
        for flag in payload.get("overlap_flags", []):
            print(f"- 주의: {flag}", flush=True)

    elif name == "보험약관 검색":
        print(
            f"- 상태: {payload['status']} / {payload['message']}",
            flush=True,
        )
        findings = payload.get("findings", [])
        if findings:
            print(
                "- 적용 조항: "
                + ", ".join(
                    f"[{item['evidence_id']}] {item['article']}"
                    for item in findings
                ),
                flush=True,
            )

    elif name == "예상 지급액 계산":
        if payload["status"] == "calculated":
            print(
                f"- 참고 과실: 고객 "
                f"{payload['customer_reference_fault_percent']}% / 상대 "
                f"{payload['counterparty_reference_fault_percent']}%",
                flush=True,
            )
            print(
                f"- 대물: "
                f"{_won(payload['counterparty_property_damage']['estimated_payment'])} "
                f"/ 자차: "
                f"{_won(payload['customer_vehicle_damage']['estimated_payment'])}",
                flush=True,
            )
            print(
                f"- 예상 초기 총지급액: "
                f"{_won(payload['estimated_initial_total_payment'])}",
                flush=True,
            )
        else:
            print(
                f"- 계산 보류: {', '.join(payload['missing_inputs'])}",
                flush=True,
            )


def _run_with_progress(
    name: str,
    function: Callable[..., Any],
    *args: Any,
) -> Any:
    started_at = time.perf_counter()
    print(f"   - {name} 시작", flush=True)
    try:
        result = function(*args)
    except Exception:
        elapsed = time.perf_counter() - started_at
        print(f"   - {name} 실패 ({elapsed:.1f}초)", flush=True)
        raise

    elapsed = time.perf_counter() - started_at
    print(f"   - {name} 완료 ({elapsed:.1f}초)", flush=True)
    return result


class ClaimReviewOrchestrator:
    def __init__(self) -> None:
        load_dotenv()
        llm = ChatOpenAI(
            model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
            temperature=0,
        )

        self.normalizer = InputNormalizer(llm)
        self.case_agent = CaseLawAgent(llm)
        self.law_agent = LawAgent(llm)
        self.customer_lookup = CustomerLookup()
        self.terms_retriever = TermsRetriever()
        self.report_agent = ReportAgent(llm)

    def run(
        self,
        claim_id: str,
        customer_id: str,
        employee_input: str,
    ) -> dict:
        total_started_at = time.perf_counter()

        stage_started_at = time.perf_counter()
        print("[1/5] 사고내용을 구조화하고 있습니다...", flush=True)
        accident = self.normalizer.run(
            claim_id=claim_id,
            customer_id=customer_id,
            text=employee_input,
        )
        print(
            f"[1/5] 사고내용 구조화 완료 "
            f"({time.perf_counter() - stage_started_at:.1f}초)",
            flush=True,
        )
        _print_result("입력 구조화 Agent", accident)

        # 서로 독립적인 세 작업은 병렬 실행합니다.
        print(
            "[2/5] 판례·법률·고객정보를 동시에 분석하고 있습니다...",
            flush=True,
        )
        with ThreadPoolExecutor(max_workers=3) as executor:
            case_future = executor.submit(
                _run_with_progress,
                "판례 Agent",
                self.case_agent.run,
                accident,
            )
            law_future = executor.submit(
                _run_with_progress,
                "법률 Agent",
                self.law_agent.run,
                accident,
            )
            customer_future = executor.submit(
                _run_with_progress,
                "고객정보 조회",
                self.customer_lookup.run,
                accident,
            )

            cases = case_future.result()
            laws = law_future.result()
            customer = customer_future.result()
        print("[2/5] 병렬 분석 완료", flush=True)
        _print_result("판례 Agent", cases)
        _print_result("법률 Agent", laws)
        _print_result("고객정보 조회", customer)

        # 상품코드와 약관버전은 고객 조회 결과가 있어야 결정됩니다.
        stage_started_at = time.perf_counter()
        print("[3/5] 보험약관 적용 가능성을 확인하고 있습니다...", flush=True)
        terms = self.terms_retriever.run(accident, customer)
        print(
            f"[3/5] 보험약관 확인 완료 "
            f"({time.perf_counter() - stage_started_at:.1f}초)",
            flush=True,
        )
        _print_result("보험약관 검색", terms)

        stage_started_at = time.perf_counter()
        print("[4/5] 예상 지급액을 계산하고 있습니다...", flush=True)
        payment = calculate_payment_estimate(
            accident=accident,
            cases=cases,
            customer=customer,
            terms=terms,
        )
        print(
            f"[4/5] 예상 지급액 계산 완료 "
            f"({time.perf_counter() - stage_started_at:.1f}초)",
            flush=True,
        )
        _print_result("예상 지급액 계산", payment)

        stage_started_at = time.perf_counter()
        print("[5/5] 최종 검토 보고서를 작성하고 있습니다...", flush=True)
        report = self.report_agent.run(
            accident=accident,
            cases=cases,
            laws=laws,
            customer=customer,
            terms=terms,
            payment=payment,
        )
        print(
            f"[5/5] 최종 보고서 작성 완료 "
            f"({time.perf_counter() - stage_started_at:.1f}초)",
            flush=True,
        )
        print(
            f"[완료] 전체 분석시간: "
            f"{time.perf_counter() - total_started_at:.1f}초",
            flush=True,
        )

        return {
            "normalized_input": accident.model_dump(),
            "case_agent": cases.model_dump(),
            "law_agent": laws.model_dump(),
            "customer_lookup": customer.model_dump(),
            "terms_retriever": terms.model_dump(),
            "final_report": report.model_dump(),
        }
