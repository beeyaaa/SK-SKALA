import re

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable

from src.schemas import AccidentFacts


AMOUNT_RE = r"(\d+(?:,\d{3})*(?:\.\d+)?)\s*(억원|천만원|백만원|만원|천원|원)"
AMOUNT_UNITS = {
    "억원": 100_000_000,
    "천만원": 10_000_000,
    "백만원": 1_000_000,
    "만원": 10_000,
    "천원": 1_000,
    "원": 1,
}
COST_WORDS = ("수리비", "피해액", "손해액", "추정 비용", "예상 비용")


def _extract_cost(text: str, party_pattern: str) -> int | None:
    pattern = re.compile(
        rf"(?:{party_pattern})"
        rf"[^.!?\n]{{0,50}}?"
        rf"(?:수리비|피해액|손해액|추정\s*비용|예상\s*비용)"
        rf"[^\d]{{0,15}}{AMOUNT_RE}"
    )
    matched = pattern.search(text)
    if not matched:
        return None

    number = float(matched.group(1).replace(",", ""))
    return int(number * AMOUNT_UNITS[matched.group(2)])


def _is_cost_missing_fact(value: str, party: str) -> bool:
    return party in value and any(word in value for word in COST_WORDS)


class InputNormalizer:
    def __init__(self, llm: Runnable) -> None:
        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                "당신은 자동차보험 사고 접수 문장을 구조화한다. "
                "입력에 없는 사실은 추정하지 말고 missing_facts에 기록한다. "
                "금액은 원 단위 정수, 날짜는 YYYY-MM-DD로 반환한다. "
                "고객과 상대방의 행동, 차로, 유턴·진로변경 여부, 제한속도, "
                "추정속도, 파손부위와 증거를 입력 문장 그대로 빠짐없이 구분한다.",
            ),
            (
                "human",
                "claim_id={claim_id}\ncustomer_id={customer_id}\n사고내용:\n{text}",
            ),
        ])
        self.chain = prompt | llm.with_structured_output(AccidentFacts)

    def run(
        self,
        claim_id: str,
        customer_id: str,
        text: str,
    ) -> AccidentFacts:
        result = self.chain.invoke({
            "claim_id": claim_id,
            "customer_id": customer_id,
            "text": text,
        })

        # 금액은 계산에 직접 사용되므로 LLM이 놓친 경우 원문에서 한 번 더
        # 결정론적으로 추출합니다.
        customer_cost = (
            result.customer_estimated_cost
            or _extract_cost(text, r"고객(?:\s*차량)?|자차")
        )
        counterparty_cost = (
            result.counterparty_estimated_cost
            or _extract_cost(
                text,
                r"상대(?:방)?(?:\s*(?:차량|오토바이))?",
            )
        )

        missing_facts = list(result.missing_facts)
        if customer_cost is not None:
            missing_facts = [
                item for item in missing_facts
                if not _is_cost_missing_fact(item, "고객")
            ]
        if counterparty_cost is not None:
            missing_facts = [
                item for item in missing_facts
                if not _is_cost_missing_fact(item, "상대")
            ]
        if re.search(
            r"인명\s*피해.{0,20}(?:없|확인되지\s*않)",
            text,
        ):
            missing_facts = [
                item for item in missing_facts
                if "인명" not in item
            ]

        return result.model_copy(update={
            "customer_estimated_cost": customer_cost,
            "counterparty_estimated_cost": counterparty_cost,
            "missing_facts": missing_facts,
        })
