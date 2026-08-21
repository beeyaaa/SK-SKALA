"""분석 산출물을 모아 최종 reports/report.md를 생성한다."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


def _markdown_table(frame: pd.DataFrame, decimals: int = 4) -> str:
    """외부 tabulate 의존성 없이 작은 DataFrame을 Markdown 표로 변환한다."""
    display = frame.copy()
    for column in display.select_dtypes(include="number").columns:
        if "p_value" in str(column) or str(column).endswith("p_holm"):
            display[column] = display[column].map(
                lambda value: (
                    "<1e-300"
                    if pd.notna(value) and value == 0
                    else f"{value:.2e}"
                    if pd.notna(value)
                    else ""
                )
            )
        else:
            display[column] = display[column].map(
                lambda value: f"{value:.{decimals}f}" if pd.notna(value) else ""
            )
    headers = [str(column) for column in display.columns]
    rows = [[str(value) for value in row] for row in display.to_numpy()]
    lines = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join(["---"] * len(headers)) + " |",
    ]
    lines.extend("| " + " | ".join(row) + " |" for row in rows)
    return "\n".join(lines)


def generate_report(project_root: Path) -> Path:
    """실행 결과 CSV와 그림을 읽어 한국어 최종 분석 보고서를 생성한다."""
    table_dir = project_root / "reports" / "tables"
    report_path = project_root / "reports" / "report.md"
    required = {
        "data_quality": "pandas_polars_summary.csv",
        "target": "target_distribution.csv",
        "missingness": "eda_missingness.csv",
        "numeric_associations": "numeric_associations.csv",
        "categorical_associations": "categorical_associations.csv",
        "mutual_information": "mutual_information.csv",
        "single_cv": "single_feature_cv.csv",
        "metrics": "model_metrics.csv",
        "hypothesis": "hypothesis_result.csv",
        "importance": "permutation_importance.csv",
    }
    missing_files = [name for name in required.values() if not (table_dir / name).exists()]
    if missing_files:
        raise FileNotFoundError(f"보고서 생성에 필요한 결과 파일이 없습니다: {missing_files}")

    tables = {
        key: pd.read_csv(table_dir / filename) for key, filename in required.items()
    }
    hypothesis = tables["hypothesis"].iloc[0]
    best_feature = str(hypothesis["best_single_feature"])
    reject_h0 = bool(hypothesis["ci_entirely_above_margin"])
    conclusion = (
        "H₀를 기각하고 H₁을 지지한다."
        if reject_h0
        else "H₀를 기각할 충분한 근거가 없다. H₀가 참임을 증명한 것은 아니다."
    )

    report = f"""# Adult Census 혼인 경험 예측 분석 보고서

## 1. 연구 질문과 가설

1994년 미국 Adult Census 표본에서 나이·학력·직업 등 여러 특성을 함께 사용하면, 최적 단일 특성만 사용했을 때보다 조사 시점까지의 혼인 경험 여부를 실질적으로 더 잘 예측할 수 있는가?

- H₀: 여러 특성 모델은 최적 단일 특성 모델보다 혼인 경험 여부의 예측 성능을 실질적으로 개선하지 못한다.
- H₁: 여러 특성 모델은 최적 단일 특성 모델보다 혼인 경험 여부의 예측 성능을 실질적으로 개선한다.
- 주 지표: ROC-AUC
- 사전 정의한 실질적 개선 기준: AUC 차이 0.02 초과

이 분석의 확률은 미래 결혼 가능성이 아니라, **1994년 표본에서 비슷한 특성의 사람이 조사 시점까지 한 번 이상 혼인했을 추정 확률**이다.

## 2. 데이터 준비와 품질

Pandas와 Polars로 동일한 UCI Adult 원본을 불러와 행·열, 컬럼 순서, 결측치, 고유값과 중복 행을 비교했다.

{_markdown_table(tables['data_quality'], 0)}

- 완전 중복 24행은 개인 식별자가 없어 동일인 중복으로 단정할 수 없으므로 자동 삭제하지 않았다.
- 결측치는 모델 Pipeline 내부에서만 대치한다.

### 결측치

{_markdown_table(tables['missingness'], 2)}

![결측치](figures/eda_missing_values.png)

## 3. Target과 입력 특성

- Target 0: `Never-married`
- Target 1: 혼인, 이혼, 별거, 사별 경험

{_markdown_table(tables['target'], 2)}

