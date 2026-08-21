"""Train/test 분할과 EDA·통계검정·Mutual Information 분석."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import chi2_contingency, pointbiserialr, ttest_ind
from sklearn.feature_selection import mutual_info_classif
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OrdinalEncoder
from statsmodels.stats.multitest import multipletests

from src.config import CATEGORICAL_FEATURES, OPTIONAL_FEATURES, TARGET
from src.features import BASE_FEATURES, EXTENDED_FEATURES


NUMERIC_ANALYSIS_FEATURES = [
    column for column in EXTENDED_FEATURES
    if column not in CATEGORICAL_FEATURES + OPTIONAL_FEATURES
]
CATEGORICAL_ANALYSIS_FEATURES = CATEGORICAL_FEATURES + OPTIONAL_FEATURES


def split_prepared_data(
    df: pd.DataFrame,
    test_size: float = 0.2,
    random_state: int = 42,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """타깃 비율을 유지하면서 학습·테스트 행을 분리한다."""
    train_df, test_df = train_test_split(
        df,
        test_size=test_size,
        stratify=df[TARGET],
        random_state=random_state,
    )
    return train_df.sort_index(), test_df.sort_index()


def build_split_summary(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
) -> pd.DataFrame:
    """분할별 행 수와 타깃 비율을 반환한다."""
    rows: list[dict[str, object]] = []
    for split_name, frame in (("train", train_df), ("test", test_df)):
        for target_value in (0, 1):
            count = int((frame[TARGET] == target_value).sum())
            rows.append(
                {
                    "split": split_name,
                    TARGET: target_value,
                    "count": count,
                    "percentage": count / len(frame) * 100,
                }
            )
    return pd.DataFrame(rows)


def build_descriptive_statistics(train_df: pd.DataFrame) -> pd.DataFrame:
    """숫자형 특성의 타깃 집단별 기술통계를 계산한다."""
    result = (
        train_df.groupby(TARGET)[NUMERIC_ANALYSIS_FEATURES]
        .agg(["count", "mean", "std", "var", "median", "min", "max"])
        .stack(level=0, future_stack=True)
        .reset_index()
        .rename(columns={"level_1": "feature"})
    )
    ordered = [
        TARGET,
        "feature",
        "count",
        "mean",
        "std",
        "var",
        "median",
        "min",
        "max",
    ]
    return result[ordered]


def _cohens_d(group_1: pd.Series, group_0: pd.Series) -> float:
    """두 독립집단의 pooled-standard-deviation Cohen's d를 계산한다."""
    x1 = group_1.dropna().to_numpy(dtype=float)
    x0 = group_0.dropna().to_numpy(dtype=float)
    pooled_variance = (
        ((len(x1) - 1) * np.var(x1, ddof=1))
        + ((len(x0) - 1) * np.var(x0, ddof=1))
    ) / (len(x1) + len(x0) - 2)
    if pooled_variance <= 0:
        return 0.0
    return float((np.mean(x1) - np.mean(x0)) / np.sqrt(pooled_variance))


def analyze_numeric_associations(train_df: pd.DataFrame) -> pd.DataFrame:
    """Point-biserial 상관과 Welch t-test, 효과크기를 계산한다."""
    rows: list[dict[str, object]] = []
    for feature in NUMERIC_ANALYSIS_FEATURES:
        clean = train_df[[feature, TARGET]].dropna()
        group_1 = clean.loc[clean[TARGET] == 1, feature]
        group_0 = clean.loc[clean[TARGET] == 0, feature]
        correlation = pointbiserialr(clean[TARGET], clean[feature])
        welch_test = ttest_ind(group_1, group_0, equal_var=False)
        rows.append(
            {
                "feature": feature,
                "point_biserial_r": float(correlation.statistic),
                "correlation_p_value": float(correlation.pvalue),
                "mean_ever_married_1": float(group_1.mean()),
                "mean_ever_married_0": float(group_0.mean()),
                "mean_difference": float(group_1.mean() - group_0.mean()),
                "welch_t_statistic": float(welch_test.statistic),
                "welch_p_value": float(welch_test.pvalue),
                "cohens_d": _cohens_d(group_1, group_0),
            }
        )

    result = pd.DataFrame(rows)
    result["welch_p_holm"] = multipletests(
        result["welch_p_value"], method="holm"
    )[1]
    return result.sort_values(
        "point_biserial_r", key=lambda values: values.abs(), ascending=False
    ).reset_index(drop=True)


