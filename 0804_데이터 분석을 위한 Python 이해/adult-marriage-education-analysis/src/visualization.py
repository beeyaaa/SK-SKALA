"""한글 EDA 정적·인터랙티브 시각화."""

from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MPL_CACHE = PROJECT_ROOT / "data" / ".matplotlib"
MPL_CACHE.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("MPLCONFIGDIR", str(MPL_CACHE))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
import numpy as np
import pandas as pd
import plotly.express as px
import seaborn as sns
from sklearn.preprocessing import MinMaxScaler, RobustScaler, StandardScaler

from src.config import HYPOTHESIS_FEATURE, NUMERIC_MODEL_FEATURES, TARGET

FONT_PATH = Path("/System/Library/Fonts/AppleSDGothicNeo.ttc")
KOREAN_FONT_NAME = "sans-serif"
if FONT_PATH.exists():
    font_manager.fontManager.addfont(str(FONT_PATH))
    KOREAN_FONT_NAME = font_manager.FontProperties(
        fname=str(FONT_PATH)
    ).get_name()
    plt.rcParams["font.family"] = KOREAN_FONT_NAME
plt.rcParams["axes.unicode_minus"] = False

BLUE = "#356AA0"
GOLD = "#D6A84B"
INK = "#20242A"
GRID = "#D9DEE5"


def _set_korean_theme(style: str = "whitegrid") -> None:
    """Seaborn 테마 적용 후에도 한글 폰트를 유지한다."""
    sns.set_theme(
        style=style,
        rc={
            "font.family": KOREAN_FONT_NAME,
            "axes.unicode_minus": False,
        },
    )


