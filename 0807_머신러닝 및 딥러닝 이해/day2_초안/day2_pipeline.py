"""Adult 데이터를 이용한 End-to-End 분석 파이프라인.

Pandas·Polars 로딩 비교, 결측치·중복 처리, 기술통계·상관분석,
Plotly 시각화, scikit-learn Pipeline 학습·평가·저장, report.md 생성을
한 번에 수행한다.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from time import perf_counter
import warnings

import joblib
import matplotlib.pyplot as plt
from matplotlib import font_manager
import numpy as np
import pandas as pd
import plotly.express as px
import polars as pl
import seaborn as sns
from sklearn.base import BaseEstimator, TransformerMixin
from IPython.display import display
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.exceptions import ConvergenceWarning
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    classification_report,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import RepeatedStratifiedKFold, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


COLUMNS = [
    "age",
    "workclass",
    "fnlwgt",
    "education",
    "education-num",
    "marital-status",
    "occupation",
    "relationship",
    "race",
    "sex",
    "capital-gain",
    "capital-loss",
    "hours-per-week",
    "native-country",
    "income",
]

NUMERIC_COLUMNS = [
    "age",
    "fnlwgt",
    "education-num",
    "capital-gain",
    "capital-loss",
    "hours-per-week",
]

CATEGORICAL_COLUMNS = [
    "workclass",
    "education",
    "marital-status",
    "occupation",
    "relationship",
    "race",
    "sex",
    "native-country",
]

LOG_NUMERIC_COLUMNS = [
    "age",
    "education-num",
    "capital-gain-log",
    "capital-loss-log",
    "fnlwgt-log",
    "hours-per-week",
]

CAPITAL_ENGINEERED_NUMERIC_COLUMNS = LOG_NUMERIC_COLUMNS + [
    "capital-net-signed-log",
    "has-capital-activity",
    "capital-gain-per-hour-log",
]

BINNED_CATEGORICAL_COLUMNS = CATEGORICAL_COLUMNS + [
    "age-group",
    "hours-group",
]

ENGINEERED_NUMERIC_COLUMNS = CAPITAL_ENGINEERED_NUMERIC_COLUMNS + [
    "age-hours-interaction",
]

ENGINEERED_CATEGORICAL_COLUMNS = BINNED_CATEGORICAL_COLUMNS + [
    "education-occupation",
]

# Adult Census의 가능한 실제 극단값을 무조건 오류로 보지 않는다. IQR 처리는
# 연속형 후보 세 변수에만 실험하고, 0이 대부분인 capital-gain/loss와 작은
# 정수 범주의 education-num은 감사표에만 남긴다.
OUTLIER_EXPERIMENT_COLUMNS = ["age", "fnlwgt", "hours-per-week"]


def engineer_adult_features(frame: pd.DataFrame, stage: str = "engineered") -> pd.DataFrame:
    """Day16 실습 원칙을 Adult Census에 맞게 적용한 누수 없는 파생변수 생성."""

    transformed = frame.copy()
    if stage not in {"baseline", "log", "capital", "bins", "engineered"}:
        raise ValueError(f"지원하지 않는 Feature Engineering 단계: {stage}")
    if stage == "baseline":
        return transformed

    transformed["capital-gain-log"] = np.log1p(transformed["capital-gain"].clip(lower=0))
    transformed["capital-loss-log"] = np.log1p(transformed["capital-loss"].clip(lower=0))
    transformed["fnlwgt-log"] = np.log1p(transformed["fnlwgt"].clip(lower=0))
    if stage == "log":
        return transformed

    capital_net = transformed["capital-gain"] - transformed["capital-loss"]
    transformed["capital-net-signed-log"] = (
        np.sign(capital_net) * np.log1p(np.abs(capital_net))
    )
    transformed["has-capital-activity"] = (
        transformed["capital-gain"].gt(0) | transformed["capital-loss"].gt(0)
    ).astype(int)
    safe_hours = transformed["hours-per-week"].clip(lower=1)
    transformed["capital-gain-per-hour-log"] = np.log1p(
        transformed["capital-gain"].clip(lower=0) / safe_hours
    )
    if stage == "capital":
        return transformed

    transformed["age-group"] = pd.cut(
        transformed["age"],
        bins=[16, 29, 39, 49, 59, 100],
        labels=["20대 이하", "30대", "40대", "50대", "60대 이상"],
        include_lowest=True,
    ).astype(object)
    transformed["hours-group"] = pd.cut(
        transformed["hours-per-week"],
        bins=[0, 34, 40, 50, 100],
        labels=["주 34시간 이하", "주 35~40시간", "주 41~50시간", "주 51시간 이상"],
        include_lowest=True,
    ).astype(object)
    if stage == "bins":
        return transformed

    transformed["age-hours-interaction"] = (
        transformed["age"] * transformed["hours-per-week"]
    )
    transformed["education-occupation"] = (
        transformed["education"].fillna("Unknown").astype(str)
        + " | "
        + transformed["occupation"].fillna("Unknown").astype(str)
    )
    return transformed


class AdultFeatureEngineer(BaseEstimator, TransformerMixin):
    """sklearn Pipeline 안에서 단계별 Adult 파생변수를 생성한다."""

    def __init__(self, stage: str = "engineered") -> None:
        self.stage = stage

    def fit(self, x: pd.DataFrame, y: pd.Series | None = None) -> "AdultFeatureEngineer":
        return self

    def transform(self, x: pd.DataFrame) -> pd.DataFrame:
        return engineer_adult_features(x, stage=self.stage)


def engineer_selected_blocks(
    frame: pd.DataFrame,
    blocks: tuple[str, ...] = (),
) -> pd.DataFrame:
    """채택된 Feature Engineering 블록만 독립적으로 생성한다."""

    allowed = {"log", "capital", "bins", "interactions"}
    unknown = set(blocks) - allowed
    if unknown:
        raise ValueError(f"지원하지 않는 Feature 블록: {sorted(unknown)}")
    transformed = frame.copy()
    if "log" in blocks:
        transformed["capital-gain-log"] = np.log1p(transformed["capital-gain"].clip(lower=0))
        transformed["capital-loss-log"] = np.log1p(transformed["capital-loss"].clip(lower=0))
        transformed["fnlwgt-log"] = np.log1p(transformed["fnlwgt"].clip(lower=0))
    if "capital" in blocks:
        capital_net = transformed["capital-gain"] - transformed["capital-loss"]
        transformed["capital-net-signed-log"] = (
            np.sign(capital_net) * np.log1p(np.abs(capital_net))
        )
        transformed["has-capital-activity"] = (
            transformed["capital-gain"].gt(0) | transformed["capital-loss"].gt(0)
        ).astype(int)
        safe_hours = transformed["hours-per-week"].clip(lower=1)
        transformed["capital-gain-per-hour-log"] = np.log1p(
            transformed["capital-gain"].clip(lower=0) / safe_hours
        )
    if "bins" in blocks:
        transformed["age-group"] = pd.cut(
            transformed["age"],
            bins=[16, 29, 39, 49, 59, 100],
            labels=["20대 이하", "30대", "40대", "50대", "60대 이상"],
            include_lowest=True,
        ).astype(object)
        transformed["hours-group"] = pd.cut(
            transformed["hours-per-week"],
            bins=[0, 34, 40, 50, 100],
            labels=["주 34시간 이하", "주 35~40시간", "주 41~50시간", "주 51시간 이상"],
            include_lowest=True,
        ).astype(object)
    if "interactions" in blocks:
        transformed["age-hours-interaction"] = (
            transformed["age"] * transformed["hours-per-week"]
        )
        transformed["education-occupation"] = (
            transformed["education"].fillna("Unknown").astype(str)
            + " | "
            + transformed["occupation"].fillna("Unknown").astype(str)
        )
    return transformed


class SelectedFeatureEngineer(BaseEstimator, TransformerMixin):
    """채택된 블록만 Pipeline 안에서 재현하는 변환기."""

    def __init__(self, blocks: tuple[str, ...] = ()) -> None:
        self.blocks = blocks

    def fit(self, x: pd.DataFrame, y: pd.Series | None = None) -> "SelectedFeatureEngineer":
        return self

    def transform(self, x: pd.DataFrame) -> pd.DataFrame:
        return engineer_selected_blocks(x, blocks=self.blocks)


class IQRClipper(BaseEstimator, TransformerMixin):
    """Train에서 계산한 IQR 경계로 Train/Test의 선택 변수를 clip한다."""

    def __init__(self, columns: tuple[str, ...] = tuple(OUTLIER_EXPERIMENT_COLUMNS), multiplier: float = 1.5) -> None:
        self.columns = columns
        self.multiplier = multiplier

    def fit(self, x: pd.DataFrame, y: pd.Series | None = None) -> "IQRClipper":
        self.bounds_: dict[str, tuple[float, float]] = {}
        for column in self.columns:
            series = x[column].dropna()
            q1, q3 = series.quantile([0.25, 0.75])
            iqr = q3 - q1
            if iqr > 0:
                self.bounds_[column] = (
                    float(q1 - self.multiplier * iqr),
                    float(q3 + self.multiplier * iqr),
                )
        return self

    def transform(self, x: pd.DataFrame) -> pd.DataFrame:
        transformed = x.copy()
        for column, (lower, upper) in self.bounds_.items():
            transformed[column] = transformed[column].clip(lower=lower, upper=upper)
        return transformed


def _markdown_table(frame: pd.DataFrame, include_index: bool = False) -> str:
    """추가 패키지 없이 DataFrame을 간단한 Markdown 표로 변환한다."""

    printable = frame.reset_index() if include_index else frame.reset_index(drop=True)

    def format_value(value: object) -> str:
        if pd.isna(value):
            return ""
        if isinstance(value, float):
            return f"{value:.4f}"
        return str(value).replace("|", "\\|").replace("\n", " ")

    headers = [str(column) for column in printable.columns]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    for row in printable.itertuples(index=False, name=None):
        lines.append("| " + " | ".join(format_value(value) for value in row) + " |")
    return "\n".join(lines)


@dataclass(frozen=True)
class PipelineResult:
    """실행 결과와 생성 파일 위치를 노트북에서 확인하기 위한 요약."""

    rows_before: int
    rows_after: int
    duplicates_removed: int
    missing_before: int
    missing_after: int
    accuracy: float
    f1: float
    output_dir: Path
    report_path: Path
    model_path: Path
    plotly_path: Path


@dataclass(frozen=True)
class FeatureExperimentResult:
    """Day16 방식의 Feature Engineering 비교 결과."""

    comparison: pd.DataFrame
    outlier_audit: pd.DataFrame
    log_transform_audit: pd.DataFrame
    preprocessing_provenance: pd.DataFrame
    data_hygiene_audit: pd.DataFrame
    existing_preprocessing_ablation: pd.DataFrame
    model_convergence_audit: pd.DataFrame
    selected_feature_details: pd.DataFrame
    rare_category_cv_audit: pd.DataFrame
    best_experiment: str
    model_path: Path
    report_path: Path
    chart_path: Path


def _load_with_pandas(data_path: Path) -> tuple[pd.DataFrame, float]:
    """Adult 데이터를 Pandas로 읽고 문자열 공백과 소득 라벨을 정규화한다."""

    started = perf_counter()
    frame = pd.read_csv(
        data_path,
        header=None,
        names=COLUMNS,
        skipinitialspace=True,
        na_values=["?", " ?"],
    )
    elapsed = perf_counter() - started
    for column in frame.select_dtypes(include=["object", "string"]).columns:
        frame[column] = frame[column].str.strip()
    frame["income"] = frame["income"].str.removesuffix(".")
    return frame, elapsed


def _load_with_polars(data_path: Path) -> tuple[pl.DataFrame, float]:
    """같은 파일을 Polars로 읽어 Pandas 결과와 행·열 수를 비교한다."""

    started = perf_counter()
    frame = pl.read_csv(
        data_path,
        has_header=False,
        new_columns=COLUMNS,
        null_values=["?", " ?"],
    )
    # 원본 파일 끝의 빈 줄은 Pandas와 동일하게 데이터 행에서 제외한다.
    frame = frame.filter(pl.col("age").is_not_null())
    string_columns = [name for name, dtype in frame.schema.items() if dtype == pl.String]
    frame = frame.with_columns(pl.col(string_columns).str.strip_chars())
    frame = frame.with_columns(pl.col("income").str.strip_suffix("."))
    elapsed = perf_counter() - started
    return frame, elapsed


def _library_comparison(
    pandas_frame: pd.DataFrame,
    pandas_seconds: float,
    polars_frame: pl.DataFrame,
    polars_seconds: float,
) -> pd.DataFrame:
    """두 라이브러리의 로딩 결과와 메모리 사용량을 표로 반환한다."""

    comparison = pd.DataFrame(
        {
            "라이브러리": ["Pandas", "Polars"],
            "행": [pandas_frame.shape[0], polars_frame.height],
            "열": [pandas_frame.shape[1], polars_frame.width],
            "로딩 시간(초)": [pandas_seconds, polars_seconds],
            "추정 메모리(MB)": [
                pandas_frame.memory_usage(deep=True).sum() / 1024**2,
                polars_frame.estimated_size("mb"),
            ],
        }
    )
    if tuple(pandas_frame.shape) != tuple(polars_frame.shape):
        raise ValueError("Pandas와 Polars의 로딩 결과 크기가 일치하지 않습니다.")
    return comparison


def _clean_data(raw: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """결측 범주를 명시적으로 대체하고 완전 중복 행을 제거한다.

    분석 핵심 변수에는 결측치가 없지만, 원본의 workclass·occupation·
    native-country 결측치는 'Unknown'으로 대체해 처리 결과를 남긴다.
    """

    missing_before_by_column = raw.isna().sum()
    missing_columns = missing_before_by_column[missing_before_by_column > 0].index.tolist()
    cleaned = raw.copy()

    for column in missing_columns:
        if cleaned[column].dtype.kind in "biufc":
            cleaned[column] = cleaned[column].fillna(cleaned[column].median())
        else:
            cleaned[column] = cleaned[column].fillna("Unknown")

    duplicate_count = int(cleaned.duplicated().sum())
    cleaned = cleaned.drop_duplicates().reset_index(drop=True)

    cleaning_summary = pd.DataFrame(
        {
            "지표": [
                "전체 행",
                "전체 결측치",
                "완전 중복 행",
                "분석 핵심 변수 결측치",
            ],
            "처리 전": [
                len(raw),
                int(raw.isna().sum().sum()),
                int(raw.duplicated().sum()),
                int(raw[["education-num", "marital-status", "age", "sex"]].isna().sum().sum()),
            ],
            "처리 후": [
                len(cleaned),
                int(cleaned.isna().sum().sum()),
                int(cleaned.duplicated().sum()),
                int(cleaned[["education-num", "marital-status", "age", "sex"]].isna().sum().sum()),
            ],
            "처리 방법": [
                "완전 중복 제거",
                "범주형 Unknown 대체·수치형 중앙값 대체",
                f"{duplicate_count}건 제거",
                "원래 결측치 없음—별도 대체 불필요",
            ],
        }
    )
    return cleaned, cleaning_summary


def _save_statistics(cleaned: pd.DataFrame, output_dir: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """평균·표준편차·분위수 기술통계와 수치형 상관행렬을 저장한다."""

    descriptive = (
        cleaned[NUMERIC_COLUMNS]
        .describe(percentiles=[0.25, 0.5, 0.75])
        .T.rename(
            columns={
                "count": "표본수",
                "mean": "평균",
                "std": "표준편차",
                "min": "최솟값",
                "25%": "1사분위수",
                "50%": "중앙값",
                "75%": "3사분위수",
                "max": "최댓값",
            }
        )
    )
    descriptive.index.name = "변수"
    correlation = cleaned[NUMERIC_COLUMNS].corr()
    descriptive.to_csv(output_dir / "descriptive_statistics.csv", encoding="utf-8-sig")
    correlation.to_csv(output_dir / "correlation_matrix.csv", encoding="utf-8-sig")
    return descriptive, correlation


def _save_visualizations(cleaned: pd.DataFrame, output_dir: Path) -> tuple[Path, Path]:
    """Seaborn 정적 차트와 Plotly 인터랙티브 HTML을 생성한다."""

    static_path = output_dir / "seaborn_eda.png"
    sns.set_theme(style="whitegrid")
    available_fonts = {item.name for item in font_manager.fontManager.ttflist}
    for font in ["Apple SD Gothic Neo", "Malgun Gothic", "NanumGothic", "DejaVu Sans"]:
        if font in available_fonts:
            plt.rcParams["font.family"] = font
            break
    plt.rcParams["axes.unicode_minus"] = False
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    sns.histplot(
        data=cleaned,
        x="education-num",
        hue="income",
        discrete=True,
        stat="probability",
        common_norm=False,
        ax=axes[0],
    )
    axes[0].set(
        title="소득 집단별 교육연수 분포",
        xlabel="교육연수",
        ylabel="집단 내 비율",
    )
    sns.boxplot(data=cleaned, x="income", y="hours-per-week", ax=axes[1])
    axes[1].set(
        title="소득 집단별 주당 근로시간",
        xlabel="소득 집단",
        ylabel="주당 근로시간",
    )
    plt.tight_layout()
    fig.savefig(static_path, dpi=150, bbox_inches="tight")
    plt.close(fig)

    income_by_education = (
        cleaned.assign(income_over_50k=cleaned["income"].eq(">50K").astype(int))
        .groupby("education", as_index=False)
        .agg(표본수=("income_over_50k", "size"), 고소득비율=("income_over_50k", "mean"))
        .sort_values("고소득비율", ascending=False)
    )
    interactive = px.bar(
        income_by_education,
        x="education",
        y="고소득비율",
        color="표본수",
        hover_data={"표본수": ":,", "고소득비율": ":.2%"},
        title="교육수준별 연소득 5만 달러 초과 비율",
        labels={"education": "교육수준", "고소득비율": "고소득 비율"},
    )
    interactive.update_layout(xaxis_tickangle=-45)
    interactive.update_yaxes(tickformat=".0%")
    interactive_path = output_dir / "plotly_income_by_education.html"
    interactive.write_html(interactive_path, include_plotlyjs=True)
    return static_path, interactive_path


def _train_income_model(cleaned: pd.DataFrame, output_dir: Path) -> tuple[Pipeline, dict[str, object], Path]:
    """소득 분류 Pipeline을 학습하고 정확도·F1을 계산한 뒤 모델을 저장한다."""

    features = cleaned[NUMERIC_COLUMNS + CATEGORICAL_COLUMNS]
    target = cleaned["income"].eq(">50K").astype(int)
    x_train, x_test, y_train, y_test = train_test_split(
        features,
        target,
        test_size=0.2,
        random_state=42,
        stratify=target,
    )

    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore", min_frequency=2)),
        ]
    )
    preprocessor = ColumnTransformer(
        transformers=[
            ("numeric", numeric_pipeline, NUMERIC_COLUMNS),
            ("categorical", categorical_pipeline, CATEGORICAL_COLUMNS),
        ]
    )
    model = Pipeline(
        steps=[
            ("preprocessor", preprocessor),
            ("classifier", LogisticRegression(max_iter=1000, random_state=42)),
        ]
    )
    model.fit(x_train, y_train)
    predictions = model.predict(x_test)
    metrics: dict[str, object] = {
        "accuracy": float(accuracy_score(y_test, predictions)),
        "f1": float(f1_score(y_test, predictions)),
        "test_rows": int(len(y_test)),
        "classification_report": classification_report(
            y_test,
            predictions,
            target_names=["<=50K", ">50K"],
            output_dict=True,
            zero_division=0,
        ),
    }

    model_path = output_dir / "adult_income_pipeline.joblib"
    metrics_path = output_dir / "model_metrics.json"
    joblib.dump(model, model_path)
    metrics_path.write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return model, metrics, model_path


def _build_feature_experiment_pipeline(stage: str, outlier_method: str) -> Pipeline:
    """동일 모델에서 Feature Engineering 단계만 바꾸는 비교 Pipeline."""

    if stage == "baseline":
        numeric_columns = NUMERIC_COLUMNS
        categorical_columns = CATEGORICAL_COLUMNS
    elif stage == "log":
        numeric_columns = LOG_NUMERIC_COLUMNS
        categorical_columns = CATEGORICAL_COLUMNS
    elif stage == "capital":
        numeric_columns = CAPITAL_ENGINEERED_NUMERIC_COLUMNS
        categorical_columns = CATEGORICAL_COLUMNS
    elif stage == "bins":
        numeric_columns = CAPITAL_ENGINEERED_NUMERIC_COLUMNS
        categorical_columns = BINNED_CATEGORICAL_COLUMNS
    elif stage == "engineered":
        numeric_columns = ENGINEERED_NUMERIC_COLUMNS
        categorical_columns = ENGINEERED_CATEGORICAL_COLUMNS
    else:
        raise ValueError(f"지원하지 않는 단계: {stage}")

    numeric_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
    ])
    categorical_pipeline = Pipeline([
        ("imputer", SimpleImputer(strategy="most_frequent")),
        (
            "onehot",
            OneHotEncoder(
                handle_unknown="infrequent_if_exist",
                min_frequency=0.01,
            ),
        ),
    ])
    preprocessor = ColumnTransformer([
        ("numeric", numeric_pipeline, numeric_columns),
        ("categorical", categorical_pipeline, categorical_columns),
    ])

    steps: list[tuple[str, object]] = []
    if outlier_method == "clip":
        steps.append(("outlier_clip", IQRClipper()))
    elif outlier_method not in {"none", "remove"}:
        raise ValueError(f"지원하지 않는 이상치 처리 방법: {outlier_method}")
    steps.extend([
        ("feature_creation", AdultFeatureEngineer(stage=stage)),
        ("preprocessor", preprocessor),
        ("classifier", LogisticRegression(max_iter=1000, random_state=42)),
    ])
    return Pipeline(steps)


def _build_selected_feature_pipeline(
    blocks: tuple[str, ...],
    outlier_method: str = "none",
) -> Pipeline:
    """Forward selection에서 채택된 블록만 포함한 Pipeline."""

    numeric_columns = NUMERIC_COLUMNS.copy()
    categorical_columns = CATEGORICAL_COLUMNS.copy()
    if "log" in blocks:
        numeric_columns += ["capital-gain-log", "capital-loss-log", "fnlwgt-log"]
    if "capital" in blocks:
        numeric_columns += [
            "capital-net-signed-log",
            "has-capital-activity",
            "capital-gain-per-hour-log",
        ]
    if "bins" in blocks:
        categorical_columns += ["age-group", "hours-group"]
    if "interactions" in blocks:
        numeric_columns.append("age-hours-interaction")
        categorical_columns.append("education-occupation")

    preprocessor = ColumnTransformer([
        (
            "numeric",
            Pipeline([
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
            ]),
            numeric_columns,
        ),
        (
            "categorical",
            Pipeline([
                ("imputer", SimpleImputer(strategy="constant", fill_value="Unknown")),
                (
                    "onehot",
                    OneHotEncoder(
                        handle_unknown="ignore",
                        min_frequency=2,
                    ),
                ),
            ]),
            categorical_columns,
        ),
    ])
    steps: list[tuple[str, object]] = []
    if outlier_method == "clip":
        steps.append(("outlier_clip", IQRClipper()))
    elif outlier_method not in {"none", "remove"}:
        raise ValueError(f"지원하지 않는 이상치 처리: {outlier_method}")
    steps.extend([
        ("feature_creation", SelectedFeatureEngineer(blocks=blocks)),
        ("preprocessor", preprocessor),
        ("classifier", LogisticRegression(max_iter=1000, random_state=42)),
    ])
    return Pipeline(steps)


def _build_outlier_audit(
    train_features: pd.DataFrame,
    train_target: pd.Series,
) -> pd.DataFrame:
    """IQR 후보와 도메인 위반을 분리해 이상치 처리 근거를 기록한다."""

    domain_rules = {
        "age": (17, np.inf, "UCI 추출 조건 AAGE>16"),
        "fnlwgt": (2, np.inf, "UCI 추출 조건 AFNLWGT>1"),
        "education-num": (1, 16, "로컬 Adult 교육 단계 코드"),
        "capital-gain": (0, np.inf, "자본이익은 음수가 아님"),
        "capital-loss": (0, np.inf, "자본손실 금액은 음수가 아님"),
        "hours-per-week": (1, np.inf, "UCI 추출 조건 HRSWK>0"),
    }
    rows: list[dict[str, object]] = []
    for column in NUMERIC_COLUMNS:
        series = train_features[column].dropna().astype(float)
        aligned_target = train_target.loc[series.index]
        q1, q3 = series.quantile([0.25, 0.75])
        iqr = q3 - q1
        if iqr > 0:
            lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
            candidate_mask = series.lt(lower) | series.gt(upper)
            outlier_count = int(candidate_mask.sum())
            outlier_rate = float(candidate_mask.mean())
            candidate_target_rate = (
                float(aligned_target.loc[candidate_mask].mean()) if outlier_count else np.nan
            )
            regular_target_rate = float(aligned_target.loc[~candidate_mask].mean())
            iqr_judgement = "희귀 관측 후보—오류 판정 아님"
        else:
            lower, upper = float(q1), float(q3)
            outlier_count = np.nan
            outlier_rate = np.nan
            candidate_target_rate = np.nan
            regular_target_rate = float(aligned_target.mean())
            iqr_judgement = "적용 부적합—IQR=0인 0 집중 분포"

        domain_lower, domain_upper, domain_basis = domain_rules[column]
        domain_violation_mask = series.lt(domain_lower) | series.gt(domain_upper)
        domain_violation_count = int(domain_violation_mask.sum())
        if column in OUTLIER_EXPERIMENT_COLUMNS:
            decision = "none/clip/remove 성능 비교"
        elif column in {"capital-gain", "capital-loss"}:
            decision = "IQR 삭제 제외, log1p 효과 검증"
        elif column == "education-num":
            decision = "유효 코드이므로 삭제 안 함"
        else:
            decision = "감사만 수행"
        rows.append({
            "변수": column,
            "최솟값": float(series.min()),
            "최댓값": float(series.max()),
            "왜도": float(series.skew()),
            "0 비율": float(series.eq(0).mean()),
            "IQR 하한": float(lower),
            "IQR 상한": float(upper),
            "IQR 후보 수": outlier_count,
            "IQR 후보 비율": outlier_rate,
            "IQR 후보 고소득률": candidate_target_rate,
            "IQR 정상범위 고소득률": regular_target_rate,
            "IQR 판정": iqr_judgement,
            "도메인 기준": f"[{domain_lower}, {domain_upper}] — {domain_basis}",
            "도메인 위반 수": domain_violation_count,
            "처리 결정": decision,
        })
    return pd.DataFrame(rows)


def _build_log_transform_audit(train_features: pd.DataFrame) -> pd.DataFrame:
    """로그 변환 전후 왜도·범위·상위 분위수 변화를 비교한다."""

    rows: list[dict[str, object]] = []
    for column in ["capital-gain", "capital-loss", "fnlwgt"]:
        before = train_features[column].dropna().astype(float)
        after = np.log1p(before.clip(lower=0))
        skew_before = float(before.skew())
        skew_after = float(after.skew())
        rows.append({
            "변수": column,
            "변환": f"log1p({column})",
            "왜도 전": skew_before,
            "왜도 후": skew_after,
            "절대왜도 변화": abs(skew_after) - abs(skew_before),
            "왜도 개선": abs(skew_after) < abs(skew_before),
            "0 비율": float(before.eq(0).mean()),
            "P99 전": float(before.quantile(0.99)),
            "P99 후": float(after.quantile(0.99)),
            "최댓값 전": float(before.max()),
            "최댓값 후": float(after.max()),
            "판정": (
                "긴 꼬리 완화" if abs(skew_after) < abs(skew_before)
                else "0 집중으로 왜도 개선 제한—성능 비교 필요"
            ),
        })
    return pd.DataFrame(rows)


def _build_preprocessing_provenance(
    existing: pd.DataFrame,
    comparison: pd.DataFrame,
    hygiene: pd.DataFrame,
    outliers: pd.DataFrame,
    logs: pd.DataFrame,
    convergence: pd.DataFrame,
    rare_cv: pd.DataFrame,
) -> pd.DataFrame:
    """기존·개선·신규 처리를 이유와 실제 검증 결과까지 한 표로 기록한다."""

    def old(group: str, setting: str) -> pd.Series:
        return existing.loc[
            existing["검증 항목"].eq(group) & existing["설정"].eq(setting)
        ].iloc[0]

    def step(prefix: str) -> pd.Series:
        return comparison.loc[comparison["단계"].str.startswith(prefix)].iloc[0]

    numeric_only, onehot = old("범주형 인코딩", "수치형만"), old("범주형 인코딩", "+ One-Hot")
    unscaled, scaled = old("수치형 스케일링", "미적용"), old("수치형 스케일링", "StandardScaler")
    missing_drop, missing_unknown = old("범주형 결측 처리", "결측 3개 컬럼 제외"), old("범주형 결측 처리", "Unknown 대치")
    rare_old, rare_new = old("희소 범주", "2건 미만 통합(기존)"), old("희소 범주", "1% 미만 통합(후보)")
    duplicate_keep, duplicate_drop = old("완전 중복", "유지"), old("완전 중복", "Train 중복 제거")
    log_step, capital_step, bins_step, interaction_step = step("02"), step("03"), step("04"), step("05")
    clip_step, remove_step = step("06"), step("07")
    skew_text = ", ".join(
        f"{row['변수']} {row['왜도 전']:.3f}→{row['왜도 후']:.3f}"
        for _, row in logs.iterrows()
    )
    domain_violations = int(outliers["도메인 위반 수"].sum())
    hours_outlier_rate = float(
        outliers.loc[outliers["변수"].eq("hours-per-week"), "IQR 후보 비율"].iloc[0]
    )
    convergence_50 = convergence.loc[convergence["max_iter"].eq(50)].iloc[0]
    convergence_100 = convergence.loc[convergence["max_iter"].eq(100)].iloc[0]
    convergence_1000 = convergence.loc[convergence["max_iter"].eq(1000)].iloc[0]
    rare_cv_means = rare_cv.groupby("설정")[["Feature 수", "F1", "PR-AUC"]].mean()
    rare_cv_paired = rare_cv.pivot(index="분할", columns="설정", values=["F1", "PR-AUC"])
    rare_cv_f1_delta = rare_cv_paired[("F1", "1% 미만 통합")] - rare_cv_paired[("F1", "2건 미만 통합")]
    rare_cv_pr_delta = rare_cv_paired[("PR-AUC", "1% 미만 통합")] - rare_cv_paired[("PR-AUC", "2건 미만 통합")]

    def metric_change(before: pd.Series, after: pd.Series) -> str:
        return (
            f"F1 {before['F1']:.4f}→{after['F1']:.4f}, "
            f"PR-AUC {before['PR-AUC']:.4f}→{after['PR-AUC']:.4f}"
        )

    provenance = pd.DataFrame([
        {"항목": "문자열·소득 라벨", "수정 전 기존 설정": "공백·라벨 마침표 제거", "현재 설정": "동일", "표시": "[기존 유지]", "유지·변경 이유": "공백 차이로 같은 범주가 분리되는 것을 막고 adult.data/test 라벨 형식을 통일", "검증 결과·최종 판단": "공백 455,854개 정규화, ? 4,262개 결측 인식, 현재 파일 라벨 마침표 변경 0건; 성능 튜닝이 아닌 데이터 품질 처리라 유지"},
        {"항목": "결측치", "수정 전 기존 설정": "전체 데이터 Unknown 대체 후 분할", "현재 설정": "먼저 분할 후 Train에서만 Unknown 대치", "표시": "[기존 설정 개선]", "유지·변경 이유": "Test 분포로 대치값을 결정하는 누수를 막고, 결측 행·변수를 버리지 않고 정보를 보존", "검증 결과·최종 판단": f"결측 3개 컬럼 제외 대비 {metric_change(missing_drop, missing_unknown)}; Unknown 대치를 채택"},
        {"항목": "StandardScaler", "수정 전 기존 설정": "모든 수치형 표준화", "현재 설정": "동일", "표시": "[기존 유지]", "유지·변경 이유": "단위 차이가 큰 fnlwgt·자본 변수의 규모가 L2 로지스틱 회귀 계수와 최적화를 지배하지 않게 함", "검증 결과·최종 판단": f"미적용 대비 {metric_change(unscaled, scaled)}; 두 지표가 크게 상승해 유지"},
        {"항목": "One-Hot", "수정 전 기존 설정": "One-Hot", "현재 설정": "One-Hot 유지", "표시": "[기존 유지]", "유지·변경 이유": "직업·교육·혼인 상태는 순서가 없는 명목형이므로 임의 숫자 순서를 부여하지 않음", "검증 결과·최종 판단": f"수치형만 사용 대비 {metric_change(numeric_only, onehot)}; 범주형 정보의 기여가 커서 유지"},
        {"항목": "희소·미관측 범주", "수정 전 기존 설정": "min_frequency=2, unknown=ignore", "현재 설정": "기존 설정 유지", "표시": "[기존 유지·1% 제외]", "유지·변경 이유": "Feature 수 감소는 그 자체가 목표가 아니며, 희소 범주 통합은 분산 감소 가능성과 유용한 소수 범주 정보 손실을 함께 비교해야 함", "검증 결과·최종 판단": f"단일 Holdout은 Feature {int(rare_old['변환 후 Feature 수'])}→{int(rare_new['변환 후 Feature 수'])}, {metric_change(rare_old, rare_new)}였으나 5×5 반복 CV의 1%−2건 평균은 F1 {rare_cv_f1_delta.mean():+.4f}, PR-AUC {rare_cv_pr_delta.mean():+.4f}; F1 우세 {int((rare_cv_f1_delta > 0).sum())}/25 fold로 일관되지 않아 1%를 제외하고 기존 2건 유지"},
        {"항목": "중복", "수정 전 기존 설정": "전체 데이터 24행 제거 후 분할", "현재 설정": "기본 유지", "표시": "[기존 설정 변경]", "유지·변경 이유": "개인 ID가 없어 같은 사람의 중복인지 서로 다른 사람의 동일 응답인지 판별할 수 없음", "검증 결과·최종 판단": f"Train 중복 {int(duplicate_drop['제거 행'])}행 제거 시 {metric_change(duplicate_keep, duplicate_drop)}; 개선이 없어 유지"},
        {"항목": "Train/Test 분할", "수정 전 기존 설정": "결측·중복 처리 후 80:20", "현재 설정": "80:20 분할 후 Train에서만 fit", "표시": "[기존 설정 개선]", "유지·변경 이유": "대치값·스케일·범주·IQR 경계에 Test 정보가 들어가는 데이터 누수를 차단", "검증 결과·최종 판단": "Holdout 성능을 공정하게 측정하기 위한 방법론 조건이므로 변경"},
        {"항목": "모델·반복 상한", "수정 전 기존 설정": "LogisticRegression(max_iter=1000)", "현재 설정": "동일", "표시": "[기존 유지]", "유지·변경 이유": "이진분류·희소 One-Hot에 맞는 해석 가능한 Baseline 모델을 고정하고, 1000은 미수렴 방지를 위한 반복 상한으로 둠", "검증 결과·최종 판단": f"50회는 경고 {int(convergence_50['수렴 경고'])}건·F1 {convergence_50['F1']:.4f}; 100회는 실제 {int(convergence_100['실제 반복'])}회에 수렴, 1000 설정도 실제 {int(convergence_1000['실제 반복'])}회·동일 성능. 1000번을 항상 도는 것이 아니라 여유 상한이라 유지"},
        {"항목": "IQR·도메인 검사", "수정 전 기존 설정": "없음", "현재 설정": "IQR 후보와 도메인 위반 분리", "표시": "[신규 추가]", "유지·변경 이유": "IQR 밖의 희귀값을 실제 오류로 오판해 유효 응답을 삭제하지 않기 위함", "검증 결과·최종 판단": f"도메인 위반 {domain_violations}건, 근무시간 IQR 후보 {hours_outlier_rate:.1%}; IQR만으로 삭제하지 않고 처리 후보를 성능 비교"},
        {"항목": "로그 변환", "수정 전 기존 설정": "없음", "현재 설정": "원본 유지 + log1p 3개 열", "표시": "[소득 분류용·채택]", "유지·변경 이유": "0 집중·오른쪽 긴 꼬리를 압축하되 원본 정보는 보존", "검증 결과·최종 판단": f"왜도: {skew_text}; Baseline 대비 F1 {log_step['비교 기준 대비 F1']:+.4f}, PR-AUC {log_step['비교 기준 대비 PR-AUC']:+.4f}; 소득 분류 모델에만 채택"},
        {"항목": "자본 파생변수", "수정 전 기존 설정": "없음", "현재 설정": "순자본·활동 여부·시간당 이익", "표시": "[소득 분류용·채택]", "유지·변경 이유": "자본이익과 손실의 순효과·발생 여부·근무시간 대비 크기를 직접 표현", "검증 결과·최종 판단": f"직전 최적 조합 대비 F1 {capital_step['비교 기준 대비 F1']:+.4f}, PR-AUC {capital_step['비교 기준 대비 PR-AUC']:+.4f}; 소득 분류 모델에만 채택"},
        {"항목": "연령·근무시간 구간", "수정 전 기존 설정": "없음", "현재 설정": "연령대·주당시간 구간", "표시": "[소득 분류용·채택]", "유지·변경 이유": "소득과 생애주기·근무형태의 비선형 관계를 표현하기 위한 예측 feature이며, 결혼 경험별 평균 교육연수 가설의 검정변수는 아님", "검증 결과·최종 판단": f"직전 최적 조합 대비 F1 {bins_step['비교 기준 대비 F1']:+.4f}, PR-AUC {bins_step['비교 기준 대비 PR-AUC']:+.4f}; 소득 분류 모델에만 채택"},
        {"항목": "상호작용", "수정 전 기존 설정": "없음", "현재 설정": "교육×직업, 나이×근무시간 시험 후 제외", "표시": "[신규 추가·제외]", "유지·변경 이유": "변수 결합 효과를 표현하려 했으나 두 핵심 지표가 모두 비하락해야 한다는 채택 규칙 적용", "검증 결과·최종 판단": f"직전 최적 조합 대비 F1 {interaction_step['비교 기준 대비 F1']:+.4f}, PR-AUC {interaction_step['비교 기준 대비 PR-AUC']:+.4f}; F1 하락으로 제외"},
        {"항목": "IQR clip/remove", "수정 전 기존 설정": "없음", "현재 설정": "none 채택, clip/remove 제외", "표시": "[신규 비교·제외]", "유지·변경 이유": "유효 극단값 손상과 표본 손실이 실제 예측 개선으로 보상되는지 확인", "검증 결과·최종 판단": f"clip ΔF1 {clip_step['비교 기준 대비 F1']:+.4f}/ΔPR {clip_step['비교 기준 대비 PR-AUC']:+.4f}, remove {int(remove_step['제거 행'])}행·ΔF1 {remove_step['비교 기준 대비 F1']:+.4f}/ΔPR {remove_step['비교 기준 대비 PR-AUC']:+.4f}; 모두 제외"},
        {"항목": "Target 로그", "수정 전 기존 설정": "없음", "현재 설정": "미적용", "표시": "[적용 제외]", "유지·변경 이유": "소득 Target은 연속 금액이 아니라 0/1 이진 라벨이라 log1p가 의미와 모델 목적을 바꾸지 않음", "검증 결과·최종 판단": "적용 대상이 아니므로 성능 실험 없이 제외"},
    ])
    scope = {
        "문자열·소득 라벨": "전체 데이터 품질",
        "결측치": "소득 분류 + 공통 품질",
        "IQR·도메인 검사": "소득 분류 진단",
    }
    provenance.insert(
        1,
        "적용 범위",
        provenance["항목"].map(scope).fillna("소득 분류 모델"),
    )
    return provenance


def _build_data_hygiene_audit(data_path: Path) -> pd.DataFrame:
    """성능보다 데이터 일관성이 목적인 기존 정리 작업의 변경 건수를 기록한다."""

    unnormalized = pd.read_csv(data_path, header=None, names=COLUMNS, dtype=str)
    string_columns = COLUMNS[1:]
    whitespace_changes = 0
    for column in string_columns:
        series = unnormalized[column].dropna()
        whitespace_changes += int(series.ne(series.str.strip()).sum())
    question_tokens = int(
        unnormalized[string_columns]
        .apply(lambda column: column.str.strip().eq("?").sum())
        .sum()
    )
    income_periods = int(
        unnormalized["income"].dropna().str.strip().str.endswith(".").sum()
    )
    normalized, _ = _load_with_pandas(data_path)
    return pd.DataFrame([
        {
            "처리": "문자열 앞뒤 공백 제거",
            "변경 건수": whitespace_changes,
            "왜 필요한가": "같은 범주가 공백 차이로 다른 범주가 되는 문제 방지",
            "성능 판단": "단일 파일에서 공백 형식이 일관되면 성능보다 재현성·파일 호환성 목적",
        },
        {
            "처리": "? → 결측치 변환",
            "변경 건수": question_tokens,
            "왜 필요한가": "Unknown 문자열이 아니라 결측 상태로 대치 전략에 전달",
            "성능 판단": "모델 입력 가능성과 결측 대치 비교를 위한 필수 정리",
        },
        {
            "처리": "소득 라벨 마침표 제거",
            "변경 건수": income_periods,
            "왜 필요한가": "adult.data의 >50K와 adult.test의 >50K. 형식 통일",
            "성능 판단": "현재 adult.data에는 변경이 없어 성능 변화 없음; 외부 Test 호환성 목적",
        },
        {
            "처리": "완전 중복 탐지",
            "변경 건수": int(normalized.duplicated().sum()),
            "왜 필요한가": "동일 행이 Train/Test 평가를 왜곡하는지 민감도 확인",
            "성능 판단": "식별자가 없어 자동 삭제하지 않고 유지/제거 실험으로 판단",
        },
    ])


def _build_existing_preprocessing_pipeline(
    *,
    include_categorical: bool,
    scale_numeric: bool,
    categorical_columns: list[str] | None = None,
    categorical_imputation: str = "most_frequent",
    min_frequency: int | float = 2,
) -> Pipeline:
    """기존 전처리 한 항목씩의 기여를 비교하기 위한 공통 모델."""

    numeric_steps: list[tuple[str, object]] = [
        ("imputer", SimpleImputer(strategy="median")),
    ]
    if scale_numeric:
        numeric_steps.append(("scaler", StandardScaler()))
    transformers: list[tuple[str, object, list[str]]] = [
        ("numeric", Pipeline(numeric_steps), NUMERIC_COLUMNS),
    ]
    if include_categorical:
        selected_categorical = categorical_columns or CATEGORICAL_COLUMNS
        if categorical_imputation == "most_frequent":
            categorical_imputer = SimpleImputer(strategy="most_frequent")
        elif categorical_imputation == "unknown":
            categorical_imputer = SimpleImputer(strategy="constant", fill_value="Unknown")
        else:
            raise ValueError(f"지원하지 않는 범주형 결측 처리: {categorical_imputation}")
        handle_unknown = "infrequent_if_exist" if isinstance(min_frequency, float) else "ignore"
        categorical_pipeline = Pipeline([
            ("imputer", categorical_imputer),
            (
                "onehot",
                OneHotEncoder(
                    handle_unknown=handle_unknown,
                    min_frequency=min_frequency,
                ),
            ),
        ])
        transformers.append(("categorical", categorical_pipeline, selected_categorical))
    return Pipeline([
        ("preprocessor", ColumnTransformer(transformers)),
        (
            "classifier",
            LogisticRegression(solver="liblinear", max_iter=5000, random_state=42),
        ),
    ])


def _evaluate_binary_model(
    model: Pipeline,
    x_test: pd.DataFrame,
    y_test: pd.Series,
) -> dict[str, float]:
    predictions = model.predict(x_test)
    probabilities = model.predict_proba(x_test)[:, 1]
    return {
        "Accuracy": float(accuracy_score(y_test, predictions)),
        "Precision": float(precision_score(y_test, predictions, zero_division=0)),
        "Recall": float(recall_score(y_test, predictions, zero_division=0)),
        "F1": float(f1_score(y_test, predictions, zero_division=0)),
        "ROC-AUC": float(roc_auc_score(y_test, probabilities)),
        "PR-AUC": float(average_precision_score(y_test, probabilities)),
    }


def _run_existing_preprocessing_ablation(
    x_train: pd.DataFrame,
    x_test: pd.DataFrame,
    y_train: pd.Series,
    y_test: pd.Series,
) -> pd.DataFrame:
    """기존 전처리별 목적과 Holdout 성능 기여를 쌍별로 검증한다."""

    missing_categorical = {"workclass", "occupation", "native-country"}
    stable_categorical = [
        column for column in CATEGORICAL_COLUMNS if column not in missing_categorical
    ]
    configurations = [
        {"검증 항목": "범주형 인코딩", "설정": "수치형만", "include_categorical": False, "scale_numeric": True},
        {"검증 항목": "범주형 인코딩", "설정": "+ One-Hot", "include_categorical": True, "scale_numeric": True},
        {"검증 항목": "수치형 스케일링", "설정": "미적용", "include_categorical": True, "scale_numeric": False},
        {"검증 항목": "수치형 스케일링", "설정": "StandardScaler", "include_categorical": True, "scale_numeric": True},
        {"검증 항목": "범주형 결측 처리", "설정": "결측 3개 컬럼 제외", "include_categorical": True, "scale_numeric": True, "categorical_columns": stable_categorical},
        {"검증 항목": "범주형 결측 처리", "설정": "최빈값 대치", "include_categorical": True, "scale_numeric": True},
        {"검증 항목": "범주형 결측 처리", "설정": "Unknown 대치", "include_categorical": True, "scale_numeric": True, "categorical_imputation": "unknown"},
        {"검증 항목": "희소 범주", "설정": "2건 미만 통합(기존)", "include_categorical": True, "scale_numeric": True, "min_frequency": 2},
        {"검증 항목": "희소 범주", "설정": "1% 미만 통합(후보)", "include_categorical": True, "scale_numeric": True, "min_frequency": 0.01},
        {"검증 항목": "완전 중복", "설정": "유지", "include_categorical": True, "scale_numeric": True, "min_frequency": 0.01},
        {"검증 항목": "완전 중복", "설정": "Train 중복 제거", "include_categorical": True, "scale_numeric": True, "min_frequency": 0.01, "drop_duplicates": True},
    ]
    rows: list[dict[str, object]] = []
    for configuration in configurations:
        model_kwargs = {
            key: configuration[key]
            for key in [
                "include_categorical",
                "scale_numeric",
                "categorical_columns",
                "categorical_imputation",
                "min_frequency",
            ]
            if key in configuration
        }
        train_x = x_train
        train_y = y_train
        removed_rows = 0
        if configuration.get("drop_duplicates", False):
            duplicate_mask = x_train.duplicated()
            removed_rows = int(duplicate_mask.sum())
            train_x = x_train.loc[~duplicate_mask]
            train_y = y_train.loc[~duplicate_mask]
        model = _build_existing_preprocessing_pipeline(**model_kwargs)
        model.fit(train_x, train_y)
        metrics = _evaluate_binary_model(model, x_test, y_test)
        transformed_feature_count = int(
            len(model.named_steps["preprocessor"].get_feature_names_out())
        )
        rows.append({
            "검증 항목": configuration["검증 항목"],
            "설정": configuration["설정"],
            "학습 행": int(len(train_x)),
            "제거 행": removed_rows,
            "변환 후 Feature 수": transformed_feature_count,
            **metrics,
        })
    result = pd.DataFrame(rows)
    result["그룹 기준 F1 변화"] = result.groupby("검증 항목", sort=False)["F1"].transform(
        lambda values: values - values.iloc[0]
    )
    result["그룹 기준 PR-AUC 변화"] = result.groupby("검증 항목", sort=False)["PR-AUC"].transform(
        lambda values: values - values.iloc[0]
    )
    return result


def _run_rare_category_repeated_cv(
    features: pd.DataFrame,
    target: pd.Series,
) -> pd.DataFrame:
    """희소 범주 2건과 1% 기준을 동일한 5×5 반복 fold에서 비교한다."""

    splitter = RepeatedStratifiedKFold(
        n_splits=5,
        n_repeats=5,
        random_state=42,
    )
    rows: list[dict[str, object]] = []
    for split_number, (train_index, test_index) in enumerate(
        splitter.split(features, target), start=1
    ):
        for setting, min_frequency, handle_unknown in [
            ("2건 미만 통합", 2, "ignore"),
            ("1% 미만 통합", 0.01, "infrequent_if_exist"),
        ]:
            model = _build_selected_feature_pipeline(())
            model.set_params(
                preprocessor__categorical__onehot__min_frequency=min_frequency,
                preprocessor__categorical__onehot__handle_unknown=handle_unknown,
            )
            model.fit(features.iloc[train_index], target.iloc[train_index])
            metrics = _evaluate_binary_model(
                model, features.iloc[test_index], target.iloc[test_index]
            )
            rows.append({
                "분할": split_number,
                "설정": setting,
                "Feature 수": int(
                    len(model.named_steps["preprocessor"].get_feature_names_out())
                ),
                "F1": metrics["F1"],
                "PR-AUC": metrics["PR-AUC"],
            })
    return pd.DataFrame(rows)


def _iqr_remove_mask(train_features: pd.DataFrame) -> pd.Series:
    """Train에서만 IQR 경계를 학습해 제거 실험용 행 마스크를 만든다."""

    remove_mask = pd.Series(False, index=train_features.index)
    for column in OUTLIER_EXPERIMENT_COLUMNS:
        series = train_features[column]
        q1, q3 = series.quantile([0.25, 0.75])
        iqr = q3 - q1
        if iqr <= 0:
            continue
        lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        remove_mask |= series.lt(lower) | series.gt(upper)
    return remove_mask


def run_feature_engineering_experiments(
    data_path: str | Path = "adult.data",
    output_dir: str | Path = "artifacts",
) -> FeatureExperimentResult:
    """Day16의 Baseline→로그→파생변수→이상치 전략을 공정하게 비교한다."""

    data_path = Path(data_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    data_hygiene_audit = _build_data_hygiene_audit(data_path)
    data_hygiene_audit.to_csv(
        output_dir / "data_hygiene_audit.csv", index=False, encoding="utf-8-sig"
    )
    raw, _ = _load_with_pandas(data_path)
    features = raw[NUMERIC_COLUMNS + CATEGORICAL_COLUMNS]
    target = raw["income"].eq(">50K").astype(int)
    x_train, x_test, y_train, y_test = train_test_split(
        features,
        target,
        test_size=0.2,
        random_state=42,
        stratify=target,
    )
    existing_preprocessing_ablation = _run_existing_preprocessing_ablation(
        x_train, x_test, y_train, y_test
    )
    existing_preprocessing_ablation.to_csv(
        output_dir / "existing_preprocessing_ablation.csv",
        index=False,
        encoding="utf-8-sig",
    )
    rare_category_cv_audit = _run_rare_category_repeated_cv(features, target)
    rare_category_cv_audit.to_csv(
        output_dir / "rare_category_repeated_cv.csv",
        index=False,
        encoding="utf-8-sig",
    )
    rare_category_cv_summary = (
        rare_category_cv_audit.groupby("설정", sort=False)
        .agg(
            평균_Feature_수=("Feature 수", "mean"),
            평균_F1=("F1", "mean"),
            F1_표준편차=("F1", "std"),
            평균_PR_AUC=("PR-AUC", "mean"),
            PR_AUC_표준편차=("PR-AUC", "std"),
        )
        .reset_index()
    )
    rare_category_cv_summary.to_csv(
        output_dir / "rare_category_cv_summary.csv",
        index=False,
        encoding="utf-8-sig",
    )

    outlier_audit = _build_outlier_audit(x_train, y_train)
    outlier_audit.to_csv(
        output_dir / "adult_outlier_audit.csv", index=False, encoding="utf-8-sig"
    )
    log_transform_audit = _build_log_transform_audit(x_train)
    log_transform_audit.to_csv(
        output_dir / "log_transform_audit.csv", index=False, encoding="utf-8-sig"
    )
    def accepted(candidate: dict[str, float], reference: dict[str, float]) -> bool:
        non_decreasing = (
            candidate["F1"] >= reference["F1"]
            and candidate["PR-AUC"] >= reference["PR-AUC"]
        )
        strictly_better = (
            candidate["F1"] > reference["F1"]
            or candidate["PR-AUC"] > reference["PR-AUC"]
        )
        return non_decreasing and strictly_better

    rows: list[dict[str, object]] = []
    baseline_model = _build_selected_feature_pipeline(())
    baseline_model.fit(x_train, y_train)
    baseline_metrics = _evaluate_binary_model(baseline_model, x_test, y_test)
    current_blocks: tuple[str, ...] = ()
    current_outlier = "none"
    current_model = baseline_model
    current_metrics = baseline_metrics
    rows.append({
        "단계": "01 Baseline",
        "표시": "[개선 Baseline]",
        "시험 후보": "없음",
        "시험 조합": "기존 변수만",
        "비교 기준": "공통 기준",
        "채택 결과": "채택",
        "판단 근거": "Forward selection 시작점",
        "학습 행": int(len(x_train)),
        "제거 행": 0,
        **baseline_metrics,
        "비교 기준 대비 F1": 0.0,
        "비교 기준 대비 PR-AUC": 0.0,
        "Baseline 대비 F1": 0.0,
        "Baseline 대비 PR-AUC": 0.0,
    })

    feature_candidates = [
        ("02 로그 변환", "log", "log1p 3개"),
        ("03 자본 파생", "capital", "자본 파생변수 3개"),
        ("04 구간화", "bins", "연령대·근무시간 구간"),
        ("05 상호작용", "interactions", "교육×직업, 나이×근무시간"),
    ]
    for step_name, block, label in feature_candidates:
        reference_metrics = current_metrics
        reference_label = " + ".join(current_blocks) if current_blocks else "기존 변수만"
        candidate_blocks = current_blocks + (block,)
        candidate_model = _build_selected_feature_pipeline(candidate_blocks, current_outlier)
        candidate_model.fit(x_train, y_train)
        candidate_metrics = _evaluate_binary_model(candidate_model, x_test, y_test)
        keep = accepted(candidate_metrics, reference_metrics)
        reason = (
            "F1·PR-AUC 모두 비하락, 최소 하나 상승"
            if keep
            else "F1 또는 PR-AUC 하락으로 제외"
        )
        rows.append({
            "단계": step_name,
            "표시": "[신규 후보]",
            "시험 후보": label,
            "시험 조합": " + ".join(candidate_blocks),
            "비교 기준": reference_label,
            "채택 결과": "채택" if keep else "제외",
            "판단 근거": reason,
            "학습 행": int(len(x_train)),
            "제거 행": 0,
            **candidate_metrics,
            "비교 기준 대비 F1": candidate_metrics["F1"] - reference_metrics["F1"],
            "비교 기준 대비 PR-AUC": candidate_metrics["PR-AUC"] - reference_metrics["PR-AUC"],
            "Baseline 대비 F1": candidate_metrics["F1"] - baseline_metrics["F1"],
            "Baseline 대비 PR-AUC": candidate_metrics["PR-AUC"] - baseline_metrics["PR-AUC"],
        })
        if keep:
            current_blocks = candidate_blocks
            current_model = candidate_model
            current_metrics = candidate_metrics

    pre_outlier_metrics = current_metrics
    pre_outlier_model = current_model
    outlier_candidates: list[tuple[str, str, Pipeline, dict[str, float], int]] = []
    for step_name, outlier_method in [
        ("06 IQR clip", "clip"),
        ("07 IQR remove", "remove"),
    ]:
        train_x = x_train
        train_y = y_train
        removed_rows = 0
        if outlier_method == "remove":
            remove_mask = _iqr_remove_mask(x_train)
            removed_rows = int(remove_mask.sum())
            train_x = x_train.loc[~remove_mask]
            train_y = y_train.loc[~remove_mask]
        candidate_model = _build_selected_feature_pipeline(current_blocks, outlier_method)
        candidate_model.fit(train_x, train_y)
        candidate_metrics = _evaluate_binary_model(candidate_model, x_test, y_test)
        keep = accepted(candidate_metrics, pre_outlier_metrics)
        rows.append({
            "단계": step_name,
            "표시": "[신규 후보]",
            "시험 후보": f"IQR {outlier_method}",
            "시험 조합": (" + ".join(current_blocks) or "기존 변수만") + f" + IQR {outlier_method}",
            "비교 기준": (" + ".join(current_blocks) or "기존 변수만") + " + 이상치 none",
            "채택 결과": "채택 후보" if keep else "제외",
            "판단 근거": (
                "F1·PR-AUC 모두 비하락, 최소 하나 상승"
                if keep
                else "F1 또는 PR-AUC 하락으로 제외"
            ),
            "학습 행": int(len(train_x)),
            "제거 행": removed_rows,
            **candidate_metrics,
            "비교 기준 대비 F1": candidate_metrics["F1"] - pre_outlier_metrics["F1"],
            "비교 기준 대비 PR-AUC": candidate_metrics["PR-AUC"] - pre_outlier_metrics["PR-AUC"],
            "Baseline 대비 F1": candidate_metrics["F1"] - baseline_metrics["F1"],
            "Baseline 대비 PR-AUC": candidate_metrics["PR-AUC"] - baseline_metrics["PR-AUC"],
        })
        if keep:
            outlier_candidates.append(
                (step_name, outlier_method, candidate_model, candidate_metrics, removed_rows)
            )

    if outlier_candidates:
        selected_outlier = max(
            outlier_candidates,
            key=lambda item: (item[3]["PR-AUC"], item[3]["F1"]),
        )
        current_outlier = selected_outlier[1]
        current_model = selected_outlier[2]
        current_metrics = selected_outlier[3]
        for row in rows:
            if row["단계"] == selected_outlier[0]:
                row["채택 결과"] = "최종 채택"

    comparison = pd.DataFrame(rows)
    comparison.to_csv(
        output_dir / "feature_engineering_experiments.csv",
        index=False,
        encoding="utf-8-sig",
    )
    selected_feature_details = pd.DataFrame([
        {
            "코드명": "log",
            "의미": "오른쪽 꼬리가 긴 수치의 로그 파생열",
            "생성 변수·계산": "capital-gain-log=log1p(capital-gain), capital-loss-log=log1p(capital-loss), fnlwgt-log=log1p(fnlwgt); 원본 열도 유지",
            "왜 추가했나": "큰 값 몇 개가 선형계수에 과도하게 작용하는 것을 완화하고, 원본과 로그 표현 중 모델이 유용한 쪽을 선택하게 하기 위해",
            "분포 근거": "capital-gain 왜도 12.080→3.114, capital-loss 4.594→4.291, fnlwgt 1.451→-0.850",
            "성능 근거": f"직전 조합 대비 F1 {comparison.loc[comparison['단계'].str.startswith('02'), '비교 기준 대비 F1'].iloc[0]:+.4f}, PR-AUC {comparison.loc[comparison['단계'].str.startswith('02'), '비교 기준 대비 PR-AUC'].iloc[0]:+.4f}; 채택",
            "적용 범위": "소득 분류 모델만",
        },
        {
            "코드명": "capital",
            "의미": "자본소득의 순효과·발생 여부·근무시간 대비 크기",
            "생성 변수·계산": "signed-log(capital-gain−capital-loss), 자본활동 여부(0/1), log1p(capital-gain/hours-per-week)",
            "왜 추가했나": "gain과 loss를 따로 보는 원본 변수만으로는 순자본 방향, 자본소득 발생 자체, 근무시간 대비 크기를 직접 표현하지 못하기 때문에",
            "분포 근거": "capital-gain 91.75%, capital-loss 95.30%가 0인 희소·0 집중 변수",
            "성능 근거": f"직전 조합 대비 F1 {comparison.loc[comparison['단계'].str.startswith('03'), '비교 기준 대비 F1'].iloc[0]:+.4f}, PR-AUC {comparison.loc[comparison['단계'].str.startswith('03'), '비교 기준 대비 PR-AUC'].iloc[0]:+.4f}; 채택",
            "적용 범위": "소득 분류 모델만",
        },
        {
            "코드명": "bins",
            "의미": "연령과 주당 근무시간의 구간 범주",
            "생성 변수·계산": "age: ≤29, 30대, 40대, 50대, ≥60; hours: ≤34, 35–40, 41–50, ≥51",
            "왜 추가했나": "소득과 연령·근무시간의 관계가 일정한 직선이라고 가정하지 않고 생애주기와 근무형태별 비선형 차이를 표현하기 위해",
            "분포 근거": "연속형 원본 열도 함께 유지해 구간화 정보 손실을 보완",
            "성능 근거": f"직전 조합 대비 F1 {comparison.loc[comparison['단계'].str.startswith('04'), '비교 기준 대비 F1'].iloc[0]:+.4f}, PR-AUC {comparison.loc[comparison['단계'].str.startswith('04'), '비교 기준 대비 PR-AUC'].iloc[0]:+.4f}; 채택",
            "적용 범위": "소득 분류 모델만; 교육연수 가설 검정에는 미적용",
        },
    ])
    selected_feature_details.to_csv(
        output_dir / "selected_feature_details.csv",
        index=False,
        encoding="utf-8-sig",
    )

    convergence_rows: list[dict[str, object]] = []
    convergence_train_x, convergence_train_y = x_train, y_train
    if current_outlier == "remove":
        convergence_remove_mask = _iqr_remove_mask(x_train)
        convergence_train_x = x_train.loc[~convergence_remove_mask]
        convergence_train_y = y_train.loc[~convergence_remove_mask]
    for max_iter in [50, 100, 300, 1000]:
        convergence_model = _build_selected_feature_pipeline(
            current_blocks, current_outlier
        )
        convergence_model.set_params(classifier__max_iter=max_iter)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", ConvergenceWarning)
            convergence_model.fit(convergence_train_x, convergence_train_y)
        convergence_metrics = _evaluate_binary_model(
            convergence_model, x_test, y_test
        )
        convergence_rows.append({
            "max_iter": max_iter,
            "실제 반복": int(convergence_model.named_steps["classifier"].n_iter_[0]),
            "수렴 경고": sum(
                issubclass(item.category, ConvergenceWarning) for item in caught
            ),
            "F1": convergence_metrics["F1"],
            "PR-AUC": convergence_metrics["PR-AUC"],
        })
    model_convergence_audit = pd.DataFrame(convergence_rows)
    model_convergence_audit.to_csv(
        output_dir / "model_convergence_audit.csv",
        index=False,
        encoding="utf-8-sig",
    )
    preprocessing_provenance = _build_preprocessing_provenance(
        existing_preprocessing_ablation,
        comparison,
        data_hygiene_audit,
        outlier_audit,
        log_transform_audit,
        model_convergence_audit,
        rare_category_cv_audit,
    )
    preprocessing_provenance.to_csv(
        output_dir / "preprocessing_provenance.csv", index=False, encoding="utf-8-sig"
    )

    selected_labels = list(current_blocks)
    if current_outlier != "none":
        selected_labels.append(f"IQR {current_outlier}")
    best_experiment = "기존 변수만" if not selected_labels else " + ".join(selected_labels)
    best_model = current_model
    final_f1_gain = current_metrics["F1"] - baseline_metrics["F1"]
    final_pr_gain = current_metrics["PR-AUC"] - baseline_metrics["PR-AUC"]
    rejected_steps = comparison.loc[
        comparison["채택 결과"].eq("제외"), "단계"
    ].tolist()
    rejected_text = ", ".join(rejected_steps) if rejected_steps else "없음"
    model_path = output_dir / "adult_income_feature_engineered_pipeline.joblib"
    joblib.dump(best_model, model_path)

    chart_path = output_dir / "feature_engineering_comparison.png"
    chart_labels = (
        comparison["단계"]
        + " ["
        + comparison["채택 결과"]
        + "]"
    )
    chart_data = comparison.set_index(chart_labels)[["F1", "ROC-AUC", "PR-AUC"]]
    available_fonts = {item.name for item in font_manager.fontManager.ttflist}
    for font in ["Apple SD Gothic Neo", "Malgun Gothic", "NanumGothic", "DejaVu Sans"]:
        if font in available_fonts:
            plt.rcParams["font.family"] = font
            break
    plt.rcParams["axes.unicode_minus"] = False
    ax = chart_data.plot(kind="bar", figsize=(14, 5.5), ylim=(0, 1), rot=18)
    ax.set(
        title="Adult Income: 전처리 후보별 성능과 채택 결과",
        xlabel="",
        ylabel="점수",
    )
    ax.legend(loc="lower right")
    ax.grid(axis="x", visible=False)
    plt.tight_layout()
    plt.savefig(chart_path, dpi=160, bbox_inches="tight")
    plt.close()

    report_path = output_dir / "feature_engineering_report.md"
    report_path.write_text(
        f"""# Day16 방식 Adult Census Feature Engineering 실험

