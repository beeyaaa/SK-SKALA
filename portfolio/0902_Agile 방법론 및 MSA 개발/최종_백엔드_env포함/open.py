#!/usr/bin/env python3
"""로컬 AI 추천 실습 환경을 점검하고 Docker 서비스를 한 번에 실행한다.

사용 위치:
    msa-lecture 프로젝트 루트에서 `python3 open.py`

이 스크립트는 데이터를 삭제하거나 컨테이너를 종료하지 않는다. 환경파일을
확인하고, 변경된 User/Recommend 이미지만 빌드한 뒤 기존 Compose 서비스들을
백그라운드로 기동한다.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
ROOT_ENV = PROJECT_ROOT / ".env"
ROOT_ENV_EXAMPLE = PROJECT_ROOT / ".env.example"
RECOMMEND_ENV = PROJECT_ROOT / "recommend-service" / ".env"
RECOMMEND_ENV_EXAMPLE = PROJECT_ROOT / "recommend-service" / ".env.example"
COMPOSE_BUILD = PROJECT_ROOT / "docker-compose.build.yml"
COMPOSE_LOCAL = PROJECT_ROOT / "docker-compose.local.yml"
HEALTH_URL = "http://localhost:8085/health"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="AI 추천 백엔드의 환경설정 확인, 빌드 및 Docker 실행"
    )
    parser.add_argument(
        "--no-build",
        action="store_true",
        help="User/Recommend 이미지 빌드를 생략하고 현재 로컬 이미지를 사용합니다.",
    )
    parser.add_argument(
        "--allow-fallback",
        action="store_true",
        help="OpenAI API Key가 없어도 규칙 기반 fallback 모드로 실행합니다.",
    )
    parser.add_argument(
        "--no-health-wait",
        action="store_true",
        help="컨테이너 실행 후 Recommend Service의 health 응답을 기다리지 않습니다.",
    )
    return parser.parse_args()


def read_env(path: Path) -> dict[str, str]:
    """간단한 KEY=VALUE 형식만 읽으며 환경변수 값은 화면에 출력하지 않는다."""
    values: dict[str, str] = {}
    if not path.is_file():
        return values

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        if line.startswith("export "):
            line = line.removeprefix("export ").strip()
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def ensure_env_file(target: Path, example: Path) -> bool:
    """환경파일이 없으면 안전한 example을 복사한다. 기존 파일은 덮어쓰지 않는다."""
    if target.is_file():
        try:
            target.chmod(0o600)
        except OSError:
            pass
        return False

    if not example.is_file():
        raise RuntimeError(f"환경변수 예시 파일이 없습니다: {example}")

    shutil.copyfile(example, target)
    try:
        target.chmod(0o600)
    except OSError:
        pass
    print(f"[환경설정] {target.relative_to(PROJECT_ROOT)} 파일을 생성했습니다.")
    return True


def validate_project() -> None:
    """변경 파일 ZIP이 완전한 원본 프로젝트 위에 풀렸는지 확인한다."""
    required_paths = [
        COMPOSE_BUILD,
        COMPOSE_LOCAL,
        PROJECT_ROOT / "user-service" / "build.gradle",
        PROJECT_ROOT / "recommend-service" / "requirements.txt",
        PROJECT_ROOT / "course-service",
        PROJECT_ROOT / "enrollment-service",
    ]
    missing = [str(path.relative_to(PROJECT_ROOT)) for path in required_paths if not path.exists()]
    if missing:
        joined = "\n  - ".join(missing)
        raise RuntimeError(
            "변경 파일만으로는 실행할 수 없습니다. msa-lecture 원본 프로젝트 루트에 "
            f"ZIP을 먼저 풀어주세요.\n  - {joined}"
        )


def validate_environment(allow_fallback: bool) -> None:
    """Compose에 필요한 DB 값과 실제 AI 호출에 필요한 Key 설정을 검증한다."""
    created_root = ensure_env_file(ROOT_ENV, ROOT_ENV_EXAMPLE)
    ensure_env_file(RECOMMEND_ENV, RECOMMEND_ENV_EXAMPLE)

    root_values = read_env(ROOT_ENV)
    recommend_values = read_env(RECOMMEND_ENV)
    missing_db = [
        key
        for key in ("MYSQL_ROOT_PASSWORD", "MYSQL_PASSWORD")
        if not root_values.get(key)
    ]

    if created_root or missing_db:
        fields = ", ".join(missing_db) if missing_db else "MYSQL_ROOT_PASSWORD, MYSQL_PASSWORD"
        raise RuntimeError(
            f".env에서 다음 값을 먼저 입력한 뒤 다시 실행하세요: {fields}"
        )

    has_openai_key = bool(
        root_values.get("OPENAI_API_KEY")
        or recommend_values.get("OPENAI_API_KEY")
    )
    if not has_openai_key and not allow_fallback:
        raise RuntimeError(
            "OPENAI_API_KEY가 비어 있습니다. .env 또는 recommend-service/.env에 키를 "
            "입력하거나, 규칙 기반 결과만 확인하려면 --allow-fallback을 사용하세요."
        )

    mode = "OpenAI 연동" if has_openai_key else "규칙 기반 fallback"
    print(f"[환경설정] DB 필수값 확인 완료 / 추천 모드: {mode}")


def run(command: list[str]) -> None:
    """명령을 프로젝트 루트에서 실행하고 실패하면 즉시 전체 실행을 중단한다."""
    print(f"\n[실행] {' '.join(command)}")
    subprocess.run(command, cwd=PROJECT_ROOT, check=True)


def compose_base() -> list[str]:
    return [
        "docker",
        "compose",
        "--env-file",
        str(ROOT_ENV),
        "-f",
        str(COMPOSE_BUILD),
        "-f",
        str(COMPOSE_LOCAL),
    ]


def validate_docker() -> None:
    if shutil.which("docker") is None:
        raise RuntimeError("Docker 명령을 찾을 수 없습니다. Docker Desktop을 설치해 주세요.")

    run(["docker", "compose", "version"])
    try:
        subprocess.run(
            ["docker", "info"],
            cwd=PROJECT_ROOT,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except subprocess.CalledProcessError as error:
        raise RuntimeError("Docker Engine이 실행 중이 아닙니다. Docker Desktop을 켜주세요.") from error
    print("[Docker] Docker Engine 연결 확인 완료")


def wait_for_recommend_service(timeout_seconds: int = 180) -> None:
    """의존 서비스 기동 시간을 고려해 Recommend health endpoint를 기다린다."""
    deadline = time.monotonic() + timeout_seconds
    print(f"\n[상태 확인] {HEALTH_URL} 응답을 기다립니다(최대 {timeout_seconds}초).")

    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(HEALTH_URL, timeout=3) as response:
                if 200 <= response.status < 300:
                    print("[완료] Recommend Service가 정상 실행되었습니다.")
                    return
        except (urllib.error.URLError, TimeoutError):
            pass
        time.sleep(3)

    raise RuntimeError(
        "Recommend Service가 제한 시간 안에 준비되지 않았습니다. "
        "Docker 로그를 확인하세요:\n"
        "docker compose -f docker-compose.build.yml -f docker-compose.local.yml "
        "logs -f recommend-service"
    )


def main() -> int:
    args = parse_args()
    try:
        validate_project()
        validate_environment(args.allow_fallback)
        validate_docker()

        compose = compose_base()
        if not args.no_build:
            # 변경된 Java/Python 서비스만 빌드하여 전체 신규 빌드를 피한다.
            run([*compose, "build", "user-service", "recommend-service"])

        # 나머지 서비스는 교육용으로 사전 로드된 이미지를 사용한다.
        run([*compose, "up", "-d", "--no-build", "--pull", "never"])
        run([*compose, "ps"])

        if not args.no_health_wait:
            wait_for_recommend_service()

        print("\n프론트 실행: cd vue-frontend && npm ci && npm run dev")
        print("접속 주소: http://localhost:3000")
        return 0
    except (RuntimeError, subprocess.CalledProcessError) as error:
        print(f"\n[실패] {error}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\n[중단] 사용자 요청으로 실행을 중단했습니다.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
