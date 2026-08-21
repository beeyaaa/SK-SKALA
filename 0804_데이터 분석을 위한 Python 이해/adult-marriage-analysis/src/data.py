"""Pandas/Polars 데이터 로딩과 1차 데이터 품질 비교를 담당한다."""

from __future__ import annotations

from pathlib import Path
from urllib.request import urlopen

import numpy as np
import pandas as pd
import polars as pl

from src.config import (
    ADULT_DATA_URL,
    COLS,
    INTEGER_COLUMNS,
    MARRIAGE_MAP,
    RAW_DATA_FILENAME,
    TARGET,
)


def ensure_raw_data(
    raw_dir: Path,
    url: str = ADULT_DATA_URL,
    filename: str = RAW_DATA_FILENAME,
) -> Path:
    """원본 파일이 없을 때만 내려받고 로컬 경로를 반환한다."""
    raw_dir.mkdir(parents=True, exist_ok=True)
    destination = raw_dir / filename

    if destination.exists() and destination.stat().st_size > 0:
        return destination

    try:
        with urlopen(url, timeout=30) as response:
            payload = response.read()
    except Exception as exc:
        raise RuntimeError(
            f"Adult 데이터를 내려받지 못했습니다: {url}"
        ) from exc

    if not payload:
        raise RuntimeError("다운로드한 Adult 데이터가 비어 있습니다.")

    destination.write_bytes(payload)
    return destination


def _clean_pandas_strings(df: pd.DataFrame) -> pd.DataFrame:
    """문자열 공백·물음표 결측·income 마침표를 정리한다."""
    cleaned = df.copy()
    string_columns = cleaned.select_dtypes(include=["object", "string"]).columns

    for column in string_columns:
        values = cleaned[column].astype("string").str.strip()
        if column == "income":
            values = values.str.replace(r"\.$", "", regex=True)
        values = values.replace({"?": pd.NA, "": pd.NA})
        # scikit-learn의 SimpleImputer가 안정적으로 처리하도록 문자열 컬럼은
        # object dtype과 np.nan 결측 표현으로 통일한다.
        cleaned[column] = values.astype(object).where(values.notna(), np.nan)

    return cleaned


def load_with_pandas(path: Path) -> pd.DataFrame:
    """Adult 원본 파일을 Pandas DataFrame으로 읽고 문자열을 정리한다."""
    frame = pd.read_csv(
        path,
        header=None,
        names=COLS,
        skipinitialspace=True,
        na_values=["?", " ?"],
    )
    return _clean_pandas_strings(frame)


def _clean_polars_strings(df: pl.DataFrame) -> pl.DataFrame:
    """Pandas와 동일한 규칙으로 Polars 문자열 컬럼을 정리한다."""
    string_columns = [
        column
        for column, dtype in df.schema.items()
        if dtype == pl.String
    ]

    expressions: list[pl.Expr] = []
    for column in string_columns:
        value = pl.col(column).str.strip_chars()
        if column == "income":
            value = value.str.replace(r"\.$", "")
        expressions.append(
            pl.when(value.is_in(["?", ""]))
            .then(None)
            .otherwise(value)
            .alias(column)
        )

    return df.with_columns(expressions)


def load_with_polars(path: Path) -> pl.DataFrame:
    """Adult 원본 파일을 Polars DataFrame으로 읽고 문자열을 정리한다."""
    frame = pl.read_csv(
        path,
        has_header=False,
        new_columns=COLS,
        schema_overrides={column: pl.String for column in COLS},
        infer_schema_length=10_000,
    )
    cleaned = _clean_polars_strings(frame)

    # UCI 원본 끝에는 빈 줄이 하나 더 있으므로 완전 빈 행을 제거한다.
    cleaned = cleaned.filter(
        pl.any_horizontal(pl.all().is_not_null())
    )

    # Polars에는 Pandas의 skipinitialspace에 해당하는 옵션이 없어 문자열을
    # 먼저 정리한 뒤 숫자 컬럼을 명시적으로 변환한다.
    return cleaned.with_columns(
        pl.col(INTEGER_COLUMNS).cast(pl.Int64)
    )


