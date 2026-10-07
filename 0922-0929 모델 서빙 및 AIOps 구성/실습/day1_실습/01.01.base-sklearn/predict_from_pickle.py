"""
2단계: pickle로 저장된 model.pkl을 다시 불러와 predict한다.

핵심 포인트 — 이 스크립트는 model을 다시 학습하지 않는다. run.sh가 이 스크립트를
train_and_pickle.py와는 별도의 python 프로세스로 실행하므로, 1단계에서 메모리에
있던 model 객체는 이미 사라진 상태다. pickle.load만으로 학습된 model 전체(트리
구조·가중치)를 그대로 복원해 predict를 실행할 수 있다는 것이 이 예시가 보여주는
지점이다.
"""

import pickle
import time

import numpy as np


def main():
    model_path = "model.pkl"

    # 1) 테스트 데이터 로드 (1단계에서 저장한 것)
    data = np.load("test_data.npz")
    X_test = data["X_test"]
    y_test = data["y_test"]
    acc_inproc = float(data["acc_inproc"])

    # 2) pickle에서 model 복원 — 이 시점까지 RandomForestClassifier를 새로 학습한 적 없음
    with open(model_path, "rb") as f:
        model = pickle.load(f)
    print(f"[pickle] 로드 완료: {model_path} ({type(model).__name__})")

    # 3) predict 실행
    t0 = time.time()
    pred = model.predict(X_test)
    latency = time.time() - t0

    acc_pickle = (pred == y_test).mean()
    print(f"\n[pickle 복원 모델] 테스트 정확도: {acc_pickle:.4f} ({(pred == y_test).sum()}/{len(y_test)})")
    print(f"[pickle 복원 모델] predict 소요 시간 ({len(X_test)}개 샘플): {latency * 1000:.3f} ms")

    # 4) 1단계(학습 직후, 같은 프로세스)와 결과가 동일한지 검증
    print(f"\n[비교] 학습 직후 테스트 정확도      : {acc_inproc:.4f}")
    print(f"[비교] pickle 복원 후 테스트 정확도  : {acc_pickle:.4f}")
    if abs(acc_inproc - acc_pickle) < 1e-9:
        print("[비교] 결과 일치 ✅ — 다시 학습하지 않고 pickle만으로 동일한 모델을 복원했다.")
    else:
        print("[비교] 결과 불일치 ⚠️")

    # 5) predict 몇 개를 직접 눈으로 확인
    print("\n[샘플 예측] 처음 5개")
    for i in range(min(5, len(X_test))):
        print(f"  입력={X_test[i]}  실제={y_test[i]}  예측={pred[i]}")


if __name__ == "__main__":
    main()
