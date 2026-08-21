"""Question-driven EDA에 사용하는 데이터 품질·분포 요약 함수."""

from __future__ import annotations

import pandas as pd

from src.config import (
    CATEGORICAL_FEATURES,
    NUMERIC_FEATURES,
    SKEWED_NUMERIC_FEATURES,
    TARGET,
)


EDA_NUMERIC_FEATURES = NUMERIC_FEATURES + SKEWED_NUMERIC_FEATURES
EDA_CATEGORICAL_FEATURES = CATEGORICAL_FEATURES + ["income"]


def build_missingness_summary(df: pd.DataFrame) -> pd.DataFrame:
    """결측치가 있는 컬럼을 결측 비율 내림차순으로 정리한다."""
    summary = pd.DataFrame(
        {
            "column": df.columns,
            "missing_count": df.isna().sum().to_numpy(),
            "missing_rate_pct": (df.isna().mean() * 100).to_numpy(),
        }
    )
    return summary.query("missing_count > 0").sort_values(
        "missing_count", ascending=False
    ).reset_index(drop=True)


def build_validity_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Adult 데이터의 주요 숫자형 컬럼에 대한 논리적 범위를 점검한다."""
    rules = [
        ("age", "17 <= age <= 90", df["age"].between(17, 90)),
        (
            "education-num",
            "1 <= education-num <= 16",
            df["education-num"].between(1, 16),
        ),
        (
            "hours-per-week",
            "1 <= hours-per-week <= 99",
            df["hours-per-week"].between(1, 99),
        ),
        ("capital-gain", "capital-gain >= 0", df["capital-gain"].ge(0)),
        ("capital-loss", "capital-loss >= 0", df["capital-loss"].ge(0)),
    ]
    return pd.DataFrame(
        [
            {
                "column": column,
                "rule": rule,
                "invalid_count": int((~valid.fillna(False)).sum()),
                "status": "PASS" if valid.fillna(False).all() else "CHECK",
            }
            for column, rule, valid in rules
        ]
    )


def build_numeric_distribution_summary(df: pd.DataFrame) -> pd.DataFrame:
    """모델 숫자형 후보의 중심·산포·왜도를 요약한다."""
    rows = []
    for feature in EDA_NUMERIC_FEATURES:
        values = df[feature].dropna()
        rows.append(
            {
                "feature": feature,
                "count": int(values.size),
                "mean": float(values.mean()),
                "median": float(values.median()),
                "std": float(values.std()),
                "min": float(values.min()),
                "max": float(values.max()),
                "skewness": float(values.skew()),
                "zero_rate_pct": float(values.eq(0).mean() * 100),
            }
        )
    return pd.DataFrame(rows)


def build_iqr_outlier_summary(df: pd.DataFrame) -> pd.DataFrame:
    """1.5×IQR 규칙으로 잠재적 이상치를 표시하되 삭제 여부는 결정하지 않는다."""
    rows = []
    for feature in EDA_NUMERIC_FEATURES:
        values = df[feature].dropna()
        q1, q3 = values.quantile([0.25, 0.75])
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        outlier_mask = (values < lower) | (values > upper)
        rows.append(
            {
                "feature": feature,
                "q1": float(q1),
                "q3": float(q3),
                "iqr": float(iqr),
                "lower_fence": float(lower),
                "upper_fence": float(upper),
                "outlier_count": int(outlier_mask.sum()),
                "outlier_rate_pct": float(outlier_mask.mean() * 100),
            }
        )
    return pd.DataFrame(rows).sort_values(
        "outlier_rate_pct", ascending=False
    ).reset_index(drop=True)


def build_categorical_summary(df: pd.DataFrame) -> pd.DataFrame:
    """범주형 후보의 cardinality, 결측치와 최빈 범주를 요약한다."""
    rows = []
    for feature in EDA_CATEGORICAL_FEATURES:
        values = df[feature].astype("string").fillna("Missing")
        counts = values.value_counts(dropna=False)
        rows.append(
            {
                "feature": feature,
                "cardinality_including_missing": int(counts.size),
                "missing_count": int(df[feature].isna().sum()),
                "top_category": str(counts.index[0]),
                "top_count": int(counts.iloc[0]),
                "top_share_pct": float(counts.iloc[0] / len(df) * 100),
            }
        )
    return pd.DataFrame(rows)


def build_numeric_correlation(df: pd.DataFrame) -> pd.DataFrame:
    """숫자형 후보 간 Pearson 상관행렬을 반환한다."""
    return df[EDA_NUMERIC_FEATURES].corr(method="pearson")


def build_numeric_target_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Target 그룹별 숫자형 후보의 중심과 산포를 long-form으로 요약한다."""
    rows = []
    for feature in EDA_NUMERIC_FEATURES:
        for target_value, values in df.groupby(TARGET)[feature]:
            clean = values.dropna()
            rows.append(
                {
                    "feature": feature,
                    TARGET: int(target_value),
                    "sample_size": int(clean.size),
                    "mean": float(clean.mean()),
                    "median": float(clean.median()),
                    "std": float(clean.std()),
                    "q1": float(clean.quantile(0.25)),
                    "q3": float(clean.quantile(0.75)),
                }
            )
    return pd.DataFrame(rows)


def build_categorical_target_rates(df: pd.DataFrame) -> pd.DataFrame:
    """범주형 후보의 각 범주별 Target=1 비율과 표본 수를 계산한다."""
    rows = []
    for feature in EDA_CATEGORICAL_FEATURES:
        values = df[feature].astype("string").fillna("Missing")
        grouped = (
            df.assign(_category=values)
            .groupby("_category", observed=True)[TARGET]
            .agg(sample_size="size", ever_married_count="sum", target_rate="mean")
            .reset_index()
        )
        for _, row in grouped.iterrows():
            rows.append(
                {
                    "feature": feature,
                    "category": str(row["_category"]),
                    "sample_size": int(row["sample_size"]),
                    "ever_married_count": int(row["ever_married_count"]),
                    "target_rate_pct": float(row["target_rate"] * 100),
                }
            )
    return pd.DataFrame(rows)
