"""공통 실습 앱 — 4가지 배포 방법(온프레미스 / Docker / RayCluster CRD /
RayService CRD / 순수 Deployment)에서 동일하게 재사용하는 Ray Serve 애플리케이션.

RAY SERVE.md의 "4-1. 핵심 구성 요소" 3가지를 그대로 실습한다:
- Deployment: Greeter, Shouter, Driver 각각 @serve.deployment
- ServeHandle: Driver가 greeter_handle/shouter_handle을 생성자로 받아 .remote()로 호출
- Ingress deployment: Driver가 HTTP 요청을 받는 최상위 deployment

1_onprem_Rayserve/app.py와 동일한 코드 — 이 실습은 "같은 앱을 컨테이너 안에서
`serve run`으로 띄운다"는 점만 다르다(호스트 venv가 아니라 Docker 이미지).
"""
import os

from starlette.requests import Request
from ray import serve

METHOD = os.environ.get("RAY_SERVE_DEMO_METHOD", "1b_Docker_Ray컨테이너")


@serve.deployment
class Greeter:
    """서브 deployment #1 — 이름을 받아 인사말을 만든다."""

    def greet(self, name: str) -> str:
        return f"안녕하세요, {name}님!"


@serve.deployment
class Shouter:
    """서브 deployment #2 — 문자열을 강조(대문자+!!!)한다."""

    def shout(self, text: str) -> str:
        return text.upper() + "!!!"


@serve.deployment
class Driver:
    """Ingress deployment — HTTP 요청을 받아 ServeHandle로 두 서브 deployment를
    순서대로 원격 호출(Greeter -> Shouter)한 뒤 결과를 합쳐 반환한다."""

    def __init__(self, greeter_handle, shouter_handle):
        self._greeter = greeter_handle
        self._shouter = shouter_handle

    async def __call__(self, request: Request) -> dict:
        name = request.query_params.get("name", "Ray Serve")
        greeting = await self._greeter.greet.remote(name)
        shouted = await self._shouter.shout.remote(greeting)
        return {
            "greeting": greeting,
            "shouted": shouted,
            "served_by_method": METHOD,
            "hostname": os.environ.get("HOSTNAME", "unknown"),  # 컨테이너 ID가 찍힌다
        }


greeter = Greeter.bind()
shouter = Shouter.bind()
app = Driver.bind(greeter, shouter)
