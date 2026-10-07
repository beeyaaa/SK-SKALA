"""
ml_serving_pipeline — Pipeline Model Serving을 Airflow DAG로 구현한 메인 실습 DAG.

복잡한 ML 작업(수집→전처리→학습→평가→서빙)을 여러 단계(Pipeline Stage)로 쪼개고,
각 단계를 Airflow 태스크로 정의해 >> 연산자로 실행 순서를 그래프(DAG)로 선언한다.

이 DAG 하나가 다음 개념들을 전부 시연한다:
  - Pipeline Model Serving : t6_serve_smoke_test까지 이어지는 다단계 서빙 구조
  - DAG                    : 시작점 1개(t1) → 팬아웃([t3,t4]) → 팬인(t5) → 끝점 1개(t6)
  - Pipeline Stage         : t1 >> t2 >> [t3, t4] >> t5 >> t6 의 각 노드
  - BashOperator           : t1_ingest — 셸 명령을 그대로 태스크로
  - PythonOperator         : t2~t6 — Python 함수를 태스크로
  - Many-to-one Dependency : [t3_train_logreg, t4_train_rf] >> t5_evaluate_select
  - schedule(@daily)       : Scheduler가 매일 자동 실행 (unpause 직후 최근 구간 1회 자동 생성)
"""

from __future__ import annotations

import pickle
from datetime import datetime
from pathlib import Path

from airflow.models.dag import DAG
from airflow.providers.standard.operators.bash import BashOperator
from airflow.providers.standard.operators.python import PythonOperator

# 이 실습 폴더(base-airflow/) 기준 데이터 경로 — 모든 스테이지가 파일로 산출물을 주고받는다
DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def preprocess():
    """t2: Iris 데이터를 로드해 표준화하고, 이후 스테이지가 쓸 features.npz로 저장한다."""
    import numpy as np
    from sklearn.datasets import load_iris
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import StandardScaler

    X, y = load_iris(return_X_y=True)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=0, stratify=y
    )
    scaler = StandardScaler().fit(X_train)
    np.savez(
        DATA_DIR / "features.npz",
        X_train=scaler.transform(X_train).astype("float32"),
        X_test=scaler.transform(X_test).astype("float32"),
        y_train=y_train,
        y_test=y_test,
    )
    print(f"[preprocess] features.npz 저장 완료 (train={len(y_train)}, test={len(y_test)})")


def train_model(model_name: str):
    """t3/t4: features.npz를 읽어 모델 하나를 학습하고, 정확도를 반환(→ XCom)한다.

    반환값이 Metastore(SQLite)의 xcom 테이블에 저장되고, t5가 xcom_pull로 읽는다.
    """
    import numpy as np

    data = np.load(DATA_DIR / "features.npz")
    if model_name == "logreg":
        from sklearn.linear_model import LogisticRegression
        model = LogisticRegression(max_iter=300, random_state=0)
    else:
        from sklearn.ensemble import RandomForestClassifier
        model = RandomForestClassifier(random_state=0)

    model.fit(data["X_train"], data["y_train"])
    acc = float((model.predict(data["X_test"]) == data["y_test"]).mean())

    with open(DATA_DIR / f"model_{model_name}.pkl", "wb") as f:
        pickle.dump(model, f)
    print(f"[train:{model_name}] 테스트 정확도={acc:.4f} -> model_{model_name}.pkl 저장")
    return acc  # ← XCom으로 Metastore에 저장된다


def evaluate_select(ti):
    """t5: 팬인(many-to-one) 지점 — 두 학습 태스크의 XCom(정확도)을 모아 최고 모델을 고른다."""
    import shutil

    accs = ti.xcom_pull(task_ids=["t3_train_logreg", "t4_train_rf"])
    candidates = dict(zip(["logreg", "rf"], accs))
    best = max(candidates, key=candidates.get)
    shutil.copy(DATA_DIR / f"model_{best}.pkl", DATA_DIR / "best_model.pkl")
    print(f"[evaluate] 후보 정확도={candidates} -> best={best} (best_model.pkl로 승격)")
    return best


def serve_smoke_test():
    """t6: 서빙 스테이지 — 승격된 best_model.pkl을 로드해 실제 predict가 되는지 확인한다."""
    import numpy as np

    with open(DATA_DIR / "best_model.pkl", "rb") as f:
        model = pickle.load(f)
    data = np.load(DATA_DIR / "features.npz")
    sample_X, sample_y = data["X_test"][:3], data["y_test"][:3]
    pred = model.predict(sample_X)
    print(f"[serve] smoke test — 실제={list(sample_y)} 예측={list(pred)}")
    assert list(pred) == list(sample_y), "서빙 smoke test 실패"
    print("[serve] smoke test 통과 ✅ — 파이프라인 끝단에서 서빙 가능 상태 확인")


with DAG(
    dag_id="ml_serving_pipeline",
    description="Pipeline Model Serving 실습 — 수집→전처리→학습x2→평가→서빙 6단계",
    start_date=datetime(2024, 1, 1),
    schedule="@daily",          # Scheduler가 매일 자동 실행 (schedule_interval 개념)
    catchup=False,              # 과거 구간 전부가 아니라 최근 구간만
    tags=["base-airflow", "pipeline-model-serving"],
) as dag:
    # t1: BashOperator — 셸 명령을 그대로 Airflow 태스크로 등록
    t1_ingest = BashOperator(
        task_id="t1_ingest",
        bash_command=(
            f"mkdir -p '{DATA_DIR}' && "
            f"date -u +%FT%TZ > '{DATA_DIR}/ingest_marker.txt' && "
            f"echo '[ingest] 원천 데이터 수집 완료 (marker 기록)'"
        ),
    )

    # t2~t6: PythonOperator — Python 함수를 Airflow 태스크로 실행
    t2_preprocess = PythonOperator(task_id="t2_preprocess", python_callable=preprocess)
    t3_train_logreg = PythonOperator(
        task_id="t3_train_logreg", python_callable=train_model, op_kwargs={"model_name": "logreg"}
    )
    t4_train_rf = PythonOperator(
        task_id="t4_train_rf", python_callable=train_model, op_kwargs={"model_name": "rf"}
    )
    t5_evaluate_select = PythonOperator(task_id="t5_evaluate_select", python_callable=evaluate_select)
    t6_serve_smoke_test = PythonOperator(task_id="t6_serve_smoke_test", python_callable=serve_smoke_test)

    # DAG 구조: 시작점 1개 → 팬아웃 → 팬인(many-to-one) → 끝점 1개
    t1_ingest >> t2_preprocess >> [t3_train_logreg, t4_train_rf] >> t5_evaluate_select >> t6_serve_smoke_test
