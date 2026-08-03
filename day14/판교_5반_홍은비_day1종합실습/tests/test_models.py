"""Pydantic 스키마 검증 테스트."""

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from src.models import IpLocationRecord, WeatherRecord

NOW = datetime.now(UTC)


def test_valid_weather_record() -> None:
    """정상 날씨 레코드 생성."""
    record = WeatherRecord(
        collected_at=NOW,
        forecast_time=NOW,
        temperature_c=30.5,
        precipitation_probability=20,
    )
    assert record.temperature_c == 30.5


def test_invalid_precipitation_probability() -> None:
    """강수확률 100 초과 차단."""
    with pytest.raises(ValidationError):
        WeatherRecord(
            collected_at=NOW,
            forecast_time=NOW,
            temperature_c=30.5,
            precipitation_probability=150,
        )


def test_invalid_ip_latitude() -> None:
    """위도 허용 범위 초과 차단."""
    with pytest.raises(ValidationError):
        IpLocationRecord(
            collected_at=NOW,
            ip="8.8.8.8",
            country="United States",
            country_code="US",
            region="California",
            city="Mountain View",
            latitude=100,
            longitude=-122.08,
            timezone="America/Los_Angeles",
        )


def test_strict_type_rejects_string_probability() -> None:
    """엄격 모드에서 문자열 강수확률 차단."""
    with pytest.raises(ValidationError):
        WeatherRecord(
            collected_at=NOW,
            forecast_time=NOW,
            temperature_c=30.5,
            precipitation_probability="20",
        )
