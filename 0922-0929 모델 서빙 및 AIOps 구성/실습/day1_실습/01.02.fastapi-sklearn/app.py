"""
2단계: FastAPI + pickle로 model.pkl을 실제 HTTP 서비스로 띄운다.

핵심 포인트 — lifespan에서 pickle.load()로 RandomForestClassifier를 프로세스
생애주기 동안 딱 한 번만 로드해 전역 상태에 두고, 요청마다 그 객체를 재사용한다
(요청마다 pickle.load()를 다시 부르면 매번 디스크 I/O + 역직렬화 비용을 치르게
된다 — 실제 서빙에서 흔히 하는 실수). RandomForestClassifier는 자체적으로
전처리를 요구하지 않으므로, ONNX/PyTorch 예시의 scaler.npz 같은 보조 파일이
필요 없다 — model.pkl 하나가 학습된 트리 구조까지 전부 담고 있다.
"""

import pickle
from contextlib import asynccontextmanager
from time import perf_counter

import numpy as np
import sklearn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

IRIS_CLASS_NAMES = ["setosa", "versicolor", "virginica"]

ml_state: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- startup: model.pkl을 프로세스 생애주기 동안 한 번만 로드 ---
    with open("model.pkl", "rb") as f:
        model = pickle.load(f)
    ml_state["model"] = model
    print(f"[startup] pickle 로드 완료: model.pkl ({type(model).__name__})")
    print(f"[startup] scikit-learn 버전: {sklearn.__version__}")
    print(f"[startup] n_estimators={model.n_estimators}, classes_={list(model.classes_)}")
    yield
    # --- shutdown: 정리할 리소스 없음(GC에 맡김) ---
    ml_state.clear()


app = FastAPI(title="Iris scikit-learn pickle API", lifespan=lifespan)


class IrisFeatures(BaseModel):
    sepal_length_cm: float = Field(..., ge=0, description="꽃받침 길이(cm)")
    sepal_width_cm: float = Field(..., ge=0, description="꽃받침 너비(cm)")
    petal_length_cm: float = Field(..., ge=0, description="꽃잎 길이(cm)")
    petal_width_cm: float = Field(..., ge=0, description="꽃잎 너비(cm)")


class PredictResponse(BaseModel):
    predicted_class: str
    probabilities: dict
    latency_ms: float


@app.get("/health")
def health():
    if "model" not in ml_state:
        raise HTTPException(status_code=503, detail="model not loaded")
    model = ml_state["model"]
    return {
        "status": "ok",
        "scikit_learn_version": sklearn.__version__,
        "model_type": type(model).__name__,
        "n_estimators": model.n_estimators,
    }


@app.post("/predict", response_model=PredictResponse)
def predict(features: IrisFeatures):
    # RandomForestClassifier는 학습 때 쓴 원본 cm 단위 값을 그대로 받는다 —
    # ONNX/PyTorch 예시처럼 별도 표준화(scaler)를 재현할 필요가 없다.
    raw = np.array(
        [[
            features.sepal_length_cm,
            features.sepal_width_cm,
            features.petal_length_cm,
            features.petal_width_cm,
        ]]
    )

    model = ml_state["model"]
    t0 = perf_counter()
    probs = model.predict_proba(raw)[0]
    latency_ms = (perf_counter() - t0) * 1000

    pred_idx = int(probs.argmax())

    return PredictResponse(
        predicted_class=IRIS_CLASS_NAMES[pred_idx],
        probabilities={name: round(float(p), 4) for name, p in zip(IRIS_CLASS_NAMES, probs)},
        latency_ms=round(latency_ms, 4),
    )
