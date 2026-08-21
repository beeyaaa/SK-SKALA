"""Practice 1 - 자료구조 집계, 컴프리헨션, 제너레이터 실습.
작성자: 홍은비

1. amount가 1,000 이상인 거래 필터링 및 지역별 총매출 계산
2. Counter와 defaultdict를 이용한 거래 건수/카테고리별 금액 집계
3. amount가 1,000보다 큰 거래 제너레이터와 리스트의 메모리 비교
4. 월별-카테고리별 총매출 집계 및 총매출 상위 3개 출력
"""

from __future__ import annotations

import json
import logging
import sys
from collections import Counter, defaultdict
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Any

DATA_FILE = Path(__file__).with_name("Python_Practice1_Data.json")
MIN_AMOUNT = 1000
REQUIRED_KEYS = {"region", "category", "amount", "month"}

SalesRecord = dict[str, Any]

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def load_sales(path: Path) -> list[SalesRecord]:
    """JSON 파일에서 sales 리스트를 읽고 구조 검증"""
    if not path.is_file():
        raise FileNotFoundError(f"데이터 파일을 찾을 수 없습니다: {path}")

    with path.open(encoding="utf-8") as file:
        sales = json.load(file)

    # - list: 여러 거래의 순차 반복 처리
    # - dict: 거래 속성을 의미 있는 키로 표현
    if not isinstance(sales, list):
        raise TypeError("데이터 파일의 sales는 리스트여야 합니다.")

    for index, row in enumerate(sales, start=1):
        if not isinstance(row, dict):
            raise TypeError(f"{index}번째 레코드는 딕셔너리가 아닙니다.")

        missing_keys = REQUIRED_KEYS - row.keys()
        if missing_keys:
            missing = ", ".join(sorted(missing_keys))
            raise ValueError(f"{index}번째 레코드의 필수 키가 없습니다: {missing}")

        if not isinstance(row["amount"], (int, float)):
            raise TypeError(f"{index}번째 레코드의 amount가 숫자가 아닙니다.")

    logger.info("데이터 %d건을 불러왔습니다.", len(sales))
    return sales

# 1) 리스트/딕셔너리 컴프리헨션
def filter_sales(
    sales: Iterable[SalesRecord], min_amount: int = MIN_AMOUNT
) -> list[SalesRecord]:
    """amount가 기준 금액 이상인 거래만 리스트 컴프리헨션으로 반환"""
    # - list comprehension: 조건에 맞는 거래의 새 리스트 생성
    # -> 일반 for + append 대비 명확한 필터링 의도와 간결한 코드
    return [row for row in sales if row["amount"] >= min_amount]

# 1) 리스트/딕셔너리 컴프리헨션
def calculate_region_totals(sales: list[SalesRecord]) -> dict[str, int]:
    """필터링된 거래의 지역별 총매출을 딕셔너리 컴프리헨션으로 계산"""
    # - set: 중복 지역 자동 제거 및 고유 지역 추출
    regions = {row["region"] for row in sales}

    # - dict: '지역 -> 총매출' 관계의 명확한 표현과 조회
    return {
        region: sum(row["amount"] for row in sales if row["region"] == region)
        for region in sorted(regions)
    }

# 2) Counter + defaultdict
def summarize_sales(
    sales: Iterable[SalesRecord],
) -> tuple[Counter[str], dict[str, list[int]]]:
    """Counter로 지역별 거래 건수를, defaultdict로 카테고리별 amount 리스트"""
    sales_list = list(sales)

    # - Counter: 지역별 출현 횟수 자동 계산
    region_counts = Counter(row["region"] for row in sales_list)

    # - list: 카테고리별 여러 amount 저장
    # - defaultdict(list): 새 키의 빈 리스트 자동 생성 및 키 확인 조건문 제거
    category_amounts: defaultdict[str, list[int]] = defaultdict(list)
    for row in sales_list:
        category_amounts[row["category"]].append(row["amount"])

    return region_counts, dict(category_amounts)

# 3) 제너레이터와 리스트의 메모리 크기 비교
def iter_high_sales(
    sales: Iterable[SalesRecord], min_amount: int = MIN_AMOUNT
) -> Iterator[SalesRecord]:
    """amount가 기준 금액보다 큰 거래의 지연 반환"""
    # - generator: 결과 미저장, yield를 통한 한 건씩 처리, 메모리 절약
    for row in sales:
        if row["amount"] > min_amount:
            yield row

# 4) 종합 - 월별 카테고리 매출 집계
def aggregate_month_category(
    sales: Iterable[SalesRecord],
) -> dict[str, dict[str, int]]:
    """sales 데이터를 month·category 기준으로 그룹핑해 총매출 dict를 완성 (컴프리헨션 + defaultdict)"""
    # - 중첩 dict: month와 category의 2단계 집계 구조 표현
    # - defaultdict(int): 새 조합의 기본값 0 생성 및 즉시 누적
    totals: defaultdict[str, defaultdict[str, int]] = defaultdict(
        lambda: defaultdict(int)
    )

    for row in sales:
        totals[row["month"]][row["category"]] += row["amount"]

    # - 일반 dict 변환: 출력 및 결과 검증 용이성 확보
    return {
        month: dict(sorted(category_totals.items()))
        for month, category_totals in sorted(totals.items())
    }


