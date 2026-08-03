"""CSV·Parquet 저장 및 재로딩 테스트."""

from datetime import UTC, datetime
from pathlib import Path

import pandas as pd

from src.models import WeatherRecord
from src.storage import benchmark_dataset, save_benchmark_summary


def test_save_and_reload_csv_parquet(tmp_path: Path) -> None:
    """임시 경로의 CSV·Parquet 저장 결과와 주요 값 일치 확인."""
    records = [
        WeatherRecord(
            collected_at=datetime(2026, 8, 3, tzinfo=UTC),
            forecast_time=datetime(2026, 8, 3, 12),
            temperature_c=30.5,
            precipitation_probability=20,
        )
    ]

    performance = benchmark_dataset("weather", records, tmp_path)
    summary_path = save_benchmark_summary(performance, tmp_path)

    csv_data = pd.read_csv(tmp_path / "weather.csv")
    parquet_data = pd.read_parquet(tmp_path / "weather.parquet")

    assert {result.format for result in performance} == {"CSV", "Parquet"}
    assert len(csv_data) == len(parquet_data) == 1
    assert csv_data["forecast_time"].tolist() == parquet_data["forecast_time"].tolist()
    assert summary_path.exists()
