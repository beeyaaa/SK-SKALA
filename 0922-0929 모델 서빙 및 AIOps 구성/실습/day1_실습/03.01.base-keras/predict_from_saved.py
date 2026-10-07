"""
2단계: 저장된 iris_model.keras를 모델 정의 코드 없이 로드해 predict한다.

핵심 포인트 — 이 스크립트에는 build_model()도, keras.Sequential([...])도 없다.
run.sh가 이 스크립트를 train_and_save.py와는 별도의 python 프로세스로 실행하므로,
1단계에서 메모리에 있던 model 객체는 이미 사라진 상태다.
keras.models.load_model("iris_model.keras") 한 줄이 .keras 파일 안에 저장된
아키텍처+가중치+컴파일 설정을 전부 읽어 완전한 모델을 복원한다 — 재학습도,
모델 구조 재정의도 없이 학습 때와 동일한 predict 결과를 재현할 수 있다는 것이
이 예시가 보여주는 지점이다.
"""

import os

# 1단계와 동일하게 TensorFlow 백엔드 고정 (keras import 전에 설정)
os.environ.setdefault("KERAS_BACKEND", "tensorflow")

import time

import keras
import numpy as np


def main():
    model_path = "iris_model.keras"

    # 1) 테스트 데이터 로드 (1단계에서 저장한 것)
    data = np.load("test_data.npz")
    X_test = data["X_test"]
    y_test = data["y_test"]
    acc_inproc = float(data["acc_inproc"])

    # 2) 모델 복원 — 이 프로세스 어디에도 모델 구조를 정의하는 코드가 없다
    model = keras.models.load_model(model_path)
    print(f"[Keras] 로드 완료: {model_path} (백엔드={keras.backend.backend()})")
    model.summary()

    # 3) predict 실행
    t0 = time.time()
    pred = model.predict(X_test, verbose=0).argmax(axis=1)
    latency = time.time() - t0

    acc_loaded = float((pred == y_test).mean())
    print(f"\n[복원 모델] 테스트 정확도: {acc_loaded:.4f} ({int((pred == y_test).sum())}/{len(y_test)})")
    print(f"[복원 모델] predict 소요 시간 ({len(X_test)}개 샘플): {latency * 1000:.3f} ms")

    # 4) 1단계(학습 직후, 같은 프로세스)와 결과가 동일한지 검증
    print(f"\n[비교] 학습 직후 테스트 정확도      : {acc_inproc:.4f}")
    print(f"[비교] .keras 복원 후 테스트 정확도  : {acc_loaded:.4f}")
    if abs(acc_inproc - acc_loaded) < 1e-9:
        print("[비교] 결과 일치 ✅ — 재학습도 모델 정의 코드도 없이 .keras 파일만으로 동일한 모델을 복원했다.")
    else:
        print("[비교] 결과 불일치 ⚠️")


if __name__ == "__main__":
    main()
