"""
sensor_wait_for_file — Sensor 개념 실습 DAG.

Sensor는 "특정 상태가 될 때까지 주기적으로 폴링(poke)하는 Operator의 한 종류"다.
FileSensor가 watched_uploads/trigger.txt 가 나타날 때까지 poke_interval=3초마다
확인하고, 파일이 생기면 그제서야 다음 태스크(process_file)로 넘어간다.

run.sh가 DAG 트리거 후 15초 뒤에 파일을 생성하므로, 태스크 로그에 poke 시도가
여러 번 찍힌 뒤 성공하는 것("아직 없음 → 재시도 → 감지")을 실제로 볼 수 있다.
(같은 저장소의 SENSOR(AIRFLOW SENSOR)/base 실습에서 검증된 패턴)
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from airflow.models.dag import DAG
from airflow.providers.standard.operators.bash import BashOperator
from airflow.providers.standard.sensors.filesystem import FileSensor

# filepath가 절대경로면 fs_default 커넥션의 basepath와 무관하게 이 경로를 가리킨다
WATCH_FILE = str(Path(__file__).resolve().parent.parent / "watched_uploads" / "trigger.txt")

with DAG(
    dag_id="sensor_wait_for_file",
    description="Sensor 실습 — trigger.txt가 나타날 때까지 3초마다 poke",
    start_date=datetime(2024, 1, 1),
    schedule=None,
    catchup=False,
    tags=["base-airflow", "sensor"],
) as dag:
    wait_for_file = FileSensor(
        task_id="wait_for_file",
        fs_conn_id="fs_default",
        filepath=WATCH_FILE,
        poke_interval=3,   # 3초마다 존재 여부 확인(poke)
        timeout=60,        # 60초 안에 안 나타나면 실패
        mode="poke",       # poke 모드 — 대기하는 동안 Worker 슬롯을 점유
    )

    process_file = BashOperator(
        task_id="process_file",
        bash_command=f"echo '[process] 감지된 파일 내용:' && cat '{WATCH_FILE}'",
    )

    # Sensor가 게이트 역할 — 파일이 생겨야만 후속 처리가 실행된다
    wait_for_file >> process_file