def compare_frames(
    pandas_df: pd.DataFrame,
    polars_df: pl.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """프레임 전체와 컬럼별 품질 비교표를 반환한다."""
    pandas_nulls = pandas_df.isna().sum()
    polars_nulls = polars_df.null_count().row(0, named=True)

    summary = pd.DataFrame(
        [
            {
                "pandas_rows": len(pandas_df),
                "polars_rows": polars_df.height,
                "pandas_columns": pandas_df.shape[1],
                "polars_columns": polars_df.width,
                "column_order_equal": list(pandas_df.columns)
                == polars_df.columns,
                "total_nulls_equal": int(pandas_nulls.sum())
                == sum(polars_nulls.values()),
                "pandas_duplicate_rows": int(pandas_df.duplicated().sum()),
                "polars_duplicate_rows": int(
                    polars_df.height - polars_df.unique().height
                ),
            }
        ]
    )

    details: list[dict[str, object]] = []
    for column in COLS:
        pandas_unique = int(pandas_df[column].nunique(dropna=True))
        polars_unique = int(polars_df[column].drop_nulls().n_unique())
        details.append(
            {
                "column": column,
                "pandas_dtype": str(pandas_df[column].dtype),
                "polars_dtype": str(polars_df.schema[column]),
                "pandas_nulls": int(pandas_nulls[column]),
                "polars_nulls": int(polars_nulls[column]),
                "null_count_equal": int(pandas_nulls[column])
                == int(polars_nulls[column]),
                "pandas_unique": pandas_unique,
                "polars_unique": polars_unique,
                "unique_count_equal": pandas_unique == polars_unique,
            }
        )

    return summary, pd.DataFrame(details)


def add_target_pandas(df: pd.DataFrame) -> pd.DataFrame:
    """Pandas 데이터에 혼인 경험 타깃을 추가하고 허용값을 검증한다."""
    unknown_mask = df["marital-status"].isna() | ~df["marital-status"].isin(
        MARRIAGE_MAP
    )
    if unknown_mask.any():
        unknown_values = df.loc[unknown_mask, "marital-status"].unique().tolist()
        raise ValueError(f"정의되지 않은 marital-status 값: {unknown_values}")

    prepared = df.copy()
    prepared[TARGET] = prepared["marital-status"].map(MARRIAGE_MAP).astype("int8")
    return prepared


def add_target_polars(df: pl.DataFrame) -> pl.DataFrame:
    """Polars 데이터에 혼인 경험 타깃을 추가하고 허용값을 검증한다."""
    status = pl.col("marital-status")
    unknown = df.filter(status.is_null() | ~status.is_in(list(MARRIAGE_MAP)))
    if unknown.height:
        unknown_values = unknown["marital-status"].unique().to_list()
        raise ValueError(f"정의되지 않은 marital-status 값: {unknown_values}")

    return df.with_columns(
        status.replace_strict(MARRIAGE_MAP, return_dtype=pl.Int8).alias(TARGET)
    )


def compare_target_distribution(
    pandas_df: pd.DataFrame,
    polars_df: pl.DataFrame,
) -> pd.DataFrame:
    """Pandas와 Polars의 타깃별 건수를 나란히 비교한다."""
    pandas_counts = pandas_df[TARGET].value_counts().sort_index()
    polars_counts = {
        row[TARGET]: row["count"]
        for row in (
            polars_df.group_by(TARGET)
            .len(name="count")
            .sort(TARGET)
            .iter_rows(named=True)
        )
    }

    rows: list[dict[str, object]] = []
    for target_value in (0, 1):
        pandas_count = int(pandas_counts.get(target_value, 0))
        polars_count = int(polars_counts.get(target_value, 0))
        rows.append(
            {
                TARGET: target_value,
                "label": "혼인 경험 없음" if target_value == 0 else "혼인 경험 있음",
                "pandas_count": pandas_count,
                "polars_count": polars_count,
                "count_equal": pandas_count == polars_count,
                "percentage": pandas_count / len(pandas_df) * 100,
            }
        )

    return pd.DataFrame(rows)


def run_data_loading_stage(project_root: Path) -> tuple[pd.DataFrame, pl.DataFrame]:
    """1단계 로딩·비교를 실행하고 결과표를 reports/tables에 저장한다."""
    raw_path = ensure_raw_data(project_root / "data" / "raw")
    pandas_df = load_with_pandas(raw_path)
    polars_df = load_with_polars(raw_path)
    summary, details = compare_frames(pandas_df, polars_df)

    table_dir = project_root / "reports" / "tables"
    table_dir.mkdir(parents=True, exist_ok=True)
    summary.to_csv(table_dir / "pandas_polars_summary.csv", index=False)
    details.to_csv(table_dir / "pandas_polars_columns.csv", index=False)

    print("\n[1단계] Pandas / Polars 로딩 비교")
    print(summary.to_string(index=False))
    print("\n컬럼별 비교 결과:")
    print(details.to_string(index=False))
    return pandas_df, polars_df


def run_target_stage(
    project_root: Path,
    pandas_df: pd.DataFrame,
    polars_df: pl.DataFrame,
) -> tuple[pd.DataFrame, pl.DataFrame]:
    """2단계 타깃 생성을 실행하고 분포 비교표를 저장한다."""
    pandas_prepared = add_target_pandas(pandas_df)
    polars_prepared = add_target_polars(polars_df)
    target_distribution = compare_target_distribution(
        pandas_prepared, polars_prepared
    )

    if not target_distribution["count_equal"].all():
        raise AssertionError("Pandas와 Polars의 타깃 분포가 일치하지 않습니다.")

    table_dir = project_root / "reports" / "tables"
    table_dir.mkdir(parents=True, exist_ok=True)
    target_distribution.to_csv(
        table_dir / "target_distribution.csv", index=False
    )

    print("\n[2단계] 혼인 경험 타깃 생성")
    print(target_distribution.to_string(index=False, float_format="%.2f"))
    return pandas_prepared, polars_prepared
