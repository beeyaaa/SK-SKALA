"""Jupyter 커널 없이 04 Feature Engineering의 계산과 산출물을 검증한다."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.analysis import split_data
from src.config import TARGET
from src.data import add_target, load_pandas, resolve_raw_path
from src.feature_engineering import (
    build_feature_audit,
    build_feature_decisions,
    build_preprocessing_pipeline,
    transformed_feature_names,
)
from src.visualization import (
    create_encoding_summary_chart,
    create_feature_audit_chart,
    create_scaling_comparison_chart,
    create_transformation_chart,
)


def main() -> None:
    tables = ROOT / "reports" / "tables"
    figures = ROOT / "reports" / "figures"
    tables.mkdir(parents=True, exist_ok=True)
    figures.mkdir(parents=True, exist_ok=True)

    prepared_df = add_target(load_pandas(resolve_raw_path(ROOT)))
    train_df, test_df = split_data(prepared_df)
    audit = build_feature_audit(train_df)
    decisions = build_feature_decisions(train_df)
    audit.to_csv(tables / "feature_engineering_audit.csv", index=False)
    decisions.to_csv(tables / "feature_engineering_decisions.csv", index=False)

    pipeline = build_preprocessing_pipeline()
    train_matrix = pipeline.fit_transform(train_df.drop(columns=[TARGET]))
    test_matrix = pipeline.transform(test_df.drop(columns=[TARGET]))
    feature_names = transformed_feature_names(pipeline)

    assert train_matrix.shape[0] == len(train_df)
    assert test_matrix.shape[0] == len(test_df)
    assert train_matrix.shape[1] == test_matrix.shape[1] == len(feature_names)
    assert np.isfinite(train_matrix).all() and np.isfinite(test_matrix).all()

    create_feature_audit_chart(train_df, audit, figures / "04_feature_audit.png")
    create_transformation_chart(train_df, figures / "04_log_transformation.png")
    create_scaling_comparison_chart(train_df, figures / "04_scaling_comparison.png")
    create_encoding_summary_chart(train_df, feature_names, figures / "04_encoding_summary.png")

    summary = pd.DataFrame([{
        "Train 행": train_matrix.shape[0],
        "Test 행": test_matrix.shape[0],
        "변환 후 Feature 수": train_matrix.shape[1],
        "Train 결측치": int(pd.isna(train_matrix).sum()),
        "Test 결측치": int(pd.isna(test_matrix).sum()),
    }])
    summary.to_csv(tables / "feature_engineering_validation.csv", index=False)
    print(summary.to_string(index=False))
    print("검증 완료: 계산, Pipeline, 표와 그림 생성이 정상입니다.")


if __name__ == "__main__":
    main()