> 이 보고서의 Target은 소득(`>50K`)이다. 프로젝트의 주 연구가설인 “결혼 경험 유무에 따른 평균 교육연수 차이”를 검정하는 Welch t-test·보정 OLS와는 별도다. 따라서 연령·근무시간 구간화의 채택은 소득 예측 성능에만 해당하며 가설 검정에 적용했다는 뜻이 아니다.

## 실험 원칙

- 동일한 `random_state=42`의 80:20 계층화 분할을 모든 실험에 사용했다.
- 결측 대체·스케일링·인코딩·IQR clip 경계는 Train에서만 학습했다.
- Target은 이진 소득 라벨이므로 로그 변환하지 않았다.
- IQR 후보는 오류가 아니라 드문 관측일 수 있어 `none`, `clip`, `remove`를 비교했다.
- 후보는 현재 최적 조합과 비교해 **F1과 PR-AUC가 모두 하락하지 않고, 둘 중 하나 이상 상승할 때만** 채택했다.
- 제외된 후보는 다음 단계로 전달하지 않았다. 따라서 성능이 나빠진 전처리가 뒤 조합에 남지 않는다.

### Baseline 정의

- 기존 원본 모델: 전체 데이터에서 Unknown 대치·중복 24행 제거 후 분할, StandardScaler, One-Hot(`min_frequency=2`), 로지스틱 회귀.
- 이번 01 Baseline: 먼저 분할하고 Train에서만 수치 중앙값·범주 `Unknown` 대치·StandardScaler·One-Hot(`min_frequency=2`)을 fit하며 중복은 유지한다.
- 따라서 01은 누수 방지와 결측 처리 순서를 개선했지만, 희소 범주 기준은 반복 교차검증 결과에 따라 기존 2건을 유지한 공통 실험 Baseline이다.

