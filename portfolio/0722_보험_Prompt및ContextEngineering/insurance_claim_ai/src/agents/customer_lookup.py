from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.schemas import AccidentFacts, CustomerLookupOutput


DAMAGE_TOKENS = ("좌측", "우측", "전방", "후방", "범퍼", "도어")


def _records(frame: pd.DataFrame) -> list[dict]:
    clean = frame.where(pd.notna(frame), None)
    records = []
    for record in clean.to_dict(orient="records"):
        converted = {}
        for key, value in record.items():
            if pd.isna(value):
                value = None
            elif hasattr(value, "isoformat"):
                value = value.isoformat()
            elif hasattr(value, "item"):
                value = value.item()
            converted[key] = value
        records.append(converted)
    return records


def _damage_overlap(current_damage: str | None, prior_damage: str) -> bool:
    current_tokens = {
        token for token in DAMAGE_TOKENS
        if token in (current_damage or "")
    }
    prior_tokens = {
        token for token in DAMAGE_TOKENS
        if token in (prior_damage or "")
    }
    return len(current_tokens & prior_tokens) >= 2


class CustomerLookup:
    def __init__(self, data_dir: Path | None = None) -> None:
        project_dir = Path(__file__).resolve().parents[2]
        self.data_dir = data_dir or project_dir / "data"

    def run(self, accident: AccidentFacts) -> CustomerLookupOutput:
        customers = pd.read_csv(
            self.data_dir / "customers.csv",
            encoding="utf-8-sig",
            dtype={"customer_id": "string", "차량번호": "string"},
        )
        contracts = pd.read_csv(
            self.data_dir / "contracts.csv",
            encoding="utf-8-sig",
            parse_dates=["계약시작일", "계약종료일"],
            dtype={
                "policy_id": "string",
                "customer_id": "string",
                "차량번호": "string",
            },
        )
        coverages = pd.read_csv(
            self.data_dir / "coverages.csv",
            encoding="utf-8-sig",
            dtype={"policy_id": "string"},
        )
        history = pd.read_csv(
            self.data_dir / "accident_history.csv",
            encoding="utf-8-sig",
            parse_dates=["사고일", "종결일"],
            dtype={
                "history_id": "string",
                "customer_id": "string",
                "policy_id": "string",
            },
        )

        customer_rows = customers[
            customers["customer_id"] == accident.customer_id
        ]
        if customer_rows.empty:
            raise LookupError(f"고객을 찾지 못했습니다: {accident.customer_id}")

        accident_date = pd.Timestamp(accident.accident_date)
        customer_contracts = contracts[
            (contracts["customer_id"] == accident.customer_id)
            & (contracts["계약시작일"] <= accident_date)
            & (contracts["계약종료일"] >= accident_date)
        ]
        if customer_contracts.empty:
            raise LookupError("사고일 기준 유효 계약이 없습니다.")

        policy = customer_contracts.iloc[0].to_dict()
        policy_coverages = coverages[
            coverages["policy_id"] == policy["policy_id"]
        ]
        customer_history = history[
            history["customer_id"] == accident.customer_id
        ].copy()
        open_claims = customer_history[
            customer_history["처리상태"] != "종결"
        ]

        overlap_flags = []
        for record in _records(open_claims):
            if _damage_overlap(
                accident.customer_damage,
                str(record.get("고객차량파손", "")),
            ):
                overlap_flags.append(
                    f"{record['history_id']}의 기존 파손 "
                    f"({record['고객차량파손']})과 현재 파손 "
                    f"({accident.customer_damage})의 중첩 가능성 확인 필요"
                )

        return CustomerLookupOutput(
            customer_id=accident.customer_id,
            customer_name=str(customer_rows.iloc[0]["고객명"]),
            policy={
                key: (
                    value.isoformat()
                    if hasattr(value, "isoformat")
                    else value
                )
                for key, value in policy.items()
            },
            coverages=_records(policy_coverages),
            prior_accidents=_records(customer_history),
            open_claims=_records(open_claims),
            overlap_flags=overlap_flags,
            history_use_limitation=(
                "과거 사고이력은 기존 파손·중복·미종결 건 확인에만 사용하며 "
                "현재 사고의 과실비율 산정에는 사용하지 않습니다."
            ),
        )
