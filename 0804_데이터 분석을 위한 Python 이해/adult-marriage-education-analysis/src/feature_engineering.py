"""Train/Test 누수를 막는 Adult Census Feature Engineering 도구."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, StandardScaler

from src.config import (
    ENGINEERED_CATEGORICAL_FEATURES,
    ENGINEERED_NUMERIC_FEATURES,
    NUMERIC_MODEL_FEATURES,
)


def build_feature_audit(train_df: pd.DataFrame) -> pd.DataFrame:
    """Train 데이터의 타입·결측·고유값·왜도·0 비율·IQR 이상치를 요약한다."""
    rows: list[dict[str, object]] = []
    for column in train_df.columns:
        series = train_df[column]
        row: dict[str, object] = {
            "컬럼": column,
            "타입": str(series.dtype),
            "결측치 수": int(series.isna().sum()),
            "결측률(%)": float(series.isna().mean() * 100),
            "고유값 수": int(series.nunique(dropna=True)),
            "왜도": np.nan,
            "0 비율(%)": np.nan,
            "IQR 이상치 수": np.nan,
            "IQR 이상치율(%)": np.nan,
        }
        if pd.api.types.is_numeric_dtype(series):
            clean = series.dropna()
            q1, q3 = clean.quantile([0.25, 0.75])
            iqr = q3 - q1
            if iqr == 0:
                outlier_count = np.nan
                outlier_rate = np.nan
            else:
                outlier_count = int(((clean < q1 - 1.5 * iqr) | (clean > q3 + 1.5 * iqr)).sum())
                outlier_rate = float(outlier_count / len(clean) * 100)
            row.update({
                "왜도": float(clean.skew()),
                "0 비율(%)": float(clean.eq(0).mean() * 100),
                "IQR 이상치 수": outlier_count,
                "IQR 이상치율(%)": outlier_rate,
            })
        rows.append(row)
    return pd.DataFrame(rows)


def engineer_features(df: pd.DataFrame) -> pd.DataFrame:
    """업무 질문과 고정 기준만 사용해 누수 없는 파생변수를 만든다."""
    engineered = df.copy()
    engineered["capital-gain-log"] = np.log1p(engineered["capital-gain"])
    engineered["capital-loss-log"] = np.log1p(engineered["capital-loss"])
    capital_net = engineered["capital-gain"] - engineered["capital-loss"]
    engineered["capital-net-signed-log"] = np.sign(capital_net) * np.log1p(np.abs(capital_net))
    engineered["age-group"] = pd.cut(
        engineered["age"],
        bins=[16, 29, 39, 49, 59, 100],
        labels=["20대 이하", "30대", "40대", "50대", "60대 이상"],
        include_lowest=True,
    ).astype(object)
    engineered["hours-group"] = pd.cut(
        engineered["hours-per-week"],
        bins=[0, 34, 40, 50, 100],
        labels=["주 34시간 이하", "주 35~40시간", "주 41~50시간", "주 51시간 이상"],
        include_lowest=True,
    ).astype(object)
    return engineered


def build_preprocessing_pipeline() -> Pipeline:
    """파생변수→결측 대치→인코딩/스케일링을 하나의 Pipeline으로 묶는다."""
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
                drop="first",
                sparse_output=False,
            ),
        ),
    ])
    preprocessor = ColumnTransformer([
        ("numeric", numeric_pipeline, ENGINEERED_NUMERIC_FEATURES),
        ("categorical", categorical_pipeline, ENGINEERED_CATEGORICAL_FEATURES),
    ], verbose_feature_names_out=True)
    return Pipeline([
        ("feature_creation", FunctionTransformer(engineer_features, validate=False)),
        ("preprocessor", preprocessor),
    ])


def build_feature_decisions(train_df: pd.DataFrame) -> pd.DataFrame:
    """PDF 체크리스트를 Adult 데이터에 적용한 결정과 근거를 표로 남긴다."""
    audit = build_feature_audit(train_df).set_index("컬럼")
    target_rate = train_df["ever_married"].mean()
    return pd.DataFrame([
        {
            "점검 항목": "완전 중복 행",
            "관찰": f"{train_df.duplicated().sum():,}행",
            "결정": "유지",
            "근거": "개인 식별자가 없어 동일한 특성의 서로 다른 사람일 수 있음",
        },
        {
            "점검 항목": "범주형 결측치",
            "관찰": f"workclass {audit.loc['workclass', '결측률(%)']:.2f}%, occupation {audit.loc['occupation', '결측률(%)']:.2f}%",
            "결정": "최빈값 대치",
            "근거": "Train에서만 최빈값을 학습하고 Test에는 transform만 적용",
        },
        {
            "점검 항목": "수치형 이상치",
            "관찰": "IQR 기준 후보가 존재",
            "결정": "일괄 삭제 안 함",
            "근거": "Adult의 나이·근무시간·자본소득 극단값은 가능한 실제 관측값",
        },
        {
            "점검 항목": "자본소득 분포",
            "관찰": f"capital-gain 0 비율 {audit.loc['capital-gain', '0 비율(%)']:.1f}%",
            "결정": "log1p 파생값 사용",
            "근거": "0을 보존하면서 긴 오른쪽 꼬리를 완화",
        },
        {
            "점검 항목": "범주형 인코딩",
            "관찰": "명목형 범주",
            "결정": "One-Hot Encoding",
            "근거": "Label Encoding의 임의 순서 정보를 만들지 않음",
        },
        {
            "점검 항목": "희소 범주",
            "관찰": "occupation·workclass 등에 저빈도 범주 존재",
            "결정": "1% 미만 통합",
            "근거": "OneHotEncoder(min_frequency=0.01)로 Train 기준 통합",
        },
        {
            "점검 항목": "수치형 스케일",
            "관찰": "단위와 범위가 서로 다름",
            "결정": "StandardScaler",
            "근거": "로지스틱 회귀 계수·정규화가 스케일에 좌우되지 않도록 함",
        },
        {
            "점검 항목": "Target 불균형",
            "관찰": f"미혼 외 {target_rate:.1%}, 미혼 {1-target_rate:.1%}",
            "결정": "재표본화 안 함",
            "근거": "두 집단이 충분히 균형적이며 불필요한 합성·삭제를 피함",
        },
    ])


def transformed_feature_names(fitted_pipeline: Pipeline) -> list[str]:
    """적합된 전처리기의 출력 컬럼명을 반환한다."""
    return fitted_pipeline.named_steps["preprocessor"].get_feature_names_out().tolist()


def raw_numeric_columns() -> list[str]:
    """스케일링 비교에 사용할 원본 숫자형 모델 후보를 반환한다."""
    return NUMERIC_MODEL_FEATURES.copy()
