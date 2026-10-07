import os
from openai import OpenAI

client = OpenAI(
    base_url=os.getenv("OPENAI_BASE_URL", "http://127.0.0.1:8000/v1"),
    api_key=os.environ["VLLM_API_KEY"],
    timeout=30,
    max_retries=2,
)
stream = client.chat.completions.create(
    model=os.getenv("SERVED_MODEL_NAME", "assistant"),
    messages=[{"role": "user", "content": "모델 서빙을 한 문장으로 설명해줘."}],
    max_tokens=64,
    temperature=0,  # greedy decoding — 지정하지 않으면 vLLM 기본 샘플링(temperature=1.0류)이
                     # 적용돼, 같은 컨테이너 안에서 몇 번째 추론 요청이냐에 따라 결과가 크게
                     # 흔들린다(실제로 관찰됨: README "원인 분석" 참고). 데모의 재현성을 위해 고정.
    stream=True,
)
for chunk in stream:
    print(chunk.choices[0].delta.content or "", end="", flush=True)
print()
