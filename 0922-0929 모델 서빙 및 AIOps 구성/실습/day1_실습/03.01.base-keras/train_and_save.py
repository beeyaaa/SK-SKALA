"""
1단계: Keras 3(TensorFlow 백엔드)로 붓꽃(Iris) 분류 모델을 학습하고 .keras 파일로 저장한다.

핵심 포인트 — `tensorflow.keras`가 아니라 독립 패키지 `keras`(3.x)를 쓰되,
백엔드를 KERAS_BACKEND=tensorflow로 고정한다(환경변수는 keras를 import하기
*전에* 설정돼야 하고, import 이후엔 바꿀 수 없다). 학습이 끝난 모델은
`model.save("iris_model.keras")` 한 줄로 Keras v3 네이티브 포맷에 저장되는데,
이 파일 하나에 아키텍처+가중치+컴파일 설정이 전부 담긴다 — 그래서 2단계
(predict_from_saved.py)는 build_model() 같은 모델 정의 코드를 아예 갖지 않고도
load_model()만으로 완전한 모델을 복원할 수 있다.
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
    """4개 특성(꽃받침/꽃잎 길이·너비) -> 3개 클래스(붓꽃 품종)로 분류하는 작은 MLP.

    base-sklearn·base-pytorch·TENSORFLOW/base와 같은 문제, 같은 4->16->8->3 구조 —
    프레임워크별 저장/복원 경로를 나란히 비교할 수 있게 했다.
    """
    return keras.Sequential([
        keras.layers.Input(shape=(4,)),
        keras.layers.Dense(16, activation="relu"),
        keras.layers.Dense(8, activation="relu"),
        keras.layers.Dense(3),
    ])


def main():
    keras.utils.set_random_seed(0)
    print(f"[Keras] 버전: {keras.__version__}, 백엔드: {keras.backend.backend()}")

    # 1) 데이터 준비 — base-sklearn·base-pytorch와 동일한 Iris 분할
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

    # 3) 학습 직후(같은 프로세스) 정확도 확인 — 2단계 결과와 비교할 기준값
    pred = model.predict(X_test_scaled, verbose=0).argmax(axis=1)
    acc_inproc = float((pred == y_test).mean())
    print(f"[학습 직후] 테스트 정확도: {acc_inproc:.4f} ({int((pred == y_test).sum())}/{len(y_test)})")

    # 4) Keras v3 네이티브 포맷으로 저장 — 아키텍처+가중치+컴파일 설정 전부 포함
    model.save("iris_model.keras")
    print("[Keras] 저장 완료: iris_model.keras")

    # 5) 다음 단계(predict_from_saved.py)가 재사용할 테스트 데이터·기준 정확도 저장
    np.savez("test_data.npz", X_test=X_test_scaled, y_test=y_test, acc_inproc=acc_inproc)
    print("[데이터] 테스트셋 저장 완료: test_data.npz")


if __name__ == "__main__":
    t0 = time.time()
    main()
    print(f"\n총 소요 시간: {time.time() - t0:.2f}s")
