"""
1단계: scikit-learn으로 붓꽃(Iris) 분류 모델을 학습하고 pickle로 저장한다.

_통합개념/SCIKIT-LEARN.md의 "6. 어떻게 사용하는데" 예시(train_test_split ->
RandomForestClassifier -> fit -> predict)와 동일한 패턴을 그대로 쓰되, 학습이
끝난 model 객체를 표준 라이브러리 pickle로 파일에 그대로 저장하는 부분을 더한
최소 예시다.
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

    # 3) 학습 직후(같은 프로세스) 정확도 확인 — 2단계 결과와 비교할 기준값
    pred_inproc = model.predict(X_test)
    acc_inproc = (pred_inproc == y_test).mean()
    print(f"[학습 직후] 테스트 정확도: {acc_inproc:.4f} ({(pred_inproc == y_test).sum()}/{len(y_test)})")

    # 4) pickle로 저장 — 학습된 model 객체(트리 구조·가중치 전부)를 그대로 직렬화
    model_path = "model.pkl"
    with open(model_path, "wb") as f:
        pickle.dump(model, f)
    print(f"[pickle] 저장 완료: {model_path}")

    # 5) 다음 단계(predict_from_pickle.py)에서 그대로 재사용할 수 있도록 테스트 데이터 저장
    np.savez("test_data.npz", X_test=X_test, y_test=y_test, acc_inproc=acc_inproc)
    print("[데이터] 테스트셋 저장 완료: test_data.npz")


if __name__ == "__main__":
    t0 = time.time()
    main()
    print(f"\n총 소요 시간: {time.time() - t0:.2f}s")
