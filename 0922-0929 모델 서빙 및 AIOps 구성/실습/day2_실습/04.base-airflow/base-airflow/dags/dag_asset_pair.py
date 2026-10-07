"""
asset_producer / asset_consumer — Asset(Airflow Asset) 개념 실습 DAG 한 쌍.

cron이 아니라 "데이터가 갱신됐다"는 이벤트로 DAG를 잇는다:
  - asset_producer 가 report_source.csv 를 쓰고 outlets=[report_asset] 으로 Asset 갱신
  - asset_consumer 는 schedule=[report_asset] — cron 없이 Asset 이벤트만으로 자동 트리거

검증 포인트: consumer의 run_id가 manual__ 이 아니라 **asset_triggered__** 로 시작한다.
(같은 저장소의 MLFLOW/dag3 실습에서 검증된 것과 동일한 패턴)
"""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

from airflow.sdk import DAG, Asset, task

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# 두 DAG 사이의 유일한 결합점 — "report_source 데이터가 갱신됐다"는 사실 자체를 표현
report_asset = Asset("report_source")


with DAG(
    dag_id="asset_producer",
    start_date=datetime(2024, 1, 1),
    schedule=None,  # 실습에선 수동 트리거 (실전이라면 @daily 등)
    catchup=False,
    tags=["base-airflow", "asset"],
):

    @task(outlets=[report_asset])  # 이 태스크 성공 = report_asset 갱신 이벤트 발생
    def write_report_source():
        DATA_DIR.mkdir(exist_ok=True)
        path = DATA_DIR / "report_source.csv"
        with open(path, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(["item", "qty"])
            w.writerows([["apple", 3], ["banana", 5], ["cherry", 2]])
        print(f"[producer] {path} 작성 완료 -> outlets로 report_asset 갱신 이벤트 발생")

    write_report_source()


with DAG(
    dag_id="asset_consumer",
    schedule=[report_asset],  # ← cron이 아니라 Asset 이벤트가 스케줄
    catchup=False,
    tags=["base-airflow", "asset"],
):

    @task
    def summarize_report(**context):
        # 나를 트리거한 Asset 이벤트 확인 (어떤 데이터 갱신 때문에 실행됐는가)
        for asset, events in context["triggering_asset_events"].items():
            print(f"[consumer] 트리거한 Asset: {asset.name} (이벤트 {len(events)}건)")

        with open(DATA_DIR / "report_source.csv") as f:
            rows = list(csv.DictReader(f))
        total = sum(int(r["qty"]) for r in rows)
        print(f"[consumer] report_source.csv {len(rows)}행 읽음 — qty 합계={total}")

    summarize_report()
