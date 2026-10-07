# ============================================================
# 작성자   : Codex (홍은비 실습 보조)
# 작성일자 : 2026-10-07
# 내용     : [실습 2] GPT 답변 생성 및 RAGAS 단계별 평가
#            - Dense·Hybrid·Reranker의 답변과 세 지표 비교
#            - 실행 중 예상 API 비용을 계산해 상한 확인
# 변경내역 :
#            - 2026-10-07  Codex  RAGAS 평가 스크립트 작성
# ============================================================
"""저장된 검색 문맥으로 답변을 생성하고 RAGAS 지표를 계산한다."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MODEL = "gpt-4o-mini"
EMBEDDING_MODEL = "text-embedding-3-small"
# - 공식 요금표의 일반 입력·출력 단가(USD/백만 토큰)를 비용 계산에 사용
INPUT_USD_PER_MILLION = 0.15
OUTPUT_USD_PER_MILLION = 0.60
EMBEDDING_USD_PER_MILLION = 0.02
METRICS = ("faithfulness", "answer_relevancy", "llm_context_precision_without_reference")


def read_rows(path: Path) -> tuple[list[dict], str]:
    """RAGAS 입력 행을 검증하고 재실행 확인용 해시 반환."""
    rows = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(rows, list) or not rows:
        raise ValueError("입력 JSON에는 검색 결과 행이 하나 이상 있어야 합니다.")
    for number, row in enumerate(rows, 1):
        if not isinstance(row, dict) or not isinstance(row.get("user_input"), str):
            raise ValueError(f"{number}번째 행의 user_input이 올바르지 않습니다.")
        contexts = row.get("retrieved_contexts")
        if not isinstance(contexts, list) or not contexts or not all(
            isinstance(context, str) and context.strip() for context in contexts
        ):
            raise ValueError(f"{number}번째 행의 retrieved_contexts가 올바르지 않습니다.")
    canonical = json.dumps(rows, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return rows, hashlib.sha256(canonical).hexdigest()


def load_progress(path: Path, rows: list[dict], input_hash: str) -> dict:
    """동일 입력의 이전 결과를 복원하거나 새 결과 파일 구조 생성."""
    if path.exists():
        progress = json.loads(path.read_text(encoding="utf-8"))
        if progress.get("input_sha256") != input_hash or progress.get("model") != MODEL:
            raise ValueError("기존 결과 파일의 입력 또는 모델이 다릅니다. 다른 --output 경로를 사용하세요.")
        # - 비용은 파일에 저장하지 않고 현재 실행에서만 누적
        progress.pop("usage", None)
        progress["total_cost_usd"] = 0.0
        return progress
    return {
        "input_sha256": input_hash,
        "model": MODEL,
        "embedding_model": EMBEDDING_MODEL,
        "rows": [
            {"stage": row.get("stage", ""), "user_input": row["user_input"],
             "retrieved_contexts": row["retrieved_contexts"],
             "response": row.get("response", ""), "scores": {}}
            for row in rows
        ],
        "total_cost_usd": 0.0,
    }


def save_progress(path: Path, progress: dict) -> None:
    """답변·점수만 JSON에 저장해 재실행 시 중복 호출 방지."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    public_result = {key: value for key, value in progress.items() if key != "total_cost_usd"}
    temporary.write_text(json.dumps(public_result, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def record_cost(progress: dict, model: str, input_tokens: int,
                output_tokens: int) -> None:
    """API 응답의 실제 토큰 수로 누적 예상 비용만 계산."""
    if model == EMBEDDING_MODEL:
        cost = input_tokens * EMBEDDING_USD_PER_MILLION / 1_000_000
    elif model == MODEL:
        cost = (input_tokens * INPUT_USD_PER_MILLION
                + output_tokens * OUTPUT_USD_PER_MILLION) / 1_000_000
    else:
        raise ValueError(f"요금표에 없는 모델입니다: {model}")
    progress["total_cost_usd"] += cost


def check_budget(progress: dict, limit_usd: float) -> None:
    """새 작업 시작 전에 누적 사용액이 사용자 지정 상한에 닿았는지 확인."""
    if progress["total_cost_usd"] >= limit_usd:
        raise RuntimeError(f"비용 상한 ${limit_usd:.4f}에 도달해 실행을 멈췄습니다.")


def generate_answer(client, row: dict, progress: dict) -> str:
    """검색된 문맥만 근거로 짧은 한국어 답변 생성."""
    contexts = "\n\n".join(
        f"[문맥 {index}] {context}"
        for index, context in enumerate(row["retrieved_contexts"], 1)
    )
    completion = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": (
                "제공된 문맥에 근거해 한국어로 간결하게 답하세요. "
                "문맥에서 확인할 수 없는 내용은 추측하지 말고 확인할 수 없다고 답하세요."
            )},
            {"role": "user", "content": f"질문: {row['user_input']}\n\n{contexts}"},
        ],
        temperature=0,
        max_completion_tokens=300,
    )
    usage = completion.usage
    if usage is None:
        raise RuntimeError("답변 생성 응답에 토큰 사용량이 없습니다.")
    record_cost(progress, MODEL, usage.prompt_tokens, usage.completion_tokens)
    choice = completion.choices[0]
    if choice.finish_reason != "stop" or not choice.message.content:
        raise RuntimeError(f"답변 생성이 완료되지 않았습니다: {choice.finish_reason}")
    return choice.message.content.strip()


