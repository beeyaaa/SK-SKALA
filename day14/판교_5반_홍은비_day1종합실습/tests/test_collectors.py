"""실제 인터넷을 사용하지 않는 비동기 API 수집 테스트."""

import httpx
import pytest

from src.collectors import fetch_all_data


@pytest.mark.asyncio
async def test_fetch_all_data() -> None:
    """Open-Meteo·Countries·ip-api 요청의 동시 수집 확인."""
    payloads = {
        "/v1/forecast": {"api": "weather"},
        "/alpha/KOR": {"api": "country"},
        "/json/8.8.8.8": {"api": "ip_location"},
    }
    called_paths: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        called_paths.append(request.url.path)
        return httpx.Response(
            status_code=200,
            json=payloads[request.url.path],
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        result = await fetch_all_data(client)

    assert set(called_paths) == set(payloads)
    assert result["weather"].payload == {"api": "weather"}
    assert result["country"].payload == {"api": "country"}
    assert result["ip_location"].payload == {"api": "ip_location"}
