"""
[실습 4] 시각화 4종 · 통계 검정 · sklearn Pipeline

# 작성자   : 홍은비
# 작성일자 : 2026-08-04

# 프로그램 설명
- 실습 3에서 사용한 sales_100k.csv를 읽고 같은 IQR 공식으로 amount 이상치를 제거한다.
- 하나의 2×2 Figure에 히스토그램+KDE, 박스플롯, 월별 라인, 상관 히트맵을 작성한다.
- 서울·부산 평균 매출 t-test와 지역·카테고리 독립성 카이제곱 검정을 수행하고
  p-value가 0.05보다 작은지에 따라 검정 결과를 한 줄로 해석한다.
- ColumnTransformer와 Pipeline으로 매출 예측 모델을 학습·평가·저장·재로딩한다.
- 실습 3의 region·category 집계 결과를 Plotly 막대 차트로 만들고 HTML로 저장한다.

# 변경 내역
- 실제 파일이 100만 행인 점을 고려해 KDE와 모델 학습에는 재현 가능한 표본을 사용한다.
- 통계 검정과 월별·지역별 집계는 IQR 이상치를 제거한 전체 데이터를 사용한다.
- 입력 파일·필수 컬럼·표본 크기를 검증하고 차트와 모델을 outputs·models에 분리한다.
"""

from __future__ import annotations

from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import seaborn as sns
from scipy.stats import chi2_contingency, ttest_ind
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OrdinalEncoder, StandardScaler


BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / "data" / "sales_100k.csv"
OUTPUT_DIR = BASE_DIR / "outputs"
MODEL_DIR = BASE_DIR / "models"
EDA_IMAGE_PATH = OUTPUT_DIR / "eda_dashboard.png"
MODEL_PATH = MODEL_DIR / "sales_pipeline.joblib"
PLOTLY_HTML_PATH = OUTPUT_DIR / "interactive_sales.html"

ALPHA = 0.05
RANDOM_STATE = 42
MAX_VISUAL_ROWS = 100000
MAX_MODEL_ROWS = 100000

NUMERIC_FEATURES = ["quantity", "unit_price", "customer_age"]
CATEGORICAL_FEATURES = [
    "region",
    "category",
    "payment_method",
    "customer_gender",
]
FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES
TARGET = "amount"
REQUIRED_COLUMNS = {
    "order_date",
    TARGET,
    *FEATURES,
}


def validate_input(csv_path: Path) -> None:
    """CSV 파일 존재 여부와 실습에 필요한 컬럼 구성을 확인한다."""
    if not csv_path.is_file():
        raise FileNotFoundError(f"CSV 파일을 찾을 수 없습니다: {csv_path}")

    columns = set(pd.read_csv(csv_path, nrows=0, encoding="utf-8-sig").columns)
    missing = REQUIRED_COLUMNS - columns
    if missing:
        raise ValueError(f"필수 컬럼이 누락됐습니다: {sorted(missing)}")


def load_and_clean(csv_path: Path) -> pd.DataFrame:
    """필요한 컬럼만 읽고 실습 3과 같은 amount IQR 정상 범위를 적용한다."""
    df = pd.read_csv(
        csv_path,
        usecols=sorted(REQUIRED_COLUMNS),
        encoding="utf-8-sig",
        dtype={column: "category" for column in CATEGORICAL_FEATURES},
    )
    df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")

    q1 = df[TARGET].quantile(0.25)
    q3 = df[TARGET].quantile(0.75)
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    cleaned = df[df[TARGET].between(lower, upper, inclusive="both")].copy()

    if cleaned.empty:
        raise ValueError("IQR 이상치 제거 후 분석할 행이 없습니다.")

    print("\n=== 실습 3 연계: IQR 이상치 제거 ===")
    print(f"정상 범위: {lower:,.2f} <= amount <= {upper:,.2f}")
    print(f"제거 전: {len(df):,}행 / 제거 후: {len(cleaned):,}행")
    return cleaned


def sample_rows(df: pd.DataFrame, max_rows: int) -> pd.DataFrame:
    """대용량 연산 시간을 줄이되 결과를 재현할 수 있도록 고정 시드로 표본을 만든다."""
    if max_rows <= 0:
        raise ValueError("표본 행 수는 1 이상이어야 합니다.")
    if len(df) <= max_rows:
        return df
    return df.sample(n=max_rows, random_state=RANDOM_STATE)


