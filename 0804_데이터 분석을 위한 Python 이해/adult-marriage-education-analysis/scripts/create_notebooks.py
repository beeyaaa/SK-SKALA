"""새 프로젝트의 01~04 Jupyter Notebook을 생성한다."""

from pathlib import Path

import nbformat as nbf


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_DIR = ROOT / "notebooks"


def metadata():
    return {
        "kernelspec": {
            "display_name": "Adult Marriage (.venv)",
            "language": "python",
            "name": "adult-marriage-education",
        },
        "language_info": {"name": "python", "version": "3.14"},
    }


SETUP = (
    "from pathlib import Path\n"
    "import sys\n\n"
    "project_root = Path.cwd()\n"
    "if project_root.name == 'notebooks':\n"
    "    project_root = project_root.parent\n"
    "if not (project_root / 'src').exists():\n"
    "    raise RuntimeError('adult-marriage-education-analysis 프로젝트 루트에서 실행하세요.')\n"
    "sys.path.insert(0, str(project_root))\n"
    "project_root"
)


def create_01():
    notebook = nbf.v4.new_notebook(metadata=metadata())
    notebook.cells = [
        nbf.v4.new_markdown_cell(
            "# 01. 데이터 로딩과 품질 점검\n\n"
            "## 목표\n\n"
            "Adult Census 원본을 Pandas와 Polars로 각각 읽고 행·열, 결측치, 중복 행이 일치하는지 확인합니다."
        ),
        nbf.v4.new_code_cell(SETUP),
        nbf.v4.new_code_cell(
            "from src.data import load_pandas, load_polars, compare_loaders, resolve_raw_path\n\n"
            "raw_path = resolve_raw_path(project_root)\n"
            "pandas_df = load_pandas(raw_path)\n"
            "polars_df = load_polars(raw_path)\n"
            "print('원본 경로:', raw_path)\n"
            "print('Pandas:', pandas_df.shape)\n"
            "print('Polars:', polars_df.shape)"
        ),
        nbf.v4.new_markdown_cell("## 원본 데이터 미리보기"),
        nbf.v4.new_code_cell("pandas_df.head()"),
        nbf.v4.new_code_cell("polars_df.head()"),
        nbf.v4.new_markdown_cell("## Pandas와 Polars 비교"),
        nbf.v4.new_code_cell(
            "loader_comparison = compare_loaders(pandas_df, polars_df)\n"
            "loader_comparison.to_csv(project_root / 'reports' / 'tables' / 'loader_comparison.csv', index=False)\n"
            "loader_comparison"
        ),
        nbf.v4.new_markdown_cell("## 결측치와 중복 행"),
        nbf.v4.new_code_cell(
            "missing_summary = (\n"
            "    pandas_df.isna().sum().rename('결측치 수').to_frame()\n"
            "    .assign(**{'결측률(%)': lambda x: x['결측치 수'] / len(pandas_df) * 100})\n"
            "    .query('`결측치 수` > 0')\n"
            "    .sort_values('결측치 수', ascending=False)\n"
            ")\n"
            "print('완전 중복 행:', pandas_df.duplicated().sum())\n"
            "missing_summary"
        ),
        nbf.v4.new_markdown_cell(
            "## 정리\n\n"
            "- 두 라이브러리 결과가 일치하는지 확인합니다.\n"
            "- 개인 식별자가 없어 완전 중복 행은 자동 삭제하지 않습니다.\n"
            "- 범주형 결측치는 이후 Pipeline 내부에서 처리합니다."
        ),
        nbf.v4.new_code_cell(
            "assert loader_comparison['일치 여부'].all()\n"
            "assert len(pandas_df) == 32_561\n"
            "print('검증 완료: 데이터 로딩과 품질 점검이 정상입니다.')"
        ),
    ]
    nbf.write(notebook, NOTEBOOK_DIR / "01_data_quality.ipynb")


