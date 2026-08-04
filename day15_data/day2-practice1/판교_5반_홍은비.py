"""
[실습 3] Pandas EDA · Polars Lazy · DuckDB SQL 비교

# 작성자   : 홍은비
# 작성일자 : 2026-08-04

# 코드 설명
- sales_100k.csv의 기본 EDA와 amount 컬럼 IQR 이상치 제거를 수행한다.
- Pandas named aggregation, Polars Lazy API, DuckDB SQL로 동일한
  region·category별 total·mean·count를 계산한다.
- 세 도구가 CSV 읽기부터 집계 완료까지 수행하도록 하여 동일한
  조건에서 timeit 실행 시간을 비교한다.

# 변경 내역
- 중복 코드를 함수로 분리하고, 필수 컬럼·파일·라이브러리를 검증한다.
- 세 도구의 집계 대상을 amount IQR 정상 범위와 필수 그룹 키 비결측 행으로 통일한다.
"""

from __future__ import annotations

import timeit
from pathlib import Path
from typing import Any

try:
    import duckdb
    import pandas as pd
    import polars as pl
except ImportError as exc:
    raise SystemExit(
        f"필수 패키지가 없습니다: {exc.name}\n"
        "설치: python -m pip install -r requirements.txt"
    ) from exc


CSV_PATH = Path(__file__).resolve().with_name("sales_100k.csv")
GROUP_KEYS = ["region", "category"]
REQUIRED_COLUMNS = {*GROUP_KEYS, "amount"}
BENCHMARK_NUMBER = 3  # 세 도구 모두 동일한 반복 횟수를 사용한다.


def validate_input(csv_path: Path) -> None:
    """CSV 파일과 집계에 필요한 컬럼이 존재하는지 먼저 확인한다."""
    if not csv_path.is_file():
        raise FileNotFoundError(f"CSV 파일을 찾을 수 없습니다: {csv_path}")

    columns = set(pd.read_csv(csv_path, nrows=0, encoding="utf-8-sig").columns)
    missing = REQUIRED_COLUMNS - columns
    if missing:
        raise ValueError(f"필수 컬럼이 누락됐습니다: {sorted(missing)}")


def load_and_explore(csv_path: Path) -> pd.DataFrame:
    """Pandas로 CSV를 로드하고 info, 결측치, 기술통계를 출력한다."""
    df = pd.read_csv(csv_path, encoding="utf-8-sig")

    print("\n=== 1) Pandas 기본 EDA: df.info() ===")
    df.info()
    print("\n=== 컬럼별 결측치: df.isnull().sum() ===")
    print(df.isnull().sum())
    print("\n=== 수치형 컬럼 기술통계 ===")
    print(df.describe())
    return df


def calculate_iqr_bounds(df: pd.DataFrame) -> tuple[float, float]:
    """amount의 Q1, Q3로 [Q1-1.5*IQR, Q3+1.5*IQR] 정상 범위를 계산한다."""
    if not pd.api.types.is_numeric_dtype(df["amount"]):
        raise TypeError("amount 컬럼은 수치형이어야 합니다.")

    q1 = float(df["amount"].quantile(0.25))
    q3 = float(df["amount"].quantile(0.75))
    iqr = q3 - q1
    lower = q1 - 1.5 * iqr
    upper = q3 + 1.5 * iqr
    print(
        f"\nIQR 계산: Q1={q1:,.2f}, Q3={q3:,.2f}, IQR={iqr:,.2f}\n"
        f"정상 범위: {lower:,.2f} <= amount <= {upper:,.2f}"
    )
    return lower, upper


def remove_outliers(
    df: pd.DataFrame, lower: float, upper: float
) -> pd.DataFrame:
    """Pandas between(하한, 상한)으로 amount IQR 이상치를 제거한다."""
    before = len(df)
    cleaned = df[df["amount"].between(lower, upper, inclusive="both")].copy()
    after = len(cleaned)
    print(f"\n이상치 제거 전 행 수: {before:,}")
    print(f"이상치 제거 후 행 수: {after:,}")
    print(f"제거된 행 수: {before - after:,}")
    return cleaned


def pandas_named_aggregation(df: pd.DataFrame) -> pd.DataFrame:
    """Pandas named aggregation으로 region·category별 매출을 집계한다."""
    return (
        df.dropna(subset=GROUP_KEYS)
        .groupby(GROUP_KEYS, as_index=False)
        .agg(
            total=("amount", "sum"),
            mean=("amount", "mean"),
            count=("amount", "count"),
        )
        .sort_values(
            ["total", "region", "category"],
            ascending=[False, True, True],
            ignore_index=True,
        )
    )