def create_eda_visualizations(df: pd.DataFrame) -> None:
    """fig, axes = plt.subplots(2, 2) 하나에 EDA 차트 네 종류를 작성한다."""
    visual_df = sample_rows(df, MAX_VISUAL_ROWS)
    monthly_sales = (
        df.dropna(subset=["order_date"])
        .assign(month=lambda frame: frame["order_date"].dt.to_period("M").dt.to_timestamp())
        .groupby("month", as_index=False, observed=True)[TARGET]
        .sum()
        .sort_values("month")
    )
    correlation = df[[*NUMERIC_FEATURES, TARGET]].corr(numeric_only=True)

    sns.set_theme(style="whitegrid")
    fig, axes = plt.subplots(2, 2, figsize=(16, 11))

    sns.histplot(visual_df[TARGET], bins=40, kde=True, ax=axes[0, 0])
    axes[0, 0].set_title("Amount Distribution (Histogram + KDE)")
    axes[0, 0].set_xlabel("Amount")

    sns.boxplot(data=visual_df, x="region", y=TARGET, ax=axes[0, 1])
    axes[0, 1].set_title("Amount by Region (Box Plot)")
    axes[0, 1].tick_params(axis="x", rotation=30)

    sns.lineplot(
        data=monthly_sales,
        x="month",
        y=TARGET,
        marker="o",
        ax=axes[1, 0],
    )
    axes[1, 0].set_title("Monthly Total Sales")
    axes[1, 0].set_xlabel("Month")
    axes[1, 0].set_ylabel("Total Amount")
    axes[1, 0].tick_params(axis="x", rotation=45)

    sns.heatmap(correlation, annot=True, fmt=".2f", cmap="coolwarm", ax=axes[1, 1])
    axes[1, 1].set_title("Numeric Correlation Heatmap")

    fig.suptitle("Sales EDA Dashboard", fontsize=18)
    fig.tight_layout()
    fig.savefig(EDA_IMAGE_PATH, dpi=150, bbox_inches="tight")
    plt.show()
    plt.close(fig)
    print(f"\n2×2 EDA 이미지 저장: {EDA_IMAGE_PATH}")


def interpret_p_value(p_value: float, test_name: str) -> str:
    """유의수준 0.05를 기준으로 p-value의 의미를 한 줄로 반환한다."""
    if p_value < ALPHA:
        return f"{test_name}: p < {ALPHA}이므로 귀무가설을 기각합니다. 통계적으로 유의합니다."
    return f"{test_name}: p >= {ALPHA}이므로 귀무가설을 기각할 수 없습니다."


def run_statistical_tests(df: pd.DataFrame) -> None:
    """서울·부산 Welch t-test와 지역·카테고리 카이제곱 검정을 수행한다."""
    seoul = df.loc[df["region"] == "서울", TARGET].dropna()
    busan = df.loc[df["region"] == "부산", TARGET].dropna()
    if len(seoul) < 2 or len(busan) < 2:
        raise ValueError("서울·부산 t-test를 수행하기 위한 표본이 부족합니다.")

    t_statistic, t_p_value = ttest_ind(
        seoul,
        busan,
        equal_var=False,
        nan_policy="omit",
    )
    print("\n=== t-test: 서울 vs 부산 평균 매출 ===")
    print(f"서울 평균: {seoul.mean():,.2f} / 부산 평균: {busan.mean():,.2f}")
    print(f"t-statistic: {t_statistic:.6f} / p-value: {t_p_value:.6g}")
    print(interpret_p_value(float(t_p_value), "t-test"))

    contingency_table = pd.crosstab(df["region"], df["category"])
    if contingency_table.shape[0] < 2 or contingency_table.shape[1] < 2:
        raise ValueError("카이제곱 검정을 위한 분할표의 범주가 부족합니다.")

    chi2, chi_p_value, degrees_of_freedom, _ = chi2_contingency(contingency_table)
    print("\n=== 카이제곱 검정: 지역 × 카테고리 ===")
    print("분할표:")
    print(contingency_table)
    print(
        f"chi2-statistic: {chi2:.6f} / 자유도: {degrees_of_freedom} "
        f"/ p-value: {chi_p_value:.6g}"
    )
    print(interpret_p_value(float(chi_p_value), "카이제곱 검정"))


