"""
invalid_cycle_demo — DAG의 "A(Acyclic, 순환 없음)"가 강제 규칙임을 증명하는 반례 DAG.

t_a >> t_b >> t_a 로 일부러 순환을 만들면, 이 파일은 dag-processor의 파싱 단계에서
거부되어 DAG 목록에 아예 등록되지 않는다 — `airflow dags list-import-errors`에
"Cycle detected" 에러로 나타나는 것이 이 실습의 검증 포인트다.

(즉 이 파일이 "에러로 남아있는 것"이 정상이다 — 순환이 있으면 어떤 태스크를 먼저
실행해야 할지 결정할 수 없으므로, Airflow는 실행 시도조차 하지 않고 파싱에서 막는다.)
"""

from __future__ import annotations

from datetime import datetime

from airflow.models.dag import DAG
from airflow.providers.standard.operators.bash import BashOperator

with DAG(
    dag_id="invalid_cycle_demo",
    description="순환이 있는 그래프는 DAG가 될 수 없음을 보여주는 반례",
    start_date=datetime(2024, 1, 1),
    schedule=None,
    catchup=False,
    tags=["base-airflow", "dag-반례"],
) as dag:
    t_a = BashOperator(task_id="t_a", bash_command="echo a")
    t_b = BashOperator(task_id="t_b", bash_command="echo b")

    t_a >> t_b
    t_b >> t_a  # ← 순환! 파싱 단계에서 "Cycle detected"로 거부된다
