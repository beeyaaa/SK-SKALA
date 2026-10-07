"""4단계: 평가용 Dataset을 실제로 만들고 evaluate()로 반복 실행한다.
LANGSMITH.md 3번 "데이터셋을 만들어 evaluate()로 실험을 반복 실행" 문장을 실제로 검증한다.
평가자는 결정론적인 키워드 포함 여부로 구성해, LLM-judge 없이도 재현 가능한 점수를 만든다.
"""
from langsmith import Client
from langsmith.evaluation import evaluate

from chain_setup import chain

DATASET_NAME = "langsmith-lab-qa-dataset"

EXAMPLES = [
    {"inputs": {"question": "RAG란 무엇인가?"}, "outputs": {"must_contain": ["검색", "생성"]}},
    {"inputs": {"question": "벡터 데이터베이스는 왜 필요한가?"}, "outputs": {"must_contain": ["벡터"]}},
    {"inputs": {"question": "LangSmith의 Run은 무엇을 기록하는가?"}, "outputs": {"must_contain": ["기록"]}},
]


def target(inputs: dict) -> dict:
    result = chain.invoke({"question": inputs["question"]})
    return {"answer": result.content}


def keyword_match_evaluator(run, example) -> dict:
    """정답 키워드가 실제 응답에 포함돼 있는지 확인하는 결정론적 평가자(LLM judge 아님)."""
    answer = run.outputs.get("answer", "") if run.outputs else ""
    must_contain = example.outputs.get("must_contain", [])
    hit = any(kw in answer for kw in must_contain)
    return {"key": "keyword_match", "score": 1.0 if hit else 0.0,
            "comment": f"must_contain={must_contain}"}


if __name__ == "__main__":
    client = Client()

    if client.has_dataset(dataset_name=DATASET_NAME):
        print(f"기존 Dataset 재사용: {DATASET_NAME}")
        dataset = client.read_dataset(dataset_name=DATASET_NAME)
    else:
        dataset = client.create_dataset(
            dataset_name=DATASET_NAME,
            description="LangSmith 실습용 QA 데이터셋 — 키워드 포함 여부로 채점",
        )
        client.create_examples(dataset_id=dataset.id, examples=EXAMPLES)
        print(f"신규 Dataset 생성: {dataset.id}")

    print(f"\n=== Dataset의 실제 예제 목록 ===")
    for ex in client.list_examples(dataset_id=dataset.id):
        print(f"- inputs={ex.inputs} outputs={ex.outputs}")

    print(f"\n=== evaluate() 실행 (실제 Ollama 호출 {len(EXAMPLES)}건) ===")
    results = evaluate(
        target,
        data=DATASET_NAME,
        evaluators=[keyword_match_evaluator],
        experiment_prefix="qwen2.5-0.5b-baseline",
        max_concurrency=1,
    )

    print("\n=== 실험 결과 (실제 점수) ===")
    total, hits = 0, 0
    for row in results:
        total += 1
        run = row["run"]
        eval_results = row["evaluation_results"]["results"]
        for er in eval_results:
            hits += er.score
            print(f"- Q: {row['example'].inputs['question']!r} "
                  f"score={er.score} comment={er.comment}")
    print(f"\n총 {total}건 중 keyword_match 평균 점수: {hits/total:.2f}")
