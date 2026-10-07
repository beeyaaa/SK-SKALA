"""
solution.py — mlflow 실습과제 "정답" 스크립트.

exercise.py의 TODO 11개를 전부 채우면 이 파일과 동일하게 동작해야 한다.
막히면 이 파일을 참고하되, 먼저 exercise.py를 스스로 채워보는 것을 권장한다.

이 스크립트 하나로 아래 4가지 기능을 전부 연습한다.
  1) 모델 개발      — Wine 데이터셋으로 RandomForestClassifier 3종 학습
  2) 지표/성능 로깅  — log_params + log_metrics (accuracy/precision/recall/f1)
  3) 아티팩트 로깅   — confusion_matrix.png, classification_report.txt
  4) 모델 로깅+등록  — log_model → 3개 Run 중 최고 성능 선택 → register_model
                       → Alias(champion) 지정 → Tag 기록
"""

import os

import matplotlib

matplotlib.use("Agg")  # 컨테이너 안에는 디스플레이가 없으므로 파일로만 저장
import matplotlib.pyplot as plt
import mlflow
import mlflow.sklearn
from mlflow import MlflowClient
from sklearn.datasets import load_wine
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split

EXPERIMENT_NAME = "wine-quality-rf"
MODEL_NAME = "wine_rf_classifier"

# 비교해볼 하이퍼파라미터 3가지 조합 — 각각 별도의 mlflow Run으로 기록되어
# Tracking UI에서 "Compare Runs"로 나란히 비교할 수 있게 된다.
PARAM_GRID = [
    {"n_estimators": 50, "max_depth": 3},
    {"n_estimators": 100, "max_depth": 5},
    {"n_estimators": 200, "max_depth": None},
]

ARTIFACT_DIR = "artifacts_out"


def load_data():
    """Wine 데이터셋(178 샘플, 13 특성, 3개 클래스)을 train/test로 분리한다."""
    X, y = load_wine(return_X_y=True, as_frame=True)
    return train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)


def train_and_log_one_run(params, X_train, X_test, y_train, y_test):
    """
    하이퍼파라미터 하나(params)로 모델 하나를 학습하고, 그 결과를 mlflow Run
    하나에 전부 기록한다. 반환값은 이후 "최고 성능 Run 고르기" 단계에서 쓴다.
    """
    run_name = f"rf_n{params['n_estimators']}_d{params['max_depth']}"

    with mlflow.start_run(run_name=run_name) as run:
        # ── ① 모델 개발: 하이퍼파라미터 기록 + 학습 ──────────────────────
        mlflow.log_params(params)

        model = RandomForestClassifier(random_state=42, **params)
        model.fit(X_train, y_train)

        # ── ② 성능 지표 계산 + 로깅 ──────────────────────────────────────
        y_pred = model.predict(X_test)
        metrics = {
            "accuracy": accuracy_score(y_test, y_pred),
            "precision_macro": precision_score(y_test, y_pred, average="macro"),
            "recall_macro": recall_score(y_test, y_pred, average="macro"),
            "f1_macro": f1_score(y_test, y_pred, average="macro"),
        }
        mlflow.log_metrics(metrics)

        # ── ③ 아티팩트 로깅: 혼동행렬 PNG + 분류 리포트 TXT ──────────────
        os.makedirs(ARTIFACT_DIR, exist_ok=True)

        cm = confusion_matrix(y_test, y_pred)
        fig, ax = plt.subplots(figsize=(5, 4))
        ConfusionMatrixDisplay(cm).plot(ax=ax)
        ax.set_title(run_name)
        cm_path = os.path.join(ARTIFACT_DIR, f"confusion_matrix_{run_name}.png")
        fig.savefig(cm_path, bbox_inches="tight")
        plt.close(fig)
        mlflow.log_artifact(cm_path)

        report = classification_report(y_test, y_pred)
        report_path = os.path.join(ARTIFACT_DIR, f"classification_report_{run_name}.txt")
        with open(report_path, "w") as f:
            f.write(report)
        mlflow.log_artifact(report_path)

        # ── ④ 모델 로깅: 학습된 model 객체를 MLflow 표준 포맷(MLmodel)으로 저장 ──
        mlflow.sklearn.log_model(model, artifact_path="model")

        print(f"[{run_name}] run_id={run.info.run_id} accuracy={metrics['accuracy']:.4f}")
        return {"run_id": run.info.run_id, "run_name": run_name, **metrics}


def main():
    tracking_uri = os.environ.get("MLFLOW_TRACKING_URI", "http://mlflow-server:5000")
    mlflow.set_tracking_uri(tracking_uri)
    mlflow.set_experiment(EXPERIMENT_NAME)
    print(f"[setup] tracking_uri={tracking_uri} experiment={EXPERIMENT_NAME}")

    X_train, X_test, y_train, y_test = load_data()
    print(f"[data] train={len(X_train)} rows, test={len(X_test)} rows, features={X_train.shape[1]}")

    # 하이퍼파라미터 3종을 각각 별도 Run으로 학습·기록
    results = [
        train_and_log_one_run(params, X_train, X_test, y_train, y_test)
        for params in PARAM_GRID
    ]

    # ── 최고 성능 Run 선택 ────────────────────────────────────────────────
    best = max(results, key=lambda r: r["accuracy"])
    print(f"[select] best run: {best['run_name']} (accuracy={best['accuracy']:.4f})")

    # ── 모델 등록: 최고 성능 Run의 model/ 폴더를 Model Registry에 새 버전으로 등록 ──
    model_uri = f"runs:/{best['run_id']}/model"
    result = mlflow.register_model(model_uri=model_uri, name=MODEL_NAME)
    print(f"[register] {MODEL_NAME} version={result.version} (source={model_uri})")

    # ── Alias(champion) 지정 + 검증 지표를 Tag로 기록 (2.9.0+ 권장 방식) ────
    client = MlflowClient()
    client.set_registered_model_alias(name=MODEL_NAME, alias="champion", version=result.version)
    client.set_model_version_tag(
        name=MODEL_NAME, version=result.version,
        key="val_accuracy", value=f"{best['accuracy']:.4f}",
    )
    print(f"[alias] {MODEL_NAME}@champion -> version {result.version}")
    print("[done] mlflow 실습과제 정답 스크립트 실행 완료")


if __name__ == "__main__":
    main()