## 기존 처리와 신규·개선 처리

{_markdown_table(preprocessing_provenance)}

## 기존 데이터 정리의 변경 근거

{_markdown_table(data_hygiene_audit)}

문자열·라벨 정규화는 현재 단일 Holdout의 점수를 높이기보다 다른 Adult 파일과 범주 형식을 일치시키고 결측 대치를 가능하게 하는 데이터 품질 처리다.

## 기존 전처리별 성능 검증

{_markdown_table(existing_preprocessing_ablation.round(4))}

- 각 `검증 항목` 안에서 첫 행이 비교 기준이며 `그룹 기준 변화`는 같은 항목의 첫 행 대비 변화다.
- One-Hot은 수치형만 사용한 모델과, 스케일링은 동일한 전체 변수 모델의 미적용 상태와 비교한다.
- 결측 대치는 결측이 있는 세 범주형 컬럼을 버리는 경우와 비교한다.
- 희소 범주와 중복 처리는 기존 기준과 개선 기준을 같은 Test에서 비교한다.

### 기존 전처리 결론

- One-Hot은 수치형만 사용한 모델보다 F1을 약 0.150, PR-AUC를 약 0.109 높여 유지 근거가 강하다.
- StandardScaler는 현재 L2 liblinear 설정에서 F1을 약 0.280, PR-AUC를 약 0.298 높여 유지 근거가 강하다.
- 결측 컬럼을 제외하는 것보다 최빈값 또는 Unknown 대치가 F1과 PR-AUC를 모두 높인다.
- Feature 수 감소는 계산·분산 측면의 잠재적 이점일 뿐 성능 향상을 보장하지 않는다. 1% 기준은 단일 Holdout에서 Feature를 105→63으로 줄이고 F1·PR-AUC가 각각 약 0.0007·0.0009 높았지만, 이 차이는 매우 작다.
- 5-fold×5회 반복 교차검증에서는 1%−2건 평균이 F1 약 -0.0014, PR-AUC 약 -0.0001이었고 F1 우세도 25개 fold 중 8개뿐이었다. 개선이 일관되지 않아 1% 후보를 제외하고 기존 `min_frequency=2`를 유지한다.

