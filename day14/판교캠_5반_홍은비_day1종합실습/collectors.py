"""asyncio와 httpx를 이용한 외부 API 동시 수집."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from time import perf_counter
from typing import Any

import httpx

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
COUNTRIES_URL = "https://countries.dev/alpha/KOR"
IP_API_URL = "http://ip-api.com/json/8.8.8.8"

API_REQUESTS: dict[str, tuple[str, dict[str, Any] | None]] = {
    "weather": (
        OPEN_METEO_URL,
        {
            "latitude": 37.5665,
            "longitude": 126.9780,
            "hourly": "temperature_2m,precipitation_probability",
            "forecast_days": 3,
            "timezone": "Asia/Seoul",
        },
    ),
    "country": (COUNTRIES_URL, None),
    "ip_location": (IP_API_URL, None),
}


class CollectionError(RuntimeError):
    """하나 이상의 API 수집 실패."""


@dataclass(frozen=True)
class FetchResult:
    """API 한 건의 응답과 소요 시간."""

    name: str
    payload: Any
    elapsed_ms: float


async def fetch_json(
    client: httpx.AsyncClient,
    name: str,
    url: str,
    params: dict[str, Any] | None,
) -> FetchResult:
    """API 한 개를 호출하고 JSON 응답과 소요 시간을 반환."""
    started_at = perf_counter()
    response = await client.get(url, params=params)
    response.raise_for_status()

    try:
        payload = response.json()
    except ValueError as error:
        raise CollectionError(f"{name}: JSON 응답이 아닙니다.") from error

    elapsed_ms = (perf_counter() - started_at) * 1_000
    return FetchResult(name=name, payload=payload, elapsed_ms=elapsed_ms)


async def collect_all() -> dict[str, FetchResult]:
    """세 API를 asyncio.gather()로 동시에 수집."""
    timeout = httpx.Timeout(20.0, connect=10.0)
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        tasks = [
            fetch_json(client, name, url, params) for name, (url, params) in API_REQUESTS.items()
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    failures: list[str] = []
    collected: dict[str, FetchResult] = {}

    for name, result in zip(API_REQUESTS, results, strict=True):
        if isinstance(result, BaseException):
            failures.append(f"{name}: {result}")
        else:
            collected[name] = result

    if failures:
        raise CollectionError("API 수집 실패 - " + " | ".join(failures))

    return collected