def create_target_definition_chart(df: pd.DataFrame, output_path: Path) -> Path:
    """원본 혼인 상태와 미혼/미혼 외 Target 분포를 한글 차트로 저장한다."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    status = df["marital-status"].value_counts().sort_values()
    target = df[TARGET].map({0: "미혼", 1: "미혼 외"}).value_counts()
    _set_korean_theme("whitegrid")
    figure, axes = plt.subplots(1, 2, figsize=(15, 6))
    axes[0].barh(status.index, status.values, color=BLUE)
    axes[0].set_title("원본 혼인 상태별 표본 수", loc="left", fontweight="bold")
    axes[0].set_xlabel("표본 수")
    axes[0].set_ylabel("")
    axes[1].bar(target.index, target.values, color=[GOLD if label == "미혼" else BLUE for label in target.index])
    axes[1].set_title("생성한 혼인 경험 여부 Target", loc="left", fontweight="bold")
    axes[1].set_xlabel("")
    axes[1].set_ylabel("표본 수")
    axes[1].set_ylim(0, target.values.max() * 1.18)
    for index, value in enumerate(target.values):
        axes[1].text(
            index,
            value + target.values.max() * 0.025,
            f"{value:,}\n({value / len(df):.1%})",
            ha="center",
        )
    figure.suptitle("미혼과 미혼 외 Target 정의", x=0.04, y=0.98, ha="left", fontsize=18, fontweight="bold")
    figure.text(0.04, 0.91, f"Adult Census 전체 데이터, n={len(df):,}", color="#5C6673")
    for axis in axes:
        axis.grid(axis="y", visible=False)
        sns.despine(ax=axis)
    figure.tight_layout(rect=[0, 0, 1, 0.86])
    figure.savefig(output_path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(figure)
    return output_path


def create_education_hypothesis_chart(train_df: pd.DataFrame, output_path: Path) -> Path:
    """미혼/미혼 외 집단별 교육 수준 분포와 평균을 저장한다."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plot_data = train_df[[TARGET, HYPOTHESIS_FEATURE]].copy()
    plot_data["혼인 경험 집단"] = plot_data[TARGET].map(
        {0: "미혼", 1: "미혼 외"}
    )
    palette = {"미혼": GOLD, "미혼 외": BLUE}
    _set_korean_theme("whitegrid")
    figure, axes = plt.subplots(1, 2, figsize=(14, 6))
    sns.boxplot(
        data=plot_data, x="혼인 경험 집단", y=HYPOTHESIS_FEATURE,
        hue="혼인 경험 집단", palette=palette, legend=False, ax=axes[0]
    )
    axes[0].set_title("집단별 교육 수준 분포", loc="left", fontweight="bold")
    axes[0].set_xlabel("")
    axes[0].set_ylabel("교육 수준(education-num)")
    sns.histplot(
        data=plot_data, x=HYPOTHESIS_FEATURE, hue="혼인 경험 집단",
        palette=palette, discrete=True, stat="density", common_norm=False,
        element="step", ax=axes[1]
    )
    axes[1].set_title("집단별 교육 수준 밀도", loc="left", fontweight="bold")
    axes[1].set_xlabel("교육 수준(education-num)")
    axes[1].set_ylabel("밀도")
    figure.suptitle("미혼/미혼 외 집단의 교육 수준", x=0.04, y=0.98, ha="left", fontsize=18, fontweight="bold")
    figure.text(0.04, 0.91, f"Train 데이터, n={len(train_df):,}; 원본 단위 사용", color="#5C6673")
    figure.tight_layout(rect=[0, 0, 1, 0.86])
    figure.savefig(output_path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(figure)
    return output_path


def create_multicollinearity_chart(
    train_df: pd.DataFrame, vif: pd.DataFrame, output_path: Path
) -> Path:
    """숫자형 상관행렬과 VIF를 함께 저장한다."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    correlation = train_df[NUMERIC_MODEL_FEATURES].corr()
    _set_korean_theme("white")
    figure, axes = plt.subplots(1, 2, figsize=(15, 6))
    sns.heatmap(
        correlation, annot=True, fmt=".2f", cmap="vlag", center=0,
        vmin=-1, vmax=1, square=True, linewidths=0.6, ax=axes[0]
    )
    axes[0].set_title("숫자형 변수 상관행렬", loc="left", fontweight="bold")
    ordered = vif.sort_values("VIF")
    axes[1].barh(ordered["변수"], ordered["VIF"], color=BLUE)
    axes[1].axvline(5, color=GOLD, linestyle="--", label="주의 기준 VIF=5")
    axes[1].set_title("숫자형 변수 VIF", loc="left", fontweight="bold")
    axes[1].set_xlabel("VIF")
    axes[1].set_ylabel("")
    axes[1].legend(frameon=False)
    figure.suptitle("다중공선성 진단", x=0.04, y=0.98, ha="left", fontsize=18, fontweight="bold")
    figure.text(0.04, 0.91, f"Train 데이터, n={len(train_df):,}", color="#5C6673")
    figure.tight_layout(rect=[0, 0, 1, 0.86])
    figure.savefig(output_path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(figure)
    return output_path


def create_interactive_education_rate(train_df: pd.DataFrame, output_path: Path) -> Path:
    """교육 수준별 미혼 외 비율 Plotly HTML을 저장한다."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    rates = (
        train_df.groupby(HYPOTHESIS_FEATURE)[TARGET]
        .agg(표본수="size", 미혼외표본수="sum", 미혼외비율="mean")
        .reset_index()
    )
    rates["미혼 외 비율(%)"] = rates["미혼외비율"] * 100
    figure = px.bar(
        rates, x=HYPOTHESIS_FEATURE, y="미혼 외 비율(%)",
        custom_data=["표본수", "미혼외표본수"],
        labels={HYPOTHESIS_FEATURE: "교육 수준(education-num)"},
        title="교육 수준별 미혼 외 비율<br><sup>Train 데이터, 각 교육 수준이 분모</sup>",
    )
    figure.update_traces(
        marker_color=BLUE,
        hovertemplate="교육 수준: %{x}<br>미혼 외 비율: %{y:.1f}%<br>표본 수: %{customdata[0]:,}<br>미혼 외: %{customdata[1]:,}<extra></extra>",
    )
    figure.update_layout(template="plotly_white", showlegend=False, font_color=INK)
    figure.update_yaxes(range=[0, 100], ticksuffix="%")
    figure.write_html(output_path, include_plotlyjs=True, full_html=True)
    return output_path


