# ============================================================
# 작성자   : 홍은비
# 작성일자 : 2026-08-03
# 내용     : [실습 2] 파일 I/O, 예외 처리, Pydantic 검증 파이프라인
#            - 배포 JSON 기반 sales_input.csv 생성
#            - SalesRecord 스키마 기반 데이터 검증
#            - 정상 데이터 CSV / 오류 데이터 JSON 저장
# 변경내역 :
#            - 2026-08-03  홍은비  최초 작성
#            - build_input_csv, safe_load_csv, SalesRecord 구현
#            - validate_records, save_results 구현
# ============================================================

import ast
import csv
import json
import logging
import sys
from pathlib import Path

from pydantic import BaseModel, Field, ValidationError, field_validator

BASE_DIR = Path(__file__).parent
JSON_PATH = BASE_DIR / "Python_Practice1_Data.json"
CSV_PATH = BASE_DIR / "sales_input.csv"
VALID_OUTPUT_PATH = BASE_DIR / "sales_valid.csv"
ERRORS_OUTPUT_PATH = BASE_DIR / "sales_errors.json"

FIELDNAMES = ["month", "region", "amount", "category"]

# - 검증 연습용 오류 데이터
# - month 빈 문자열 -> 문자열 검증 오류
# - region 빈 문자열 -> 문자열 검증 오류
# - amount 0 -> 양수 조건 검증 오류
BROKEN_ROWS = [
    {
        "month": "",
        "region": "경기",
        "amount": 1500,
        "category": "생활용품",
    },
    {
        "month": "2024-02",
        "region": "",
        "amount": 2000,
        "category": "전자",
    },
    {
        "month": "2024-02",
        "region": "대전",
        "amount": 0,
        "category": "도서",
    },
]

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s:%(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


class SalesRecord(BaseModel):
    """판매 데이터 1건 검증."""

    month: str
    region: str
    amount: int = Field(gt=0)
    category: str | None = None

    @field_validator("month", "region")
    @classmethod
    def not_empty(cls, value: str) -> str:
        """month·region 빈 값 차단."""
        if not value.strip():
            raise ValueError("빈 값은 입력할 수 없습니다.")

        return value.strip()


def build_input_csv() -> None:
    """배포 JSON 기반 정상 4건·오류 3건 입력 CSV 생성."""
    text = JSON_PATH.read_text(encoding="utf-8").strip()

    try:
        sales = json.loads(text)
    except json.JSONDecodeError:
        # - 'sales = [...]' 형식 처리 -> 등호 오른쪽 안전 해석
        sales = ast.literal_eval(text.split("=", 1)[1].strip())

    if not isinstance(sales, list) or len(sales) < 4:
        raise ValueError("배포 데이터에 정상 판매 데이터가 4건 이상 필요합니다.")

    # - 정상 4건 뒤에 검증용 오류 3건 추가
    rows = [row.copy() for row in sales[:4]]
    rows.extend(row.copy() for row in BROKEN_ROWS)

    # - category 선택 항목 -> 빈 값 허용 여부 확인
    rows[3] = {**rows[3], "category": ""}

    with CSV_PATH.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=FIELDNAMES,
            extrasaction="ignore",
        )
        writer.writeheader()
        writer.writerows(rows)

    logger.info("입력 CSV 생성:%d건 (정상 4 + 오류 3)", len(rows))


def safe_load_csv(file_path: Path) -> list[dict] | None:
    """CSV 파일 안전 로딩."""
    try:
        with file_path.open(
            "r",
            encoding="utf-8-sig",
            newline="",
        ) as file:
            data = list(csv.DictReader(file))

        logger.info(
            "CSV 로딩 성공: %s (%d건)",
            file_path.name,
            len(data),
        )
        return data

    except FileNotFoundError:
        logger.error("CSV 파일이 없습니다: %s", file_path)
        return None

    except (OSError, csv.Error) as error:
        logger.error("CSV 로딩 실패: %s", error)
        return None

    finally:
        print("로딩 종료")


def validate_records(
    raw_data: list[dict],
) -> tuple[list[SalesRecord], list[dict]]:
    """정상 데이터·오류 데이터 분리."""
    valid = []
    errors = []

    for row in raw_data:
        try:
            record = SalesRecord.model_validate(row)
            valid.append(record)

        except ValidationError as error:
            print(error)
            errors.append(
                {
                    "row": row,
                    "error": str(error),
                }
            )

    return valid, errors


def save_results(
    valid: list[SalesRecord],
    errors: list[dict],
    valid_path: Path,
    error_path: Path,
) -> None:
    """정상 데이터 CSV·오류 데이터 JSON 저장."""
    with valid_path.open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "month",
                "region",
                "amount",
                "category",
            ],
        )
        writer.writeheader()

        # - Pydantic 모델 -> dict 변환 후 저장
        writer.writerows(
            record.model_dump()
            for record in valid
        )

    with error_path.open(
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            errors,
            file,
            ensure_ascii=False,
            indent=4,
        )

    logger.info("정상 데이터 저장: %d건", len(valid))
    logger.info("오류 데이터 저장: %d건", len(errors))


def main() -> None:
    """입력 CSV 생성·검증·저장·재로딩 실행."""

    # - 존재하지 않는 CSV 파일 -> None 반환 확인
    assert safe_load_csv(
        BASE_DIR / "not_exists.csv"
    ) is None

    # - 배포 JSON -> 정상 4건 + 오류 3건 입력 CSV 생성
    try:
        build_input_csv()
    except (OSError, ValueError, SyntaxError, IndexError) as error:
        logger.error("입력 CSV 생성 실패:%s", error)
        return

    # - 생성한 입력 CSV 로딩
    raw_data = safe_load_csv(CSV_PATH)
    if raw_data is None:
        return

    assert len(raw_data) == 7

    # - Pydantic 검증
    valid, errors = validate_records(raw_data)

    # - 검증 과정의 데이터 누락 여부 확인
    assert len(valid) + len(errors) == len(raw_data)

    # - 정상 데이터·오류 데이터 저장
    save_results(
        valid,
        errors,
        VALID_OUTPUT_PATH,
        ERRORS_OUTPUT_PATH,
    )

    # - 저장된 정상 CSV 재로딩
    reloaded = safe_load_csv(VALID_OUTPUT_PATH)

    assert reloaded is not None

    # - 저장 전후 정상 데이터 건수 확인
    assert len(reloaded) == len(valid)

    # - 체크포인트 -> 정상 4건 / 오류 3건 / 재로딩 4건
    assert len(valid) == 4
    assert len(errors) == 3
    assert len(reloaded) == 4

    print("\n=== 검증 결과 ===")
    print(f"전체 데이터: {len(raw_data)}건")
    print(f"정상 데이터: {len(valid)}건")
    print(f"오류 데이터: {len(errors)}건")
    print(f"재로딩 데이터: {len(reloaded)}건")


if __name__ == "__main__":
    main()