def _bias_corrected_cramers_v(table: pd.DataFrame, chi2: float) -> float:
    """작은 표본 편향을 보정한 Cramér's V를 계산한다."""
    n = table.to_numpy().sum()
    rows, columns = table.shape
    if n <= 1:
        return 0.0
    phi2 = chi2 / n
    phi2_corrected = max(
        0.0, phi2 - ((columns - 1) * (rows - 1)) / (n - 1)
    )
    rows_corrected = rows - ((rows - 1) ** 2) / (n - 1)
    columns_corrected = columns - ((columns - 1) ** 2) / (n - 1)
    denominator = min(columns_corrected - 1, rows_corrected - 1)
    return float(np.sqrt(phi2_corrected / denominator)) if denominator > 0 else 0.0


def analyze_categorical_associations(train_df: pd.DataFrame) -> pd.DataFrame:
    """범주형 특성별 chi-square와 Cramér's V를 계산한다."""
    rows: list[dict[str, object]] = []
    for feature in CATEGORICAL_ANALYSIS_FEATURES:
        values = train_df[feature].astype("string").fillna("Unknown")
        table = pd.crosstab(values, train_df[TARGET])
        chi2, p_value, degrees_of_freedom, _ = chi2_contingency(table)
        rows.append(
            {
                "feature": feature,
                "categories": table.shape[0],
                "chi2": float(chi2),
                "degrees_of_freedom": int(degrees_of_freedom),
                "p_value": float(p_value),
                "cramers_v": _bias_corrected_cramers_v(table, chi2),
            }
        )

    result = pd.DataFrame(rows)
    result["p_holm"] = multipletests(result["p_value"], method="holm")[1]
    return result.sort_values("cramers_v", ascending=False).reset_index(drop=True)


def calculate_mutual_information(
    train_df: pd.DataFrame,
    random_state: int = 42,
) -> pd.DataFrame:
    """훈련 데이터에서만 확장 후보 특성의 Mutual Information을 계산한다."""
    encoded = train_df[EXTENDED_FEATURES].copy()

    for feature in NUMERIC_ANALYSIS_FEATURES:
        encoded[feature] = encoded[feature].fillna(encoded[feature].median())

    encoder = OrdinalEncoder(
        handle_unknown="use_encoded_value",
        unknown_value=-1,
    )
    encoded[CATEGORICAL_ANALYSIS_FEATURES] = encoder.fit_transform(
        encoded[CATEGORICAL_ANALYSIS_FEATURES]
        .astype("string")
        .fillna("Unknown")
    )
    discrete_mask = [
        feature in CATEGORICAL_ANALYSIS_FEATURES
        for feature in encoded.columns
    ]
    scores = mutual_info_classif(
        encoded,
        train_df[TARGET],
        discrete_features=discrete_mask,
        random_state=random_state,
    )
    return (
        pd.DataFrame({"feature": encoded.columns, "mutual_information": scores})
        .sort_values("mutual_information", ascending=False)
        .reset_index(drop=True)
    )


def run_statistics_stage(
    project_root,
    prepared_df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """3단계 분할·통계분석을 실행하고 결과표를 저장한다."""
    train_df, test_df = split_prepared_data(prepared_df)
    outputs = {
        "split_summary": build_split_summary(train_df, test_df),
        "descriptive_statistics": build_descriptive_statistics(train_df),
        "numeric_associations": analyze_numeric_associations(train_df),
        "categorical_associations": analyze_categorical_associations(train_df),
        "mutual_information": calculate_mutual_information(train_df),
    }

    table_dir = project_root / "reports" / "tables"
    table_dir.mkdir(parents=True, exist_ok=True)
    for name, table in outputs.items():
        table.to_csv(table_dir / f"{name}.csv", index=False)

    print("\n[3단계] Train / Test 분할")
    print(outputs["split_summary"].to_string(index=False, float_format="%.2f"))
    print("\n숫자형 관련성 분석:")
    print(outputs["numeric_associations"].to_string(index=False, float_format="%.4f"))
    print("\n범주형 관련성 분석:")
    print(outputs["categorical_associations"].to_string(index=False, float_format="%.4f"))
    print("\nMutual Information:")
    print(outputs["mutual_information"].to_string(index=False, float_format="%.4f"))
    return train_df, test_df

