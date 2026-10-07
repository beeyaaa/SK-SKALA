"""3단계: 특정 Run에 실제로 피드백을 남기고 다시 읽어온다.
LANGSMITH.md 6번 코드의 client.create_feedback(...) 예시를 그대로 실행한다.
"""
import json
from langsmith import Client

if __name__ == "__main__":
    client = Client()

    with open("run_ids.json") as f:
        run_ids = json.load(f)

    target_run_id = run_ids[0]
    print(f"대상 Run: {target_run_id}")

    fb = client.create_feedback(
        run_id=target_run_id,
        key="user_thumbs",
        score=1,
        comment="실습 스크립트에서 남긴 실제 피드백 — RAG 정의 응답이 정확했는지 평가",
    )
    print(f"\n=== 생성된 Feedback (실제 서버 응답) ===")
    print(f"id={fb.id} key={fb.key} score={fb.score} comment={fb.comment}")

    fetched = list(client.list_feedback(run_ids=[target_run_id]))
    print(f"\n=== 해당 Run의 Feedback 목록 재조회 ({len(fetched)}건) ===")
    for f in fetched:
        print(f"- key={f.key} score={f.score} comment={f.comment}")