def create_02():
    notebook = nbf.v4.new_notebook(metadata=metadata())
    notebook.cells = [
        nbf.v4.new_markdown_cell(
            "# 02. Target과 전체 변수 확인\n\n"
            "## 연구 가설\n\n"
            "- H₀: 미혼 집단과 미혼 외 집단의 평균 `education-num`은 같다.\n"
            "- H₁: 두 집단의 평균 `education-num`은 다르다.\n\n"
            "이 노트북에서는 데이터에 어떤 값이 있는지 확인하고 Target과 변수 역할을 고정합니다."
        ),
        nbf.v4.new_code_cell(SETUP),
        nbf.v4.new_code_cell(
            "import pandas as pd\n"
            "from IPython.display import Image, display\n"
            "from src.config import EVER_MARRIED_STATUSES, NEVER_MARRIED_STATUS, TARGET\n"
            "from src.data import (add_target, build_column_profile, build_feature_policy, load_pandas, resolve_raw_path)\n"
            "from src.visualization import create_target_definition_chart\n\n"
            "raw_df = load_pandas(resolve_raw_path(project_root))\n"
            "prepared_df = add_target(raw_df)"
        ),
        nbf.v4.new_markdown_cell("## 1. 전체 컬럼 프로파일"),
        nbf.v4.new_code_cell(
            "column_profile = build_column_profile(raw_df)\n"
            "column_profile.to_csv(project_root / 'reports' / 'tables' / 'column_profile.csv', index=False)\n"
            "column_profile"
        ),
        nbf.v4.new_markdown_cell("## 2. 범주형 컬럼의 고유값과 빈도"),
        nbf.v4.new_code_cell(
            "categorical_columns = raw_df.select_dtypes(include=['object', 'string']).columns\n"
            "for column in categorical_columns:\n"
            "    print(f'\\n[{column}]')\n"
            "    print(raw_df[column].value_counts(dropna=False).to_string())"
        ),
        nbf.v4.new_markdown_cell("## 3. 원본 marital-status 확인"),
        nbf.v4.new_code_cell(
            "marital_status_counts = raw_df['marital-status'].value_counts().rename_axis('혼인 상태').reset_index(name='표본 수')\n"
            "marital_status_counts"
        ),
        nbf.v4.new_markdown_cell(
            "## 4. 미혼/미혼 외 Target 생성\n\n"
            "`Never-married`만 미혼(0)으로 정의합니다. `Married-*`, `Divorced`, `Separated`, `Widowed`는 미혼 외, 즉 혼인 경험 있음(1)으로 정의합니다."
        ),
        nbf.v4.new_code_cell(
            "print('미혼으로 분류한 원본 상태:', NEVER_MARRIED_STATUS)\n"
            "print('미혼 외로 분류한 원본 상태:', sorted(EVER_MARRIED_STATUSES))\n"
            "target_distribution = (\n"
            "    prepared_df[TARGET].map({0: '미혼', 1: '미혼 외'})\n"
            "    .value_counts().rename_axis('집단').reset_index(name='표본 수')\n"
            ")\n"
            "target_distribution['비율(%)'] = target_distribution['표본 수'] / len(prepared_df) * 100\n"
            "target_distribution"
        ),
        nbf.v4.new_code_cell(
            "target_chart_path = create_target_definition_chart(\n"
            "    prepared_df, project_root / 'reports' / 'figures' / '02_target_definition.png'\n"
            ")\n"
            "display(Image(filename=str(target_chart_path)))"
        ),
        nbf.v4.new_markdown_cell("![미혼과 미혼 외 Target 정의](../reports/figures/02_target_definition.png)"),
        nbf.v4.new_markdown_cell("## 5. 변수 역할과 누수 방지 정책"),
        nbf.v4.new_code_cell(
            "feature_policy = build_feature_policy()\n"
            "feature_policy.to_csv(project_root / 'reports' / 'tables' / 'feature_policy.csv', index=False)\n"
            "feature_policy"
        ),
        nbf.v4.new_markdown_cell(
            "## 다음 단계\n\n"
            "03에서는 Train/Test를 먼저 나눈 후 Train 데이터만 사용해 교육 수준 분포, 숫자형 상관행렬, VIF, Welch t-test와 효과크기를 계산합니다."
        ),
        nbf.v4.new_code_cell(
            "assert prepared_df[TARGET].isin([0, 1]).all()\n"
            "assert prepared_df[TARGET].isna().sum() == 0\n"
            "assert target_chart_path.exists()\n"
            "print('검증 완료: Target과 변수 역할이 정상적으로 정의됐습니다.')"
        ),
    ]
    nbf.write(notebook, NOTEBOOK_DIR / "02_target_and_features.ipynb")


