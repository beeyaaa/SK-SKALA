"""
1단계: PyTorch로 붓꽃(Iris) 분류 모델을 학습하고 TorchScript로 컴파일해 저장한다.

핵심 포인트 — torch.jit.script(model)은 IrisNet의 Python 코드(forward 메서드)를
분석해서 자체적으로 실행 가능한 그래프 표현(ScriptModule)으로 컴파일한다. 저장된
.pt 파일은 이 그래프 자체를 담고 있어서, 2단계(infer_torchscript.py)는 IrisNet
클래스 정의를 아예 import하지 않고도 로드해서 실행할 수 있다 — ONNX가 프레임워크
간 이식성을 위한 것이라면, TorchScript는 "PyTorch 생태계 안에서" Python 인터프리터
자체에 대한 의존을 끊기 위한 것이다(LibTorch로 C++에서도 그대로 실행 가능).
"""

import time

import numpy as np
import torch
import torch.nn as nn
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler


class IrisNet(nn.Module):
    """4개 특성(꽃받침/꽃잎 길이·너비) -> 3개 클래스(붓꽃 품종)로 분류하는 작은 MLP.

    _통합개념_실습/ONNX/base_onnxruntime와 동일한 모델 정의 — 같은 문제로 "ONNX 경로"와
    "TorchScript 경로"를 나란히 비교할 수 있게 했다.
    """

    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(4, 16),
            nn.ReLU(),
            nn.Linear(16, 8),
            nn.ReLU(),
            nn.Linear(8, 3),
        )

    def forward(self, x):
        return self.net(x)


def main():
    torch.manual_seed(0)

    # 1) 데이터 준비 — scikit-learn의 Iris 데이터셋(150 샘플, 4 특성, 3 클래스)
    X, y = load_iris(return_X_y=True)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=0, stratify=y
    )
    scaler = StandardScaler().fit(X_train)
    X_train = scaler.transform(X_train).astype(np.float32)
    X_test = scaler.transform(X_test).astype(np.float32)

    X_train_t = torch.from_numpy(X_train)
    y_train_t = torch.from_numpy(y_train).long()

    # 2) 학습 — 평범한 PyTorch eager mode 학습 루프
    model = IrisNet()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.05)
    loss_fn = nn.CrossEntropyLoss()

    model.train()
    for epoch in range(200):
        optimizer.zero_grad()
        logits = model(X_train_t)
        loss = loss_fn(logits, y_train_t)
        loss.backward()
        optimizer.step()
        if (epoch + 1) % 50 == 0:
            print(f"  epoch {epoch + 1:>3}/200  loss={loss.item():.4f}")

    # 3) 학습 정확도 확인 (eager mode PyTorch 자체 추론)
    model.eval()
    with torch.no_grad():
        X_test_t = torch.from_numpy(X_test)
        pred_eager = model(X_test_t).argmax(dim=1).numpy()
    acc_eager = (pred_eager == y_test).mean()
    print(f"[Eager PyTorch] 테스트 정확도: {acc_eager:.4f} ({(pred_eager == y_test).sum()}/{len(y_test)})")

    # 4) TorchScript로 컴파일 — torch.jit.script는 forward()의 Python 코드를
    #    직접 분석(파싱)해서 정적 그래프(ScriptModule)로 변환한다.
    #    (torch.onnx.export처럼 더미 입력을 "실행해서" 그래프를 추적하는 trace 방식과 달리,
    #     script 방식은 조건문·반복문이 있어도 실제 제어 흐름 구조 자체를 그대로 컴파일한다.)
    scripted = torch.jit.script(model)
    print("[TorchScript] 컴파일된 그래프(code):")
    print(scripted.code)

    pt_path = "iris_model.pt"
    scripted.save(pt_path)
    print(f"[TorchScript] 저장 완료: {pt_path}")

    # 5) TorchScript 모델로도 같은 입력에 같은 결과가 나오는지 즉시 확인
    with torch.no_grad():
        pred_script = scripted(X_test_t).argmax(dim=1).numpy()
    acc_script = (pred_script == y_test).mean()
    print(f"[TorchScript(같은 프로세스)] 테스트 정확도: {acc_script:.4f}")

    # 6) 다음 단계(infer_torchscript.py)에서 재사용할 테스트 데이터·정확도 저장
    np.savez("test_data.npz", X_test=X_test, y_test=y_test, acc_eager=acc_eager)
    print("[데이터] 테스트셋 저장 완료: test_data.npz")


if __name__ == "__main__":
    t0 = time.time()
    main()
    print(f"\n총 소요 시간: {time.time() - t0:.2f}s")