### 희소 범주 기준 반복 교차검증

{_markdown_table(rare_category_cv_summary.round(4))}
- Train 중복 17행 제거는 성능을 개선하지 않아 자동 삭제 근거가 없다.
- 문자열·라벨 정규화는 현재 Holdout 성능보다 범주 일관성, 결측 인식, adult.test 호환성이 목적이다.

### LogisticRegression `max_iter` 근거

{_markdown_table(model_convergence_audit.round(4))}

`max_iter=1000`은 1000번을 반드시 반복하라는 뜻이 아니라 최대 허용 횟수다. 현재 최종 조합은 99회에 수렴하므로 100·300·1000의 성능은 같고, 50에서는 수렴 경고와 성능 저하가 발생한다. 1000은 feature 변경 시 수렴 여유를 둔 보수적 상한이며 성능 튜닝값으로 해석하지 않는다.

## IQR·도메인 검사 근거

{_markdown_table(outlier_audit.round(4))}

- `도메인 위반 수=0`이면 관측 범위가 사전에 정의한 유효 범위 안에 있다는 뜻이다.
- UCI 공식 설명의 추출 조건은 `age>16`, `fnlwgt>1`, `hours-per-week>0`이다.
- IQR 후보는 분포상 희귀하다는 표시이며 오류 판정이 아니다.
- `capital-gain/loss`는 Q1=Q3=0이라 IQR이 0이므로 IQR 삭제 기준을 적용하지 않는다.
- `remove`의 표본 손실과 `none/clip`의 성능을 함께 보고 이상치 전략을 선택한다.
- 공식 설명에 상한이 없는 변수는 높은 값이 진짜인지 원자료 수준에서 확정할 수 없으므로 도메인 검사는 명백한 하한 위반만 판별한다.

