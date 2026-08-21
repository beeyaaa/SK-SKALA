"""4단계 전처리 Pipeline·모델 비교 Jupyter Notebook을 재생성한다."""

from pathlib import Path

import nbformat as nbf


PROJECT_ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_PATH = PROJECT_ROOT / "notebooks" / "04_modeling.ipynb"


def build_notebook() -> nbf.NotebookNode:
    """단일/다변수 로지스틱 모델 비교 노트북을 구성한다."""
    notebook = nbf.v4.new_notebook()
    notebook.metadata["kernelspec"] = {
        "display_name": "Python 3",
        "language": "python",
        "name": "python3",
    }
    notebook.metadata["language_info"] = {"name": "python", "version": "3.14"}

    notebook.cells = [
        nbf.v4.new_markdown_cell(
            "# 04. 전처리 Pipeline과 단일·다변수 모델 비교\n\n"
            "## tl;dr\n\n"
            "- 5-fold CV에서 `age` 단일 모델의 평균 ROC-AUC가 **0.855**로 가장 높았습니다.\n"
            "- 테스트 ROC-AUC는 나이 단일 모델 **0.858**, 다변수 모델 **0.861**입니다.\n"
            "- AUC 개선은 **0.0028**이고 bootstrap 95% CI는 약 **[-0.0003, 0.0063]**으로, "
            "사전 기준 0.02를 넘지 못했습니다.\n"
            "- 따라서 이번 로지스틱 회귀 비교에서는 H0를 기각할 충분한 근거가 없습니다."
        ),
        nbf.v4.new_markdown_cell(
            "## Context & Methods\n\n"
            "단일 모델과 다변수 모델 모두 LogisticRegression을 사용하여 알고리즘 차이가 아니라 "
            "추가 특성의 정보 이득을 비교합니다.\n\n"
            "### Key Assumptions\n\n"
            "- 숫자형: median 대치 → 표준화\n"
            "- `capital-gain/loss`: median 대치 → log1p → 표준화\n"
            "- 범주형: `Unknown` 대치 → One-Hot Encoding\n"
            "- 전처리는 각 CV 훈련 fold 안에서만 학습됩니다.\n"
            "- H0 기각을 위한 실질적 개선 기준은 AUC 0.02 초과입니다."
        ),
        nbf.v4.new_code_cell(
            "from pathlib import Path\n"
            "import contextlib\n"
            "import io\n"
            "import sys\n\n"
            "import joblib\n"
            "import pandas as pd\n"
            "from IPython.display import Image, display\n\n"
            "project_root = Path.cwd()\n"
            "if project_root.name == 'notebooks':\n"
            "    project_root = project_root.parent\n"
            "if not (project_root / 'src').exists():\n"
            "    raise RuntimeError('adult-marriage-analysis 프로젝트 루트에서 실행하세요.')\n"
            "sys.path.insert(0, str(project_root))\n\n"
            "from src.data import add_target_pandas, ensure_raw_data, load_with_pandas\n"
            "from src.features import BASE_FEATURES, build_preprocessing_audit\n"
            "from src.modeling import run_modeling_stage\n"
            "from src.statistics import split_prepared_data\n"
            "from src.visualization import (\n"
            "    create_calibration_chart,\n"
            "    create_preprocessing_diagnostics,\n"
            ")"
        ),
        nbf.v4.new_markdown_cell("## Data\n\n### 1. 동일한 train/test 분할 재현"),
        nbf.v4.new_code_cell(
            "raw_path = ensure_raw_data(project_root / 'data' / 'raw')\n"
            "prepared_df = add_target_pandas(load_with_pandas(raw_path))\n"
            "train_df, test_df = split_prepared_data(prepared_df)\n\n"
            "print('Train:', train_df.shape)\n"
            "print('Test:', test_df.shape)\n"
            "print('Base features:', BASE_FEATURES)"
        ),
        nbf.v4.new_markdown_cell(
            "### 2. 전처리 전·후 진단\n\n"
            "결측치는 Pipeline 내부 imputer로 제거하고, 0이 아닌 `capital-gain`의 긴 꼬리는 "
            "`log1p`로 완화한 뒤 표준화합니다. 차트의 after 값은 대치 단계 직후를 의미합니다."
        ),
        nbf.v4.new_code_cell(
            "preprocessing_audit = build_preprocessing_audit(train_df)\n"
            "preprocessing_audit.to_csv(\n"
            "    project_root / 'reports' / 'tables' / 'preprocessing_audit.csv',\n"
            "    index=False,\n"
            ")\n"
            "preprocessing_audit"
        ),
        nbf.v4.new_code_cell(
            "preprocessing_path = create_preprocessing_diagnostics(\n"
            "    train_df,\n"
            "    project_root / 'reports' / 'figures' / 'preprocessing_diagnostics.png',\n"
            ")\n"
            "display(Image(filename=str(preprocessing_path)))"
        ),
        nbf.v4.new_markdown_cell("## Results\n\n### 3. 5-fold 단일 특성 선택과 최종 평가"),
        nbf.v4.new_code_cell(
            "captured_output = io.StringIO()\n"
            "with contextlib.redirect_stdout(captured_output):\n"
            "    modeling = run_modeling_stage(project_root, train_df, test_df)\n\n"
            "print('선택된 최적 단일 특성:', modeling.best_feature)\n"
            "modeling.single_cv.round(4)"
        ),
        nbf.v4.new_markdown_cell("### 4. 테스트 성능 비교"),
        nbf.v4.new_code_cell("modeling.model_metrics.round(4)"),
        nbf.v4.new_markdown_cell(
            "Accuracy와 F1은 소폭 개선됐지만, 확률 구분력인 ROC-AUC 개선은 0.0028에 불과합니다. "
            "Brier score는 낮을수록 좋으며 다변수 모델에서 0.1376에서 0.1345로 감소했습니다."
        ),
        nbf.v4.new_markdown_cell("### 5. 가설 판단"),
        nbf.v4.new_code_cell("modeling.hypothesis_result.round(4)"),
        nbf.v4.new_markdown_cell(
            "`auc_delta`가 0.02보다 작고 신뢰구간도 0.02를 포함하지 않으므로, "
            "다변수 모델이 실질적으로 더 우수하다는 H1을 지지하지 못합니다. "
            "이는 H0가 참임을 증명한 것이 아니라 H0를 기각할 근거가 부족하다는 의미입니다."
        ),
        nbf.v4.new_markdown_cell("### 6. 로지스틱 계수와 원본 특성 중요도"),
        nbf.v4.new_code_cell(
            "logistic_coefficients = pd.read_csv(\n"
            "    project_root / 'reports' / 'tables' / 'logistic_coefficients.csv'\n"
            ")\n"
            "logistic_coefficients.head(15).round(4)"
        ),
        nbf.v4.new_code_cell(
            "permutation_importance = pd.read_csv(\n"
            "    project_root / 'reports' / 'tables' / 'permutation_importance.csv'\n"
            ")\n"
            "permutation_importance.round(4)"
        ),
        nbf.v4.new_markdown_cell(
            "Permutation importance에서도 나이를 섞었을 때 AUC가 약 0.310 감소해, "
            "다변수 모델이 사실상 나이에 크게 의존하고 있음을 확인할 수 있습니다."
        ),
        nbf.v4.new_markdown_cell("### 7. 테스트 확률 calibration"),
        nbf.v4.new_code_cell(
            "calibration_path = create_calibration_chart(\n"
            "    modeling.y_test,\n"
            "    modeling.single_probabilities,\n"
            "    modeling.multivariable_probabilities,\n"
            "    project_root / 'reports' / 'figures' / 'calibration_curve.png',\n"
            ")\n"
            "display(Image(filename=str(calibration_path)))"
        ),
        nbf.v4.new_markdown_cell("### 8. 예시 인물의 혼인 경험 확률 출력"),
        nbf.v4.new_code_cell(
            "example_person = pd.DataFrame([\n"
            "    {\n"
            "        'age': 35,\n"
            "        'education-num': 13,\n"
            "        'hours-per-week': 40,\n"
            "        'capital-gain': 0,\n"
            "        'capital-loss': 0,\n"
            "        'workclass': 'Private',\n"
            "        'occupation': 'Prof-specialty',\n"
            "    }\n"
            "])\n"
            "example_probability = modeling.multivariable_model.predict_proba(\n"
            "    example_person[BASE_FEATURES]\n"
            ")[0, 1]\n\n"
            "print(f'조사 시점까지 혼인 경험이 있을 추정 확률: {example_probability:.1%}')"
        ),
        nbf.v4.new_markdown_cell(
            "위 값은 1994년 미국 표본에서 유사한 특성을 가진 사람이 조사 시점까지 혼인했을 "
            "추정 확률이며, 이 사람의 미래 결혼 확률이 아닙니다."
        ),
        nbf.v4.new_markdown_cell("## Checks\n\nPipeline, 저장 모델, 확률 범위와 가설 결과를 자동 검증합니다."),
        nbf.v4.new_code_cell(
            "single_path = project_root / 'models' / 'single_feature_logistic.joblib'\n"
            "multi_path = project_root / 'models' / 'multivariable_logistic.joblib'\n"
            "loaded_model = joblib.load(multi_path)\n"
            "loaded_probability = loaded_model.predict_proba(example_person[BASE_FEATURES])[0, 1]\n\n"
            "assert modeling.best_feature == 'age'\n"
            "assert single_path.exists() and multi_path.exists()\n"
            "assert 0 <= example_probability <= 1\n"
            "assert abs(loaded_probability - example_probability) < 1e-12\n"
            "assert not bool(modeling.hypothesis_result.loc[0, 'exceeds_practical_margin'])\n"
            "assert preprocessing_path.exists() and preprocessing_path.stat().st_size > 0\n"
            "assert calibration_path.exists() and calibration_path.stat().st_size > 0\n\n"
            "print('검증 완료: Pipeline, 모델 저장, 확률 출력과 가설 판단이 정상입니다.')"
        ),
        nbf.v4.new_markdown_cell(
            "## Takeaways\n\n"
            "1. `age`가 최적 단일 특성으로 확정됐습니다.\n"
            "2. 다변수 로지스틱 회귀는 Accuracy·F1·Brier score를 조금 개선했지만 AUC의 실질적 개선 기준을 넘지 못했습니다.\n"
            "3. 현재 가설 기준에서는 H0를 기각할 충분한 근거가 없습니다.\n"
            "4. 다음 단계에서는 비선형 모델을 비교해 변수 간 상호작용이 추가 성능을 제공하는지 확인할 수 있습니다."
        ),
    ]
    return notebook


def main() -> None:
    """Notebook 파일을 저장한다."""
    NOTEBOOK_PATH.parent.mkdir(parents=True, exist_ok=True)
    nbf.write(build_notebook(), NOTEBOOK_PATH)
    print(NOTEBOOK_PATH)


if __name__ == "__main__":
    main()
