"""LANGSMITH.md 6번 코드와 동일한 패턴 — LangChain 체인 하나를 만든다.
LLM은 유료 API 대신 로컬 Ollama(qwen2.5:0.5b)를 사용한다(이 저장소 다른 LLMOps 실습과 동일한 이유:
API 키 없이도 실제 모델 호출·실제 토큰 사용량을 만들어내기 위함).
"""
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama

OLLAMA_MODEL = "qwen2.5:0.5b"

prompt = ChatPromptTemplate.from_template(
    "다음 질문에 한국어로 두 문장 이내로 간결하게 답하라: {question}"
)
llm = ChatOllama(model=OLLAMA_MODEL, temperature=0)
chain = prompt | llm