def create_03():
    notebook = nbf.v4.new_notebook(metadata=metadata())
    notebook.cells = [
        nbf.v4.new_markdown_cell(
            "# 03. EDA·다중공선성·가설검정\n\n"
            "## 검정할 가설\n\n"
            "- H₀: 미혼 집단과 미혼 외 집단의 평균 교육 수준은 같다.\n"
            "- H₁: 두 집단의 평균 교육 수준은 다르다.\n"
            "- 유의수준: α=0.05\n\n"
            "모든 EDA와 가설검정은 Train 데이터에서만 수행합니다."
        ),
        nbf.v4.new_code_cell(SETUP),
        nbf.v4.new_code_cell(
            "import pandas as pd\n"
            "from IPython.display import Image, display\n"
            "from src.analysis import build_group_statistics, calculate_vif, run_hypothesis_test, split_data\n"
            "from src.config import NUMERIC_MODEL_FEATURES, TARGET\n"
            "from src.data import add_target, load_pandas, resolve_raw_path\n"
            "from src.visualization import (\n"
            "    create_education_hypothesis_chart, create_interactive_education_rate, create_multicollinearity_chart\n"
            ")\n\n"
            "prepared_df = add_target(load_pandas(resolve_raw_path(project_root)))\n"
            "train_df, test_df = split_data(prepared_df)\n"
            "print('Train:', train_df.shape)\n"
            "print('Test:', test_df.shape)\n"
            "print('Train 미혼 외 비율:', f\"{train_df[TARGET].mean():.2%}\")\n"
            "print('Test 미혼 외 비율:', f\"{test_df[TARGET].mean():.2%}\")"
        ),
        nbf.v4.new_markdown_cell("## 1. 집단별 교육 수준 기술통계"),
        nbf.v4.new_code_cell(
            "group_statistics = build_group_statistics(train_df)\n"
            "group_statistics.to_csv(project_root / 'reports' / 'tables' / 'education_group_statistics.csv', index=False)\n"
            "group_statistics.round(3)"
        ),
        nbf.v4.new_markdown_cell("## 2. 집단별 교육 수준 정적 시각화"),
        nbf.v4.new_code_cell(
            "education_chart_path = create_education_hypothesis_chart(\n"
            "    train_df, project_root / 'reports' / 'figures' / '03_education_by_marriage.png'\n"
            ")\n"
            "display(Image(filename=str(education_chart_path)))"
        ),
        nbf.v4.new_markdown_cell("![미혼/미혼 외 집단의 교육 수준](../reports/figures/03_education_by_marriage.png)"),
        nbf.v4.new_markdown_cell("## 3. 숫자형 상관관계와 VIF"),
        nbf.v4.new_code_cell(
            "numeric_correlation = train_df[NUMERIC_MODEL_FEATURES].corr()\n"
            "vif_table = calculate_vif(train_df)\n"
            "display(numeric_correlation.round(3))\n"
            "display(vif_table.round(3))"
        ),
        nbf.v4.new_code_cell(
            "multicollinearity_chart_path = create_multicollinearity_chart(\n"
            "    train_df, vif_table, project_root / 'reports' / 'figures' / '03_multicollinearity.png'\n"
            ")\n"
            "display(Image(filename=str(multicollinearity_chart_path)))"
        ),
        nbf.v4.new_markdown_cell("![숫자형 변수의 다중공선성 진단](../reports/figures/03_multicollinearity.png)"),
        nbf.v4.new_markdown_cell(
            "## 4. Welch t-test와 효과크기\n\n"
            "두 집단의 분산이 같다고 가정하지 않는 Welch t-test를 사용합니다. p-value와 함께 Cohen’s d를 확인합니다."
        ),
        nbf.v4.new_code_cell(
            "hypothesis_result = run_hypothesis_test(train_df)\n"
            "hypothesis_result.to_csv(project_root / 'reports' / 'tables' / 'hypothesis_result.csv', index=False)\n"
            "hypothesis_result.round(6)"
        ),
        nbf.v4.new_code_cell(
            "row = hypothesis_result.iloc[0]\n"
            "print(f\"미혼 외 집단 평균: {row['미혼 외 집단 평균']:.3f}\")\n"
            "print(f\"미혼 집단 평균: {row['미혼 집단 평균']:.3f}\")\n"
            "print(f\"평균 차이: {row['평균 차이']:.3f}\")\n"
            "print(f\"p-value: {row['p-value']:.3e}\")\n"
            "print(f\"Cohen's d: {row[\"Cohen's d\"]:.3f}\")\n"
            "print('판정:', row['판정'])\n"
            "print('주의: 이는 집단 간 연관성이지 교육 수준의 인과효과가 아닙니다.')"
        ),
        nbf.v4.new_markdown_cell("## 5. Plotly 인터랙티브 차트 — 교육 수준별 미혼 외 비율"),
        nbf.v4.new_code_cell(
            "interactive_path = create_interactive_education_rate(\n"
            "    train_df, project_root / 'reports' / 'interactive' / 'education_marriage_rate.html'\n"
            ")\n"
            "print('저장 위치:', interactive_path)"
        ),
        nbf.v4.new_markdown_cell("## 검증"),
        nbf.v4.new_code_cell(
            "assert len(train_df) == 26_048\n"
            "assert len(test_df) == 6_513\n"
            "assert set(train_df.index).isdisjoint(test_df.index)\n"
            "assert education_chart_path.exists()\n"
            "assert multicollinearity_chart_path.exists()\n"
            "assert interactive_path.exists()\n"
            "print('검증 완료: EDA·다중공선성·가설검정 산출물이 정상입니다.')"
        ),
    ]
    nbf.write(notebook, NOTEBOOK_DIR / "03_eda_hypothesis.ipynb")


