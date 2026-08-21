"""분류·확률 지표, 신뢰구간, calibration 및 중요도 계산."""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.inspection import permutation_importance
from sklearn.metrics import (
    accuracy_score,
    brier_score_loss,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


def evaluate_classifier(model_name, model, features, target):
    """학습된 분류기의 테스트 지표와 예측값을 반환한다."""
    probabilities = model.predict_proba(features)[:, 1]
    predictions = model.predict(features)
    metrics = {
        "model": model_name,
        "accuracy": accuracy_score(target, predictions),
        "f1": f1_score(target, predictions),
        "precision": precision_score(target, predictions),
        "recall": recall_score(target, predictions),
        "roc_auc": roc_auc_score(target, probabilities),
        "brier_score": brier_score_loss(target, probabilities),
    }
    return metrics, probabilities, predictions


def bootstrap_auc_difference(
    target,
    single_probabilities,
    multivariable_probabilities,
    n_bootstrap: int = 500,
    random_state: int = 42,
) -> tuple[float, float]:
    """같은 테스트 표본에서 다변수-단일 AUC 차이의 bootstrap CI를 계산한다."""
    y = np.asarray(target)
    single = np.asarray(single_probabilities)
    multi = np.asarray(multivariable_probabilities)
    random = np.random.default_rng(random_state)
    differences: list[float] = []
    for _ in range(n_bootstrap):
        indices = random.integers(0, len(y), size=len(y))
        if np.unique(y[indices]).size < 2:
            continue
        differences.append(
            roc_auc_score(y[indices], multi[indices])
            - roc_auc_score(y[indices], single[indices])
        )
    return tuple(np.quantile(differences, [0.025, 0.975]))


def extract_logistic_coefficients(model) -> pd.DataFrame:
    """Pipeline 내부 로지스틱 회귀의 변환 특성별 계수와 오즈비를 반환한다."""
    names = model.named_steps["preprocessor"].get_feature_names_out()
    coefficients = model.named_steps["classifier"].coef_[0]
    return (
        pd.DataFrame(
            {
                "transformed_feature": names,
                "coefficient": coefficients,
                "odds_ratio": np.exp(coefficients),
                "absolute_coefficient": np.abs(coefficients),
            }
        )
        .sort_values("absolute_coefficient", ascending=False)
        .reset_index(drop=True)
    )


def calculate_permutation_importance(
    model,
    features: pd.DataFrame,
    target: pd.Series,
) -> pd.DataFrame:
    """원본 컬럼 단위 ROC-AUC permutation importance를 계산한다."""
    result = permutation_importance(
        model,
        features,
        target,
        scoring="roc_auc",
        n_repeats=20,
        random_state=42,
    )
    return (
        pd.DataFrame(
            {
                "feature": features.columns,
                "importance_mean": result.importances_mean,
                "importance_std": result.importances_std,
            }
        )
        .sort_values("importance_mean", ascending=False)
        .reset_index(drop=True)
    )