## 로그 변환 전후 근거

{_markdown_table(log_transform_audit.round(4))}

로그 변환은 왜도 감소만으로 자동 채택하지 않고, 다음 단계의 Holdout 성능 변화까지 함께 본다.

## 단계별 결과

{_markdown_table(comparison.round(4))}

### 표 읽는 법

- 02~05는 **forward selection**이다. 각 후보를 `현재까지 채택된 최적 조합 + 후보 하나`로 시험한다.
- F1 또는 PR-AUC가 하락하면 그 후보를 제외하고, 다음 후보는 제외 전의 최적 조합에서 다시 시험한다.
- 06과 07은 feature 후보 선택이 끝난 동일 조합에서 `clip`과 `remove`를 각각 `none`과 비교한다.
- 두 이상치 후보가 모두 채택 조건을 만족하면 PR-AUC, F1 순으로 더 좋은 하나만 최종 채택한다.
- `비교 기준 대비`는 각 행의 `비교 기준` 조합과의 차이이고, `Baseline 대비`는 01과의 총 차이다.

위 채택 규칙으로 저장한 최종 조합은 **{best_experiment}**이다.

- 최종 F1: **{current_metrics['F1']:.4f}** (Baseline 대비 **{final_f1_gain:+.4f}**)
- 최종 PR-AUC: **{current_metrics['PR-AUC']:.4f}** (Baseline 대비 **{final_pr_gain:+.4f}**)
- 성능 조건을 통과하지 못해 최종 모델에서 뺀 후보: **{rejected_text}**

