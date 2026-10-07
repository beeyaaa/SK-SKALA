"""
2단계: Keras(TensorFlow 백엔드)로 저장한 iris_model.keras를 FastAPI로 서빙한다.

핵심 포인트 — KERAS_BACKEND는 keras를 import하기 *전에* 결정돼야 하므로, 이
파일 맨 위(다른 import보다 먼저)에서 환경변수를 강제로 tensorflow로 고정한다.
lifespan에서 model·scaler를 프로세스 시작 시 1회만 로드해 요청마다의 로딩
비용을 없앤다(ONNX/base_fastapi·PYTORCH/fastapi-pytorch과 동일한 설계).
"""

import os

# 다른 어떤 import보다도 먼저 실행돼야 한다 — keras가 import되는 순간
# 백엔드가 확정되고 이후엔 바꿀 수 없다(uvicorn 워커가 이 모듈을 처음 로드할
# 때 keras가 아직 import되지 않은 상태여야 이 설정이 실제로 적용된다).
os.environ.setdefault("KERAS_BACKEND", "tensorflow")

from contextlib import asynccontextmanager
from time import perf_counter

import keras
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

IRIS_CLASS_NAMES = ["setosa", "versicolor", "virginica"]

ml_state: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- startup: model·scaler를 프로세스 생애주기 동안 한 번만 로드 ---
    model = keras.models.load_model("iris_model.keras")
    scaler = np.load("scaler.npz")
    ml_state["model"] = model
    ml_state["mean"] = scaler["mean"]
    ml_state["scale"] = scaler["scale"]
    print(f"[startup] Keras 모델 로드 완료 (keras {keras.__version__}, 백엔드={keras.backend.backend()})")
    yield
    # --- shutdown: 정리할 리소스 없음 ---
    ml_state.clear()


app = FastAPI(title="Iris Keras(TensorFlow backend) API", lifespan=lifespan)


class IrisFeatures(BaseModel):
    sepal_length_cm: float = Field(..., ge=0, description="꽃받침 길이(cm)")
    sepal_width_cm: float = Field(..., ge=0, description="꽃받침 너비(cm)")
    petal_length_cm: float = Field(..., ge=0, description="꽃잎 길이(cm)")
    petal_width_cm: float = Field(..., ge=0, description="꽃잎 너비(cm)")


class PredictResponse(BaseModel):
    predicted_class: str
    probabilities: dict
    latency_ms: float


def softmax(logits: np.ndarray) -> np.ndarray:
    e = np.exp(logits - logits.max(axis=-1, keepdims=True))
    return e / e.sum(axis=-1, keepdims=True)


@app.get("/health")
def health():
    if "model" not in ml_state:
        raise HTTPException(status_code=503, detail="model not loaded")
    return {
        "status": "ok",
        "keras_version": keras.__version__,
        "keras_backend": keras.backend.backend(),
    }


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
    # 학습 때와 동일한 표준화: (x - mean) / scale — sklearn 없이 numpy만으로 재현
    scaled = (raw - ml_state["mean"]) / ml_state["scale"]

    t0 = perf_counter()
    logits = ml_state["model"].predict(scaled, verbose=0)
    latency_ms = (perf_counter() - t0) * 1000

    probs = softmax(logits)[0]
    pred_idx = int(probs.argmax())

    return PredictResponse(
        predicted_class=IRIS_CLASS_NAMES[pred_idx],
        probabilities={name: round(float(p), 4) for name, p in zip(IRIS_CLASS_NAMES, probs)},
        latency_ms=round(latency_ms, 4),
    )
