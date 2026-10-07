"""실제 마이크로서비스 데이터를 사용해 2단계 추천 API를 순서대로 호출한다."""

import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.config.security import verify_token
from main import app


RESULT_DIR = Path(__file__).resolve().parents[1] / "experiment-results"


def save_json(file_name: str, data: dict) -> Path:
    RESULT_DIR.mkdir(exist_ok=True)
    output_path = RESULT_DIR / file_name
    output_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return output_path


def main() -> None:
    # 로컬 실험에서는 인증 자체가 아니라 추천 결과를 검증하므로 토큰 검증만 대체한다.
    app.dependency_overrides[verify_token] = lambda: {"sub": "local-experiment"}
    client = TestClient(app)

    persona_response = client.post(
        "/api/recommend/personas/generate",
        json={"maxPersonaCount": 5},
    )
    persona_response.raise_for_status()
    persona_result = persona_response.json()
    persona_path = save_json("persona_result.json", persona_result)

    bundle_response = client.post(
        "/api/recommend/persona-bundles/generate",
        json={
            "personas": persona_result["personas"],
            "minBundleSize": 3,
            "maxBundleSize": 6,
        },
    )
    bundle_response.raise_for_status()
    bundle_result = bundle_response.json()
    bundle_path = save_json("persona_bundle_result.json", bundle_result)

    print(f"페르소나 결과: {persona_path}")
    print(json.dumps(persona_result, ensure_ascii=False, indent=2))
    print(f"\n커리큘럼 결과: {bundle_path}")
    print(json.dumps(bundle_result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