기본 입력은 `age`, `education-num`, `hours-per-week`, `capital-gain`, `capital-loss`, `workclass`, `occupation`이다. `marital-status`와 `relationship`은 정답 누수, `fnlwgt`는 표본 가중치, `education`은 중복 정보이므로 제외했다.

## 4. 분할과 EDA

전체 데이터를 Target 비율을 유지해 Train 80%(26,048행), Test 20%(6,513행)로 나눴다. 분할 이후의 EDA·통계검정·MI·단일 특성 선택은 Train에서만 수행했다.

![Stratified Target 분할](figures/eda_stratified_target_split.png)

![숫자형 분포](figures/eda_numeric_distributions.png)

![숫자형 Target 관계](figures/eda_numeric_by_target.png)

![범주별 Target 비율](figures/eda_categorical_target_rates.png)

- `capital-gain`과 `capital-loss`는 0이 많고 오른쪽 꼬리가 길어 모델에서 `log1p`를 적용했다.
- IQR 바깥 관측치는 실제 가능한 Census 응답이므로 자동 삭제하지 않았다.
- 숫자형 변수 간 상관은 전반적으로 낮았다.

## 5. 통계 분석과 Mutual Information

### 숫자형 변수와 Target

{_markdown_table(tables['numeric_associations'][['feature', 'point_biserial_r', 'welch_p_value', 'welch_p_holm', 'cohens_d']], 4)}

### 범주형 변수와 Target

{_markdown_table(tables['categorical_associations'][['feature', 'categories', 'p_value', 'p_holm', 'cramers_v']], 4)}

### Mutual Information

{_markdown_table(tables['mutual_information'], 4)}

![Target 관련성 지표](figures/eda_target_associations.png)

상관계수, 효과크기와 MI는 예측 관련성을 나타낼 뿐 인과관계를 의미하지 않는다. 최적 단일 특성은 이 표를 보고 임의로 확정하지 않고 동일한 5-fold 교차검증으로 선택했다.

## 6. 모델 전처리 Pipeline

- `age`, `education-num`, `hours-per-week`: median 대치 → StandardScaler
- `capital-gain`, `capital-loss`: median 대치 → log1p → StandardScaler
- `workclass`, `occupation`: `Unknown` 대치 → OneHotEncoder(`handle_unknown='ignore'`)

Imputer, log 변환, scaler와 encoder는 모두 Pipeline 내부에서 각 Train fold에만 fit하여 데이터 누수를 방지했다.

![전처리 진단](figures/preprocessing_diagnostics.png)

## 7. 최적 단일 특성 선택

{_markdown_table(tables['single_cv'], 4)}

Train 5-fold 평균 ROC-AUC가 가장 높은 `{best_feature}`를 최적 단일 특성으로 선택했다. Test 결과를 보고 단일 특성을 다시 선택하지 않았다.

## 8. 단일 모델과 다변수 모델 비교

{_markdown_table(tables['metrics'], 4)}

![Calibration](figures/calibration_curve.png)

### 원본 특성 Permutation Importance

{_markdown_table(tables['importance'], 4)}

## 9. 가설 판단

{_markdown_table(tables['hypothesis'], 4)}

다변수 모델과 단일 모델의 AUC 차이는 {hypothesis['auc_delta']:.4f}, bootstrap 95% 신뢰구간은 [{hypothesis['auc_delta_ci_low']:.4f}, {hypothesis['auc_delta_ci_high']:.4f}]이다. 사전 기준 0.02를 넘지 못했으므로 **{conclusion}**

## 10. 한계와 주의사항

1. Adult 데이터는 1994년 미국 Census 표본이므로 현재 한국 개인에게 직접 일반화할 수 없다.
2. 예측은 조사 시점까지의 혼인 경험이며 개인의 미래 결혼 가능성을 뜻하지 않는다.
3. 관측자료의 연관성 분석이므로 결혼의 원인을 설명하지 않는다.
4. 나이는 혼인 기회에 노출된 기간을 강하게 반영하므로 높은 예측력이 인과적 효과를 의미하지 않는다.
5. race·sex·native-country는 기본 모델에서 제외했지만 실제 활용 전에는 별도의 집단별 성능·공정성 점검이 필요하다.
6. 실질적 개선 기준 0.02는 분석 전에 정한 프로젝트 기준이며 보편적 기준은 아니다.

## 11. 재현 방법

```bash
../.venv/bin/python run_analysis.py
../.venv/bin/python -m jupyter nbconvert --execute --to notebook --inplace notebooks/*.ipynb
```
"""
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")
    return report_path
