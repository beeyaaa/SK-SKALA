"""1단계 — 자동 발견(Auto-discovery)

출처: output/_통합개념/자동 발견(Auto-discovery).md — 이 문서 자체가 "(가상 예시)"로만
표시돼 있듯, 책 원문(Observability in the AI-Native Era Ch.1)에는 실행 코드가 없다.
이 스크립트는 그 문서의 6번이 제시한 가상 예시 패턴(클러스터 API를 주기적으로 조회해
새로 나타난/사라진 서비스를 자동으로 목록에 반영)을 이 실습을 위해 실제로 동작하는
코드로 처음부터 새로 작성한 것이다 — 클러스터 API 대신 두 시점의 서비스 매니페스트
YAML(services_v1.yaml → services_v2.yaml)을 실제 파일로 두고 그 차이를 diff하는
방식으로 "watch" 동작을 재현한다.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import DATA_DIR, save_json, BASE_DIR  # noqa: E402


def parse_services_yaml(path: Path) -> set[str]:
    """아주 단순한 YAML 파서 — `- name: xxx` 줄만 뽑아낸다(외부 라이브러리 없이 표준 라이브러리만 사용)."""
    names = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("- name:"):
            names.add(line.split(":", 1)[1].strip())
    return names


def diff_targets(previous: set[str], current: set[str]) -> tuple[set[str], set[str]]:
    added = current - previous
    removed = previous - current
    return added, removed


def main() -> None:
    v1 = parse_services_yaml(DATA_DIR / "services_v1.yaml")
    v2 = parse_services_yaml(DATA_DIR / "services_v2.yaml")

    print(f"[t=0] 클러스터 API 1차 조회 → 발견된 서비스: {sorted(v1)}")
    added, removed = diff_targets(set(), v1)
    print(f"      신규 등록(ADDED): {sorted(added)}")

    print(f"\n[t=1] 클러스터 API 2차 조회(watch) → 발견된 서비스: {sorted(v2)}")
    added, removed = diff_targets(v1, v2)
    print(f"      신규 등록(ADDED): {sorted(added) or '없음'}")
    print(f"      소멸 감지(REMOVED): {sorted(removed) or '없음'}")

    target_list = sorted(v2)
    out_path = BASE_DIR / "logs" / "discovered_targets.json"
    save_json(out_path, {
        "final_target_list": target_list,
        "added_at_t1": sorted(added),
        "removed_at_t1": sorted(removed),
    })
    print(f"\n최종 모니터링 대상 목록({len(target_list)}개)을 {out_path.relative_to(BASE_DIR)}에 저장했다.")
    print("이 목록이 2단계(베이스라이닝)·3단계(이상탐지)의 입력이 된다.")


if __name__ == "__main__":
    main()
