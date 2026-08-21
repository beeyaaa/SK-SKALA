"""Pandas/Polars 로딩 일치 여부에 대한 최소 단위 테스트."""

from pathlib import Path

import pandas as pd
import pytest

from src.data import (
    add_target_pandas,
    add_target_polars,
    compare_frames,
    compare_target_distribution,
    load_with_pandas,
    load_with_polars,
)
from src.features import BASE_FEATURES, select_feature_sets


SAMPLE_ROWS = """39, State-gov, 77516, Bachelors, 13, Never-married, Adm-clerical, Not-in-family, White, Male, 2174, 0, 40, United-States, <=50K
50, Self-emp-not-inc, 83311, Bachelors, 13, Married-civ-spouse, Exec-managerial, Husband, White, Male, 0, 0, 13, United-States, <=50K
38, Private, 215646, HS-grad, 9, Divorced, ?, Not-in-family, White, Male, 0, 0, 40, United-States, <=50K
"""


def test_pandas_polars_loading_match(tmp_path: Path) -> None:
    raw_path = tmp_path / "adult.data"
    raw_path.write_text(SAMPLE_ROWS, encoding="utf-8")

    pandas_df = load_with_pandas(raw_path)
    polars_df = load_with_polars(raw_path)
    summary, details = compare_frames(pandas_df, polars_df)

    assert summary.loc[0, "pandas_rows"] == 3
    assert summary.loc[0, "column_order_equal"]
    assert summary.loc[0, "total_nulls_equal"]
    assert details["null_count_equal"].all()
    assert details["unique_count_equal"].all()


def test_target_mapping_matches_between_libraries(tmp_path: Path) -> None:
    raw_path = tmp_path / "adult.data"
    raw_path.write_text(SAMPLE_ROWS, encoding="utf-8")

    pandas_df = add_target_pandas(load_with_pandas(raw_path))
    polars_df = add_target_polars(load_with_polars(raw_path))
    distribution = compare_target_distribution(pandas_df, polars_df)

    assert pandas_df["ever_married"].tolist() == [0, 1, 1]
    assert polars_df["ever_married"].to_list() == [0, 1, 1]
    assert distribution["count_equal"].all()


def test_unknown_marital_status_is_rejected() -> None:
    frame = pd.DataFrame({"marital-status": ["Unknown-status"]})

    with pytest.raises(ValueError, match="정의되지 않은 marital-status"):
        add_target_pandas(frame)


def test_model_feature_set_blocks_leakage(tmp_path: Path) -> None:
    raw_path = tmp_path / "adult.data"
    raw_path.write_text(SAMPLE_ROWS, encoding="utf-8")
    prepared = add_target_pandas(load_with_pandas(raw_path))

    base_x, extended_x, audit_x, target = select_feature_sets(prepared)

    assert base_x.columns.tolist() == BASE_FEATURES
    assert "marital-status" not in base_x
    assert "relationship" not in base_x
    assert "income" not in base_x
    assert "income" in extended_x
    assert audit_x.columns.tolist() == ["race", "sex", "native-country"]
    assert target.tolist() == [0, 1, 1]
