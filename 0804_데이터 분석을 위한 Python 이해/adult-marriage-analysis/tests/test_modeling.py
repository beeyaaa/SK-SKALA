"""전처리 Pipeline과 모델 확률 출력의 최소 계약 테스트."""

from pathlib import Path

from src.data import add_target_pandas, load_with_pandas
from src.features import BASE_FEATURES
from src.modeling import build_logistic_pipeline
from src.statistics import split_prepared_data


def test_multivariable_pipeline_fits_and_predicts_probabilities() -> None:
    project_root = Path(__file__).resolve().parents[1]
    prepared = add_target_pandas(
        load_with_pandas(project_root / "data" / "raw" / "adult.data")
    )
    train_df, test_df = split_prepared_data(prepared)
    train_sample = train_df.head(1_000)
    test_sample = test_df.head(100)

    model = build_logistic_pipeline(BASE_FEATURES)
    model.fit(train_sample[BASE_FEATURES], train_sample["ever_married"])
    probabilities = model.predict_proba(test_sample[BASE_FEATURES])[:, 1]

    assert probabilities.shape == (100,)
    assert ((probabilities >= 0) & (probabilities <= 1)).all()
    assert "marital-status" not in BASE_FEATURES
    assert "relationship" not in BASE_FEATURES

