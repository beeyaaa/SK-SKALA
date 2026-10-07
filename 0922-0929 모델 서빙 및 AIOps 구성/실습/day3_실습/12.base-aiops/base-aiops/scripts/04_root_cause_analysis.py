"""4단계 — 근본원인분석(RCA)

출처: output/_통합개념/RCA(ROOT CAUSE ANALYSIS).md 6번 — Observability in the AI-Native
Era Ch.7이 소개하는 `suggest_root_cause()` 코드를 그대로 가져와, 이 실습의 Deploy
데이터 형식(datetime 대신 분 단위 정수 timestamp)에 맞춰 timedelta 비교 부분만 정수
비교로 바꿨다. 후보를 "직전 30분 이내 배포"로 좁히는 핵심 로직은 원문과 동일하다.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import BASE_DIR, DATA_DIR, Deploy, load_json, save_json  # noqa: E402


def suggest_root_cause(incident_time: int, deploys: list[Deploy], window_minutes: int = 30) -> dict:
    candidates = [
        d for d in deploys
        if 0 <= incident_time - d.time < window_minutes  # 인시던트 직전 window_minutes 내 배포만 후보로
    ]
    return {
        "candidate_deploys": [d.id for d in candidates],
        "related_commits": [c for d in candidates for c in d.commits],
        # SRE는 이 후보 목록 검증부터 시작하므로, 처음부터 로그를 뒤지는 수작업이 사라진다
    }


def main() -> None:
    anomalies = load_json(BASE_DIR / "logs" / "anomalies.json")
    if anomalies["anomaly_count"] == 0:
        print("이상탐지 결과가 없어 RCA를 실행할 인시던트가 없다.")
        return

    # z-score가 가장 큰(가장 심각한) 이상을 인시던트로 승격한다.
    # 각 줄 형식: "[AIOPS] t=19 checkout-api latency=88.5ms (z=2.46, baseline~79.6ms)"
    def parse_line(line: str) -> tuple[int, str, float]:
        parts = line.split(" ")
        t = int(parts[1].split("=")[1])
        service = parts[2]
        z = float(parts[4].rstrip(",").split("=")[1])
        return t, service, z

    parsed = [parse_line(line) for line in anomalies["anomalies"]]
    incident_time, incident_service, incident_z = max(parsed, key=lambda x: x[2])
    print(f"인시던트 발생: t={incident_time}, service={incident_service}, z={incident_z:.2f} (이상탐지 3단계 결과 중 가장 심각한 이상을 인시던트로 승격)")

    deploys_raw = load_json(DATA_DIR / "deploys.json")
    deploys = [Deploy(**d) for d in deploys_raw]

    result = suggest_root_cause(incident_time, deploys, window_minutes=30)
    print(f"\n직전 30분 내 배포 후보: {result['candidate_deploys'] or '없음'}")
    for commit in result["related_commits"]:
        print(f"  관련 커밋: {commit}")

    out_path = BASE_DIR / "logs" / "rca_result.json"
    save_json(out_path, {"incident_time": incident_time, "incident_service": incident_service, **result})
    print(f"\n결과를 {out_path.relative_to(BASE_DIR)}에 저장했다 — SRE는 이 후보부터 검증을 시작한다.")
    print("5단계(원격조치)가 이 후보 원인을 근거로 조치 여부를 판단한다.")


if __name__ == "__main__":
    main()
