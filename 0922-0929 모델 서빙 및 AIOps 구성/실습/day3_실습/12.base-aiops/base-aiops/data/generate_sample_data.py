"""AIOps 5단계 실습용 합성 데이터 생성기.

이 실습을 위해 새로 작성했다 — output/_통합개념/이상탐지(Anomaly Detection).md가 인용하는
책 부속 실습(03_01_total_exercise.md)의 "payment-gateway가 90~105분 구간에서 서서히
느려지도록(선형 드리프트) 설계"라는 동일한 컨셉을 이 실습만의 독립적인 코드로 재구현한
것이며, 그 실습의 파일을 그대로 복사한 것이 아니다.

생성물:
  services_v1.yaml / services_v2.yaml  — 01_auto_discovery.py용 서비스 매니페스트 두 버전
  metrics.csv                          — 02/03단계용 지연 시간 시계열
  deploys.json                         — 04단계(RCA)용 배포 이력
"""
from __future__ import annotations

import csv
import random
from pathlib import Path

random.seed(42)  # 재현 가능한 실행을 위해 고정

HERE = Path(__file__).resolve().parent

SERVICES_V1 = ["checkout-api", "payment-gateway", "fraud-detector"]
# v2에서는 fraud-detector가 내려가고(서비스 소멸) recommendation-engine이 새로 뜬다(신규 등장)
SERVICES_V2 = ["checkout-api", "payment-gateway", "recommendation-engine"]


def write_services_yaml(path: Path, services: list[str]) -> None:
    lines = ["# 자동 발견 대상 서비스 매니페스트 (실제 클러스터 API 응답을 흉내낸 합성 데이터)"]
    for svc in services:
        lines.append(f"- name: {svc}")
        lines.append(f"  port: {8000 + hash(svc) % 1000}")
        lines.append("  otel_instrumented: true")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def generate_metrics() -> list[dict]:
    rows = []
    for t in range(0, 120):
        for svc in ["checkout-api", "payment-gateway", "fraud-detector"]:
            if svc == "payment-gateway":
                base = 150.0
                if 90 <= t <= 103:
                    # 90~103분 구간에서 선형으로 저하(드리프트) — payment-gateway는 원래도
                    # 다른 서비스보다 느린 편이라는 설정(이상탐지 페이지의 baseline~150~220ms대와
                    # 같은 톤을 이 실습 데이터에서도 유지한다)
                    base = 150.0 + (t - 90) * 12.0
            elif svc == "checkout-api":
                base = 80.0
            else:  # fraud-detector
                base = 110.0
            noise = random.gauss(0, 6.0)
            rows.append({"timestamp": t, "service": svc, "latency_ms": round(max(5.0, base + noise), 1)})
    return rows


def write_metrics_csv(path: Path, rows: list[dict]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["timestamp", "service", "latency_ms"])
        writer.writeheader()
        writer.writerows(rows)


def write_deploys_json(path: Path) -> None:
    import json

    deploys = [
        {"id": "dep-101", "service": "payment-gateway", "time": 88,
         "commits": ["a1b2c3d retry 로직 타임아웃 5s→2s로 단축"]},
        {"id": "dep-102", "service": "checkout-api", "time": 40,
         "commits": ["9f8e7d6 장바구니 캐시 TTL 조정"]},
        {"id": "dep-103", "service": "payment-gateway", "time": 15,
         "commits": ["3c4d5e6 결제 수단 추가(카카오페이)"]},
    ]
    path.write_text(json.dumps(deploys, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    write_services_yaml(HERE / "services_v1.yaml", SERVICES_V1)
    write_services_yaml(HERE / "services_v2.yaml", SERVICES_V2)
    write_metrics_csv(HERE / "metrics.csv", generate_metrics())
    write_deploys_json(HERE / "deploys.json")
    print("생성 완료: services_v1.yaml, services_v2.yaml, metrics.csv, deploys.json")
