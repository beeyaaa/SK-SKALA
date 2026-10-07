
import argparse
import json
import re
from pathlib import Path

from dotenv import load_dotenv
from langchain_community.retrievers import BM25Retriever
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from openai import AuthenticationError

from insurance_terms import load_policy_articles

ROOT = Path(__file__).resolve().parents[1]
PDF = ROOT / "data/Sample_Automobile_Insurance_Policy_Terms.pdf"
RESULTS = ROOT / "results"
TOP_K = 3
FETCH_K = 8
NO_ANSWER = "제공된 약관에서 확인할 수 없습니다."

TEST_CASES = [
    ("Q1", "자기차량손해의 자기부담금 비율과 최소·최대 금액은 얼마인가요?", ["제10조"], "direct"),
    ("Q2", "전기차를 빌린 경우 하루 대차료 한도와 최대 인정기간은?", ["제7조"], "direct"),
    ("Q3", "상대방 차량의 수리비 외에 대물배상에서 인정될 수 있는 비용은?", ["제6조"], "paraphrase"),
    ("Q4", "사고와 관계없는 노후·부식 손상도 자차 보험금으로 처리되나요?", ["제12조"], "paraphrase"),
    ("Q5", "보험금 산정 시 요구할 수 있는 자료에는 무엇이 있나요?", ["제15조"], "direct"),
    ("Q6", "충돌 위치나 담보 가입 여부가 불확실하면 지급은 어떻게 하나요?", ["제14조"], "paraphrase"),
    ("Q7", "제16조에서 최종 지급액의 천 원 미만 금액은 어떻게 처리하나요?", ["제16조"], "article_number"),
    ("Q8", "판례·법률과 보험증권·약관은 각각 무엇을 결정하며, AI가 산출한 지급액은 언제 확정되나요?", ["제4조", "제17조"], "composite"),
    ("Q9", "대물배상 지급액 산식과 자기차량손해 공제 전 보상액 산식을 각각 알려주세요.", ["제6조", "제9조"], "composite"),
    ("Q10", "무사고 운전 시 월 보험료 할인율은 얼마인가요?", [], "unsupported"),
]


def tokenize(text: str) -> list[str]:
    """Keep Korean words, article numbers, Latin abbreviations and numerals."""
    return re.findall(r"[가-힣]+|[a-z]+|\d+", text.lower())


class HybridRetriever:
    """Fuse semantic and lexical ranks, then return distinct articles."""

    def __init__(self, vectorstore, documents):
        self.vectorstore = vectorstore
        self.bm25 = BM25Retriever.from_documents(documents, preprocess_func=tokenize)
        self.bm25.k = FETCH_K

    def invoke(self, question: str):
        semantic = self.vectorstore.similarity_search(question, k=FETCH_K)
        lexical = self.bm25.invoke(question)
        scores = {}
        by_article = {}
        for docs in (semantic, lexical):
            for rank, doc in enumerate(docs, start=1):
                article = doc.metadata["article"]
                scores[article] = scores.get(article, 0.0) + 1 / (60 + rank)
                by_article[article] = doc
        ranked = sorted(scores, key=lambda article: (-scores[article], article))
        return [by_article[article] for article in ranked[:TOP_K]]


def build_index(embeddings=None):
    articles = load_policy_articles(PDF)
    chunks = RecursiveCharacterTextSplitter(
        chunk_size=400, chunk_overlap=40,
    ).split_documents(articles)
    if embeddings is None:
        embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vectorstore = FAISS.from_documents(chunks, embeddings)
    return articles, chunks, vectorstore


def evaluate_retrieval(name, retriever, test_cases=TEST_CASES):
    records = []
    for case_id, question, gold, case_type in test_cases:
        docs = retriever.invoke(question)
        articles = [doc.metadata["article"] for doc in docs]
        hit = set(gold).issubset(articles) if gold else None
        context = "\n\n".join(
            f"[{doc.metadata['article']}: {doc.metadata['article_title']}, "
            f"PDF {doc.metadata['pdf_page']}쪽]\n{doc.page_content}"
            for doc in docs
        )
        records.append({
            "id": case_id, "type": case_type, "question": question,
            "gold_articles": gold, "retrieved_articles": articles,
            "hit": hit, "context": context,
        })
        print(f"{name} {case_id}: gold={gold or 'unsupported'} top_{TOP_K}={articles} hit={hit}")
    answerable = [record for record in records if record["hit"] is not None]
    hits = sum(record["hit"] for record in answerable)
    hit_rate = hits / len(answerable)
    print(f"{name} Hit@{TOP_K}: {hits}/{len(answerable)} = {hit_rate:.3f}")
    return {"name": name, "hit_at_k": hit_rate, "cases": records}


def generate_answers(result, llm):
    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "당신은 실습용 가상 자동차보험 약관의 검색 도우미입니다. "
         "검색된 조항에 명시된 내용만 사용해 질문의 조건에 맞게 직접 답하세요. "
         "질문을 뒷받침하는 조항이 문맥에 있으면 그 내용을 답해야 합니다. "
         "보상 여부를 묻는 질문에서 면책·제외 조항도 답의 근거입니다. "
         "해당 손해가 보상 제외라고 적혀 있으면 '보상하지 않습니다'라고 설명하세요. "
         f"관련 근거가 전혀 없을 때만 정확히 '{NO_ANSWER}'라고 답하세요. "
         "답변 끝에는 실제 답변에 사용한 조항 번호만 표시하세요. "
         "약관의 일반 규칙은 설명할 수 있지만 개별 사고의 지급액이나 과실비율은 확정하지 마세요."
         "\n\n검색된 조항:\n{context}"),
        ("human", "{question}"),
    ])
    for record in result["cases"]:
        response = llm.invoke(prompt.invoke({
            "question": record["question"], "context": record["context"],
        }))
        record["answer"] = response.content
        # Automatic check is limited to abstention; groundedness needs human review.
        if record["type"] == "unsupported":
            record["abstained"] = NO_ANSWER in response.content
        print(f"{result['name']} {record['id']} answer: {response.content}")


def save_result(name: str, result):
    RESULTS.mkdir(exist_ok=True)
    path = RESULTS / name
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved: {path}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline-only", action="store_true")
    parser.add_argument("--retrieval-only", action="store_true")
    args = parser.parse_args()

    load_dotenv(ROOT / ".env", override=True)
    articles, chunks, vectorstore = build_index()
    print(f"Policy articles: {len(articles)}, indexed chunks: {len(chunks)}")
    print(f"First chunk metadata: {chunks[0].metadata}")
    baseline = vectorstore.as_retriever(
        search_type="similarity", search_kwargs={"k": TOP_K},
    )
    baseline_result = evaluate_retrieval("Baseline Similarity", baseline)
    if args.baseline_only:
        save_result("baseline.json", baseline_result)
        return

    improved = HybridRetriever(vectorstore, chunks)
    improved_result = evaluate_retrieval("Candidate Hybrid", improved)
    if not args.retrieval_only:
        llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        generate_answers(baseline_result, llm)
        generate_answers(improved_result, llm)
    save_result("baseline.json", baseline_result)
    save_result("comparison.json", {
        "policy": PDF.name,
        "chunk_size": 400, "chunk_overlap": 40,
        "embedding": "text-embedding-3-small", "top_k": TOP_K,
        "baseline": baseline_result,
        "candidate": improved_result,
    })


if __name__ == "__main__":
    try:
        main()
    except AuthenticationError:
        raise SystemExit(
            "OpenAI 인증에 실패했습니다. 현재 OPENAI_API_KEY를 확인하세요."
        ) from None
