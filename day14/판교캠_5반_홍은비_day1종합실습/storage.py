"""검증된 데이터를 CSV·Parquet로 저장하고 읽기·쓰기 성능 비교."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path
from time import perf_counter

import pandas as pd
from pydantic import BaseModel


@dataclass(frozen=True)
class BenchmarkResult:
    """파일 형식별 성능 측정 결과."""

    dataset: str
    format: str
    rows: int
    write_seconds: float
    read_seconds: float
    file_bytes: int


def _minimum_time(action: Callable[[], object], repeat: int = 3) -> float:
    """동일 작업을 반복하고 가장 짧은 실행 시간을 반환."""
    measurements: list[float] = []
    for _ in range(repeat):
        started_at = perf_counter()
        action()
        measurements.append(perf_counter() - started_at)
    return min(measurements)


def _to_dataframe(records: list[BaseModel]) -> pd.DataFrame:
    """검증된 Pydantic 모델 목록을 DataFrame으로 변환."""
    return pd.DataFrame(record.model_dump(mode="json") for record in records)


def benchmark_dataset(
    dataset: str,
    records: list[BaseModel],
    output_dir: Path,
) -> list[BenchmarkResult]:
    """한 데이터셋을 CSV·Parquet로 저장하고 읽기·쓰기 성능 측정."""
    if not records:
        raise ValueError(f"{dataset}에 저장할 정상 데이터가 없습니다.")

    output_dir.mkdir(parents=True, exist_ok=True)
    frame = _to_dataframe(records)
    csv_path = output_dir / f"{dataset}.csv"
    parquet_path = output_dir / f"{dataset}.parquet"

    csv_write = _minimum_time(lambda: frame.to_csv(csv_path, index=False))
    csv_read = _minimum_time(lambda: pd.read_csv(csv_path))
    parquet_write = _minimum_time(lambda: frame.to_parquet(parquet_path, index=False))
    parquet_read = _minimum_time(lambda: pd.read_parquet(parquet_path))

    csv_reloaded = pd.read_csv(csv_path)
    parquet_reloaded = pd.read_parquet(parquet_path)
    if len(csv_reloaded) != len(frame) or len(parquet_reloaded) != len(frame):
        raise ValueError(f"{dataset} 저장 후 행 수가 달라졌습니다.")

    return [
        BenchmarkResult(
            dataset=dataset,
            format="CSV",
            rows=len(frame),
            write_seconds=csv_write,
            read_seconds=csv_read,
            file_bytes=csv_path.stat().st_size,
        ),
        BenchmarkResult(
            dataset=dataset,
            format="Parquet",
            rows=len(frame),
            write_seconds=parquet_write,
            read_seconds=parquet_read,
            file_bytes=parquet_path.stat().st_size,
        ),
    ]


def save_benchmark_summary(results: list[BenchmarkResult], output_dir: Path) -> Path:
    """전체 성능 측정 결과를 CSV로 저장."""
    summary_path = output_dir / "benchmark_results.csv"
    pd.DataFrame(asdict(result) for result in results).to_csv(summary_path, index=False)
    return summary_path
