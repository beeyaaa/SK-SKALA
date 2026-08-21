"""Train 분할, 다중공선성과 교육 수준 가설검정 함수."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import pointbiserialr, ttest_ind
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from statsmodels.stats.outliers_influence import variance_inflation_factor

from src.config import HYPOTHESIS_FEATURE, NUMERIC_MODEL_FEATURES, TARGET


def split_data(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Target 비율을 유지해 Train/Test를 80:20으로 나눈다."""
    train, test = train_test_split(
        df, test_size=0.2, stratify=df[TARGET], random_state=42
    )
    return train.sort_index(), test.sort_index()


def build_group_statistics(train_df: pd.DataFrame) -> pd.DataFrame:
    """미혼/미혼 외 집단별 education-num 기술통계를 계산한다."""
    return (
        train_df.groupby(TARGET)[HYPOTHESIS_FEATURE]
        .agg(["count", "mean", "std", "var", "median", "min", "max"])
        .reset_index()
    )


def calculate_vif(train_df: pd.DataFrame) -> pd.DataFrame:
    """숫자형 모델 후보의 VIF를 계산한다."""
    values = train_df[NUMERIC_MODEL_FEATURES].dropna()
    scaled = StandardScaler().fit_transform(values)
    return pd.DataFrame({
        "변수": NUMERIC_MODEL_FEATURES,
        "VIF": [
            float(variance_inflation_factor(scaled, index))
            for index in range(len(NUMERIC_MODEL_FEATURES))
        ],
    }).sort_values("VIF", ascending=False).reset_index(drop=True)


def run_hypothesis_test(train_df: pd.DataFrame) -> pd.DataFrame:
    """Welch t-test, Point-biserial r와 Cohen's d를 계산한다."""
    ever_married = train_df.loc[train_df[TARGET] == 1, HYPOTHESIS_FEATURE].dropna()
    never_married = train_df.loc[train_df[TARGET] == 0, HYPOTHESIS_FEATURE].dropna()
    test = ttest_ind(ever_married, never_married, equal_var=False)
    correlation = pointbiserialr(train_df[TARGET], train_df[HYPOTHESIS_FEATURE])
    pooled_variance = (
        (len(ever_married) - 1) * ever_married.var(ddof=1)
        + (len(never_married) - 1) * never_married.var(ddof=1)
    ) / (len(ever_married) + len(never_married) - 2)
    cohens_d = (ever_married.mean() - never_married.mean()) / np.sqrt(pooled_variance)
    return pd.DataFrame([{
        "미혼 외 집단 평균": ever_married.mean(),
        "미혼 집단 평균": never_married.mean(),
        "평균 차이": ever_married.mean() - never_married.mean(),
        "Welch t 통계량": test.statistic,
        "p-value": test.pvalue,
        "Point-biserial r": correlation.statistic,
        "Cohen's d": cohens_d,
        "판정": "H₀ 기각" if test.pvalue < 0.05 else "H₀ 기각 실패",
    }])
