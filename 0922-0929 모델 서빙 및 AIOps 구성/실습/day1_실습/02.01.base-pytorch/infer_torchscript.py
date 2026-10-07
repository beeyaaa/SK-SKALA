"""
2단계: 저장된 TorchScript(.pt) 모델을 IrisNet 클래스 정의 없이 로드해 추론한다.

핵심 포인트 — 이 스크립트는 IrisNet 클래스를 import하지 않는다(정의 자체가
어디에도 없다). torch.jit.load()만으로 .pt 파일 안에 저장된 그래프와 가중치를
그대로 복원해 실행할 수 있다는 것이 TorchScript가 해결하는 문제다: 모델 코드를
몰라도, 컴파일된 아티팩트 하나만 있으면 실행할 수 있다(LibTorch로 C++에서 실행할
때 특히 중요 — C++에는애초에 IrisNet 같은 Python 클래스가 존재할 수 없다).
"""

import time

import numpy as np
import torch


def main():
    pt_path = "iris_model.pt"

    # 1) 테스트 데이터 로드 (1단계에서 저장한 것)
    data = np.load("test_data.npz")
    X_test = data["X_test"].astype(np.float32)
    y_test = data["y_test"]
    acc_eager = float(data["acc_eager"])

    # 2) TorchScript 모델 로드 — IrisNet 클래스 정의가 이 프로세스 어디에도 없다
    torch.jit.set_fusion_strategy([("STATIC", 0)])  # 재현성을 위해 JIT 퓨전 최적화 끔
    scripted = torch.jit.load(pt_path)
    scripted.eval()
    print(f"[TorchScript] 로드 완료: {pt_path}")
    print(f"[TorchScript] 타입: {type(scripted)}")

    # 3) 추론 실행 — 일반 nn.Module과 동일하게 호출 가능
    X_test_t = torch.from_numpy(X_test)
    t0 = time.time()
    with torch.no_grad():
        logits = scripted(X_test_t)
    latency = time.time() - t0
    pred_script = logits.argmax(dim=1).numpy()

    acc_script = (pred_script == y_test).mean()
    print(f"\n[TorchScript] 테스트 정확도: {acc_script:.4f} ({(pred_script == y_test).sum()}/{len(y_test)})")
    print(f"[TorchScript] 추론 소요 시간 ({len(X_test)}개 샘플): {latency * 1000:.3f} ms")

    # 4) eager mode(1단계) 결과와 일치하는지 검증
    print(f"\n[비교] Eager PyTorch 테스트 정확도: {acc_eager:.4f}")
    print(f"[비교] TorchScript 테스트 정확도  : {acc_script:.4f}")
    if abs(acc_eager - acc_script) < 1e-6:
        print("[비교] 결과 일치 ✅ — IrisNet 클래스 없이도 컴파일된 .pt 파일만으로 동일하게 재현했다.")
    else:
        print("[비교] 결과 불일치 ⚠️")


if __name__ == "__main__":
    main()