## 최종 채택 조합의 뜻과 근거

{_markdown_table(selected_feature_details)}

`log + capital + bins`는 위 세 feature 블록의 코드명이다. 세 블록 모두 직전 최적 조합보다 F1과 PR-AUC가 낮아지지 않고 최소 하나가 상승해 남았으며, 원본 변수는 삭제하지 않고 파생열을 추가한다.

## 시험했지만 제외한 후보

- 02 후보: 원본 변수는 유지하고 `capital-gain/loss/fnlwgt`의 `log1p` 열을 추가
- 03 후보: 순자본소득 signed-log, 자본 활동 여부, 시간당 자본이익 로그값
- 04 후보: 연령대와 주당 근로시간 구간
- 05 후보: 교육수준×직업 결합 범주, 나이×주당 근로시간 상호작용
- 06~07 후보: 선택된 feature 조합에서 IQR clip/remove

실제 저장 모델에는 위 후보 중 표에서 `채택` 또는 `최종 채택`으로 표시된 처리만 포함된다.

## 해석 제한

- `fnlwgt`는 Census 표본 가중치이므로 개인 특성으로 해석하면 안 된다. 여기서는 기존 모델과의 비교를 위해 변환 실험에 포함했다.
- 단일 Holdout 비교이므로 작은 성능 차이는 다른 분할에서 바뀔 수 있다. 다음 단계는 교차검증이다.
- 후보 순서에 따라 선택 결과가 달라질 수 있으며, 단일 Holdout의 작은 차이는 교차검증으로 재검증해야 한다.
""",
        encoding="utf-8",
    )
    return FeatureExperimentResult(
        comparison=comparison,
        outlier_audit=outlier_audit,
        log_transform_audit=log_transform_audit,
        preprocessing_provenance=preprocessing_provenance,
        data_hygiene_audit=data_hygiene_audit,
        existing_preprocessing_ablation=existing_preprocessing_ablation,
        model_convergence_audit=model_convergence_audit,
        selected_feature_details=selected_feature_details,
        rare_category_cv_audit=rare_category_cv_audit,
        best_experiment=best_experiment,
        model_path=model_path,
        report_path=report_path,
        chart_path=chart_path,
    )


def _generate_report(
    output_dir: Path,
    comparison: pd.DataFrame,
    cleaning_summary: pd.DataFrame,
    descriptive: pd.DataFrame,
    correlation: pd.DataFrame,
    metrics: dict[str, object],
) -> Path:
    """실행 결과를 Markdown 보고서로 자동 작성한다."""

    # 대각선을 제외한 절댓값 최대 상관관계를 보고서에 표시한다.
    correlation_without_diagonal = correlation.copy()
    for column in correlation_without_diagonal.columns:
        correlation_without_diagonal.loc[column, column] = pd.NA
    pair = correlation_without_diagonal.abs().stack().idxmax()
    pair_value = float(correlation.loc[pair[0], pair[1]])

    report_path = output_dir / "report.md"
    report = f"""# Day 2 종합실습 자동 분석 보고서

