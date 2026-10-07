"""
exercise.py — mlflow 실습과제 (빈칸 채우기)

목표: Wine 데이터셋으로 RandomForestClassifier 3종을 학습하면서
      1) 모델 개발  2) 지표/성능 로깅  3) 아티팩트 로깅  4) 모델 로깅+등록
을 전부 mlflow API로 기록한다.

아래 "TODO n" 11개를 채우면 완성이다. 막히면 solution.py를 참고하되,
먼저 README.md의 "출처 개념" 링크와 힌트만 보고 스스로 채워보는 걸 권장한다.

실행: docker compose run --rm trainer python exercise.py
검증: docker compose run --rm verify   (완성 후 체크리스트 자동 확인)
"""

import os

import matplotlib

matplotlib.use("Agg")
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

PARAM_GRID = [
    {"n_estimators": 50, "max_depth": 3},
    {"n_estimators": 100, "max_depth": 5},
    {"n_estimators": 200, "max_depth": None},
]

ARTIFACT_DIR = "artifacts_out"


def load_data():
    X, y = load_wine(return_X_y=True, as_frame=True)
    return train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)


def train_and_log_one_run(params, X_train, X_test, y_train, y_test):
    run_name = f"rf_n{params['n_estimators']}_d{params['max_depth']}"

    with mlflow.start_run(run_name=run_name) as run:
        # TODO 1: params 딕셔너리를 한 번에 기록해라.
        #   힌트: mlflow.log_params(...) — 파라미터 여러 개를 한 번에 로깅하는 API.
        #   (하나씩 기록하려면 mlflow.log_param(key, value)를 여러 번 불러도 되지만,
        #    log_params는 dict 하나로 한 번에 끝낼 수 있다)

        model = RandomForestClassifier(random_state=42, **params)
        model.fit(X_train, y_train)

        y_pred = model.predict(X_test)
        metrics = {
            "accuracy": accuracy_score(y_test, y_pred),
            "precision_macro": precision_score(y_test, y_pred, average="macro"),
            "recall_macro": recall_score(y_test, y_pred, average="macro"),
            "f1_macro": f1_score(y_test, y_pred, average="macro"),
        }
        # TODO 2: metrics 딕셔너리를 한 번에 기록해라.
        #   힌트: mlflow.log_metrics(...) — log_params와 짝이 되는 지표 버전 API.

        os.makedirs(ARTIFACT_DIR, exist_ok=True)

        # 혼동행렬(confusion matrix) 이미지를 파일로 저장
        cm = confusion_matrix(y_test, y_pred)
        fig, ax = plt.subplots(figsize=(5, 4))
        ConfusionMatrixDisplay(cm).plot(ax=ax)
        ax.set_title(run_name)
        cm_path = os.path.join(ARTIFACT_DIR, f"confusion_matrix_{run_name}.png")
        fig.savefig(cm_path, bbox_inches="tight")
        plt.close(fig)
        # TODO 3: 방금 저장한 cm_path 파일을 이 Run의 아티팩트로 업로드해라.
        #   힌트: mlflow.log_artifact(파일경로) — "이미 파일로 존재하는" 로컬 경로를
        #   그대로 Run의 아티팩트 스토어에 복사하는 API.

        # 분류 리포트(precision/recall/f1 per class)를 텍스트로 저장
        report = classification_report(y_test, y_pred)
        report_path = os.path.join(ARTIFACT_DIR, f"classification_report_{run_name}.txt")
        with open(report_path, "w") as f:
            f.write(report)
        # TODO 4: report_path 파일도 TODO 3과 같은 방식으로 아티팩트 업로드해라.

        # TODO 5: 학습된 model 객체를 MLflow 표준 포맷(MLmodel 파일 포함)으로 로깅해라.
        #   힌트: mlflow.sklearn.log_model(model, artifact_path="model")
        #   log_artifact와 다르게, 이 API는 "이미 존재하는 파일"이 아니라
        #   "메모리 안의 model 객체"를 넘긴다 — MLmodel 파일이 자동 생성되고,
        #   그래야 나중에 register_model / mlflow models serve로 이어질 수 있다.

        print(f"[{run_name}] run_id={run.info.run_id} accuracy={metrics['accuracy']:.4f}")
        return {"run_id": run.info.run_id, "run_name": run_name, **metrics}


def main():
    tracking_uri = os.environ.get("MLFLOW_TRACKING_URI", "http://mlflow-server:5000")
    # TODO 6: mlflow가 이 tracking_uri를 쓰도록 설정해라.
    #   힌트: mlflow.set_tracking_uri(tracking_uri)

    # TODO 7: 이 실습 전용 Experiment를 활성화해라. (EXPERIMENT_NAME 상수 사용)
    #   힌트: mlflow.set_experiment(...) — 이름이 없으면 자동 생성된다.

    print(f"[setup] tracking_uri={tracking_uri} experiment={EXPERIMENT_NAME}")

    X_train, X_test, y_train, y_test = load_data()
    print(f"[data] train={len(X_train)} rows, test={len(X_test)} rows, features={X_train.shape[1]}")

    results = [
        train_and_log_one_run(params, X_train, X_test, y_train, y_test)
        for params in PARAM_GRID
    ]

    # TODO 8: results 중 accuracy가 가장 높은 Run을 best 변수에 담아라.
    #   힌트: max(results, key=lambda r: r["accuracy"])
    best = None

    print(f"[select] best run: {best['run_name']} (accuracy={best['accuracy']:.4f})")

    # TODO 9: best run의 model/ 아티팩트를 가리키는 model_uri를 만들고,
    #   Model Registry에 MODEL_NAME으로 새 버전 등록해라.
    #   힌트: model_uri = f"runs:/{best['run_id']}/model"
    #        result = mlflow.register_model(model_uri=model_uri, name=MODEL_NAME)
    result = None
    print(f"[register] {MODEL_NAME} version={result.version} (source=runs:/{best['run_id']}/model)")

    client = MlflowClient()
    # TODO 10: 방금 등록된 버전(result.version)에 alias "champion"을 지정해라.
    #   힌트: client.set_registered_model_alias(name=MODEL_NAME, alias="champion", version=result.version)
    #   (과거엔 stage="Staging"/"Production"을 썼지만 2.9.0부터 deprecated — alias가 표준이다)

    # TODO 11: 검증 지표(예: val_accuracy)를 이 모델 버전의 Tag로 남겨라.
    #   힌트: client.set_model_version_tag(name=MODEL_NAME, version=result.version,
    #                                      key="val_accuracy", value=f"{best['accuracy']:.4f}")

    print(f"[alias] {MODEL_NAME}@champion -> version {result.version}")
    print("[done] mlflow 실습과제 실행 완료")


if __name__ == "__main__":
    main()
