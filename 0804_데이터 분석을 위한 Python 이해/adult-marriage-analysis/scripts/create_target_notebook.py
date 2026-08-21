"""2단계 타깃 생성·누수 차단용 Jupyter Notebook을 재생성한다."""

from pathlib import Path

import nbformat as nbf


PROJECT_ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_PATH = PROJECT_ROOT / "notebooks" / "02_target_and_features.ipynb"


def build_notebook() -> nbf.NotebookNode:
    """타깃과 모델 입력 정책을 검증하는 분석 노트북을 구성한다."""
    notebook = nbf.v4.new_notebook()
    notebook.metadata["kernelspec"] = {
        "display_name": "Python 3",
        "language": "python",
        "name": "python3",
    }
    notebook.metadata["language_info"] = {"name": "python", "version": "3.14"}

    notebook.cells = [
        nbf.v4.new_markdown_cell(
            "# 02. 혼인 경험 타깃 생성과 누수 변수 차단\n\n"
            "## tl;dr\n\n"
            "- 32,561명 중 혼인 경험 없음은 **10,683명(32.81%)**, "
            "혼인 경험 있음은 **21,878명(67.19%)**입니다.\n"
            "- `marital-status`는 타깃 생성 후 제거하고, `relationship`은 정답을 "
            "직접 암시하므로 모델 입력에서 제외합니다.\n"
            "- 기본 모델은 7개 특성, 확장 모델은 `income`을 추가한 8개 특성을 사용합니다."
        ),
        nbf.v4.new_markdown_cell(
            "## Context & Methods\n\n"
            "### Key Assumptions\n\n"
            "`Never-married`만 0으로 정의하고, 혼인·이혼·별거·사별 상태는 모두 1로 "
            "정의합니다. 이는 미래 결혼 가능성이 아니라 조사 시점까지의 누적 혼인 경험입니다."
        ),
        nbf.v4.new_code_cell(
            "from pathlib import Path\n"
            "import sys\n"
            "import pandas as pd\n\n"
            "project_root = Path.cwd()\n"
            "if project_root.name == 'notebooks':\n"
            "    project_root = project_root.parent\n"
            "if not (project_root / 'src').exists():\n"
            "    raise RuntimeError('adult-marriage-analysis 프로젝트 루트에서 실행하세요.')\n"
            "sys.path.insert(0, str(project_root))\n\n"
            "from src.data import (\n"
            "    add_target_pandas,\n"
            "    add_target_polars,\n"
            "    compare_target_distribution,\n"
            "    ensure_raw_data,\n"
            "    load_with_pandas,\n"
            "    load_with_polars,\n"
            ")\n"
            "from src.features import (\n"
            "    BASE_FEATURES,\n"
            "    EXTENDED_FEATURES,\n"
            "    build_feature_missingness,\n"
            "    build_feature_policy,\n"
            "    select_feature_sets,\n"
            ")"
        ),
        nbf.v4.new_markdown_cell("## Data\n\n### 1. 정제 데이터에 타깃 추가"),
        nbf.v4.new_code_cell(
            "raw_path = ensure_raw_data(project_root / 'data' / 'raw')\n"
            "pandas_prepared = add_target_pandas(load_with_pandas(raw_path))\n"
            "polars_prepared = add_target_polars(load_with_polars(raw_path))\n\n"
            "pandas_prepared[['marital-status', 'ever_married']].head()"
        ),
        nbf.v4.new_markdown_cell("## Results\n\n### 2. 타깃 분포와 라이브러리 간 일치"),
        nbf.v4.new_code_cell(
            "target_distribution = compare_target_distribution(\n"
            "    pandas_prepared, polars_prepared\n"
            ")\n"
            "target_distribution"
        ),
        nbf.v4.new_markdown_cell("### 3. 원래 혼인 상태가 어떻게 매핑됐는지 확인"),
        nbf.v4.new_code_cell(
            "status_mapping_check = (\n"
            "    pandas_prepared\n"
            "    .groupby(['marital-status', 'ever_married'], as_index=False)\n"
            "    .size()\n"
            "    .sort_values(['ever_married', 'size'], ascending=[True, False])\n"
            ")\n"
            "status_mapping_check"
        ),
        nbf.v4.new_markdown_cell("### 4. 모델 입력·제외 정책 확인"),
        nbf.v4.new_code_cell("feature_policy = build_feature_policy()\nfeature_policy"),
        nbf.v4.new_markdown_cell("### 5. 기본·확장·공정성 데이터 분리"),
        nbf.v4.new_code_cell(
            "base_x, extended_x, audit_x, target = select_feature_sets(\n"
            "    pandas_prepared\n"
            ")\n\n"
            "feature_set_summary = pd.DataFrame([\n"
            "    {'set': '기본 모델', 'rows': len(base_x), 'columns': base_x.shape[1], "
            "'features': ', '.join(base_x.columns)},\n"
            "    {'set': '확장 모델', 'rows': len(extended_x), 'columns': extended_x.shape[1], "
            "'features': ', '.join(extended_x.columns)},\n"
            "    {'set': '공정성 점검', 'rows': len(audit_x), 'columns': audit_x.shape[1], "
            "'features': ', '.join(audit_x.columns)},\n"
            "])\n"
            "feature_set_summary"
        ),
        nbf.v4.new_markdown_cell("### 6. 입력 후보의 결측치 확인"),
        nbf.v4.new_code_cell(
            "feature_missingness = build_feature_missingness(pandas_prepared)\n"
            "feature_missingness"
        ),
        nbf.v4.new_markdown_cell("## Checks\n\n타깃과 누수 차단 규칙을 자동 검증합니다."),
        nbf.v4.new_code_cell(
            "assert set(target.unique()) == {0, 1}\n"
            "assert target.notna().all()\n"
            "assert target_distribution['count_equal'].all()\n"
            "assert target_distribution['pandas_count'].sum() == 32_561\n"
            "assert 'marital-status' not in base_x.columns\n"
            "assert 'relationship' not in base_x.columns\n"
            "assert 'fnlwgt' not in base_x.columns\n"
            "assert 'income' not in base_x.columns\n"
            "assert 'income' in extended_x.columns\n\n"
            "print('검증 완료: 타깃 생성과 누수 변수 차단이 올바릅니다.')"
        ),
        nbf.v4.new_markdown_cell(
            "## Takeaways\n\n"
            "1. 양성 클래스가 67.19%로 더 많으므로 단순 정확도만으로 평가하지 않습니다.\n"
            "2. `workclass`와 `occupation`의 결측치는 이후 Pipeline에서 `Unknown`으로 대치합니다.\n"
            "3. `income`은 현재 시점 정보이므로 기본 모델과 분리해 추가 효과만 점검합니다.\n"
            "4. 다음 단계에서는 train/test를 먼저 나눈 뒤 훈련 데이터에서 EDA와 통계분석을 수행합니다."
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

