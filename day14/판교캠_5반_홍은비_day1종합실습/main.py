"""Day 1 종합 실습 데이터 수집 미니 파이프라인 실행 파일."""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime
from pathlib import Path

from pydantic import BaseModel, ValidationError

from collectors import CollectionError, collect_all
from models import CountryRecord, IpLocationRecord
from storage import BenchmarkResult, benchmark_dataset, save_benchmark_summary
from transformers import normalize_country, normalize_ip_location, normalize_weather

BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
REPORT_PATH = BASE_DIR / "report.md"

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def _print_benchmarks(results: list[BenchmarkResult]) -> None:
    """CSV·Parquet 성능 비교 결과 출력."""
    print("\n[CSV·Parquet 성능 비교]")
    for result in results:
        print(
            f"- {result.dataset:11s} {result.format:7s} "
            f"rows={result.rows:3d} "
            f"write={result.write_seconds:.6f}s "
            f"read={result.read_seconds:.6f}s "
            f"size={result.file_bytes:,}bytes"
        )


def _write_report(
    api_times: dict[str, float],
    datasets: dict[str, list[BaseModel]],
    validation_errors: list[str],
    benchmarks: list[BenchmarkResult],
) -> None:
    """실행 결과와 본인 의견 초안을 Markdown으로 저장."""
    lines = [
        "# Day 1 종합 실습 실행결과",
        "",
        f"- 실행 시각(UTC): {datetime.now(UTC).isoformat()}",
        f"- API 수집 성공: {len(api_times)}/3",
        f"- 검증 오류: {len(validation_errors)}건",
        "",
        "## API 응답 시간",
        "",
    ]
    lines.extend(f"- {name}: {elapsed:.2f}ms" for name, elapsed in api_times.items())
    lines.extend(["", "## 검증 데이터 건수", ""])
    lines.extend(f"- {name}: {len(records)}건" for name, records in datasets.items())
    lines.extend(
        [
            "",
            "## CSV·Parquet 성능 비교",
            "",
            "| 데이터셋 | 형식 | 행 | 쓰기(초) | 읽기(초) | 크기(bytes) |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    lines.extend(
        f"| {item.dataset} | {item.format} | {item.rows} | "
        f"{item.write_seconds:.6f} | {item.read_seconds:.6f} | {item.file_bytes} |"
        for item in benchmarks
    )
    lines.extend(
        [
            "",
            "## 본인 의견",
            "",
            "- asyncio.gather()를 사용해 서로 독립적인 API 요청의 대기 시간을 겹쳐 처리했다.",
            "- Pydantic 검증을 저장 전에 적용해 타입과 값 범위가 잘못된 데이터의 유입을 차단했다.",
            "- 소규모 데이터에서는 Parquet 초기화 비용 때문에 CSV보다 느릴 수 있으나, "
            "Parquet는 타입 보존과 대용량 컬럼 분석에 유리하다.",
            "",
            "## 개선 사항",
            "",
            "- 일시적인 API 장애에 대비한 지수 백오프 재시도 추가",
            "- 반복 실행 시 날짜별 파티셔닝과 중복 데이터 제거 추가",
            "- 운영 환경에서는 구조화 로그와 모니터링 지표 연동",
            "",
        ]
    )
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


async def run_pipeline() -> int:
    """수집·검증·저장·성능 비교 전체 파이프라인 실행."""
    try:
        collected = await collect_all()
    except CollectionError as error:
        logger.error("비동기 수집 실패: %s", error)
        return 1

    print("[API 비동기 수집]")
    for name, result in collected.items():
        print(f"- {name}: 정상 응답 ({result.elapsed_ms:.2f}ms)")

    collected_at = datetime.now(UTC)
    validation_errors: list[str] = []

    try:
        weather, weather_errors = normalize_weather(
            collected["weather"].payload,
            collected_at,
        )
        validation_errors.extend(weather_errors)
        country: CountryRecord = normalize_country(
            collected["country"].payload,
            collected_at,
        )
        ip_location: IpLocationRecord = normalize_ip_location(
            collected["ip_location"].payload,
            collected_at,
        )
    except (KeyError, TypeError, ValueError, ValidationError) as error:
        logger.error("스키마 검증 실패: %s", error)
        return 1

    if validation_errors:
        for error in validation_errors:
            logger.error("레코드 검증 실패: %s", error)

    datasets: dict[str, list[BaseModel]] = {
        "weather": weather,
        "country": [country],
        "ip_location": [ip_location],
    }

    print("\n[Pydantic v2 검증]")
    for name, records in datasets.items():
        print(f"- {name}: 정상 {len(records)}건")
    print(f"- 검증 오류: {len(validation_errors)}건")

    try:
        benchmarks = [
            result
            for name, records in datasets.items()
            for result in benchmark_dataset(name, records, OUTPUT_DIR)
        ]
        summary_path = save_benchmark_summary(benchmarks, OUTPUT_DIR)
    except (OSError, ValueError, ImportError) as error:
        logger.error("저장 또는 성능 비교 실패: %s", error)
        return 1

    _print_benchmarks(benchmarks)
    print(f"\n성능 요약 저장: {summary_path}")

    api_times = {name: result.elapsed_ms for name, result in collected.items()}
    _write_report(api_times, datasets, validation_errors, benchmarks)
    print(f"실행결과 보고서 저장: {REPORT_PATH}")
    print("\nDay 1 종합 실습 파이프라인을 완료했습니다.")
    return 0


def main() -> int:
    """비동기 파이프라인 진입점."""
    return asyncio.run(run_pipeline())


if __name__ == "__main__":
    raise SystemExit(main())