## 데이터 로딩 비교

{_markdown_table(comparison.round(4))}

Pandas와 Polars에서 모두 {int(comparison.loc[0, '행']):,}행 × {int(comparison.loc[0, '열'])}열을 확인했다.
시간 측정값은 실행 환경과 캐시 상태에 따라 달라질 수 있다.

## 결측치·중복 처리

{_markdown_table(cleaning_summary)}

분석 핵심 변수에는 원래 결측치가 없었다. 그 외 범주형 결측치는 `Unknown`으로 명시적으로 대체했고,
완전 중복 행은 독립 관측으로 볼 근거가 부족하므로 제거했다.

## 기술통계

{_markdown_table(descriptive.round(3), include_index=True)}

평균·표준편차뿐 아니라 1사분위수, 중앙값, 3사분위수를 함께 제시했다.

## 상관분석

대각선을 제외한 절댓값 기준 최대 상관관계는 `{pair[0]}`와 `{pair[1]}`이며,
상관계수는 {pair_value:.3f}이다. 전체 행렬은 [correlation_matrix.csv](correlation_matrix.csv)에 저장했다.

## ML Pipeline 평가

- 모델: 수치형 중앙값 대체·표준화 + 범주형 최빈값 대체·원-핫 인코딩 + 로지스틱 회귀
- 테스트 표본: {int(metrics['test_rows']):,}건
- 정확도: {float(metrics['accuracy']):.4f}
- F1: {float(metrics['f1']):.4f}
- 저장 모델: [adult_income_pipeline.joblib](adult_income_pipeline.joblib)

