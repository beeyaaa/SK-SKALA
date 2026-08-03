"""서로 다른 API 응답에서 필요한 필드를 추출하고 Pydantic으로 검증."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import ValidationError

from models import CountryRecord, IpLocationRecord, WeatherRecord


def _required_mapping(payload: Any, field_name: str) -> dict[str, Any]:
    """값이 딕셔너리인지 확인."""
    if not isinstance(payload, dict):
        raise ValueError(f"{field_name}는 JSON 객체여야 합니다.")
    return payload


def normalize_weather(
    payload: Any,
    collected_at: datetime,
) -> tuple[list[WeatherRecord], list[str]]:
    """Open-Meteo 병렬 배열을 시간대별 레코드로 변환."""
    root = _required_mapping(payload, "Open-Meteo 응답")
    hourly = _required_mapping(root.get("hourly"), "hourly")

    times = hourly.get("time")
    temperatures = hourly.get("temperature_2m")
    probabilities = hourly.get("precipitation_probability")
    arrays = (times, temperatures, probabilities)

    if not all(isinstance(values, list) for values in arrays):
        raise ValueError("Open-Meteo hourly 필드가 리스트가 아닙니다.")
    if len({len(values) for values in arrays}) != 1:
        raise ValueError("Open-Meteo hourly 배열 길이가 서로 다릅니다.")

    valid: list[WeatherRecord] = []
    errors: list[str] = []

    for index, (forecast_time, temperature, probability) in enumerate(
        zip(times, temperatures, probabilities, strict=True),
        start=1,
    ):
        try:
            valid.append(
                WeatherRecord.model_validate(
                    {
                        "collected_at": collected_at,
                        "forecast_time": forecast_time,
                        "temperature_c": temperature,
                        "precipitation_probability": probability,
                    }
                )
            )
        except ValidationError as error:
            errors.append(f"weather #{index}: {error}")

    return valid, errors


def _unwrap_country(payload: Any) -> dict[str, Any]:
    """countries.dev의 직접 응답 또는 data 래핑 응답을 처리."""
    root = _required_mapping(payload, "Countries 응답")
    data = root.get("data", root)
    if isinstance(data, list):
        if not data:
            raise ValueError("Countries 응답이 비어 있습니다.")
        data = data[0]
    return _required_mapping(data, "Countries 국가 데이터")


def _country_name(value: Any) -> str:
    """문자열 또는 {common, official} 형태의 국가명을 정규화."""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        name = value.get("common") or value.get("official")
        if isinstance(name, str):
            return name
    raise ValueError("국가명을 찾을 수 없습니다.")


def _optional_first(value: Any) -> str | None:
    """문자열 또는 문자열 리스트에서 첫 값을 반환."""
    if isinstance(value, str):
        return value or None
    if isinstance(value, list) and value and isinstance(value[0], str):
        return value[0]
    return None


def normalize_country(payload: Any, collected_at: datetime) -> CountryRecord:
    """Countries 국가 응답을 공통 국가 모델로 변환."""
    data = _unwrap_country(payload)
    name_value = data.get("name") or data.get("countryName") or data.get("officialName")
    code = data.get("cca3") or data.get("alpha3Code") or data.get("code")

    return CountryRecord.model_validate(
        {
            "collected_at": collected_at,
            "name": _country_name(name_value),
            "country_code": code,
            "capital": _optional_first(data.get("capital")),
            "region": _optional_first(data.get("region")),
        }
    )


def normalize_ip_location(payload: Any, collected_at: datetime) -> IpLocationRecord:
    """ip-api 응답을 IP 위치 모델로 변환."""
    data = _required_mapping(payload, "ip-api 응답")
    if data.get("status") != "success":
        raise ValueError(f"ip-api 실패 응답: {data.get('message', '원인 불명')}")

    return IpLocationRecord.model_validate(
        {
            "collected_at": collected_at,
            "ip": data.get("query"),
            "country": data.get("country"),
            "country_code": data.get("countryCode"),
            "region": data.get("regionName"),
            "city": data.get("city"),
            "latitude": data.get("lat"),
            "longitude": data.get("lon"),
            "timezone": data.get("timezone"),
        }
    )
