"""전체 분석 Pipeline의 실행 진입점."""

from pathlib import Path

from src.data import run_data_loading_stage, run_target_stage
from src.eda import (
    build_categorical_summary,
    build_categorical_target_rates,
    build_iqr_outlier_summary,
    build_missingness_summary,
    build_numeric_correlation,
    build_numeric_distribution_summary,
    build_numeric_target_summary,
    build_validity_summary,
)
from src.features import (
    BASE_FEATURES,
    EXTENDED_FEATURES,
    build_feature_missingness,
    build_feature_policy,
    build_preprocessing_audit,
    select_feature_sets,
)
from src.statistics import (
    analyze_categorical_associations,
    analyze_numeric_associations,
    build_split_summary,
    calculate_mutual_information,
    run_statistics_stage,
)
from src.modeling import run_modeling_stage
from src.reporting import generate_report
from src.visualization import (
    create_categorical_cardinality_chart,
    create_categorical_target_rate_chart,
    create_calibration_chart,
    create_correlation_heatmap,
    create_missingness_chart,
    create_numeric_distribution_grid,
    create_numeric_target_boxplots,
    create_outlier_boxplots,
    create_preprocessing_diagnostics,
    create_split_target_distribution_chart,
    create_target_association_overview,
    run_visualization_stage,
)


def main() -> None:
    """현재 구현된 분석 단계를 순서대로 실행한다."""
    project_root = Path(__file__).resolve().parent
    pandas_df, polars_df = run_data_loading_stage(project_root)
    pandas_df, _ = run_target_stage(project_root, pandas_df, polars_df)

    base_x, extended_x, audit_x, target = select_feature_sets(pandas_df)
    feature_policy = build_feature_policy()
    feature_missingness = build_feature_missingness(pandas_df)

    table_dir = project_root / "reports" / "tables"
    feature_policy.to_csv(table_dir / "feature_policy.csv", index=False)
    feature_missingness.to_csv(table_dir / "feature_missingness.csv", index=False)

    print("\n[2단계] 모델 입력 컬럼 분리")
    print("기본 모델:", BASE_FEATURES, base_x.shape)
    print("확장 모델:", EXTENDED_FEATURES, extended_x.shape)
    print("공정성 점검:", audit_x.columns.tolist(), audit_x.shape)
    print("타깃:", target.name, target.shape)
    print("\n입력 후보 결측치:")
    print(feature_missingness.to_string(index=False, float_format="%.2f"))

    train_df, test_df = run_statistics_stage(project_root, pandas_df)

    eda_tables = {
        "eda_missingness": build_missingness_summary(pandas_df),
        "eda_validity": build_validity_summary(pandas_df),
        "eda_numeric_distribution": build_numeric_distribution_summary(train_df),
        "eda_iqr_outliers": build_iqr_outlier_summary(train_df),
        "eda_categorical_summary": build_categorical_summary(train_df),
        "eda_numeric_correlation": build_numeric_correlation(train_df),
        "eda_numeric_target_summary": build_numeric_target_summary(train_df),
        "eda_categorical_target_rates": build_categorical_target_rates(train_df),
    }
    for name, table in eda_tables.items():
        table.to_csv(table_dir / f"{name}.csv", index=True if "correlation" in name else False)

    print("\n[Question-driven EDA]")
    print("Q1. 결측치는 어디에, 얼마나 존재하는가?")
    print(eda_tables["eda_missingness"].to_string(index=False, float_format="%.2f"))
    print("Next Action: 모델 범주형 결측은 Pipeline 내부에서 Unknown으로 대치")
    print("\nQ2. 논리적으로 유효하지 않은 값은 없는가?")
    print(eda_tables["eda_validity"].to_string(index=False))
    print("Next Action: 범위 위반이 없으므로 오류값 대치 없이 진행")
    print("\nQ3. 숫자형 분포와 이상치는 어떠한가?")
    print(eda_tables["eda_numeric_distribution"].to_string(index=False, float_format="%.2f"))
    print("Next Action: capital-gain·capital-loss에 log1p 적용; IQR 이상치는 자동 삭제하지 않음")
    print("\nQ4. 범주형 구성과 숫자형 상관은 어떠한가?")
    print(eda_tables["eda_categorical_summary"].to_string(index=False, float_format="%.2f"))
    print("Next Action: 범주형은 OneHotEncoder, 특성 선택은 교차검증으로 결정")
    print("\nQ5. 각 변수는 Target과 어떤 관계가 있는가?")
    print(eda_tables["eda_numeric_target_summary"].to_string(index=False, float_format="%.2f"))
    print(eda_tables["eda_categorical_target_rates"].to_string(index=False, float_format="%.2f"))
    print("Next Action: 관계의 크기와 교차검증 성능을 함께 사용해 후보를 비교")

    figure_dir = project_root / "reports" / "figures"
    split_summary = build_split_summary(train_df, test_df)
    numeric_associations = analyze_numeric_associations(train_df)
    categorical_associations = analyze_categorical_associations(train_df)
    mutual_information = calculate_mutual_information(train_df)
    eda_chart_paths = [
        create_split_target_distribution_chart(
            split_summary, figure_dir / "eda_stratified_target_split.png"
        ),
        create_missingness_chart(pandas_df, figure_dir / "eda_missing_values.png"),
        create_numeric_distribution_grid(train_df, figure_dir / "eda_numeric_distributions.png"),
        create_outlier_boxplots(train_df, figure_dir / "eda_numeric_outliers.png"),
        create_categorical_cardinality_chart(train_df, figure_dir / "eda_categorical_cardinality.png"),
        create_correlation_heatmap(train_df, figure_dir / "eda_numeric_correlation.png"),
        create_numeric_target_boxplots(train_df, figure_dir / "eda_numeric_by_target.png"),
        create_categorical_target_rate_chart(train_df, figure_dir / "eda_categorical_target_rates.png"),
        create_target_association_overview(
            numeric_associations,
            categorical_associations,
            mutual_information,
            figure_dir / "eda_target_associations.png",
        ),
    ]
    print("EDA charts:")
    for chart_path in eda_chart_paths:
        print("-", chart_path)

    run_visualization_stage(project_root, train_df)
    preprocessing_path = create_preprocessing_diagnostics(
        train_df,
        project_root / "reports" / "figures" / "preprocessing_diagnostics.png",
    )
    preprocessing_audit = build_preprocessing_audit(train_df)
    preprocessing_audit.to_csv(
        project_root / "reports" / "tables" / "preprocessing_audit.csv",
        index=False,
    )
    print("Preprocessing:", preprocessing_path)
    modeling = run_modeling_stage(project_root, train_df, test_df)
    calibration_path = create_calibration_chart(
        modeling.y_test,
        modeling.single_probabilities,
        modeling.multivariable_probabilities,
        project_root / "reports" / "figures" / "calibration_curve.png",
    )
    print("Calibration:", calibration_path)
    report_path = generate_report(project_root)
    print("Report:", report_path)


if __name__ == "__main__":
    main()
