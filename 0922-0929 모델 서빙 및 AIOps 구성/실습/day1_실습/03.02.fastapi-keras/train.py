"""
1단계: Keras(TensorFlow 백엔드)로 붓꽃(Iris) 분류 모델을 학습하고 저장한다.

_통합개념_실습/KERAS/base-keras와 같은 모델(keras.Sequential, 4->16->8->3)을 쓰되,
이번엔 백엔드를 KERAS_BACKEND=tensorflow로 고정하고, FastAPI 서빙까지 포함한다.
학습 때 쓴 StandardScaler의 mean_/scale_도 scaler.npz로 함께 저장한다 —
app.py(서빙 쪽)는 sklearn을 아예 import하지 않고 이 두 배열만으로 표준화를
재현한다(ONNX/base_fastapi·PYTORCH/fastapi-pytorch과 동일한 설계).
"""

import os

# keras를 import하기 전에 반드시 설정 — import 이후엔 백엔드를 바꿀 수 없다.
os.environ.setdefault("KERAS_BACKEND", "tensorflow")

import time

import keras
import numpy as np
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler


def build_model() -> keras.Model:
    """4개 특성(꽃받침/꽃잎 길이·너비) -> 3개 클래스(붓꽃 품종)로 분류하는 작은 MLP."""
    return keras.Sequential([
        keras.layers.Input(shape=(4,)),
        keras.layers.Dense(16, activation="relu"),
        keras.layers.Dense(8, activation="relu"),
        keras.layers.Dense(3),
    ])


def main():
    keras.utils.set_random_seed(0)
    print(f"[Keras] 버전: {keras.__version__}, 백엔드: {keras.backend.backend()}")

    # 1) 데이터 준비 — KERAS/base-keras·TENSORFLOW/base와 동일한 Iris 분할
    X, y = load_iris(return_X_y=True)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=0, stratify=y
    )
    scaler = StandardScaler().fit(X_train)
    X_train_scaled = scaler.transform(X_train).astype(np.float32)
    X_test_scaled = scaler.transform(X_test).astype(np.float32)

    # 2) 학습
    model = build_model()
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=0.05),
        loss=keras.losses.SparseCategoricalCrossentropy(from_logits=True),
        metrics=["accuracy"],
    )
    model.fit(X_train_scaled, y_train, epochs=200, verbose=0)

    # 3) 테스트 정확도 확인
    test_loss, test_acc = model.evaluate(X_test_scaled, y_test, verbose=0)
    print(f"[Keras/{keras.backend.backend()}] 테스트 정확도: {test_acc:.4f}")

    # 4) 모델 저장 — Keras v3 네이티브 포맷(아키텍처+가중치)
    model.save("iris_model.keras")
    print("[Keras] 저장 완료: iris_model.keras")

    # 5) FastAPI 서빙(app.py)이 학습 때와 동일하게 표준화를 재현할 수 있도록
    #    StandardScaler의 mean_/scale_을 그대로 저장 — sklearn 없이도 복원 가능
    np.savez("scaler.npz", mean=scaler.mean_.astype(np.float32), scale=scaler.scale_.astype(np.float32))
    print("[Scaler] 저장 완료: scaler.npz (mean, scale)")


if __name__ == "__main__":
    t0 = time.time()
    main()
    print(f"\n총 소요 시간: {time.time() - t0:.2f}s")