def create_feature_audit_chart(
    train_df: pd.DataFrame, audit: pd.DataFrame, output_path: Path
) -> Path:
    """결측률·이상치율·고유값·Target 비율을 한 화면에 저장한다."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    _set_korean_theme("whitegrid")
    figure, axes = plt.subplots(2, 2, figsize=(15, 10))

    missing = audit.loc[audit["결측률(%)"] > 0].sort_values("결측률(%)")
    axes[0, 0].barh(missing["컬럼"], missing["결측률(%)"], color=BLUE)
    axes[0, 0].set_title("컬럼별 결측률", loc="left", fontweight="bold")
    axes[0, 0].set_xlabel("결측률(%)")

    outliers = audit.dropna(subset=["IQR 이상치율(%)"]).sort_values("IQR 이상치율(%)")
    axes[0, 1].barh(outliers["컬럼"], outliers["IQR 이상치율(%)"], color=GOLD)
    axes[0, 1].set_title("숫자형 변수의 IQR 이상치 후보", loc="left", fontweight="bold")
    axes[0, 1].set_xlabel("후보 비율(%)")

    categorical = audit.loc[audit["타입"].isin(["object", "string"]), :].sort_values("고유값 수")
    axes[1, 0].barh(categorical["컬럼"], categorical["고유값 수"], color=BLUE)
    axes[1, 0].set_title("범주형 변수의 고유값 수", loc="left", fontweight="bold")
    axes[1, 0].set_xlabel("고유값 수")

    target_counts = train_df[TARGET].map({0: "미혼", 1: "미혼 외"}).value_counts()
    axes[1, 1].bar(
        target_counts.index,
        target_counts.values,
        color=[GOLD if label == "미혼" else BLUE for label in target_counts.index],
    )
    axes[1, 1].set_title("Train Target 분포", loc="left", fontweight="bold")
    axes[1, 1].set_ylabel("표본 수")
    axes[1, 1].set_ylim(0, target_counts.max() * 1.15)
    for index, value in enumerate(target_counts.values):
        axes[1, 1].text(index, value + target_counts.max() * 0.025, f"{value:,}\n({value/len(train_df):.1%})", ha="center")

    figure.suptitle("Feature Engineering 전 데이터 진단", x=0.04, y=0.99, ha="left", fontsize=18, fontweight="bold")
    figure.text(0.04, 0.955, f"Train 데이터만 사용, n={len(train_df):,}", color="#5C6673")
    for axis in axes.flat:
        sns.despine(ax=axis)
    figure.tight_layout(rect=[0, 0, 1, 0.93])
    figure.savefig(output_path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(figure)
    return output_path


def create_transformation_chart(train_df: pd.DataFrame, output_path: Path) -> Path:
    """capital-gain/loss의 log1p 변환 전후 분포를 비교한다."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    _set_korean_theme("whitegrid")
    figure, axes = plt.subplots(2, 2, figsize=(15, 9))
    specs = [
        ("capital-gain", "자본 이득 원본", False),
        ("capital-gain", "자본 이득 log1p", True),
        ("capital-loss", "자본 손실 원본", False),
        ("capital-loss", "자본 손실 log1p", True),
    ]
    for axis, (column, title, use_log) in zip(axes.flat, specs):
        positive = train_df.loc[train_df[column] > 0, column]
        values = np.log1p(positive) if use_log else positive
        sns.histplot(values, bins=35, color=BLUE, ax=axis)
        axis.set_title(title, loc="left", fontweight="bold")
        axis.set_xlabel("log1p 값" if use_log else "원본 값")
        axis.set_ylabel("표본 수")
        axis.text(
            0.98, 0.94,
            f"0 비율 {train_df[column].eq(0).mean():.1%}\n양수 n={len(positive):,}",
            transform=axis.transAxes, ha="right", va="top", color="#5C6673",
        )
        sns.despine(ax=axis)
    figure.suptitle("긴 꼬리 분포의 로그 변환 전·후", x=0.04, y=0.99, ha="left", fontsize=18, fontweight="bold")
    figure.text(0.04, 0.95, "형태 비교를 위해 양수 관측값만 표시; 변환에서는 0을 그대로 유지", color="#5C6673")
    figure.tight_layout(rect=[0, 0, 1, 0.92])
    figure.savefig(output_path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(figure)
    return output_path


def create_scaling_comparison_chart(train_df: pd.DataFrame, output_path: Path) -> Path:
    """MinMax·Standard·Robust 스케일링의 결과를 비교한다."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    from src.feature_engineering import engineer_features
    columns = ["age", "education-num", "hours-per-week", "capital-gain-log", "capital-loss-log"]
    sample = engineer_features(train_df)[columns].sample(min(6_000, len(train_df)), random_state=42)
    scalers = [
        ("원본", None),
        ("Min-Max", MinMaxScaler()),
        ("Standard", StandardScaler()),
        ("Robust", RobustScaler()),
    ]
    _set_korean_theme("whitegrid")
    figure, axes = plt.subplots(2, 2, figsize=(16, 10))
    for axis, (name, scaler) in zip(axes.flat, scalers):
        values = sample.to_numpy() if scaler is None else scaler.fit_transform(sample)
        long_data = pd.DataFrame(values, columns=columns).melt(var_name="변수", value_name="변환 값")
        sns.boxplot(data=long_data, x="변수", y="변환 값", color=BLUE, showfliers=False, ax=axis)
        axis.set_title(name, loc="left", fontweight="bold")
        axis.set_xlabel("")
        axis.tick_params(axis="x", rotation=20)
        sns.despine(ax=axis)
    figure.suptitle("스케일링 방법 비교", x=0.04, y=0.99, ha="left", fontsize=18, fontweight="bold")
    figure.text(0.04, 0.95, "Train 표본 6,000개; 박스플롯의 극단점은 표시하지 않음", color="#5C6673")
    figure.tight_layout(rect=[0, 0, 1, 0.92])
    figure.savefig(output_path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(figure)
    return output_path


def create_encoding_summary_chart(
    train_df: pd.DataFrame, feature_names: list[str], output_path: Path
) -> Path:
    """범주형 고유값 수와 One-Hot 출력 컬럼 수를 비교한다."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    engineered_columns = ["workclass", "occupation", "income", "age-group", "hours-group"]
    from src.feature_engineering import engineer_features
    engineered = engineer_features(train_df)
    raw_counts = pd.Series({column: engineered[column].nunique(dropna=True) for column in engineered_columns})
    encoded_counts = pd.Series({
        column: sum(f"categorical__{column}_" in name for name in feature_names)
        for column in engineered_columns
    })
    comparison = pd.DataFrame({"원본 고유값": raw_counts, "인코딩 후 컬럼": encoded_counts}).reset_index(names="변수")
    long_data = comparison.melt(id_vars="변수", var_name="구분", value_name="개수")
    _set_korean_theme("whitegrid")
    figure, axis = plt.subplots(figsize=(12, 6))
    sns.barplot(data=long_data, y="변수", x="개수", hue="구분", palette=[GOLD, BLUE], ax=axis)
    axis.set_title("범주형 변수의 One-Hot Encoding 결과", loc="left", fontweight="bold")
    axis.set_xlabel("범주 또는 출력 컬럼 수")
    axis.set_ylabel("")
    axis.legend(frameon=False, title="")
    sns.despine(ax=axis)
    figure.suptitle("인코딩 전·후 차원 비교", x=0.04, y=0.99, ha="left", fontsize=18, fontweight="bold")
    figure.text(0.04, 0.93, "Train 기준 1% 미만 희소 범주 통합, 첫 범주는 기준 범주로 제외", color="#5C6673")
    figure.tight_layout(rect=[0, 0, 1, 0.90])
    figure.savefig(output_path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(figure)
    return output_path