def select_top3(
    month_category_totals: dict[str, dict[str, int]],
) -> list[tuple[str, str, int]]:
    """월별-카테고리별 총매출 중 금액이 큰 상위 3개를 반환한다."""
    # - tuple: (월, 카테고리, 금액)의 고정된 집계 결과 표현
    # - list: 여러 집계 결과의 금액순 정렬 및 상위 3개 선택
    aggregates = [
        (month, category, amount)
        for month, category_totals in month_category_totals.items()
        for category, amount in category_totals.items()
    ]
    return sorted(aggregates, key=lambda item: item[2], reverse=True)[:3]


def validate_results(
    sales: list[SalesRecord],
    filtered_sales: list[SalesRecord],
    region_totals: dict[str, int],
    region_counts: Counter[str],
    generator_size: int,
    list_size: int,
    top3: list[tuple[str, str, int]],
) -> None:
    """제공된 데이터에 대한 Practice 1 체크포인트를 자동 검증한다."""
    expected_region_totals = {
        "광주": 4830,
        "대구": 8320,
        "대전": 6300,
        "부산": 4550,
        "서울": 17670,
        "세종": 5750,
        "울산": 7270,
        "인천": 11950,
    }
    expected_counts = [
        ("서울", 14),
        ("부산", 13),
        ("대구", 13),
        ("인천", 12),
        ("광주", 12),
        ("대전", 12),
        ("울산", 12),
        ("세종", 12),
    ]
    expected_top3 = [
        ("2024-02", "전자", 15240),
        ("2024-04", "전자", 14010),
        ("2024-03", "전자", 13820),
    ]

    assert len(sales) == 100, "전체 데이터는 100건이어야 합니다."
    assert len(filtered_sales) == 47, "amount >= 1000인 거래는 47건이어야 합니다."
    assert region_totals == expected_region_totals, "지역별 총매출이 올바르지 않습니다."
    assert region_counts.most_common() == expected_counts, "거래 건수 순서가 다릅니다."
    assert generator_size < list_size, "제너레이터가 리스트보다 작아야 합니다."
    assert top3 == expected_top3, "총매출 상위 3개의 순서 또는 금액이 다릅니다."


def main() -> int:
    """Practice 1의 네 가지 과제를 실행하고 결과를 출력한다."""
    try:
        sales = load_sales(DATA_FILE)

        # 1) 리스트/딕셔너리 컴프리헨션
        filtered_sales = filter_sales(sales) # amount >= 1000 거래 필터링
        region_totals = calculate_region_totals(filtered_sales) # 지역별 총매출 dict를 컴프리헨션으로 계산

        # 2) Counter + defaultdict
        region_counts, category_amounts = summarize_sales(sales)

        # 3) 제너레이터와 리스트의 메모리 크기 비교
        # - 메모리 비교: 전체 저장 list vs 지연 생성 generator
        list_version = [row for row in sales if row["amount"] > MIN_AMOUNT]
        generator_version = iter_high_sales(sales)
        list_size = sys.getsizeof(list_version)
        generator_size = sys.getsizeof(generator_version)

        # 4) 월별-카테고리별 집계와 상위 3개 계산
        month_category_totals = aggregate_month_category(sales)
        top3 = select_top3(month_category_totals)

        validate_results(
            sales,
            filtered_sales,
            region_totals,
            region_counts,
            generator_size,
            list_size,
            top3,
        )

    except (FileNotFoundError, OSError, json.JSONDecodeError, TypeError, ValueError) as error:
        logger.error("Practice 1 실행 실패: %s", error)
        return 1
    except AssertionError as error:
        logger.error("결과 검증 실패: %s", error)
        return 1

    print("\n[1] amount >= 1000 거래")
    print(f"거래 건수: {len(filtered_sales)}건")
    print(f"지역별 총매출: {region_totals}")

    print("\n[2] Counter + defaultdict 집계")
    print(f"지역별 거래 건수: {region_counts.most_common()}")
    print("카테고리별 amount 요약:")
    for category, amounts in sorted(category_amounts.items()):
        print(f"- {category}: {len(amounts)}건, 합계 {sum(amounts):,}원")

    print("\n[3] 제너레이터 메모리 비교")
    print(f"리스트: {list_size} bytes")
    print(f"제너레이터: {generator_size} bytes")

    print("\n[4] 월별-카테고리별 총매출")
    for month, category_totals in month_category_totals.items():
        print(f"- {month}: {category_totals}")
    print(f"총매출 상위 3개: {top3}")

    print("\n모든 Practice 1 체크포인트를 통과했습니다.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