async def evaluate_metric(client, row: dict, progress: dict, metric_name: str) -> float:
    """RAGAS 지표 하나를 계산하고 평가·임베딩 토큰 수 기록."""
    from langchain_core.embeddings import Embeddings
    from langchain_openai import ChatOpenAI
    from ragas import EvaluationDataset, aevaluate
    from ragas.cost import CostCallbackHandler, get_token_usage_for_openai
    from ragas.metrics import Faithfulness, ResponseRelevancy, LLMContextPrecisionWithoutReference
    from ragas.run_config import RunConfig

    class MeteredEmbeddings(Embeddings):
        """답변 관련성 지표의 임베딩 요청과 사용량을 연결."""

        def embed_documents(self, texts: list[str]) -> list[list[float]]:
            """여러 질문의 임베딩을 생성하고 사용 토큰 기록."""
            result = client.embeddings.create(model=EMBEDDING_MODEL, input=texts)
            record_cost(progress, EMBEDDING_MODEL, result.usage.prompt_tokens, 0)
            return [item.embedding for item in result.data]

        def embed_query(self, text: str) -> list[float]:
            """원래 질문을 임베딩하고 사용 토큰 기록."""
            return self.embed_documents([text])[0]

    metrics = {
        "faithfulness": Faithfulness(),
        "answer_relevancy": ResponseRelevancy(strictness=3),
        "llm_context_precision_without_reference": LLMContextPrecisionWithoutReference(),
    }
    llm = ChatOpenAI(model=MODEL, temperature=0, max_tokens=900,
                     max_retries=0, api_key=os.environ["OPENAI_API_KEY"])
    dataset = EvaluationDataset.from_list([{
        "user_input": row["user_input"],
        "retrieved_contexts": row["retrieved_contexts"],
        "response": row["response"],
    }])
    usage_callback = CostCallbackHandler(get_token_usage_for_openai)
    try:
        result = await aevaluate(
            dataset, metrics=[metrics[metric_name]], llm=llm,
            embeddings=MeteredEmbeddings(), callbacks=[usage_callback],
            run_config=RunConfig(max_workers=1, max_retries=1),
            raise_exceptions=True, show_progress=False,
        )
    finally:
        # - 평가 중 오류가 나도 응답받은 호출의 비용은 합계에 반영
        for usage in usage_callback.usage_data:
            if usage.input_tokens or usage.output_tokens:
                record_cost(progress, MODEL, usage.input_tokens, usage.output_tokens)
    if not usage_callback.usage_data or not any(
        usage.input_tokens or usage.output_tokens for usage in usage_callback.usage_data
    ):
        raise RuntimeError(f"{metric_name} 평가 토큰 수를 확인할 수 없습니다.")
    score = float(result.scores[0][metric_name])
    if not math.isfinite(score):
        raise RuntimeError(f"{metric_name} 점수가 유효하지 않습니다: {score}")
    return score


async def run_evaluation(args, rows: list[dict], progress: dict, client) -> None:
    """단일 이벤트 루프에서 모든 RAGAS 평가를 실행하고 결과 저장."""
    for index, row in enumerate(progress["rows"]):
        print(f"[{index + 1}/{len(rows)}] {row['stage']}: {row['user_input']}", flush=True)
        if not row["response"]:
            check_budget(progress, args.max_cost_usd)
            try:
                row["response"] = generate_answer(client, row, progress)
            finally:
                save_progress(args.output, progress)
        for metric_name in METRICS:
            if metric_name in row["scores"]:
                continue
            check_budget(progress, args.max_cost_usd)
            try:
                row["scores"][metric_name] = await evaluate_metric(
                    client, row, progress, metric_name
                )
            finally:
                save_progress(args.output, progress)
            print(f"  {metric_name}: {row['scores'][metric_name]:.3f}", flush=True)
        print(f"  누적 예상 비용: ${progress['total_cost_usd']:.6f}", flush=True)

    print(f"완료: {args.output}\n총 예상 비용: ${progress['total_cost_usd']:.6f}")


def main() -> None:
    """입력 확인 후 단계별 답변 생성·평가와 사용량 저장."""
    import asyncio

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=ROOT / "data/ragas_input.json")
    parser.add_argument("--output", type=Path, default=ROOT / "data/ragas_results.json")
    parser.add_argument("--max-cost-usd", type=float, default=0.10,
                        help="현재 실행에서 새 작업 시작 전 비용 검사 기준(기본 $0.10)")
    parser.add_argument("--dry-run", action="store_true", help="API 호출 없이 입력만 확인")
    args = parser.parse_args()
    if args.max_cost_usd <= 0:
        parser.error("--max-cost-usd는 0보다 커야 합니다.")

    rows, input_hash = read_rows(args.input)
    progress = load_progress(args.output, rows, input_hash)
    if args.dry_run:
        print(f"평가 대상: {len(rows)}행 / 모델: {MODEL} / 비용 검사 기준: ${args.max_cost_usd:.2f}")
        print("현재 실행 예상 비용: $0.000000 (API 호출 없음)")
        return

    from dotenv import load_dotenv
    from openai import OpenAI
    # - 실습 폴더의 .env 키를 우선 사용해 오래된 터미널 키와 혼동 방지
    load_dotenv(ROOT / ".env", override=True)
    if not os.environ.get("OPENAI_API_KEY"):
        parser.error("OPENAI_API_KEY가 없습니다. .env 파일 또는 터미널 환경변수에 설정하세요.")
    client = OpenAI(max_retries=0, timeout=60)
    save_progress(args.output, progress)
    asyncio.run(run_evaluation(args, rows, progress, client))


if __name__ == "__main__":
    from openai import AuthenticationError

    try:
        main()
    except AuthenticationError:
        raise SystemExit("OpenAI API 키 인증 실패(401): .env의 OPENAI_API_KEY를 확인하세요.") from None
