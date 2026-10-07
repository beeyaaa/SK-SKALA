"""5단계 — 원격조치(Remediation)

출처: output/_통합개념/KUBERNETES REMEDIATION MCP SERVER(MCP 서버(쿠버네티스 원격
조치)).md 6번의 실제 가드레일 YAML(`allowed_actions`/`forbidden_actions`/
`require_dry_run`)을 이 스크립트의 GUARDRAIL 딕셔너리로 그대로 옮겼다. 그 문서 6번의
"kubectl 수준 쓰기 작업 실행" 단계 자체는 이 로컬 실습에 실제 쿠버네티스 클러스터가
없어 재현할 수 없으므로, 대신 감사 로그(audit log)에 실행 여부를 기록하는 것으로
대체했다 — 이 대체 사실을 아래 실행 결과에 그대로 남긴다.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import BASE_DIR, load_json, save_json  # noqa: E402

# 원문 YAML 그대로:
#   remediation_mcp_server:
#     allowed_actions: [rollback_deployment, restart_pod, toggle_feature_flag]
#     forbidden_actions: [delete_namespace, delete_pvc]
#     require_dry_run: true
GUARDRAIL = {
    "allowed_actions": ["rollback_deployment", "restart_pod", "toggle_feature_flag"],
    "forbidden_actions": ["delete_namespace", "delete_pvc"],
    "require_dry_run": True,
}


def guardrail_gate(action: str) -> dict:
    if action in GUARDRAIL["forbidden_actions"]:
        return {"action": action, "approved": False, "reason": "forbidden_actions에 명시적으로 금지됨"}
    if action not in GUARDRAIL["allowed_actions"]:
        return {"action": action, "approved": False, "reason": "allowed_actions 목록에 없음"}
    return {"action": action, "approved": True, "reason": "allowed_actions 통과"}


def main() -> None:
    rca = load_json(BASE_DIR / "logs" / "rca_result.json")
    service = rca["incident_service"]
    action = "rollback_deployment"  # 직전 배포가 원인 후보로 지목됐으므로 롤백을 제안

    print(f"RCA 후보 원인: service={service}, candidate_deploys={rca['candidate_deploys']}")
    print(f"제안 조치: {action}\n")

    gate = guardrail_gate(action)
    print(f"가드레일 판정: approved={gate['approved']} ({gate['reason']})")

    audit_entry = {
        "service": service,
        "action": action,
        "guardrail": gate,
        "dry_run": GUARDRAIL["require_dry_run"],
        "executed": False,
        "note": "실제 kubectl 실행 대신 감사 로그 기록으로 대체(로컬 실습 환경에 클러스터 없음)",
    }

    if gate["approved"] and GUARDRAIL["require_dry_run"]:
        print(f"\n[DRY RUN] {action}(service={service}) — require_dry_run=true라 영향 범위만 시뮬레이션하고 실제로는 실행하지 않음")
        audit_entry["executed"] = False
    elif gate["approved"]:
        print(f"\n[EXECUTED] {action}(service={service})")
        audit_entry["executed"] = True
    else:
        print("\n[REJECTED_BY_GUARDRAIL] 조치가 차단되어 실행되지 않음")

    out_path = BASE_DIR / "logs" / "audit_log.json"
    save_json(out_path, audit_entry)
    print(f"\n감사 로그를 {out_path.relative_to(BASE_DIR)}에 기록했다 — 이것으로 AIOps 5단계 파이프라인이 완결된다.")


if __name__ == "__main__":
    main()
