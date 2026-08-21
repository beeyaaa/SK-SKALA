"""3단계 EDA·통계·시각화 Jupyter Notebook을 재생성한다."""

from pathlib import Path

import nbformat as nbf


PROJECT_ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_PATH = PROJECT_ROOT / "notebooks" / "03_eda_statistics.ipynb"


def build_notebook() -> nbf.NotebookNode:
    """훈련 데이터 전용 탐색·통계 분석 노트북을 구성한다."""
    notebook = nbf.v4.new_notebook()
    notebook.metadata["kernelspec"] = {
        "display_name": "Python 3",
        "language": "python",
        "name": "python3",
    }
    notebook.metadata["language_info"] = {"name": "python", "version": "3.14"}

    notebook.cells = [
        nbf.v4.new_markdown_cell(
            "# 03. Train/Test 분할, EDA와 통계분석\n\n"
            "## tl;dr\n\n"
            "- 훈련 데이터는 **26,048행**, 테스트 데이터는 **6,513행**이며 혼인 경험 비율은 각각 약 67.19%입니다.\n"
            "- 나이는 혼인 경험과 가장 강한 숫자형 관련성을 보였습니다(`r=0.534`, `Cohen's d=1.345`).\n"
            "- Mutual Information도 나이가 `0.212`로 가장 높았습니다.\n"
            "- `income`은 가장 큰 범주형 관련성(`Cramér's V=0.317`)을 보였지만 현재 시점 정보이므로 확장 모델에서만 사용합니다."
        ),
        nbf.v4.new_markdown_cell(
            "## Context & Methods\n\n"
            "모델 선택에 테스트 정보가 섞이지 않도록 타깃 비율을 유지한 train/test 분할을 먼저 수행합니다. "
            "모든 EDA, 통계검정, Mutual Information은 훈련 데이터에서만 계산합니다.\n\n"
            "### Key Assumptions\n\n"
            "- Welch t-test는 두 집단 평균 차이를 검정합니다.\n"
            "- 큰 표본에서는 작은 차이도 유의할 수 있어 Cohen's d를 함께 봅니다.\n"
            "- 상관관계와 MI는 예측 관련성이지 인과효과가 아닙니다.\n"
            "- 범주형 변수에는 Pearson 상관계수를 적용하지 않습니다."
        ),
        nbf.v4.new_code_cell(
            "from pathlib import Path\n"
            "import sys\n"
            "import pandas as pd\n"
            "from IPython.display import Image, display\n\n"
            "project_root = Path.cwd()\n"
            "if project_root.name == 'notebooks':\n"
            "    project_root = project_root.parent\n"
            "if not (project_root / 'src').exists():\n"
            "    raise RuntimeError('adult-marriage-analysis 프로젝트 루트에서 실행하세요.')\n"
            "sys.path.insert(0, str(project_root))\n\n"
            "from src.data import add_target_pandas, ensure_raw_data, load_with_pandas\n"
            "from src.eda import (\n"
            "    build_categorical_summary,\n"
            "    build_categorical_target_rates,\n"
            "    build_iqr_outlier_summary,\n"
            "    build_numeric_correlation,\n"
            "    build_numeric_distribution_summary,\n"
            "    build_numeric_target_summary,\n"
            ")\n"
            "from src.statistics import (\n"
            "    analyze_categorical_associations,\n"
            "    analyze_numeric_associations,\n"
            "    build_descriptive_statistics,\n"
            "    build_split_summary,\n"
            "    calculate_mutual_information,\n"
            "    split_prepared_data,\n"
            ")\n"
            "from src.visualization import (\n"
            "    build_age_rate_figure,\n"
            "    create_categorical_cardinality_chart,\n"
            "    create_categorical_target_rate_chart,\n"
            "    create_correlation_heatmap,\n"
            "    create_age_distribution_chart,\n"
            "    create_interactive_age_rate_chart,\n"
            "    create_numeric_distribution_grid,\n"
            "    create_numeric_target_boxplots,\n"
            "    create_outlier_boxplots,\n"
            "    create_split_target_distribution_chart,\n"
            "    create_target_association_overview,\n"
            ")"
        ),
        nbf.v4.new_markdown_cell("## Data\n\n### 1. 타깃 생성 후 stratified 분할"),
        nbf.v4.new_code_cell(
            "raw_path = ensure_raw_data(project_root / 'data' / 'raw')\n"
            "prepared_df = add_target_pandas(load_with_pandas(raw_path))\n"
            "train_df, test_df = split_prepared_data(prepared_df)\n"
            "split_summary = build_split_summary(train_df, test_df)\n"
            "split_summary"
        ),
        nbf.v4.new_markdown_cell(
            "### 1-1. Stratified 분할에서 Target 비율이 유지됐는가?\n\n"
            "80:20은 행을 나누는 비율이고, 32.81:67.19는 각 분할 안의 Target 클래스 비율입니다."
        ),
        nbf.v4.new_code_cell(
            "split_target_chart_path = create_split_target_distribution_chart(\n"
            "    split_summary,\n"
            "    project_root / 'reports' / 'figures' / 'eda_stratified_target_split.png',\n"
            ")\n"
            "print('[Question] Train과 Test에 Target 비율이 동일하게 유지됐는가?')\n"
            "print('[Observed] Train과 Test 모두 Target 0 약 32.81%, Target 1 약 67.19%입니다.')\n"
            "print('[Next Action] 두 분할의 클래스 구성이 같으므로 최종 성능을 비교합니다.')\n"
            "display(Image(filename=str(split_target_chart_path)))"
        ),
        nbf.v4.new_markdown_cell(
            "## Results\n\n"
            "### 2. 수치형 변수들의 분포는 어떠한가?\n\n"
            "평균·중앙값·왜도·0의 비율을 표로 확인하고, 원본 스케일 히스토그램을 함께 봅니다."
        ),
        nbf.v4.new_code_cell(
            "numeric_distribution = build_numeric_distribution_summary(train_df)\n"
            "print('[Question] 수치형 변수들의 분포는 어떠한가?')\n"
            "display(numeric_distribution.round(3))\n"
            "skewed_features = numeric_distribution.loc[numeric_distribution.skewness.abs() > 2, 'feature'].tolist()\n"
            "print(f'[Observed] |skewness| > 2인 변수: {skewed_features}')\n"
            "print('[Next Action] capital-gain·capital-loss는 모델 Pipeline 안에서 log1p 변환합니다.')"
        ),
        nbf.v4.new_code_cell(
            "distribution_chart_path = create_numeric_distribution_grid(\n"
            "    train_df,\n"
            "    project_root / 'reports' / 'figures' / 'eda_numeric_distributions.png',\n"
            ")\n"
            "display(Image(filename=str(distribution_chart_path)))"
        ),
        nbf.v4.new_markdown_cell(
            "### 3. 이상치는 존재하는가?\n\n"
            "1.5×IQR 기준은 잠재적 극단값을 찾기 위한 진단 도구이며, 발견된 행을 자동 삭제하지 않습니다."
        ),
        nbf.v4.new_code_cell(
            "outlier_summary = build_iqr_outlier_summary(train_df)\n"
            "print('[Question] 이상치는 존재하는가?')\n"
            "display(outlier_summary.round(3))\n"
            "print('[Next Action] Adult의 실제 관측 가능 값이므로 삭제하지 않고, 긴 꼬리는 log1p와 StandardScaler로 처리합니다.')"
        ),
        nbf.v4.new_code_cell(
            "outlier_chart_path = create_outlier_boxplots(\n"
            "    train_df,\n"
            "    project_root / 'reports' / 'figures' / 'eda_numeric_outliers.png',\n"
            ")\n"
            "display(Image(filename=str(outlier_chart_path)))"
        ),
        nbf.v4.new_markdown_cell(
            "### 4. 범주형 변수의 구성과 빈도는 적절한가?\n\n"
            "고유 범주 수, 결측치, 최빈 범주의 비율을 확인해 대치·인코딩 방법을 결정합니다."
        ),
        nbf.v4.new_code_cell(
            "categorical_summary = build_categorical_summary(train_df)\n"
            "print('[Question] 범주형 변수의 구성과 빈도는 적절한가?')\n"
            "display(categorical_summary.round(3))\n"
            "print('[Next Action] 결측은 Unknown으로 대치하고 OneHotEncoder(handle_unknown=ignore)를 사용합니다.')"
        ),
        nbf.v4.new_code_cell(
            "categorical_chart_path = create_categorical_cardinality_chart(\n"
            "    train_df,\n"
            "    project_root / 'reports' / 'figures' / 'eda_categorical_cardinality.png',\n"
            ")\n"
            "display(Image(filename=str(categorical_chart_path)))"
        ),
        nbf.v4.new_markdown_cell(
            "### 5. 서로 비슷한 정보를 가진 숫자형 변수는 없는가?\n\n"
            "숫자형 후보 간 Pearson 상관행렬을 표와 heatmap으로 확인합니다."
        ),
        nbf.v4.new_code_cell(
            "numeric_correlation = build_numeric_correlation(train_df)\n"
            "print('[Question] 서로 비슷한 정보를 가진 숫자형 변수는 없는가?')\n"
            "display(numeric_correlation.round(3))\n"
            "print('[Next Action] heatmap에서 강한 중복 상관이 있는지 확인하고, 최종 선택은 교차검증으로 판단합니다.')"
        ),
        nbf.v4.new_code_cell(
            "correlation_chart_path = create_correlation_heatmap(\n"
            "    train_df,\n"
            "    project_root / 'reports' / 'figures' / 'eda_numeric_correlation.png',\n"
            ")\n"
            "display(Image(filename=str(correlation_chart_path)))"
        ),
        nbf.v4.new_markdown_cell("### 6. 숫자형 기술통계 — 혼인 경험 집단별"),
        nbf.v4.new_code_cell(
            "descriptive_statistics = build_descriptive_statistics(train_df)\n"
            "descriptive_statistics.round(3)"
        ),
        nbf.v4.new_markdown_cell(
            "### 7. Target 그룹에 따라 수치형 변수의 분포가 다른가?\n\n"
            "Target=0(혼인 경험 없음)과 Target=1(혼인 경험 있음)의 중앙값·분포를 전체 숫자형 후보에 대해 비교합니다."
        ),
        nbf.v4.new_code_cell(
            "numeric_target_summary = build_numeric_target_summary(train_df)\n"
            "print('[Question] Target 그룹에 따라 수치형 변수의 분포가 다른가?')\n"
            "display(numeric_target_summary.round(3))\n"
            "print('[Observed] 나이의 집단 차이가 가장 크며, 통계검정과 효과크기로 다음 셀에서 확인합니다.')\n"
            "print('[Next Action] 그림만으로 변수를 확정하지 않고 Point-biserial·Welch t-test·Cohen d를 함께 봅니다.')"
        ),
        nbf.v4.new_code_cell(
            "numeric_target_chart_path = create_numeric_target_boxplots(\n"
            "    train_df,\n"
            "    project_root / 'reports' / 'figures' / 'eda_numeric_by_target.png',\n"
            ")\n"
            "display(Image(filename=str(numeric_target_chart_path)))"
        ),
        nbf.v4.new_markdown_cell("### 8. Point-biserial 상관계수와 Welch t-test"),
        nbf.v4.new_code_cell(
            "numeric_associations = analyze_numeric_associations(train_df)\n"
            "numeric_associations.round(4)"
        ),
        nbf.v4.new_markdown_cell(
            "p-value가 매우 작더라도 효과크기가 작을 수 있습니다. 예를 들어 `education-num`은 "
            "통계적으로 유의하지만 Cohen's d가 약 0.064로 작습니다."
        ),
        nbf.v4.new_markdown_cell("### 9. 범주형 chi-square와 Cramér's V"),
        nbf.v4.new_code_cell(
            "categorical_associations = analyze_categorical_associations(train_df)\n"
            "categorical_associations.round(4)"
        ),
        nbf.v4.new_markdown_cell(
            "### 10. 범주에 따라 Target=1 비율이 달라지는가?\n\n"
            "각 범주의 표본 수와 혼인 경험 비율을 확인합니다. 표본 수가 작은 범주의 극단적인 비율은 주의해서 해석합니다."
        ),
        nbf.v4.new_code_cell(
            "categorical_target_rates = build_categorical_target_rates(train_df)\n"
            "print('[Question] 범주에 따라 Target=1 비율이 달라지는가?')\n"
            "display(categorical_target_rates.round(2))\n"
            "print('[Next Action] 범주를 임의 통합하지 않고 Unknown 대치 + OneHotEncoder를 적용하며, 예측 기여는 교차검증으로 판단합니다.')"
        ),
        nbf.v4.new_code_cell(
            "categorical_target_chart_path = create_categorical_target_rate_chart(\n"
            "    train_df,\n"
            "    project_root / 'reports' / 'figures' / 'eda_categorical_target_rates.png',\n"
            ")\n"
            "display(Image(filename=str(categorical_target_chart_path)))"
        ),
        nbf.v4.new_markdown_cell("### 11. Mutual Information 순위"),
        nbf.v4.new_code_cell(
            "mutual_information = calculate_mutual_information(train_df)\n"
            "mutual_information.round(4)"
        ),
        nbf.v4.new_markdown_cell(
            "### 11-1. 상관계수·Cramér’s V·Mutual Information 시각화\n\n"
            "서로 단위가 다른 세 지표를 각각의 패널에서 순위로 확인합니다. 지표 간 막대 길이를 직접 비교하지 않습니다."
        ),
        nbf.v4.new_code_cell(
            "association_chart_path = create_target_association_overview(\n"
            "    numeric_associations,\n"
            "    categorical_associations,\n"
            "    mutual_information,\n"
            "    project_root / 'reports' / 'figures' / 'eda_target_associations.png',\n"
            ")\n"
            "display(Image(filename=str(association_chart_path)))"
        ),
        nbf.v4.new_markdown_cell("### 12. Seaborn 정적 차트 — 집단별 나이 분포"),
        nbf.v4.new_code_cell(
            "static_chart_path = create_age_distribution_chart(\n"
            "    train_df,\n"
            "    project_root / 'reports' / 'figures' / 'age_distribution_by_marriage.png',\n"
            ")\n"
            "display(Image(filename=str(static_chart_path)))"
        ),
        nbf.v4.new_markdown_cell("### 13. Plotly 인터랙티브 차트 — 연령대별 혼인 경험 비율"),
        nbf.v4.new_code_cell(
            "interactive_chart_path = create_interactive_age_rate_chart(\n"
            "    train_df,\n"
            "    project_root / 'reports' / 'interactive' / 'marriage_rate_by_age_group.html',\n"
            ")\n"
            "age_rate_figure = build_age_rate_figure(train_df)\n"
            "age_rate_figure.show()"
        ),
        nbf.v4.new_markdown_cell("## Checks\n\n분할과 분석 범위를 자동 검증합니다."),
        nbf.v4.new_code_cell(
            "assert len(train_df) == 26_048\n"
            "assert len(test_df) == 6_513\n"
            "assert set(train_df.index).isdisjoint(test_df.index)\n"
            "assert split_summary.groupby('split')['percentage'].sum().round(8).eq(100).all()\n"
            "assert numeric_associations.iloc[0]['feature'] == 'age'\n"
            "assert mutual_information.iloc[0]['feature'] == 'age'\n"
            "assert split_target_chart_path.exists() and split_target_chart_path.stat().st_size > 0\n"
            "assert association_chart_path.exists() and association_chart_path.stat().st_size > 0\n"
            "assert distribution_chart_path.exists() and distribution_chart_path.stat().st_size > 0\n"
            "assert outlier_chart_path.exists() and outlier_chart_path.stat().st_size > 0\n"
            "assert categorical_chart_path.exists() and categorical_chart_path.stat().st_size > 0\n"
            "assert correlation_chart_path.exists() and correlation_chart_path.stat().st_size > 0\n"
            "assert numeric_target_chart_path.exists() and numeric_target_chart_path.stat().st_size > 0\n"
            "assert categorical_target_chart_path.exists() and categorical_target_chart_path.stat().st_size > 0\n"
            "assert static_chart_path.exists() and static_chart_path.stat().st_size > 0\n"
            "assert interactive_chart_path.exists() and interactive_chart_path.stat().st_size > 0\n\n"
            "print('검증 완료: 분할·통계분석·필수 시각화가 정상입니다.')"
        ),
        nbf.v4.new_markdown_cell(
            "## Takeaways\n\n"
            "1. 나이는 현재까지의 혼인 경험을 구분하는 가장 강한 단일 후보입니다. 다만 이를 최적 단일 모델로 확정하려면 다음 단계의 교차검증이 필요합니다.\n"
            "2. 17–24세의 혼인 경험 비율은 약 12.6%, 45–54세는 약 91.3%로 연령 노출 효과가 매우 큽니다.\n"
            "3. `education-num`은 p-value만 보면 유의하지만 실제 집단 차이는 작아 p-value와 효과크기를 함께 해석해야 합니다.\n"
            "4. 다음 단계에서는 전처리 Pipeline을 만들고 각 단일 특성 모델을 동일한 교차검증으로 평가합니다."
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