def build_pipeline() -> Pipeline:
    """수치형·범주형 전처리와 회귀 모델을 하나의 sklearn Pipeline으로 구성한다."""
    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            (
                "encoder",
                OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1),
            ),
        ]
    )
    preprocessor = ColumnTransformer(
        transformers=[
            ("numeric", numeric_pipeline, NUMERIC_FEATURES),
            ("categorical", categorical_pipeline, CATEGORICAL_FEATURES),
        ]
    )
    return Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            (
                "model",
                HistGradientBoostingRegressor(
                    max_iter=100,
                    learning_rate=0.1,
                    random_state=RANDOM_STATE,
                ),
            ),
        ]
    )


def train_evaluate_save_pipeline(df: pd.DataFrame) -> None:
    """Pipeline을 fit·predict·score하고 joblib 저장 후 재로딩 예측까지 검증한다."""
    model_df = sample_rows(df[[*FEATURES, TARGET]].dropna(subset=[TARGET]), MAX_MODEL_ROWS)
    if len(model_df) < 10:
        raise ValueError("모델 학습에 필요한 데이터가 부족합니다.")

    features = model_df[FEATURES].copy()
    # category dtype의 누락값을 sklearn 전처리기가 안정적으로 다루도록 object로 변환한다.
    features[CATEGORICAL_FEATURES] = features[CATEGORICAL_FEATURES].astype("object")
    target = model_df[TARGET]
    x_train, x_test, y_train, y_test = train_test_split(
        features,
        target,
        test_size=0.2,
        random_state=RANDOM_STATE,
    )

    pipeline = build_pipeline()
    pipeline.fit(x_train, y_train)
    predictions = pipeline.predict(x_test)
    pipeline_score = pipeline.score(x_test, y_test)

    print("\n=== sklearn Pipeline 학습·평가 ===")
    print(f"학습 행 수: {len(x_train):,} / 평가 행 수: {len(x_test):,}")
    print(f"Pipeline score(R²): {pipeline_score:.6f}")
    print(f"r2_score: {r2_score(y_test, predictions):.6f}")
    print(f"MAE: {mean_absolute_error(y_test, predictions):,.2f}")

    joblib.dump(pipeline, MODEL_PATH)
    reloaded_pipeline = joblib.load(MODEL_PATH)
    reloaded_predictions = reloaded_pipeline.predict(x_test.head(5))
    print(f"모델 저장: {MODEL_PATH}")
    print(f"재로딩 후 예측 5건: {reloaded_predictions.round(2).tolist()}")


def create_plotly_chart(df: pd.DataFrame) -> None:
    """region·category별 총매출 막대 차트를 만들고 인터랙티브 HTML로 저장한다."""
    grouped_sales = (
        df.dropna(subset=["region", "category"])
        .groupby(["region", "category"], as_index=False, observed=True)
        .agg(total=(TARGET, "sum"))
        .sort_values("total", ascending=False, ignore_index=True)
    )
    figure = px.bar(
        grouped_sales,
        x="region",
        y="total",
        color="category",
        barmode="group",
        title="지역·카테고리별 총매출",
        labels={"region": "지역", "category": "카테고리", "total": "총매출"},
    )
    figure.update_layout(hovermode="x unified")
    figure.write_html(PLOTLY_HTML_PATH, include_plotlyjs=True)
    print(f"\nPlotly HTML 저장: {PLOTLY_HTML_PATH}")


def main() -> None:
    """IQR 정제부터 시각화·통계 검정·Pipeline·Plotly 저장까지 순서대로 실행한다."""
    validate_input(CSV_PATH)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    clean_df = load_and_clean(CSV_PATH)

    create_eda_visualizations(clean_df)
    run_statistical_tests(clean_df)
    train_evaluate_save_pipeline(clean_df)
    create_plotly_chart(clean_df)

    print("\n=== 실습 4 완료 ===")
    print(f"EDA·Plotly 결과 위치: {OUTPUT_DIR}")
    print(f"Pipeline 모델 위치: {MODEL_DIR}")


if __name__ == "__main__":
    try:
        main()
    except (FileNotFoundError, ValueError, TypeError, OSError) as exc:
        raise SystemExit(f"실행 중단: {exc}") from exc