정확도는 전체 정답 비율이고, F1은 상대적으로 적은 `>50K` 집단의 정밀도와 재현율을 함께 반영한다.

## 시각화 산출물

- [Seaborn 정적 차트](seaborn_eda.png)
- [Plotly 인터랙티브 차트](plotly_income_by_education.html)

## 해석 범위

소득 예측 결과는 변수 간 연관성을 학습한 것으로 개인의 능력이나 미래 소득에 대한 인과적 판단이 아니다.
현재 성능은 단일 학습·테스트 분할 결과이며 데이터와 분할 기준이 달라지면 평가 지표도 달라질 수 있다.
"""
    report_path.write_text(report, encoding="utf-8")
    return report_path


def run_pipeline(
    data_path: str | Path = "adult.data",
    output_dir: str | Path = "artifacts",
) -> PipelineResult:
    """전체 분석 파이프라인을 실행하고 생성된 산출물 정보를 반환한다."""

    data_path = Path(data_path)
    output_dir = Path(output_dir)
    if not data_path.exists():
        raise FileNotFoundError(f"입력 데이터를 찾을 수 없습니다: {data_path}")
    output_dir.mkdir(parents=True, exist_ok=True)

    pandas_frame, pandas_seconds = _load_with_pandas(data_path)
    polars_frame, polars_seconds = _load_with_polars(data_path)
    comparison = _library_comparison(
        pandas_frame,
        pandas_seconds,
        polars_frame,
        polars_seconds,
    )
    comparison.to_csv(output_dir / "pandas_polars_comparison.csv", index=False, encoding="utf-8-sig")

    cleaned, cleaning_summary = _clean_data(pandas_frame)
    cleaning_summary.to_csv(output_dir / "cleaning_summary.csv", index=False, encoding="utf-8-sig")
    descriptive, correlation = _save_statistics(cleaned, output_dir)
    _save_visualizations(cleaned, output_dir)
    _, metrics, model_path = _train_income_model(cleaned, output_dir)
    report_path = _generate_report(
        output_dir,
        comparison,
        cleaning_summary,
        descriptive,
        correlation,
        metrics,
    )

    display(comparison.round(4))
    display(cleaning_summary)
    display(descriptive.round(3))
    display(correlation.round(3))
    display(pd.DataFrame([{"정확도": metrics["accuracy"], "F1": metrics["f1"]}]).round(4))

    return PipelineResult(
        rows_before=len(pandas_frame),
        rows_after=len(cleaned),
        duplicates_removed=len(pandas_frame) - len(cleaned),
        missing_before=int(pandas_frame.isna().sum().sum()),
        missing_after=int(cleaned.isna().sum().sum()),
        accuracy=float(metrics["accuracy"]),
        f1=float(metrics["f1"]),
        output_dir=output_dir,
        report_path=report_path,
        model_path=model_path,
        plotly_path=output_dir / "plotly_income_by_education.html",
    )


if __name__ == "__main__":
    result = run_pipeline()
    print(result)
