"""
1단계: scikit-learn으로 붓꽃(Iris) 분류 모델을 학습하고 pickle로 저장한다.

_통합개념_실습/SCIKIT-LEARN/base-sklearn와 같은 모델·데이터를 쓰되, 이 폴더는 FastAPI
서빙까지 포함한다. RandomForestClassifier는 PyTorch/ONNX 예시와 달리 별도의
StandardScaler가 필요 없다 — 학습에 쓴 원본 cm 단위 값을 그대로 fit/predict에
넣으면 되므로, pickle 파일 하나(model.pkl)에 전처리까지 포함해 저장할 게 없다.
그래서 app.py는 scaler.npz 같은 보조 파일 없이 model.pkl 하나만 로드한다.
"""

import pickle
import time

import numpy as np
from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split


def main():
    # 1) 데이터 준비 — Iris 데이터셋(150 샘플, 4 특성, 3 클래스)
    X, y = load_iris(return_X_y=True)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=0, stratify=y
    )

    # 2) 학습 — SCIKIT-LEARN.md 예시와 동일한 두 줄 패턴
    model = RandomForestClassifier(random_state=0)
    model.fit(X_train, y_train)

    # 3) 학습 직후 정확도 확인 — app.py가 서빙할 model과 같은 model
    pred = model.predict(X_test)
    acc = (pred == y_test).mean()
    print(f"[학습 직후] 테스트 정확도: {acc:.4f} ({(pred == y_test).sum()}/{len(y_test)})")

    # 4) pickle로 저장 — app.py가 lifespan에서 그대로 로드
    model_path = "model.pkl"
    with open(model_path, "wb") as f:
        pickle.dump(model, f)
    print(f"[pickle] 저장 완료: {model_path}")

    # 5) run.sh의 curl 테스트가 재사용할 원본(cm 단위) 테스트셋도 저장
    np.savez("test_data.npz", X_test=X_test.astype(np.float32), y_test=y_test, acc=acc)
    print("[데이터] 테스트셋 저장 완료: test_data.npz")


if __name__ == "__main__":
    t0 = time.time()
    main()
    print(f"\n총 소요 시간: {time.time() - t0:.2f}s")
