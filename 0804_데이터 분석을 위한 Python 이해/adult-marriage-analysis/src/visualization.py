"""과제용 Seaborn 정적 차트와 Plotly 인터랙티브 차트."""

from __future__ import annotations

import os
from pathlib import Path

# Matplotlib이 쓰기 제한된 사용자 홈 대신 프로젝트 내부 캐시를 사용하게 한다.
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_MPL_CACHE = _PROJECT_ROOT / "data" / "processed" / ".matplotlib"
_MPL_CACHE.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(_MPL_CACHE))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import seaborn as sns
from sklearn.calibration import calibration_curve

from src.config import TARGET
from src.eda import (
    EDA_CATEGORICAL_FEATURES,
    EDA_NUMERIC_FEATURES,
    build_categorical_summary,
    build_categorical_target_rates,
    build_missingness_summary,
    build_numeric_correlation,
)
from src.features import BASE_FEATURES, build_preprocessing_audit


BLUE = "#356AA0"
GOLD = "#D6A84B"
INK = "#20242A"
GRID = "#D9DEE5"


def create_missingness_chart(df: pd.DataFrame, output_path: Path) -> Path:
    """컬럼별 결측치 개수와 비율을 가로 막대로 저장한다."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    summary = build_missingness_summary(df).sort_values("missing_count")
    sns.set_theme(style="whitegrid")
    figure, axis = plt.subplots(figsize=(9, 4.8))
    axis.barh(summary["column"], summary["missing_count"], color=GOLD)
    for row_index, row in summary.reset_index(drop=True).iterrows():
        axis.text(
            row["missing_count"] + 25,
            row_index,
            f"{int(row['missing_count']):,} ({row['missing_rate_pct']:.1f}%)",
            va="center",
            fontsize=9,
        )
    axis.set_title(
        "Missing values by column", loc="left", fontweight="bold", pad=34
    )
    axis.text(
        0,
        1.015,
        f"Raw Adult data, n={len(df):,}; only columns with missing values are shown",
        transform=axis.transAxes,
        color="#5C6673",
        fontsize=10,
    )
    axis.set_xlabel("Missing rows")
    axis.set_ylabel("")
    axis.grid(axis="y", visible=False)
    sns.despine(ax=axis)
    figure.tight_layout()
    figure.savefig(output_path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(figure)
    return output_path


def create_numeric_distribution_grid(df: pd.DataFrame, output_path: Path) -> Path:
    """모델 숫자형 후보의 히스토그램을 small multiples로 저장한다."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid")
    figure, axes = plt.subplots(2, 3, figsize=(15, 8))
    axes_flat = axes.flatten()
    for axis, feature in zip(axes_flat, EDA_NUMERIC_FEATURES):
        sns.histplot(df[feature].dropna(), bins=30, color=BLUE, ax=axis)
        axis.set_title(feature, loc="left", fontweight="bold")
        axis.set_xlabel("")
        axis.set_ylabel("Rows")
        axis.grid(color=GRID, linewidth=0.8)
        sns.despine(ax=axis)
    axes_flat[-1].axis("off")
    figure.suptitle(
        "Numeric feature distributions",
        x=0.05,
        y=1.01,
        ha="left",
        fontsize=18,
        fontweight="bold",
        color=INK,
    )
    figure.text(
        0.05,
        0.96,
        f"Training set, n={len(df):,}; raw scale before model preprocessing",
        color="#5C6673",
        fontsize=10,
    )
    figure.tight_layout(rect=[0, 0, 1, 0.94])
    figure.savefig(output_path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(figure)
    return output_path


def create_outlier_boxplots(df: pd.DataFrame, output_path: Path) -> Path:
    """각 숫자형 후보의 IQR·극단값을 독립 축 box plot으로 저장한다."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid")
    figure, axes = plt.subplots(1, len(EDA_NUMERIC_FEATURES), figsize=(15, 5.5))
    for axis, feature in zip(axes, EDA_NUMERIC_FEATURES):
        sns.boxplot(y=df[feature], color=GOLD, width=0.5, fliersize=2, ax=axis)
        axis.set_title(feature, fontsize=11, fontweight="bold")
        axis.set_xlabel("")
        axis.set_ylabel("")
        axis.grid(axis="x", visible=False)
        sns.despine(ax=axis)
    figure.suptitle(
        "Potential outliers by numeric feature",
        x=0.05,
        y=1.03,
        ha="left",
        fontsize=18,
        fontweight="bold",
        color=INK,
    )
    figure.text(
        0.05,
        0.95,
        "Training set; points beyond 1.5×IQR are diagnostic flags, not automatic deletion targets",
        color="#5C6673",
        fontsize=10,
    )
    figure.tight_layout(rect=[0, 0, 1, 0.92])
    figure.savefig(output_path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(figure)
    return output_path


def create_categorical_cardinality_chart(
    df: pd.DataFrame, output_path: Path
) -> Path:
    """범주형 후보별 고유 범주 수를 가로 막대로 저장한다."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    summary = build_categorical_summary(df).sort_values(
        "cardinality_including_missing"
    )
    sns.set_theme(style="whitegrid")
    figure, axis = plt.subplots(figsize=(9, 4.8))
    axis.barh(
        summary["feature"], summary["cardinality_including_missing"], color=BLUE
    )
    for row_index, value in enumerate(summary["cardinality_including_missing"]):
        axis.text(value + 0.3, row_index, f"{int(value)}", va="center", fontsize=9)
    axis.set_title(
        "Categorical feature cardinality", loc="left", fontweight="bold", pad=34
    )
    axis.text(
        0,
        1.015,
        f"Training set, n={len(df):,}; missing is counted as one category",
        transform=axis.transAxes,
        color="#5C6673",
        fontsize=10,
    )
    axis.set_xlabel("Distinct categories")
    axis.set_ylabel("")
    axis.grid(axis="y", visible=False)
    sns.despine(ax=axis)
    figure.tight_layout()
    figure.savefig(output_path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(figure)
    return output_path


def create_correlation_heatmap(df: pd.DataFrame, output_path: Path) -> Path:
    """숫자형 후보 간 Pearson 상관행렬 heatmap을 저장한다."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    correlation = build_numeric_correlation(df)
    sns.set_theme(style="white")
    figure, axis = plt.subplots(figsize=(8, 6.5))
    mask = np.triu(np.ones_like(correlation, dtype=bool), k=1)
    sns.heatmap(
        correlation,
        mask=mask,
        annot=True,
        fmt=".2f",
        cmap=sns.diverging_palette(35, 220, as_cmap=True),
        center=0,
        vmin=-1,
        vmax=1,
        square=True,
        linewidths=0.7,
        cbar_kws={"label": "Pearson r", "shrink": 0.8},
        ax=axis,
    )
    axis.set_title("Correlation among numeric features", loc="left", fontweight="bold", pad=18)
    axis.text(
        0,
        1.01,
        f"Training set, n={len(df):,}; association does not imply causation",
        transform=axis.transAxes,
        color="#5C6673",
        fontsize=10,
    )
    axis.tick_params(axis="x", rotation=35)
    axis.tick_params(axis="y", rotation=0)
    figure.tight_layout()
    figure.savefig(output_path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(figure)
    return output_path


def create_numeric_target_boxplots(df: pd.DataFrame, output_path: Path) -> Path:
    """Target 그룹별 숫자형 후보 분포를 small-multiple box plot으로 저장한다."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plot_data = df[EDA_NUMERIC_FEATURES + [TARGET]].copy()
    plot_data["Marriage experience"] = plot_data[TARGET].map(
        {0: "Never married", 1: "Ever married"}
    )
    display_labels = {feature: feature for feature in EDA_NUMERIC_FEATURES}
    for feature in ("capital-gain", "capital-loss"):
        plot_data[feature] = np.log1p(plot_data[feature])
        display_labels[feature] = f"log1p({feature})"

    sns.set_theme(style="whitegrid")
    figure, axes = plt.subplots(2, 3, figsize=(15, 8))
    axes_flat = axes.flatten()
    palette = {"Never married": GOLD, "Ever married": BLUE}
    for axis, feature in zip(axes_flat, EDA_NUMERIC_FEATURES):
        sns.boxplot(
            data=plot_data,
            x="Marriage experience",
            y=feature,
            hue="Marriage experience",
            palette=palette,
            legend=False,
            width=0.58,
            fliersize=1.5,
            ax=axis,
        )
        axis.set_title(display_labels[feature], loc="left", fontweight="bold")
        axis.set_xlabel("")
        axis.set_ylabel("")
        axis.tick_params(axis="x", rotation=12)
        axis.grid(axis="x", visible=False)
        sns.despine(ax=axis)
    axes_flat[-1].axis("off")
    figure.suptitle(
        "Numeric features by marriage experience",
        x=0.05,
        y=1.01,
        ha="left",
        fontsize=18,
        fontweight="bold",
        color=INK,
    )
    figure.text(
        0.05,
        0.96,
        f"Training set, n={len(df):,}; capital variables use log1p for display only",
        color="#5C6673",
        fontsize=10,
    )
    figure.tight_layout(rect=[0, 0, 1, 0.94])
    figure.savefig(output_path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(figure)
    return output_path


def create_categorical_target_rate_chart(
    df: pd.DataFrame, output_path: Path
) -> Path:
    """범주형 후보의 각 범주별 Target=1 비율을 가로 막대로 저장한다."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    rates = build_categorical_target_rates(df)
    sns.set_theme(style="whitegrid")
    figure, axes = plt.subplots(1, len(EDA_CATEGORICAL_FEATURES), figsize=(18, 8))
    for axis, feature in zip(axes, EDA_CATEGORICAL_FEATURES):
        feature_rates = rates.loc[rates["feature"] == feature].sort_values(
            "target_rate_pct"
        )
        axis.barh(
            feature_rates["category"], feature_rates["target_rate_pct"], color=BLUE
        )
        for position, row in enumerate(feature_rates.itertuples(index=False)):
            axis.text(
                min(row.target_rate_pct + 1.2, 96),
                position,
                f"{row.target_rate_pct:.1f}% (n={row.sample_size:,})",
                va="center",
                fontsize=8,
            )
        axis.set_title(feature, loc="left", fontweight="bold")
        axis.set_xlim(0, 100)
        axis.set_xlabel("Ever-married share (%)")
        axis.set_ylabel("")
        axis.grid(axis="y", visible=False)
        sns.despine(ax=axis)
    figure.suptitle(
        "Marriage experience rate by category",
        x=0.04,
        y=1.01,
        ha="left",
        fontsize=18,
        fontweight="bold",
        color=INK,
    )
    figure.text(
        0.04,
        0.96,
        f"Training set, n={len(df):,}; denominator is each category; missing is shown explicitly",
        color="#5C6673",
        fontsize=10,
    )
    figure.tight_layout(rect=[0, 0, 1, 0.94], w_pad=2.5)
    figure.savefig(output_path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(figure)
    return output_path


def create_split_target_distribution_chart(
    split_summary: pd.DataFrame, output_path: Path
) -> Path:
    """Train/Test의 Target 비율이 유지되는지 100% 누적 막대로 저장한다."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plot_data = split_summary.copy()
    plot_data["label"] = plot_data[TARGET].map(
        {0: "Never married (0)", 1: "Ever married (1)"}
    )
    pivot = plot_data.pivot(index="split", columns="label", values="percentage")
    order = ["train", "test"]
    pivot = pivot.reindex(order)

    sns.set_theme(style="whitegrid")
    figure, axis = plt.subplots(figsize=(9, 4.8))
    left = np.zeros(len(pivot))
    colors = {"Never married (0)": GOLD, "Ever married (1)": BLUE}
    for label in ["Never married (0)", "Ever married (1)"]:
        values = pivot[label].to_numpy()
        axis.barh(pivot.index, values, left=left, color=colors[label], label=label)
        for position, (start, value) in enumerate(zip(left, values)):
            axis.text(
                start + value / 2,
                position,
                f"{value:.2f}%",
                ha="center",
                va="center",
                color="white" if label == "Ever married (1)" else INK,
                fontweight="bold",
                fontsize=10,
            )
        left += values
    axis.set_title(
        "Target distribution after stratified split",
        loc="left",
        fontweight="bold",
        pad=34,
    )
    axis.text(
        0,
        1.015,
        "80% Train / 20% Test; percentages are calculated within each split",
        transform=axis.transAxes,
        color="#5C6673",
        fontsize=10,
    )
    axis.set_xlim(0, 100)
    axis.set_xlabel("Share within split (%)")
    axis.set_ylabel("")
    axis.legend(frameon=False, loc="lower center", bbox_to_anchor=(0.5, -0.35), ncol=2)
    axis.grid(axis="y", visible=False)
    sns.despine(ax=axis)
    figure.tight_layout()
    figure.savefig(output_path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(figure)
    return output_path


def create_target_association_overview(
    numeric_associations: pd.DataFrame,
    categorical_associations: pd.DataFrame,
    mutual_information: pd.DataFrame,
    output_path: Path,
) -> Path:
    """Target 관련성 지표인 상관계수·Cramér's V·MI를 3-panel로 저장한다."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid")
    figure, axes = plt.subplots(1, 3, figsize=(17, 6.5))

    numeric = numeric_associations.sort_values("point_biserial_r")
    axes[0].barh(numeric["feature"], numeric["point_biserial_r"], color=BLUE)
    for position, value in enumerate(numeric["point_biserial_r"]):
        axes[0].text(value + 0.01, position, f"{value:.3f}", va="center", fontsize=9)
    axes[0].axvline(0, color=INK, linewidth=0.8)
    axes[0].set_xlim(-0.05, max(0.6, numeric["point_biserial_r"].max() + 0.08))
    axes[0].set_title("Numeric: point-biserial r", loc="left", fontweight="bold")
    axes[0].set_xlabel("Correlation with ever_married")

    categorical = categorical_associations.sort_values("cramers_v")
    axes[1].barh(categorical["feature"], categorical["cramers_v"], color=GOLD)
    for position, value in enumerate(categorical["cramers_v"]):
        axes[1].text(value + 0.008, position, f"{value:.3f}", va="center", fontsize=9)
    axes[1].set_xlim(0, max(0.4, categorical["cramers_v"].max() + 0.06))
    axes[1].set_title("Categorical: Cramér's V", loc="left", fontweight="bold")
    axes[1].set_xlabel("Association with ever_married")

    information = mutual_information.sort_values("mutual_information")
    axes[2].barh(information["feature"], information["mutual_information"], color=BLUE)
    for position, value in enumerate(information["mutual_information"]):
        axes[2].text(value + 0.004, position, f"{value:.3f}", va="center", fontsize=9)
    axes[2].set_xlim(0, max(0.25, information["mutual_information"].max() + 0.035))
    axes[2].set_title("All candidates: Mutual Information", loc="left", fontweight="bold")
    axes[2].set_xlabel("Mutual information score")

    figure.suptitle(
        "Feature association with marriage experience",
        x=0.04,
        y=1.03,
        ha="left",
        fontsize=18,
        fontweight="bold",
        color=INK,
    )
    figure.text(
        0.04,
        0.97,
        "Training set only; association and information scores do not imply causation",
        color="#5C6673",
        fontsize=10,
    )
    for axis in axes:
        axis.grid(axis="y", visible=False)
        sns.despine(ax=axis)
    figure.tight_layout(rect=[0, 0, 1, 0.94], w_pad=2.5)
    figure.savefig(output_path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(figure)
    return output_path


def create_age_distribution_chart(train_df: pd.DataFrame, output_path: Path) -> Path:
    """혼인 경험 집단별 나이 분포 box plot을 PNG로 저장한다."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plot_data = train_df[["age", TARGET]].copy()
    plot_data["Marriage experience"] = plot_data[TARGET].map(
        {0: "Never married", 1: "Ever married"}
    )

    sns.set_theme(style="whitegrid")
    figure, axis = plt.subplots(figsize=(9, 6))
    sns.boxplot(
        data=plot_data,
        x="Marriage experience",
        y="age",
        hue="Marriage experience",
        palette={"Never married": GOLD, "Ever married": BLUE},
        legend=False,
        width=0.55,
        fliersize=2,
        ax=axis,
    )
    axis.set_title(
        "Age distribution by marriage experience",
        loc="left",
        fontsize=16,
        fontweight="bold",
        color=INK,
        pad=22,
    )
    axis.text(
        0,
        1.01,
        f"Training set, n={len(train_df):,}; box shows median and interquartile range",
        transform=axis.transAxes,
        color="#5C6673",
        fontsize=10,
    )
    axis.set_xlabel("Marriage experience at survey time")
    axis.set_ylabel("Age (years)")
    axis.grid(axis="x", visible=False)
    axis.grid(axis="y", color=GRID, linewidth=0.8)
    sns.despine(ax=axis)
    figure.tight_layout()
    figure.savefig(output_path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(figure)
    return output_path


def build_age_group_rates(train_df: pd.DataFrame) -> pd.DataFrame:
    """인터랙티브 막대그래프용 연령대별 혼인 경험 비율을 계산한다."""
    age_groups = pd.cut(
        train_df["age"],
        bins=[16, 25, 35, 45, 55, 65, 91],
        labels=["17–24", "25–34", "35–44", "45–54", "55–64", "65–90"],
        right=False,
    )
    chart_data = (
        train_df.assign(age_group=age_groups)
        .groupby("age_group", observed=True)[TARGET]
        .agg(sample_size="size", ever_married_count="sum", marriage_rate="mean")
        .reset_index()
    )
    chart_data["marriage_rate_pct"] = chart_data["marriage_rate"] * 100
    return chart_data


def build_age_rate_figure(train_df: pd.DataFrame) -> go.Figure:
    """연령대별 혼인 경험 비율 Plotly Figure를 반환한다."""
    chart_data = build_age_group_rates(train_df)
    figure = px.bar(
        chart_data,
        x="age_group",
        y="marriage_rate_pct",
        custom_data=["sample_size", "ever_married_count"],
        labels={
            "age_group": "Age group",
            "marriage_rate_pct": "Ever-married share (%)",
        },
        title=(
            "Marriage experience rate by age group"
            f"<br><sup>Training set, n={len(train_df):,}; denominator is each age group</sup>"
        ),
    )
    figure.update_traces(
        marker_color=BLUE,
        marker_line_color="#244C74",
        marker_line_width=1,
        hovertemplate=(
            "Age group: %{x}<br>"
            "Ever-married share: %{y:.1f}%<br>"
            "Sample size: %{customdata[0]:,}<br>"
            "Ever married: %{customdata[1]:,}<extra></extra>"
        ),
    )
    figure.update_layout(
        template="plotly_white",
        showlegend=False,
        font_color=INK,
        title_x=0.02,
        yaxis_range=[0, 100],
        margin={"l": 70, "r": 30, "t": 90, "b": 60},
    )
    figure.update_yaxes(gridcolor=GRID, ticksuffix="%")
    return figure


def create_interactive_age_rate_chart(
    train_df: pd.DataFrame,
    output_path: Path,
) -> Path:
    """연령대별 혼인 경험 비율 Plotly 차트를 self-contained HTML로 저장한다."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    figure = build_age_rate_figure(train_df)
    figure.write_html(output_path, include_plotlyjs=True, full_html=True)
    return output_path


def run_visualization_stage(project_root: Path, train_df: pd.DataFrame) -> None:
    """3단계 필수 정적·인터랙티브 차트를 생성한다."""
    static_path = create_age_distribution_chart(
        train_df,
        project_root / "reports" / "figures" / "age_distribution_by_marriage.png",
    )
    interactive_path = create_interactive_age_rate_chart(
        train_df,
        project_root / "reports" / "interactive" / "marriage_rate_by_age_group.html",
    )
    print("\n[3단계] 시각화 저장")
    print("Seaborn:", static_path)
    print("Plotly:", interactive_path)


def create_calibration_chart(
    target: pd.Series,
    single_probabilities: pd.Series,
    multivariable_probabilities: pd.Series,
    output_path: Path,
) -> Path:
    """단일·다변수 모델의 확률 calibration curve를 PNG로 저장한다."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    single_true, single_pred = calibration_curve(
        target,
        single_probabilities,
        n_bins=10,
        strategy="quantile",
    )
    multi_true, multi_pred = calibration_curve(
        target,
        multivariable_probabilities,
        n_bins=10,
        strategy="quantile",
    )

    sns.set_theme(style="whitegrid")
    figure, axis = plt.subplots(figsize=(8, 7))
    axis.plot([0, 1], [0, 1], linestyle="--", color="#606770", label="Ideal")
    axis.plot(
        single_pred,
        single_true,
        marker="o",
        color=GOLD,
        linewidth=2,
        label="Best single feature",
    )
    axis.plot(
        multi_pred,
        multi_true,
        marker="o",
        color=BLUE,
        linewidth=2,
        label="Multivariable logistic",
    )
    axis.set_title(
        "Probability calibration on the test set",
        loc="left",
        fontsize=16,
        fontweight="bold",
        color=INK,
        pad=22,
    )
    axis.text(
        0,
        1.01,
        f"Quantile bins; n={len(target):,}; closer to the dashed line is better",
        transform=axis.transAxes,
        color="#5C6673",
        fontsize=10,
    )
    axis.set_xlabel("Mean predicted probability")
    axis.set_ylabel("Observed ever-married share")
    axis.set_xlim(0, 1)
    axis.set_ylim(0, 1)
    axis.set_aspect("equal", adjustable="box")
    axis.grid(color=GRID, linewidth=0.8)
    axis.legend(frameon=False, loc="lower right")
    sns.despine(ax=axis)
    figure.tight_layout()
    figure.savefig(output_path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(figure)
    return output_path


def create_preprocessing_diagnostics(
    train_df: pd.DataFrame,
    output_path: Path,
) -> Path:
    """결측 대치와 log1p 효과를 보여주는 3-panel 진단 차트를 저장한다."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    audit = build_preprocessing_audit(train_df).sort_values(
        "missing_before", ascending=True
    )
    nonzero_capital_gain = train_df.loc[train_df["capital-gain"] > 0, "capital-gain"]

    sns.set_theme(style="whitegrid")
    figure, axes = plt.subplots(1, 3, figsize=(17, 5.5))

    y_positions = range(len(audit))
    axes[0].barh(
        y_positions,
        audit["missing_before"],
        height=0.62,
        color=GOLD,
        edgecolor="#9B772D",
        label="Before",
    )
    axes[0].scatter(
        audit["missing_after_imputation"],
        list(y_positions),
        color=BLUE,
        s=42,
        zorder=3,
        label="After imputation",
    )
    axes[0].set_yticks(list(y_positions), audit["feature"])
    axes[0].set_xlabel("Missing rows")
    axes[0].set_title("Missing values before and after", loc="left", fontweight="bold")
    axes[0].legend(frameon=False, loc="lower right")
    axes[0].grid(axis="y", visible=False)
    for position, count in zip(y_positions, audit["missing_before"]):
        if count:
            axes[0].text(count + 25, position, f"{count:,}", va="center", fontsize=9)

    sns.histplot(
        nonzero_capital_gain,
        bins=30,
        color=GOLD,
        edgecolor="white",
        ax=axes[1],
    )
    axes[1].set_title("Capital gain: raw scale", loc="left", fontweight="bold")
    axes[1].set_xlabel("Capital gain (non-zero rows)")
    axes[1].set_ylabel("Rows")

    sns.histplot(
        np.log1p(nonzero_capital_gain),
        bins=30,
        color=BLUE,
        edgecolor="white",
        ax=axes[2],
    )
    axes[2].set_title("Capital gain: after log1p", loc="left", fontweight="bold")
    axes[2].set_xlabel("log1p(capital gain), non-zero rows")
    axes[2].set_ylabel("Rows")

    figure.suptitle(
        "Preprocessing diagnostics",
        x=0.06,
        y=1.04,
        ha="left",
        fontsize=18,
        fontweight="bold",
        color=INK,
    )
    figure.text(
        0.06,
        0.96,
        f"Training set, n={len(train_df):,}; imputation and transforms are fitted inside each training fold",
        color="#5C6673",
        fontsize=10,
    )
    for axis in axes:
        axis.grid(color=GRID, linewidth=0.8)
        sns.despine(ax=axis)
    figure.tight_layout(rect=[0, 0, 1, 0.93])
    figure.savefig(output_path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(figure)
    return output_path
