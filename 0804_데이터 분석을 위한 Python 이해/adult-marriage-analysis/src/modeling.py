"""단일 특성 교차검증, 최적 특성 선택, 다변수 모델 학습."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import joblib
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.pipeline import Pipeline

from src.config import TARGET
from src.evaluation import (
    bootstrap_auc_difference,
    extract_logistic_coefficients,
    calculate_permutation_importance,
    evaluate_classifier,
)
from src.features import BASE_FEATURES, build_preprocessor


CV_SCORING = {
    "roc_auc": "roc_auc",
    "brier": "neg_brier_score",
    "accuracy": "accuracy",
    "f1": "f1",
}


@dataclass
class ModelingArtifacts:
    """모델링 단계에서 다음 시각화·보고 단계로 넘길 결과."""

    best_feature: str
    single_model: Pipeline
    multivariable_model: Pipeline
    y_test: pd.Series
    single_probabilities: pd.Series
    multivariable_probabilities: pd.Series
    single_cv: pd.DataFrame
    model_metrics: pd.DataFrame
    hypothesis_result: pd.DataFrame


def build_logistic_pipeline(features: list[str]) -> Pipeline:
    """선택 특성용 전처리와 로지스틱 회귀를 하나의 Pipeline으로 만든다."""
    return Pipeline(
        [
            ("preprocessor", build_preprocessor(features)),
            (
                "classifier",
                LogisticRegression(
                    max_iter=2_000,
                    solver="lbfgs",
                    random_state=42,
                ),
            ),
        ]
    )


def build_cv(random_state: int = 42) -> StratifiedKFold:
    """모든 후보가 공유할 계층화 5-fold 객체를 만든다."""
    return StratifiedKFold(n_splits=5, shuffle=True, random_state=random_state)


def evaluate_single_feature_models(train_df: pd.DataFrame) -> pd.DataFrame:
    """허용 특성을 하나씩 사용해 동일한 5-fold CV 성능을 비교한다."""
    rows: list[dict[str, float | str]] = []
    cv = build_cv()
    for feature in BASE_FEATURES:
        model = build_logistic_pipeline([feature])
        scores = cross_validate(
            model,
            train_df[[feature]],
            train_df[TARGET],
            cv=cv,
            scoring=CV_SCORING,
            error_score="raise",
        )
        rows.append(
            {
                "feature": feature,
                "cv_roc_auc_mean": scores["test_roc_auc"].mean(),
                "cv_roc_auc_std": scores["test_roc_auc"].std(ddof=1),
                "cv_brier_mean": -scores["test_brier"].mean(),
                "cv_brier_std": scores["test_brier"].std(ddof=1),
                "cv_accuracy_mean": scores["test_accuracy"].mean(),
                "cv_f1_mean": scores["test_f1"].mean(),
            }
        )
    return (
        pd.DataFrame(rows)
        .sort_values("cv_roc_auc_mean", ascending=False)
        .reset_index(drop=True)
    )


def evaluate_multivariable_cv(train_df: pd.DataFrame) -> pd.DataFrame:
    """기본 특성 전체 로지스틱 회귀의 5-fold CV 성능을 계산한다."""
    scores = cross_validate(
        build_logistic_pipeline(BASE_FEATURES),
        train_df[BASE_FEATURES],
        train_df[TARGET],
        cv=build_cv(),
        scoring=CV_SCORING,
        error_score="raise",
    )
    return pd.DataFrame(
        [
            {
                "model": "multivariable_logistic",
                "cv_roc_auc_mean": scores["test_roc_auc"].mean(),
                "cv_roc_auc_std": scores["test_roc_auc"].std(ddof=1),
                "cv_brier_mean": -scores["test_brier"].mean(),
                "cv_brier_std": scores["test_brier"].std(ddof=1),
                "cv_accuracy_mean": scores["test_accuracy"].mean(),
                "cv_f1_mean": scores["test_f1"].mean(),
            }
        ]
    )


def run_modeling_stage(
    project_root: Path,
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    practical_auc_margin: float = 0.02,
) -> ModelingArtifacts:
    """4단계 단일/다변수 모델 선택·평가·저장을 실행한다."""
    single_cv = evaluate_single_feature_models(train_df)
    best_feature = str(single_cv.iloc[0]["feature"])
    multivariable_cv = evaluate_multivariable_cv(train_df)

    single_model = build_logistic_pipeline([best_feature])
    multivariable_model = build_logistic_pipeline(BASE_FEATURES)
    single_model.fit(train_df[[best_feature]], train_df[TARGET])
    multivariable_model.fit(train_df[BASE_FEATURES], train_df[TARGET])

    single_metrics, single_probabilities, _ = evaluate_classifier(
        "best_single_feature",
        single_model,
        test_df[[best_feature]],
        test_df[TARGET],
    )
    multivariable_metrics, multivariable_probabilities, multivariable_predictions = (
        evaluate_classifier(
            "multivariable_logistic",
            multivariable_model,
            test_df[BASE_FEATURES],
            test_df[TARGET],
        )
    )
    model_metrics = pd.DataFrame([single_metrics, multivariable_metrics])

    auc_delta = (
        multivariable_metrics["roc_auc"] - single_metrics["roc_auc"]
    )
    ci_low, ci_high = bootstrap_auc_difference(
        test_df[TARGET],
        single_probabilities,
        multivariable_probabilities,
    )
    hypothesis_result = pd.DataFrame(
        [
            {
                "best_single_feature": best_feature,
                "single_test_auc": single_metrics["roc_auc"],
                "multivariable_test_auc": multivariable_metrics["roc_auc"],
                "auc_delta": auc_delta,
                "auc_delta_ci_low": ci_low,
                "auc_delta_ci_high": ci_high,
                "practical_auc_margin": practical_auc_margin,
                "exceeds_practical_margin": auc_delta > practical_auc_margin,
                "ci_entirely_above_margin": ci_low > practical_auc_margin,
            }
        ]
    )

    coefficient_table = extract_logistic_coefficients(multivariable_model)
    permutation_table = calculate_permutation_importance(
        multivariable_model,
        test_df[BASE_FEATURES],
        test_df[TARGET],
    )
    confusion_table = pd.crosstab(
        pd.Series(test_df[TARGET].to_numpy(), name="actual"),
        pd.Series(multivariable_predictions, name="predicted"),
        margins=True,
    )

    table_dir = project_root / "reports" / "tables"
    model_dir = project_root / "models"
    table_dir.mkdir(parents=True, exist_ok=True)
    model_dir.mkdir(parents=True, exist_ok=True)
    single_cv.to_csv(table_dir / "single_feature_cv.csv", index=False)
    multivariable_cv.to_csv(table_dir / "multivariable_cv.csv", index=False)
    model_metrics.to_csv(table_dir / "model_metrics.csv", index=False)
    hypothesis_result.to_csv(table_dir / "hypothesis_result.csv", index=False)
    coefficient_table.to_csv(table_dir / "logistic_coefficients.csv", index=False)
    permutation_table.to_csv(table_dir / "permutation_importance.csv", index=False)
    confusion_table.to_csv(table_dir / "confusion_matrix.csv")
    joblib.dump(single_model, model_dir / "single_feature_logistic.joblib")
    joblib.dump(
        multivariable_model,
        model_dir / "multivariable_logistic.joblib",
    )

    print("\n[4단계] 단일 특성 5-fold CV")
    print(single_cv.to_string(index=False, float_format="%.4f"))
    print("\n선택된 최적 단일 특성:", best_feature)
    print("\n테스트 성능:")
    print(model_metrics.to_string(index=False, float_format="%.4f"))
    print("\n가설 판단 근거:")
    print(hypothesis_result.to_string(index=False, float_format="%.4f"))
    print("\nPermutation importance:")
    print(permutation_table.to_string(index=False, float_format="%.4f"))

    return ModelingArtifacts(
        best_feature=best_feature,
        single_model=single_model,
        multivariable_model=multivariable_model,
        y_test=test_df[TARGET].copy(),
        single_probabilities=pd.Series(
            single_probabilities,
            index=test_df.index,
            name="single_probability",
        ),
        multivariable_probabilities=pd.Series(
            multivariable_probabilities,
            index=test_df.index,
            name="multivariable_probability",
        ),
        single_cv=single_cv,
        model_metrics=model_metrics,
        hypothesis_result=hypothesis_result,
    )
