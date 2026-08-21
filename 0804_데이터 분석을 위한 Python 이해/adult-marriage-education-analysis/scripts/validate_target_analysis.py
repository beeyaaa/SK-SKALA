"""Jupyter 커널 없이 변경된 혼인 경험 Target과 02~03 산출물을 검증한다."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.analysis import (
    build_group_statistics,
    calculate_vif,
    run_hypothesis_test,
    split_data,
)
from src.config import EVER_MARRIED_STATUSES, NEVER_MARRIED_STATUS, TARGET
from src.data import (
    add_target,
    build_column_profile,
    build_feature_policy,
    load_pandas,
    resolve_raw_path,
)
from src.visualization import (
    create_education_hypothesis_chart,
    create_interactive_education_rate,
    create_multicollinearity_chart,
    create_target_definition_chart,
)


def main() -> None:
    tables = ROOT / "reports" / "tables"
    figures = ROOT / "reports" / "figures"
    interactive = ROOT / "reports" / "interactive"
    for directory in [tables, figures, interactive]:
        directory.mkdir(parents=True, exist_ok=True)

    raw_df = load_pandas(resolve_raw_path(ROOT))
    prepared_df = add_target(raw_df)
    expected_target = raw_df["marital-status"].ne(NEVER_MARRIED_STATUS).astype("int8")
    assert prepared_df[TARGET].equals(expected_target)
    assert set(raw_df.loc[prepared_df[TARGET] == 1, "marital-status"].unique()) == EVER_MARRIED_STATUSES
    assert set(raw_df.loc[prepared_df[TARGET] == 0, "marital-status"].unique()) == {NEVER_MARRIED_STATUS}

    build_column_profile(raw_df).to_csv(tables / "column_profile.csv", index=False)
    build_feature_policy().to_csv(tables / "feature_policy.csv", index=False)
    create_target_definition_chart(prepared_df, figures / "02_target_definition.png")

    train_df, test_df = split_data(prepared_df)
    group_statistics = build_group_statistics(train_df)
    vif = calculate_vif(train_df)
    hypothesis = run_hypothesis_test(train_df)
    group_statistics.to_csv(tables / "education_group_statistics.csv", index=False)
    vif.to_csv(tables / "vif.csv", index=False)
    hypothesis.to_csv(tables / "hypothesis_result.csv", index=False)
    create_education_hypothesis_chart(train_df, figures / "03_education_by_marriage.png")
    create_multicollinearity_chart(train_df, vif, figures / "03_multicollinearity.png")
    create_interactive_education_rate(train_df, interactive / "education_marriage_rate.html")

    print("전체 Target 분포")
    print(prepared_df[TARGET].value_counts().sort_index().to_string())
    print("\nTrain/Test 미혼 외 비율")
    print(f"Train {train_df[TARGET].mean():.2%} | Test {test_df[TARGET].mean():.2%}")
    print("\n가설검정")
    print(hypothesis.to_string(index=False))
    print("검증 완료: Never-married만 0이고 나머지 모든 혼인 상태는 1입니다.")


if __name__ == "__main__":
    main()
