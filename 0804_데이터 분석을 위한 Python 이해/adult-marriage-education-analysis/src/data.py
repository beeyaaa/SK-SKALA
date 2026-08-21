"""Adult 원본 로딩, 품질 프로파일과 혼인 경험 Target 생성."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import polars as pl

from src.config import (
    COLS,
    EVER_MARRIED_STATUSES,
    EXCLUDED_FEATURES,
    INTEGER_COLUMNS,
    SENSITIVE_AUDIT_FEATURES,
    TARGET,
)


def resolve_raw_path(project_root: Path) -> Path:
    """새 프로젝트 로컬 파일 또는 기존 프로젝트의 동일 원본을 찾는다."""
    candidates = [
        project_root / "data" / "raw" / "adult.data",
        project_root.parent / "adult-marriage-analysis" / "data" / "raw" / "adult.data",
    ]
    for path in candidates:
        if path.exists() and path.stat().st_size > 0:
            return path
    raise FileNotFoundError(
        "adult.data가 없습니다. UCI Adult 원본을 data/raw/adult.data에 저장하세요."
    )


def _clean_pandas(frame: pd.DataFrame) -> pd.DataFrame:
    cleaned = frame.copy()
    for column in cleaned.select_dtypes(include=["object", "string"]).columns:
        values = cleaned[column].astype("string").str.strip()
        cleaned[column] = values.replace({"?": pd.NA, "": pd.NA}).astype(object)
        cleaned[column] = cleaned[column].where(pd.notna(cleaned[column]), np.nan)
    return cleaned


def load_pandas(path: Path) -> pd.DataFrame:
    """Adult 원본을 Pandas로 읽는다."""
    frame = pd.read_csv(path, header=None, names=COLS, skipinitialspace=True)
    return _clean_pandas(frame)


def load_polars(path: Path) -> pl.DataFrame:
    """Adult 원본을 Polars로 읽고 Pandas와 같은 규칙으로 정리한다."""
    frame = pl.read_csv(
        path,
        has_header=False,
        new_columns=COLS,
        schema_overrides={column: pl.String for column in COLS},
    ).filter(pl.any_horizontal(pl.all().is_not_null()))
    string_expressions = []
    for column in COLS:
        value = pl.col(column).str.strip_chars()
        string_expressions.append(
            pl.when(value.is_in(["?", ""])).then(None).otherwise(value).alias(column)
        )
    return frame.with_columns(string_expressions).with_columns(
        pl.col(INTEGER_COLUMNS).cast(pl.Int64)
    )


def compare_loaders(pandas_df: pd.DataFrame, polars_df: pl.DataFrame) -> pd.DataFrame:
    """Pandas와 Polars의 핵심 품질 결과를 비교한다."""
    return pd.DataFrame([
        {
            "항목": "행 수",
            "Pandas": len(pandas_df),
            "Polars": polars_df.height,
            "일치 여부": len(pandas_df) == polars_df.height,
        },
        {
            "항목": "열 수",
            "Pandas": pandas_df.shape[1],
            "Polars": polars_df.width,
            "일치 여부": pandas_df.shape[1] == polars_df.width,
        },
        {
            "항목": "전체 결측치",
            "Pandas": int(pandas_df.isna().sum().sum()),
            "Polars": int(sum(polars_df.null_count().row(0))),
            "일치 여부": int(pandas_df.isna().sum().sum()) == int(sum(polars_df.null_count().row(0))),
        },
        {
            "항목": "완전 중복 행",
            "Pandas": int(pandas_df.duplicated().sum()),
            "Polars": int(polars_df.height - polars_df.unique().height),
            "일치 여부": int(pandas_df.duplicated().sum()) == int(polars_df.height - polars_df.unique().height),
        },
    ])


def add_target(df: pd.DataFrame) -> pd.DataFrame:
    """Never-married=0, 그 외 혼인 상태=1인 혼인 경험 Target을 생성한다."""
    prepared = df.copy()
    prepared[TARGET] = prepared["marital-status"].isin(
        EVER_MARRIED_STATUSES
    ).astype("int8")
    return prepared


def build_column_profile(df: pd.DataFrame) -> pd.DataFrame:
    """전체 컬럼의 타입·결측·고유값·예시 값을 한 표로 만든다."""
    rows = []
    for column in df.columns:
        examples = df[column].dropna().astype(str).unique()[:4].tolist()
        rows.append({
            "컬럼": column,
            "데이터 타입": str(df[column].dtype),
            "결측치 수": int(df[column].isna().sum()),
            "결측률(%)": float(df[column].isna().mean() * 100),
            "고유값 수": int(df[column].nunique(dropna=True)),
            "예시 값": ", ".join(examples),
        })
    return pd.DataFrame(rows)


def build_feature_policy() -> pd.DataFrame:
    """각 컬럼을 분석에서 어떻게 사용할지 명시한다."""
    rows = [
        {"컬럼": TARGET, "역할": "Target", "근거": "Never-married=0, 그 외 혼인 상태=1"},
        {"컬럼": "education-num", "역할": "가설검정 변수", "근거": "두 집단 평균 비교 대상"},
    ]
    rows.extend(
        {"컬럼": column, "역할": "모델 입력 제외", "근거": reason}
        for column, reason in EXCLUDED_FEATURES.items()
    )
    rows.extend(
        {"컬럼": column, "역할": "공정성 점검", "근거": "민감 특성으로 기본 모델과 분리"}
        for column in SENSITIVE_AUDIT_FEATURES
    )
    return pd.DataFrame(rows)
