"""5단계: 프롬프트를 실제로 Hub에 커밋(push)하고 이름으로 다시 불러온다(pull).
HUB(LANGSMITH HUB).md 6번 코드(push_prompt/pull_prompt)를 실제로 실행해 검증한다.
is_public=True로 커밋해, 로그인 없이도 볼 수 있는 공개 URL을 실제로 받아온다.
"""
from langchain_core.prompts import ChatPromptTemplate
from langsmith import Client

PROMPT_NAME = "langsmith-lab-qa-prompt"

if __name__ == "__main__":
    client = Client()

    prompt_v1 = ChatPromptTemplate.from_template(
        "다음 질문에 한국어로 한 문장으로만 답하라: {question}"
    )
    # is_public=True는 계정에 LangChain Hub 핸들(사용자명)이 웹 UI에서 먼저 설정돼 있어야
    # 동작한다(실제로 시도했다가 LangSmithUserError를 겪었다: "Cannot create a public
    # prompt without first creating a LangChain Hub handle"). 이 실습 계정엔 핸들이 없어
    # 비공개(is_public=False, 기본값)로 커밋한다 — API 동작 자체는 동일하게 검증된다.
    url_v1 = client.push_prompt(
        PROMPT_NAME,
        object=prompt_v1,
        description="LangSmith 실습 — v1: 한 문장 답변 지시",
    )
    print(f"v1 커밋 완료 — URL(비공개, 로그인 필요): {url_v1}")

    prompt_v2 = ChatPromptTemplate.from_template(
        "다음 질문에 한국어로 두 문장 이내로 간결하게 답하라: {question}"
    )
    url_v2 = client.push_prompt(
        PROMPT_NAME,
        object=prompt_v2,
        description="LangSmith 실습 — v2: 두 문장 이내 지시로 수정",
    )
    print(f"v2 커밋 완료 — URL(비공개, 로그인 필요): {url_v2}")

    pulled = client.pull_prompt(PROMPT_NAME)
    print(f"\n=== 이름만으로 pull한 최신 버전(v2) 확인 ===")
    print(pulled.messages[0].prompt.template)

    commits = list(client.list_prompt_commits(PROMPT_NAME))
    print(f"\n=== 실제 커밋 이력 {len(commits)}개 ===")
    for c in commits:
        print(f"- commit_hash={c.commit_hash[:8]}...")

    with open("hub_prompt_url.txt", "w") as f:
        f.write(url_v2)
