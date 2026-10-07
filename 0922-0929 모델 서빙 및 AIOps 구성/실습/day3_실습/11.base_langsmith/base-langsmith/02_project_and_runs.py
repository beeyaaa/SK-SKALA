"""2단계: Project 단위로 Run이 실제로 모여 있는지 확인한다.
LANGSMITH.md 4번 "Run들을 묶은 Project"를 실제 API로 검증한다.
"""
import os
from langsmith import Client

PROJECT = os.environ["LANGCHAIN_PROJECT"]

if __name__ == "__main__":
    client = Client()

    proj = client.read_project(project_name=PROJECT)
    print(f"=== Project 정보 ===")
    print(f"id={proj.id} name={proj.name}")

    runs = list(client.list_runs(project_name=PROJECT, run_type="chain", limit=20))
    print(f"\n=== 이 Project에 속한 Run {len(runs)}개 (실제 조회) ===")
    for r in sorted(runs, key=lambda x: x.start_time):
        q = None
        if r.inputs and "question" in r.inputs:
            q = r.inputs["question"]
        print(f"- {r.start_time} | status={r.status} | tokens={r.total_tokens} | input={q}")
