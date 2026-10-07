"""1단계: chain.invoke()만으로 Run이 자동 기록되는지 실제로 확인한다.
langsmith의 collect_runs() 컨텍스트로 방금 만들어진 Run ID를 코드에서 직접 받아온다.
"""
import json
import time
from langsmith import Client
from langchain_core.tracers.context import collect_runs
from langchain_core.tracers.langchain import wait_for_all_tracers

from chain_setup import chain

QUESTIONS = [
    "RAG란 무엇인가?",
    "LangSmith의 Run은 무엇을 기록하는가?",
    "벡터 데이터베이스는 왜 필요한가?",
]

if __name__ == "__main__":
    client = Client()
    run_ids = []

    with collect_runs() as cb:
        for q in QUESTIONS:
            result = chain.invoke({"question": q})
            print(f"Q: {q}\nA: {result.content}\n")

    for run in cb.traced_runs:
        run_ids.append(str(run.id))

    print("=== 실제로 생성된 Run ID ===")
    for rid in run_ids:
        print(rid)

    with open("run_ids.json", "w") as f:
        json.dump(run_ids, f, indent=2)

    # LangSmith SDK는 Run을 백그라운드 스레드에서 배치로 서버에 전송한다.
    # invoke()가 반환된 시점엔 아직 서버에 도달하지 않았을 수 있어, flush + 재시도로 기다린다.
    # (실제로 flush 없이 바로 read_run()을 호출했다가 404 Not Found를 겪고 이 부분을 추가했다.)
    wait_for_all_tracers()
    client.flush()

    print("\n=== 서버에서 방금 그 Run을 다시 조회 ===")
    for rid in run_ids:
        r = None
        for attempt in range(10):
            try:
                r = client.read_run(rid)
                break
            except Exception:
                time.sleep(1.5)
        if r is None:
            print(f"- id={rid} 조회 실패(서버 반영 지연) — 재시도 초과")
            continue
        latency = (r.end_time - r.start_time).total_seconds() if r.end_time else None
        print(f"- id={r.id} name={r.name} status={r.status} "
              f"latency={latency}s total_tokens={r.total_tokens}")
