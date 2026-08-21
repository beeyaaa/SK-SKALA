"""모델 입력 컬럼 정책과 이후 전처리 Pipeline을 담당한다."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, StandardScaler

from src.config import (
    CATEGORICAL_FEATURES,
    LEAKAGE_OR_EXCLUDED_FEATURES,
    NUMERIC_FEATURES,
    OPTIONAL_FEATURES,
    SENSITIVE_AUDIT_FEATURES,
    SKEWED_NUMERIC_FEATURES,
    TARGET,
)


BASE_FEATURES = (
    NUMERIC_FEATURES + SKEWED_NUMERIC_FEATURES + CATEGORICAL_FEATURES
)
EXTENDED_FEATURES = BASE_FEATURES + OPTIONAL_FEATURES


def build_preprocessor(features: list[str]) -> ColumnTransformer:
    """선택한 원본 특성에 맞는 누수 방지 전처리기를 만든다."""
    numeric = [feature for feature in features if feature in NUMERIC_FEATURES]
    skewed = [
        feature for feature in features if feature in SKEWED_NUMERIC_FEATURES
    ]
    categorical = [
        feature
        for feature in features
        if feature in CATEGORICAL_FEATURES + OPTIONAL_FEATURES
    ]

    transformers = []
    if numeric:
        transformers.append(
            (
                "numeric",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="median")),
                        ("scaler", StandardScaler()),
                    ]
                ),
                numeric,
            )
        )
    if skewed:
        transformers.append(
            (
                "skewed_numeric",
                Pipeline(
                    [
                        ("imputer", SimpleImputer(strategy="median")),
                        (
                            "log1p",
                            FunctionTransformer(
                                np.log1p,
                                feature_names_out="one-to-one",
                            ),
                        ),
                        ("scaler", StandardScaler()),
                    ]
                ),
                skewed,
            )
        )
    if categorical:
        transformers.append(
            (
                "categorical",
                Pipeline(
                    [
                        (
                            "imputer",
                            SimpleImputer(
                                strategy="constant",
                                fill_value="Unknown",
                            ),
                        ),
                        (
                            "encoder",
                            OneHotEncoder(handle_unknown="ignore"),
                        ),
                    ]
                ),
                categorical,
            )
        )

    if not transformers:
        raise ValueError("전처리할 허용 특성이 없습니다.")

    return ColumnTransformer(
        transformers=transformers,
        remainder="drop",
        verbose_feature_names_out=False,
    )


def build_feature_policy() -> pd.DataFrame:
    """컬럼별 사용 여부와 근거를 보고서용 표로 반환한다."""
    rows = [
        {
            "column": TARGET,
            "role": "target",
            "reason": "marital-status에서 생성한 혼인 경험 여부",
        },
        {
            "column": "marital-status",
            "role": "exclude_target_source",
            "reason": "타깃 생성에 사용되어 입력 시 정답 누수",
        },
        {
            "column": "relationship",
            "role": "exclude_leakage",
            "reason": "Husband, Wife, Unmarried가 혼인 상태를 직접 암시",
        },
        {
            "column": "fnlwgt",
            "role": "exclude_weight",
            "reason": "개인 특성이 아닌 Census 표본 가중치",
        },
        {
            "column": "education",
            "role": "exclude_duplicate",
            "reason": "education-num과 같은 정보를 중복 표현",
        },
    ]

    rows.extend(
        {
            "column": column,
            "role": "base_feature",
            "reason": "기본 예측 모델 입력",
        }
        for column in BASE_FEATURES
    )
    rows.extend(
        {
            "column": column,
            "role": "optional_feature",
            "reason": "현재 소득 정보의 추가 효과를 확장 모델에서 점검",
        }
        for column in OPTIONAL_FEATURES
    )
    rows.extend(
        {
            "column": column,
            "role": "fairness_audit",
            "reason": "기본 모델에서 제외하고 집단별 성능 점검에 사용",
        }
        for column in SENSITIVE_AUDIT_FEATURES
    )
    return pd.DataFrame(rows)


def select_feature_sets(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.Series]:
    """기본·확장·공정성 데이터와 타깃을 분리한다."""
    required = set(EXTENDED_FEATURES + SENSITIVE_AUDIT_FEATURES + [TARGET])
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"필수 컬럼이 없습니다: {missing}")

    forbidden = set(LEAKAGE_OR_EXCLUDED_FEATURES) & set(BASE_FEATURES)
    if forbidden:
        raise AssertionError(f"기본 특성에 제외 변수가 포함됨: {sorted(forbidden)}")

    return (
        df[BASE_FEATURES].copy(),
        df[EXTENDED_FEATURES].copy(),
        df[SENSITIVE_AUDIT_FEATURES].copy(),
        df[TARGET].copy(),
    )


def build_feature_missingness(df: pd.DataFrame) -> pd.DataFrame:
    """확장 모델 후보 컬럼의 결측치 수와 비율을 계산한다."""
    missing_count = df[EXTENDED_FEATURES].isna().sum()
    return pd.DataFrame(
        {
            "column": EXTENDED_FEATURES,
            "missing_count": [int(missing_count[column]) for column in EXTENDED_FEATURES],
            "missing_rate_pct": [
                float(missing_count[column] / len(df) * 100)
                for column in EXTENDED_FEATURES
            ],
        }
    )


def build_preprocessing_audit(df: pd.DataFrame) -> pd.DataFrame:
    """기본 특성별 전처리 규칙과 대치 전·후 결측치 수를 정리한다."""
    transform_map = {
        **{
            feature: "median imputation → StandardScaler"
            for feature in NUMERIC_FEATURES
        },
        **{
            feature: "median imputation → log1p → StandardScaler"
            for feature in SKEWED_NUMERIC_FEATURES
        },
        **{
            feature: "Unknown imputation → OneHotEncoder"
            for feature in CATEGORICAL_FEATURES
        },
    }
    return pd.DataFrame(
        [
            {
                "feature": feature,
                "missing_before": int(df[feature].isna().sum()),
                "missing_after_imputation": 0,
                "transformation": transform_map[feature],
            }
            for feature in BASE_FEATURES
        ]
    )