def create_04():
    notebook = nbf.v4.new_notebook(metadata=metadata())
    notebook.cells = [
        nbf.v4.new_markdown_cell(
            "# 04. 실전 Feature Engineering\n\n"
            "## tl;dr\n\n"
            "Day16 자료의 흐름(EDA → 결측·이상치 → 스케일링·인코딩 → 변환 → 파생변수)을 Adult Census에 적용합니다. "
            "모든 학습형 전처리는 Train에만 `fit`하고 Test에는 `transform`만 적용합니다."
        ),
        nbf.v4.new_code_cell(SETUP),
        nbf.v4.new_code_cell(
            "import numpy as np\n"
            "import pandas as pd\n"
            "from IPython.display import Image, display\n"
            "from src.analysis import split_data\n"
            "from src.config import TARGET\n"
            "from src.data import add_target, load_pandas, resolve_raw_path\n"
            "from src.feature_engineering import (\n"
            "    build_feature_audit, build_feature_decisions, build_preprocessing_pipeline,\n"
            "    engineer_features, transformed_feature_names\n"
            ")\n"
            "from src.visualization import (\n"
            "    create_encoding_summary_chart, create_feature_audit_chart,\n"
            "    create_scaling_comparison_chart, create_transformation_chart\n"
            ")\n\n"
            "prepared_df = add_target(load_pandas(resolve_raw_path(project_root)))\n"
            "train_df, test_df = split_data(prepared_df)\n"
            "print('Train:', train_df.shape, '| Test:', test_df.shape)"
        ),
        nbf.v4.new_markdown_cell(
            "## Context & Methods\n\n"
            "### Key Assumptions\n\n"
            "- 분석 단위는 Adult Census의 한 행(한 사람)입니다.\n"
            "- `marital-status`와 `relationship`은 Target 누수이므로 모델 입력에서 제외합니다.\n"
            "- 완전 중복은 동일 인물임을 증명할 식별자가 없어 자동 삭제하지 않습니다.\n"
            "- IQR·Z-score는 **이상치 후보 탐색** 도구일 뿐, 실제 가능한 관측값을 자동 삭제하는 규칙으로 사용하지 않습니다."
        ),
        nbf.v4.new_markdown_cell("## Data\n\n### 1. EDA 체크리스트를 한 표로 점검"),
        nbf.v4.new_code_cell(
            "feature_audit = build_feature_audit(train_df)\n"
            "feature_audit.to_csv(project_root / 'reports' / 'tables' / 'feature_engineering_audit.csv', index=False)\n"
            "feature_audit.round(3)"
        ),
        nbf.v4.new_code_cell(
            "audit_chart_path = create_feature_audit_chart(\n"
            "    train_df, feature_audit, project_root / 'reports' / 'figures' / '04_feature_audit.png'\n"
            ")\n"
            "display(Image(filename=str(audit_chart_path)))"
        ),
        nbf.v4.new_markdown_cell("![Feature Engineering 전 데이터 진단](../reports/figures/04_feature_audit.png)"),
        nbf.v4.new_markdown_cell("### 2. 처리 의사결정 로그"),
        nbf.v4.new_code_cell(
            "feature_decisions = build_feature_decisions(train_df)\n"
            "feature_decisions.to_csv(project_root / 'reports' / 'tables' / 'feature_engineering_decisions.csv', index=False)\n"
            "feature_decisions"
        ),
        nbf.v4.new_markdown_cell(
            "## Results\n\n### 3. 이상치와 긴 꼬리 분포\n\n"
            "`capital-gain`과 `capital-loss`는 0이 매우 많고 큰 양수 값이 드뭅니다. 실제 가능한 값이므로 삭제하지 않고 `log1p` 파생값을 사용합니다."
        ),
        nbf.v4.new_code_cell(
            "skew_before_after = pd.DataFrame({\n"
            "    '변수': ['capital-gain', 'capital-loss'],\n"
            "    '변환 전 왜도': [train_df['capital-gain'].skew(), train_df['capital-loss'].skew()],\n"
            "    'log1p 후 왜도': [np.log1p(train_df['capital-gain']).skew(), np.log1p(train_df['capital-loss']).skew()],\n"
            "})\n"
            "skew_before_after.round(3)"
        ),
        nbf.v4.new_code_cell(
            "transformation_chart_path = create_transformation_chart(\n"
            "    train_df, project_root / 'reports' / 'figures' / '04_log_transformation.png'\n"
            ")\n"
            "display(Image(filename=str(transformation_chart_path)))"
        ),
        nbf.v4.new_markdown_cell("![긴 꼬리 분포의 로그 변환 전후](../reports/figures/04_log_transformation.png)"),
        nbf.v4.new_markdown_cell(
            "### 4. 질문에서 파생변수 만들기\n\n"
            "- 연령대: 연령의 비선형적 차이를 보기 위한 고정 구간화\n"
            "- 근무시간대: 표준 근무시간 전후의 차이를 보기 위한 고정 구간화\n"
            "- 자본 순이득: 자본 이득과 손실을 함께 표현한 signed-log 변수\n\n"
            "구간 경계는 전체 데이터 분포에서 학습하지 않은 고정 업무 규칙이므로 Train/Test에 동일하게 적용할 수 있습니다."
        ),
        nbf.v4.new_code_cell(
            "engineered_train = engineer_features(train_df)\n"
            "engineered_train[[\n"
            "    'age', 'age-group', 'hours-per-week', 'hours-group',\n"
            "    'capital-gain-log', 'capital-loss-log', 'capital-net-signed-log'\n"
            "]].head(10)"
        ),
        nbf.v4.new_markdown_cell(
            "### 5. 스케일링 비교\n\n"
            "Min-Max, Standard, Robust를 모두 눈으로 비교합니다. 최종 Pipeline은 로지스틱 회귀의 계수와 정규화가 단위 차이에 좌우되지 않도록 `StandardScaler`를 사용합니다. "
            "자본소득은 먼저 로그 변환하여 긴 꼬리를 완화합니다."
        ),
        nbf.v4.new_code_cell(
            "scaling_chart_path = create_scaling_comparison_chart(\n"
            "    train_df, project_root / 'reports' / 'figures' / '04_scaling_comparison.png'\n"
            ")\n"
            "display(Image(filename=str(scaling_chart_path)))"
        ),
        nbf.v4.new_markdown_cell("![스케일링 방법 비교](../reports/figures/04_scaling_comparison.png)"),
        nbf.v4.new_markdown_cell(
            "### 6. 인코딩과 전체 Pipeline\n\n"
            "명목형 변수에 Label Encoding을 쓰면 존재하지 않는 순서가 생기므로 One-Hot Encoding을 사용합니다. "
            "Train에서 1% 미만인 희소 범주는 자동 통합하고, 첫 범주는 기준 범주로 제외합니다."
        ),
        nbf.v4.new_code_cell(
            "preprocessing_pipeline = build_preprocessing_pipeline()\n"
            "X_train = train_df.drop(columns=[TARGET])\n"
            "X_test = test_df.drop(columns=[TARGET])\n"
            "X_train_transformed = preprocessing_pipeline.fit_transform(X_train)\n"
            "X_test_transformed = preprocessing_pipeline.transform(X_test)\n"
            "feature_names = transformed_feature_names(preprocessing_pipeline)\n"
            "print('변환 전:', X_train.shape, X_test.shape)\n"
            "print('변환 후:', X_train_transformed.shape, X_test_transformed.shape)\n"
            "print('출력 Feature 예시:', feature_names[:12])"
        ),
        nbf.v4.new_code_cell(
            "encoding_chart_path = create_encoding_summary_chart(\n"
            "    train_df, feature_names, project_root / 'reports' / 'figures' / '04_encoding_summary.png'\n"
            ")\n"
            "display(Image(filename=str(encoding_chart_path)))"
        ),
        nbf.v4.new_markdown_cell("![인코딩 전후 차원 비교](../reports/figures/04_encoding_summary.png)"),
        nbf.v4.new_markdown_cell("### 7. 변환 결과 품질 검증"),
        nbf.v4.new_code_cell(
            "transformed_train_df = pd.DataFrame(X_train_transformed, columns=feature_names, index=X_train.index)\n"
            "transformed_test_df = pd.DataFrame(X_test_transformed, columns=feature_names, index=X_test.index)\n"
            "quality_checks = pd.DataFrame([{\n"
            "    'Train 행 수 보존': len(transformed_train_df) == len(train_df),\n"
            "    'Test 행 수 보존': len(transformed_test_df) == len(test_df),\n"
            "    'Train/Test 컬럼 수 일치': transformed_train_df.shape[1] == transformed_test_df.shape[1],\n"
            "    'Train 결측치 0개': int(transformed_train_df.isna().sum().sum()) == 0,\n"
            "    'Test 결측치 0개': int(transformed_test_df.isna().sum().sum()) == 0,\n"
            "    '무한대 없음': np.isfinite(X_train_transformed).all() and np.isfinite(X_test_transformed).all(),\n"
            "}])\n"
            "quality_checks"
        ),
        nbf.v4.new_markdown_cell(
            "## Takeaways\n\n"
            "- 결측치는 삭제하지 않고 Pipeline 내부에서 Train 기준으로 대치합니다.\n"
            "- IQR 이상치 후보는 실제 가능한 값이므로 일괄 삭제하지 않습니다.\n"
            "- 자본소득 변수는 log1p/signed-log로 긴 꼬리를 완화합니다.\n"
            "- 범주형은 희소 범주 통합 후 One-Hot Encoding, 수치형은 Standard Scaling을 적용합니다.\n"
            "- Target 분포를 확인한 결과 한쪽이 극단적으로 희소하지 않아 SMOTE나 undersampling을 적용하지 않습니다.\n"
            "- 검증 결과 Train 26,048행·Test 6,513행이 32개 Feature로 변환되며 결측치는 모두 0개였습니다.\n"
            "- 다음 모델링 단계에서는 이 전처리 Pipeline 뒤에 로지스틱 회귀를 연결하면 데이터 누수를 막을 수 있습니다."
        ),
        nbf.v4.new_code_cell(
            "assert quality_checks.all(axis=None)\n"
            "for path in [audit_chart_path, transformation_chart_path, scaling_chart_path, encoding_chart_path]:\n"
            "    assert path.exists()\n"
            "print('검증 완료: Feature Engineering Pipeline이 Train/Test에 정상 적용됐습니다.')"
        ),
    ]
    nbf.write(notebook, NOTEBOOK_DIR / "04_feature_engineering.ipynb")


def main():
    NOTEBOOK_DIR.mkdir(parents=True, exist_ok=True)
    create_01()
    create_02()
    create_03()
    create_04()
    for path in sorted(NOTEBOOK_DIR.glob("*.ipynb")):
        print(path)


if __name__ == "__main__":
    main()
