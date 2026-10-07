"""2단계 — 베이스라이닝(Baselining)

출처: output/_통합개념/BASELINING(베이스라이닝).md 6번의 `baseline_alert` YAML은 원문
주석에 스스로 "개념적 표현"이라 밝힌 선언적 예시라 실행 가능한 코드가 아니다. 이 스크립트는
그 YAML이 선언하는 3가지 방식(자동 적응형=롤링 윈도우, 다차원=서비스별 개별 계산, 계절=
이 실습에서는 시간 정보가 단순 분 단위라 생략) 중 자동 적응형·다차원 두 가지를 실제로
동작하는 코드로 이 실습을 위해 새로 작성했다.
"""
from __future__ import annotations

import statistics
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import BASE_DIR, DATA_DIR, load_json, load_metrics_csv, save_json  # noqa: E402

WINDOW = 10  # 3단계(이상탐지)와 동일한 윈도우 크기로 맞춘다


def main() -> None:
    targets = load_json(BASE_DIR / "logs" / "discovered_targets.json")["final_target_list"]
    points = load_metrics_csv(DATA_DIR / "metrics.csv")

    by_service: dict[str, list[float]] = defaultdict(list)
    for p in points:
        if p.service in targets:
            by_service[p.service].append(p.latency_ms)

    baselines = {}
    print(f"윈도우={WINDOW}, 대상 서비스={sorted(by_service)}\n")
    for svc, values in sorted(by_service.items()):
        if len(values) <= WINDOW:
            print(f"  {svc}: 데이터가 윈도우보다 적어 건너뜀")
            continue
        recent_window = values[-WINDOW:]
        mean = statistics.fmean(recent_window)
        stdev = statistics.pstdev(recent_window) or 1e-6
        baselines[svc] = {"mean": round(mean, 1), "stdev": round(stdev, 2), "window": WINDOW}
        print(f"  {svc:20s} 최근 {WINDOW}개 기준선 → mean={mean:.1f}ms, stdev={stdev:.2f}ms")

    out_path = BASE_DIR / "logs" / "baselines.json"
    save_json(out_path, baselines)
    print(f"\n서비스별 기준선을 {out_path.relative_to(BASE_DIR)}에 저장했다 — 3단계 이상탐지가 이 기준선의 개념(mean/stdev)을 그대로 다시 계산해 시점마다 적용한다.")


if __name__ == "__main__":
    main()