def polars_lazy_aggregation(
    csv_path: Path, lower: float, upper: float
) -> pl.DataFrame:
    """scan_csv → filter → group_by → agg → sort → collect Lazy 체인을 수행한다."""
    return (
        pl.scan_csv(csv_path)
        .filter(
            pl.col("amount").is_between(lower, upper, closed="both")
            & pl.col("region").is_not_null()
            & pl.col("category").is_not_null()
        )
        .group_by(GROUP_KEYS)
        .agg(
            pl.col("amount").sum().alias("total"),
            pl.col("amount").mean().alias("mean"),
            pl.col("amount").count().alias("count"),
        )
        .sort(
            ["total", "region", "category"],
            descending=[True, False, False],
        )
        .collect()
    )


def duckdb_sql_aggregation(
    csv_path: Path, lower: float, upper: float
) -> pd.DataFrame:
    """DuckDB SQL GROUP BY로 동일한 집계를 실행하고 Pandas DataFrame으로 반환한다."""
    sql = """
        SELECT
            region,
            category,
            SUM(amount) AS total,
            AVG(amount) AS mean,
            COUNT(amount) AS count
        FROM read_csv_auto(?, header = true)
        WHERE amount BETWEEN ? AND ?
          AND region IS NOT NULL
          AND category IS NOT NULL
        GROUP BY region, category
        ORDER BY total DESC, region ASC, category ASC
    """
    with duckdb.connect() as connection:
        return connection.execute(sql, [str(csv_path), lower, upper]).df()


def benchmark_tools(
    csv_path: Path, lower: float, upper: float, number: int
) -> pd.DataFrame:
    """CSV 스캔부터 집계 완료까지를 동일 number로 측정한다."""
    if number <= 0:
        raise ValueError("timeit 반복 횟수는 1 이상이어야 합니다.")

    def run_pandas() -> pd.DataFrame:
        frame = pd.read_csv(csv_path, encoding="utf-8-sig")
        frame = frame[frame["amount"].between(lower, upper, inclusive="both")]
        return pandas_named_aggregation(frame)

    def run_polars() -> pl.DataFrame:
        return polars_lazy_aggregation(csv_path, lower, upper)

    def run_duckdb() -> pd.DataFrame:
        return duckdb_sql_aggregation(csv_path, lower, upper)

    runners: dict[str, Any] = {
        "Pandas": run_pandas,
        "Polars Lazy": run_polars,
        "DuckDB SQL": run_duckdb,
    }
    records = []
    for tool_name, runner in runners.items():
        elapsed = timeit.timeit(runner, number=number)
        records.append(
            {
                "tool": tool_name,
                "number": number,
                "total_seconds": elapsed,
                "avg_seconds": elapsed / number,
            }
        )

    return pd.DataFrame(records).sort_values("total_seconds", ignore_index=True)


def main() -> None:
    """EDA, IQR 제거, 세 도구 집계, 성능 비교를 순서대로 실행한다."""
    validate_input(CSV_PATH)

    raw_df = load_and_explore(CSV_PATH)
    lower, upper = calculate_iqr_bounds(raw_df)
    clean_df = remove_outliers(raw_df, lower, upper)

    print("\n=== 2) Pandas named aggregation ===")
    pandas_result = pandas_named_aggregation(clean_df)
    print(pandas_result)

    print("\n=== 3) Polars Lazy API aggregation ===")
    polars_result = polars_lazy_aggregation(CSV_PATH, lower, upper)
    print(polars_result)

    print("\n=== 4) DuckDB SQL aggregation (Pandas DataFrame) ===")
    duckdb_result = duckdb_sql_aggregation(CSV_PATH, lower, upper)
    print(duckdb_result)

    print(f"\n=== timeit 성능 비교: 모두 number={BENCHMARK_NUMBER} ===")
    benchmark_result = benchmark_tools(
        CSV_PATH, lower, upper, number=BENCHMARK_NUMBER
    )
    print(benchmark_result.to_string(index=False))


if __name__ == "__main__":
    try:
        main()
    except (FileNotFoundError, ValueError, TypeError) as exc:
        raise SystemExit(f"실행 중단: {exc}") from exc
