"""데이터 분할과 통계분석의 핵심 계약 테스트."""

from pathlib import Path

from src.data import add_target_pandas, load_with_pandas
from src.statistics import (
    analyze_categorical_associations,
    analyze_numeric_associations,
    build_split_summary,
    calculate_mutual_information,
    split_prepared_data,
)


def _load_real_prepared_data(project_root: Path):
    raw_path = project_root / "data" / "raw" / "adult.data"
    return add_target_pandas(load_with_pandas(raw_path))


def test_split_is_reproducible_and_disjoint() -> None:
    project_root = Path(__file__).resolve().parents[1]
    prepared = _load_real_prepared_data(project_root)

    train_a, test_a = split_prepared_data(prepared)
    train_b, test_b = split_prepared_data(prepared)
    summary = build_split_summary(train_a, test_a)

    assert train_a.index.equals(train_b.index)
    assert test_a.index.equals(test_b.index)
    assert set(train_a.index).isdisjoint(test_a.index)
    assert len(train_a) + len(test_a) == len(prepared)
    assert summary.groupby("split")["percentage"].sum().round(8).eq(100).all()


def test_statistical_outputs_cover_expected_features() -> None:
    project_root = Path(__file__).resolve().parents[1]
    prepared = _load_real_prepared_data(project_root)
    train_df, _ = split_prepared_data(prepared)

    numeric = analyze_numeric_associations(train_df)
    categorical = analyze_categorical_associations(train_df)
    mutual_information = calculate_mutual_information(train_df)

    assert set(numeric["feature"]) == {
        "age",
        "education-num",
        "hours-per-week",
        "capital-gain",
        "capital-loss",
    }
    assert set(categorical["feature"]) == {"workclass", "occupation", "income"}
    assert len(mutual_information) == 8
    assert mutual_information["mutual_information"].ge(0).all()

