"""1단계 데이터 품질 확인용 Jupyter Notebook을 재생성한다."""

from pathlib import Path

import nbformat as nbf


PROJECT_ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_PATH = PROJECT_ROOT / "notebooks" / "01_data_quality.ipynb"


def build_notebook() -> nbf.NotebookNode:
    """위에서 아래로 실행 가능한 데이터 로딩 튜토리얼을 구성한다."""
    notebook = nbf.v4.new_notebook()
    notebook.metadata["kernelspec"] = {
        "display_name": "Python 3",
        "language": "python",
        "name": "python3",
    }
    notebook.metadata["language_info"] = {"name": "python", "version": "3.14"}

    notebook.cells = [
        nbf.v4.new_markdown_cell(
            "# 01. Adult Census 데이터 로딩 및 품질 비교\n\n"
            "## Goal\n\n"
            "동일한 UCI Adult 원본을 Pandas와 Polars로 읽고 shape, 컬럼, "
            "결측치, 고유값, 중복 행이 일치하는지 확인합니다."
        ),
        nbf.v4.new_markdown_cell(
            "## Setup\n\n"
            "이 노트북은 프로젝트의 `src/data.py`를 호출합니다. "
            "원본 파일이 없을 때만 UCI URL에서 다운로드합니다."
        ),
        nbf.v4.new_code_cell(
            "from pathlib import Path\n"
            "import sys\n\n"
            "import pandas as pd\n"
            "from IPython.display import Image, display\n\n"
            "project_root = Path.cwd()\n"
            "if project_root.name == 'notebooks':\n"
            "    project_root = project_root.parent\n"
            "if not (project_root / 'src').exists():\n"
            "    raise RuntimeError('adult-marriage-analysis 프로젝트 루트에서 실행하세요.')\n\n"
            "sys.path.insert(0, str(project_root))\n\n"
            "from src.data import (\n"
            "    compare_frames,\n"
            "    ensure_raw_data,\n"
            "    load_with_pandas,\n"
            "    load_with_polars,\n"
            ")\n"
            "from src.eda import build_missingness_summary, build_validity_summary\n"
            "from src.visualization import create_missingness_chart\n\n"
            "project_root"
        ),
        nbf.v4.new_markdown_cell("## Steps\n\n### 1. 동일한 원본 데이터 불러오기"),
        nbf.v4.new_code_cell(
            "raw_path = ensure_raw_data(project_root / 'data' / 'raw')\n"
            "pandas_df = load_with_pandas(raw_path)\n"
            "polars_df = load_with_polars(raw_path)\n\n"
            "print('원본 경로:', raw_path)\n"
            "print('Pandas shape:', pandas_df.shape)\n"
            "print('Polars shape:', polars_df.shape)"
        ),
        nbf.v4.new_markdown_cell("### 2. 데이터 일부 확인"),
        nbf.v4.new_code_cell("pandas_df.head()"),
        nbf.v4.new_code_cell("polars_df.head()"),
        nbf.v4.new_markdown_cell("### 3. 전체 및 컬럼별 비교"),
        nbf.v4.new_code_cell(
            "comparison_summary, column_comparison = compare_frames(\n"
            "    pandas_df, polars_df\n"
            ")\n"
            "comparison_summary"
        ),
        nbf.v4.new_code_cell("column_comparison"),
        nbf.v4.new_markdown_cell(
            "### 4. Question-driven EDA — 결측치는 어디에, 얼마나 존재하는가?\n\n"
            "결측치 개수·비율을 표와 막대그래프로 확인한 뒤 처리 방향을 기록합니다."
        ),
        nbf.v4.new_code_cell(
            "missingness = build_missingness_summary(pandas_df)\n"
            "print('[Question] 결측치는 어디에, 얼마나 존재하는가?')\n"
            "print(missingness.to_string(index=False, float_format=lambda x: f'{x:.2f}'))\n"
            "print('\\n[Next Action] workclass·occupation은 모델 Pipeline 안에서 Unknown으로 대치합니다.')\n"
            "print('[Next Action] native-country는 기본 모델 입력에서 제외하고 데이터 품질 기록만 남깁니다.')\n"
            "missingness"
        ),
        nbf.v4.new_code_cell(
            "missing_chart_path = create_missingness_chart(\n"
            "    pandas_df,\n"
            "    project_root / 'reports' / 'figures' / 'eda_missing_values.png',\n"
            ")\n"
            "display(Image(filename=str(missing_chart_path)))"
        ),
        nbf.v4.new_markdown_cell(
            "### 5. 중복이나 논리적으로 유효하지 않은 값은 없는가?\n\n"
            "중복은 개인 식별자가 없는 Census 표본이라는 점을 고려하고, 주요 숫자형 범위도 함께 점검합니다."
        ),
        nbf.v4.new_code_cell(
            "duplicate_rows = int(pandas_df.duplicated().sum())\n"
            "validity_summary = build_validity_summary(pandas_df)\n"
            "print(f'[Question] 완전 중복 행: {duplicate_rows:,}개')\n"
            "print('[Next Action] 개인 식별자가 없어 서로 다른 응답자일 수 있으므로 자동 삭제하지 않습니다.')\n"
            "print('\\n[Question] 숫자형 논리 범위 점검')\n"
            "display(validity_summary)\n"
            "print('[Next Action] 범위 위반이 없으므로 오류값 대치 없이 다음 EDA로 진행합니다.')"
        ),
        nbf.v4.new_markdown_cell("### 6. Question → Analysis → Next Action 요약"),
        nbf.v4.new_code_cell(
            "quality_decisions = pd.DataFrame([\n"
            "    {\n"
            "        'Question': '결측치는 어디에, 얼마나 존재하는가?',\n"
            "        'Analysis': '컬럼별 isna().sum(), 결측 비율, 막대그래프',\n"
            "        'Observed': ', '.join(f\"{r.column} {int(r.missing_count):,}건\" for r in missingness.itertuples()),\n"
            "        'Next Action': '범주형 입력은 Pipeline 내부에서 Unknown 대치',\n"
            "    },\n"
            "    {\n"
            "        'Question': '중복이나 유효하지 않은 값은 없는가?',\n"
            "        'Analysis': 'duplicated(), 논리 범위 규칙',\n"
            "        'Observed': f'완전 중복 {duplicate_rows:,}건, 범위 위반 {validity_summary.invalid_count.sum():,}건',\n"
            "        'Next Action': '중복은 자동 삭제하지 않고 범위 위반 없음 확인',\n"
            "    },\n"
            "])\n"
            "quality_decisions"
        ),
        nbf.v4.new_markdown_cell("## Checks\n\n두 라이브러리의 핵심 결과가 모두 일치하는지 자동 확인합니다."),
        nbf.v4.new_code_cell(
            "assert comparison_summary.loc[0, 'pandas_rows'] == 32_561\n"
            "assert comparison_summary.loc[0, 'pandas_rows'] == comparison_summary.loc[0, 'polars_rows']\n"
            "assert comparison_summary.loc[0, 'column_order_equal']\n"
            "assert comparison_summary.loc[0, 'total_nulls_equal']\n"
            "assert comparison_summary.loc[0, 'pandas_duplicate_rows'] == comparison_summary.loc[0, 'polars_duplicate_rows']\n"
            "assert column_comparison['null_count_equal'].all()\n"
            "assert column_comparison['unique_count_equal'].all()\n\n"
            "assert missing_chart_path.exists() and missing_chart_path.stat().st_size > 0\n"
            "assert validity_summary['invalid_count'].eq(0).all()\n"
            "print('검증 완료: Pandas와 Polars의 로딩 결과가 일치합니다.')"
        ),
        nbf.v4.new_markdown_cell(
            "## Next Steps\n\n"
            "- 확인된 데이터 크기: **32,561행 × 15열**\n"
            "- 결측치가 있는 컬럼: `workclass`, `occupation`, `native-country`\n"
            "- 완전 중복 행: **24개** — 개인 식별자가 없어 자동 삭제하지 않음\n"
            "- 다음 단계: `ever_married` 타깃 생성과 누수 변수 제거"
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
