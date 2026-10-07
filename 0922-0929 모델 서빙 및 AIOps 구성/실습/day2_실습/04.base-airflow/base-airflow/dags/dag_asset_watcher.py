"""
process_raw_uploads — AssetWatcher(Airflow Asset Watcher) 개념 실습 DAG.

Asset이 "다른 DAG의 outlets"가 아니라 **외부 소스를 직접 폴링(pull)해서** 갱신되는
구조다: AssetWatcher에 연결된 커스텀 트리거(DirectoryFilePatternTrigger)가 Triggerer
프로세스 안에서 watched_uploads/ 폴더를 3초마다 감시하다가, 새 *.csv 파일이
나타나면 TriggerEvent → raw_uploads Asset 갱신 → 이 DAG 자동 트리거.

asset_producer/consumer(push 방식 — 태스크의 outlets가 Asset을 갱신)와 대비되는
pull 방식이며, 파일을 쓰는 쪽이 Airflow 바깥(사람이 cp해도)이어도 동작한다.
(같은 저장소의 ASSETWATCHER(AIRFLOW ASSET WATCHER)/directory_watcher 실습에서 검증된 패턴)
"""

from __future__ import annotations

from pathlib import Path

from airflow.sdk import DAG, Asset, AssetWatcher, task

# plugins/directory_watcher_trigger.py — dags/가 아니라 plugins/에 있는 이유는
# 그 파일 상단 주석 참고 (Triggerer의 sys.path 문제를 실제로 겪고 옮겼다)
from directory_watcher_trigger import DirectoryFilePatternTrigger

WATCHED_DIR = str(Path(__file__).resolve().parent.parent / "watched_uploads")

# 이 Asset은 outlets가 아니라 watcher(트리거)가 직접 갱신시킨다
raw_uploads_asset = Asset(
    name="raw_uploads",
    watchers=[
        AssetWatcher(
            name="raw_uploads_watcher",
            trigger=DirectoryFilePatternTrigger(
                directory=WATCHED_DIR, pattern="*.csv", poke_interval=3.0
            ),
        )
    ],
)

with DAG(
    dag_id="process_raw_uploads",
    schedule=raw_uploads_asset,  # watcher가 갱신시키는 Asset을 구독
    catchup=False,
    tags=["base-airflow", "asset-watcher"],
):

    @task
    def print_triggering_files(**context):
        """이 DAG를 트리거한 Asset 이벤트(=트리거가 감지한 파일 목록)를 출력한다."""
        for asset, events in context["triggering_asset_events"].items():
            for event in events:
                print(f"[watcher-consumer] Asset '{asset.name}' 갱신 — 감지된 파일: {event.extra}")

    print_triggering_files()
