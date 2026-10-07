"""3단계 — 이상탐지(Anomaly Detection)

출처: output/_통합개념/이상탐지(Anomaly Detection).md 6번 — Observability in the
AI-Native Era 부속 실습(03_01_total_exercise.md)에서 `uv run observability_pipeline.py
all`로 실제 실행 검증된 `moving_average_anomaly_detection()` 함수를 그대로 가져와,
이 실습의 MetricPoint 데이터 형식에 맞춰 최소한으로만 이식했다 — z-score 계산 로직
자체(윈도우 평균·표준편차 대비 (x-mean)/stdev)는 원문과 동일하다.
"""
from __future__ import annotations

import statistics
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import BASE_DIR, DATA_DIR, MetricPoint, load_json, load_metrics_csv, save_json  # noqa: E402


def moving_average_anomaly_detection(
    series: list[MetricPoint], window: int = 10, z_threshold: float = 2.0
) -> list[str]:
    """서비스별 지연 시간의 이동평균·표준편차 대비 z-score로 이상치를 탐지한다.

    (원출처 그대로) 고정 임계값과 달리 서비스마다 다른 '평상시 기준선'을 스스로 학습하므로,
    payment-gateway처럼 원래 느린 서비스도 자기 기준선 대비 급격한 변화만 잡아낸다.
    """
    anomalies = []
    values = [p.latency_ms for p in series]
    for i, p in enumerate(series):
        if i < window:
            continue
        window_vals = values[i - window:i]
        mean = statistics.fmean(window_vals)
        stdev = statistics.pstdev(window_vals) or 1e-6
        z = (p.latency_ms - mean) / stdev
        if z > z_threshold:
            anomalies.append(
                f"[AIOPS] t={p.timestamp} {p.service} latency={p.latency_ms}ms (z={z:.2f}, baseline~{mean:.1f}ms)"
            )
    return anomalies


def static_threshold_alerts(series: list[MetricPoint], threshold_ms: float = 150.0) -> list[str]:
    """비교용 — 정적 임계값 알림(원출처의 1번 함수와 동일한 컨셉, 이 실습 데이터용으로 재작성)."""
    return [
        f"[STATIC] t={p.timestamp} {p.service} latency={p.latency_ms}ms > {threshold_ms}ms"
        for p in series
        if p.latency_ms > threshold_ms
    ]


def main() -> None:
    targets = load_json(BASE_DIR / "logs" / "discovered_targets.json")["final_target_list"]
    all_points = load_metrics_csv(DATA_DIR / "metrics.csv")

    by_service: dict[str, list[MetricPoint]] = defaultdict(list)
    for p in all_points:
        if p.service in targets:
            by_service[p.service].append(p)

    print("=== 정적 임계값 알림(비교용) ===")
    static_total = 0
    for svc, pts in sorted(by_service.items()):
        alerts = static_threshold_alerts(pts)
        static_total += len(alerts)
    print(f"총 {static_total}건 (노이즈 많음 — payment-gateway는 원래도 150ms를 넘나든다)\n")

    print("=== AIOps 이동평균 이상탐지 ===")
    all_anomalies = []
    for svc, pts in sorted(by_service.items()):
        anomalies = moving_average_anomaly_detection(pts, window=10, z_threshold=2.0)
        for line in anomalies[:3]:
            print(f"  {line}")
        if len(anomalies) > 3:
            print(f"  ... 외 {len(anomalies) - 3}건")
        all_anomalies.extend(anomalies)
    print(f"\n총 이상탐지: {len(all_anomalies)}건 (정적 {static_total}건 대비 {'적음 = 노이즈 감소' if len(all_anomalies) < static_total else '차이 없음'})")

    out_path = BASE_DIR / "logs" / "anomalies.json"
    save_json(out_path, {"static_alert_count": static_total, "anomaly_count": len(all_anomalies), "anomalies": all_anomalies})
    print(f"결과를 {out_path.relative_to(BASE_DIR)}에 저장했다 — 4단계(근본원인분석)가 이 이상탐지 결과를 인시던트 트리거로 사용한다.")


if __name__ == "__main__":
    main()
