"""API 응답에서 추출한 데이터의 Pydantic v2 스키마."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

NonEmptyText = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]
CountryCode3 = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=3, max_length=3),
]
CountryCode2 = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=2, max_length=2),
]


class StrictModel(BaseModel):
    """타입 자동 변환과 예상하지 못한 필드 유입 차단"""

    model_config = ConfigDict(extra="forbid", strict=True)


class WeatherRecord(StrictModel):
    """서울 시간대별 기온/강수확률 데이터"""

    source: Literal["open-meteo"] = "open-meteo"
    collected_at: datetime
    forecast_time: datetime
    temperature_c: float = Field(ge=-100, le=100)
    precipitation_probability: int = Field(ge=0, le=100)


class CountryRecord(StrictModel):
    """대한민국 국가 정보 데이터"""

    source: Literal["countries.dev"] = "countries.dev"
    collected_at: datetime
    name: NonEmptyText
    country_code: CountryCode3
    capital: NonEmptyText | None = None
    region: NonEmptyText | None = None


class IpLocationRecord(StrictModel):
    """IP 기반 지역 정보 데이터"""

    source: Literal["ip-api"] = "ip-api"
    collected_at: datetime
    ip: NonEmptyText
    country: NonEmptyText
    country_code: CountryCode2
    region: NonEmptyText
    city: NonEmptyText
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    timezone: NonEmptyText
