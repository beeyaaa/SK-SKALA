"""API JSON 변환 및 검증 파이프라인 테스트."""

from datetime import UTC, datetime

import pytest

from src.transformers import normalize_country, normalize_ip_location, normalize_weather

NOW = datetime(2026, 8, 3, tzinfo=UTC)


def test_open_meteo_payload_normalization() -> None:
    """Open-Meteo JSON 필드 추출 및 날씨 스키마 검증."""
    payload = {
        "hourly": {
            "time": ["2026-08-03T12:00:00", "2026-08-03T13:00:00"],
            "temperature_2m": [30.5, 31.0],
            "precipitation_probability": [20, 30],
        }
    }

    records, errors = normalize_weather(payload, NOW)

    assert len(records) == 2
    assert errors == []
    assert records[0].temperature_c == 30.5


def test_countries_payload_normalization() -> None:
    """Countries JSON 필드 추출 및 국가 스키마 검증."""
    payload = {
        "data": {
            "name": "South Korea",
            "code": "KOR",
            "capital": ["Seoul"],
            "region": "Asia",
        }
    }

    record = normalize_country(payload, NOW)

    assert record.country_code == "KOR"
    assert record.capital == "Seoul"


def test_ip_api_payload_normalization() -> None:
    """ip-api JSON 필드 추출 및 IP 위치 스키마 검증."""
    payload = {
        "status": "success",
        "query": "8.8.8.8",
        "country": "United States",
        "countryCode": "US",
        "regionName": "California",
        "city": "Mountain View",
        "lat": 37.4056,
        "lon": -122.0775,
        "timezone": "America/Los_Angeles",
    }

    record = normalize_ip_location(payload, NOW)

    assert record.ip == "8.8.8.8"
    assert record.country_code == "US"


def test_ip_api_failure_response() -> None:
    """ip-api 실패 응답 차단."""
    with pytest.raises(ValueError, match="ip-api 실패 응답"):
        normalize_ip_location(
            {"status": "fail", "message": "invalid query"},
            NOW,
        )
