import json
import os

from src.orchestrator import ClaimReviewOrchestrator


def _verbose_results() -> bool:
    return os.getenv("VERBOSE_RESULTS", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }


def _won(value: int | None) -> str:
    return "계산 보류" if value is None else f"{value:,}원"


def _print_final_summary(report: dict) -> None:
    payment = report["payment_estimate"]
    details = report.get("evidence_details", [])
    primary_case = next(
        (item for item in details if item["type"] == "case_law"),
        None,
    )
    laws = [item for item in details if item["type"] == "law"]
    terms = [item for item in details if item["type"] == "terms"]

    print("\n===== 핵심 검토 결과 =====")
    print(f"\n[사고 요약]\n{report['accident_summary']}")

    print("\n[잠정 결론]")
    if payment["customer_reference_fault_percent"] is not None:
        print(
            f"- 참고 과실: 고객 "
            f"{payment['customer_reference_fault_percent']}% / 상대 "
            f"{payment['counterparty_reference_fault_percent']}%"
        )
    else:
        print("- 참고 과실: 계산 보류")

    if payment["status"] == "calculated":
        print(
            f"- 대물 예상 지급: "
            f"{_won(payment['counterparty_property_damage']['estimated_payment'])}"
        )
        print(
            f"- 자차 예상 지급: "
            f"{_won(payment['customer_vehicle_damage']['estimated_payment'])}"
        )
        print(
            f"- 예상 초기 총지급액: "
            f"{_won(payment['estimated_initial_total_payment'])}"
        )
    else:
        print(
            f"- 예상 지급액: 계산 보류 "
            f"({', '.join(payment['missing_inputs'])})"
        )

    print("\n[핵심 근거]")
    if primary_case:
        print(
            f"- 판례 [{primary_case['evidence_id']}] "
            f"{primary_case['court']} {primary_case['case_no']} "
            f"({primary_case['source_file']} p.{primary_case['pdf_page']})"
        )
    if laws:
        print(
            "- 법률: "
            + ", ".join(
                f"[{item['evidence_id']}] "
                f"{item['law_name']} {item['article']}"
                for item in laws[:3]
            )
        )
    if terms:
        print(
            "- 약관: "
            + ", ".join(
                f"[{item['evidence_id']}] {item['article']} "
                f"({item['source_file']} p.{item['pdf_page']})"
                for item in terms[:5]
            )
        )

    print("\n[계약·약관]")
    for item in report["customer_checks"][:3]:
        print(f"- {item}")
    print(f"- {report['terms_analysis'][0]}")

    if report["required_human_checks"]:
        print("\n[담당자 확인사항]")
        for item in report["required_human_checks"][:5]:
            print(f"- {item}")

    print(f"\n[주의]\n- {payment['disclaimer']}")


def main() -> None:
    print("보험사고 검토 AI")
    claim_id = input("사고 접수번호: ").strip()
    customer_id = input("고객 ID: ").strip()

    print("사고 내용을 입력하세요.")
    print("여러 줄 입력이 가능하며, 입력을 마치려면 빈 줄에서 Enter를 누르세요.")
    input_lines = []
    while True:
        line = input()
        if not line.strip():
            break
        input_lines.append(line.strip())

    employee_input = " ".join(input_lines)

    if not claim_id or not customer_id or not employee_input:
        raise ValueError("접수번호, 고객 ID, 사고 내용을 모두 입력해야 합니다.")

    print("\n분석을 시작합니다.\n", flush=True)
    result = ClaimReviewOrchestrator().run(
        claim_id=claim_id,
        customer_id=customer_id,
        employee_input=employee_input,
    )

    _print_final_summary(result["final_report"])

    if _verbose_results():
        print("\n===== 전체 JSON 결과 =====")
        print(json.dumps(result["final_report"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
