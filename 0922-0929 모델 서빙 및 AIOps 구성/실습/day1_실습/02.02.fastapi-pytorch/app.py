"""
2단계: torch.jit.load()로 불러온 TorchScript 모델을 FastAPI로 서빙한다.

ONNX/base_fastapi(app.py)가 onnxruntime.InferenceSession으로 서빙하는 것과
정확히 같은 자리에서, 이번에는 torch.jit.load()로 불러온 ScriptModule을 쓴다.
_통합개념_실습/PYTORCH/base-pytorch의 핵심(IrisNet 클래스 정의를 몰라도
iris_model.pt 하나만으로 추론 가능)이 서빙 상황에서도 그대로 성립함을 보여준다
— 이 파일 어디에도 `class IrisNet`이 없다.

lifespan으로 모델·스케일러를 프로세스 시작 시 1회만 로드해 요청마다의
로딩 비용을 없앤다(ONNX/base_fastapi와 동일한 설계).
"""

from contextlib import asynccontextmanager

import numpy as np
import torch
from fastapi import FastAPI
from pydantic import BaseModel, Field

CLASS_NAMES = ["setosa", "versicolor", "virginica"]

ml_state: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # torch.jit.load()는 iris_model.pt 안에 저장된 연산 그래프 자체로 모델을
    # 복원한다 — IrisNet 클래스 정의가 이 프로세스에 없어도 동작한다.
    model = torch.jit.load("iris_model.pt")
    model.eval()
    torch.set_grad_enabled(False)  # 서빙 프로세스 전체에서 autograd 비활성화

    scaler = np.load("scaler.npz")
    ml_state["model"] = model
    ml_state["mean"] = scaler["mean"]
    ml_state["scale"] = scaler["scale"]
    print(f"[lifespan] TorchScript 모델 로드 완료 (torch {torch.__version__})")

    yield

    ml_state.clear()
    print("[lifespan] 모델 리소스 해제 완료")


app = FastAPI(title="Iris Classifier (TorchScript)", lifespan=lifespan)


class IrisFeatures(BaseModel):
    sepal_length_cm: float = Field(..., ge=0, le=15, description="꽃받침 길이(cm)")
    sepal_width_cm: float = Field(..., ge=0, le=15, description="꽃받침 너비(cm)")
    petal_length_cm: float = Field(..., ge=0, le=15, description="꽃잎 길이(cm)")
    petal_width_cm: float = Field(..., ge=0, le=15, description="꽃잎 너비(cm)")


class PredictResponse(BaseModel):
    predicted_class: str
    predicted_index: int
    probabilities: dict[str, float]


@app.get("/health")
def health():
    return {"status": "ok", "model_loaded": "model" in ml_state, "runtime": "torchscript"}


@app.post("/predict", response_model=PredictResponse)
def predict(features: IrisFeatures):
    raw = np.array(
        [[
            features.sepal_length_cm,
            features.sepal_width_cm,
            features.petal_length_cm,
            features.petal_width_cm,
        ]],
        dtype=np.float32,
    )
    scaled = (raw - ml_state["mean"]) / ml_state["scale"]

    x = torch.from_numpy(scaled)
    with torch.no_grad():
        logits = ml_state["model"](x)
    probs = torch.softmax(logits, dim=1)[0].numpy()

    idx = int(probs.argmax())
    return PredictResponse(
        predicted_class=CLASS_NAMES[idx],
        predicted_index=idx,
        probabilities={name: float(p) for name, p in zip(CLASS_NAMES, probs)},
    )
