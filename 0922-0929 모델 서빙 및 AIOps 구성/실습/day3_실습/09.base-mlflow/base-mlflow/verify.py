"""
verify.py — exercise.py(또는 solution.py) 실행 결과가 실습 체크리스트를
전부 충족했는지 mlflow API로 직접 확인하는 자동 채점 스크립트.

MlflowClient/REST API로 실제 서버 상태를 조회하기 때문에, "코드는 에러 없이
끝났지만 사실 아무것도 안 남았다"는 실수(예: log_metrics를 안 부르고도
try/except로 감싸 통과한 척)까지 잡아낸다.

실행: docker compose run --rm verify
"""

import sys

import mlflow
from mlflow import MlflowClient

EXPERIMENT_NAME = "wine-quality-rf"
MODEL_NAME = "wine_rf_classifier"
REQUIRED_PARAM_KEYS = {"n_estimators", "max_depth"}
REQUIRED_METRIC_KEYS = {"accuracy", "precision_macro", "recall_macro", "f1_macro"}

checks = []  # (통과여부, 설명)


def check(label, condition):
    checks.append((bool(condition), label))
    mark = "✅" if condition else "❌"
    print(f"{mark} {label}")


def main():
    mlflow.set_tracking_uri(
        __import__("os").environ.get("MLFLOW_TRACKING_URI", "http://mlflow-server:5000")
    )
    client = MlflowClient()

    print("=" * 70)
    print("1) Experiment / Run 확인")
    print("=" * 70)
    exp = client.get_experiment_by_name(EXPERIMENT_NAME)
    check(f"Experiment '{EXPERIMENT_NAME}' 존재", exp is not None)
    if exp is None:
        print_summary_and_exit()
        return

    runs = client.search_runs([exp.experiment_id], order_by=["start_time DESC"])
    check(f"Run이 3개 이상 기록됨 (실제: {len(runs)}개)", len(runs) >= 3)

    if runs:
        latest = runs[0]
        param_keys = set(latest.data.params.keys())
        metric_keys = set(latest.data.metrics.keys())
        check(
            f"파라미터 로깅 확인 ({sorted(REQUIRED_PARAM_KEYS)} 포함)",
            REQUIRED_PARAM_KEYS.issubset(param_keys),
        )
        check(
            f"지표 로깅 확인 ({sorted(REQUIRED_METRIC_KEYS)} 포함)",
            REQUIRED_METRIC_KEYS.issubset(metric_keys),
        )

        artifact_paths = {a.path for a in client.list_artifacts(latest.info.run_id)}
        has_cm = any(p.endswith(".png") for p in artifact_paths)
        has_report = any(p.endswith(".txt") for p in artifact_paths)
        has_model_dir = "model" in artifact_paths
        check("아티팩트 로깅 확인 (혼동행렬 PNG)", has_cm)
        check("아티팩트 로깅 확인 (분류 리포트 TXT)", has_report)
        check("모델 로깅 확인 (model/ 폴더 + MLmodel)", has_model_dir)

        if has_model_dir:
            model_files = {a.path for a in client.list_artifacts(latest.info.run_id, "model")}
            check("model/ 안에 MLmodel 파일 존재", "model/MLmodel" in model_files)

    print()
    print("=" * 70)
    print("2) Model Registry 확인")
    print("=" * 70)
    try:
        rm = client.get_registered_model(MODEL_NAME)
        check(f"등록된 모델 '{MODEL_NAME}' 존재", rm is not None)
    except Exception:
        check(f"등록된 모델 '{MODEL_NAME}' 존재", False)
        print_summary_and_exit()
        return

    versions = list(client.search_model_versions(f"name='{MODEL_NAME}'"))
    check(f"모델 버전이 1개 이상 등록됨 (실제: {len(versions)}개)", len(versions) >= 1)

    try:
        champion = client.get_model_version_by_alias(MODEL_NAME, "champion")
        check(f"Alias 'champion'이 버전에 지정됨 (version={champion.version})", True)
        tags = champion.tags or {}
        check(f"등록된 버전에 val_accuracy Tag 존재 (실제: {tags.get('val_accuracy')})", "val_accuracy" in tags)
    except Exception:
        check("Alias 'champion'이 버전에 지정됨", False)
        champion = None

    print()
    print("=" * 70)
    print("3) 등록된 모델로 실제 추론(round-trip) 확인")
    print("=" * 70)
    if champion is not None:
        try:
            from sklearn.datasets import load_wine

            model_uri = f"models:/{MODEL_NAME}@champion"
            loaded = mlflow.pyfunc.load_model(model_uri)
            X, _ = load_wine(return_X_y=True, as_frame=True)
            pred = loaded.predict(X.iloc[:3])
            check(f"models:/{MODEL_NAME}@champion 로드 + predict 성공 (예측: {list(pred)})", True)
        except Exception as e:
            check(f"models:/{MODEL_NAME}@champion 로드 + predict 성공 ({e})", False)

    print_summary_and_exit()


def print_summary_and_exit():
    print()
    print("=" * 70)
    passed = sum(1 for ok, _ in checks if ok)
    total = len(checks)
    print(f"결과: {passed}/{total} 통과")
    if passed == total and total > 0:
        print("🎉 전체 체크리스트 통과 — 실습과제 완료!")
        sys.exit(0)
    else:
        print("⚠️  아직 통과하지 못한 항목이 있다 — exercise.py의 TODO를 다시 확인해라.")
        sys.exit(1)


if __name__ == "__main__":
    main()
