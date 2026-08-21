"""소득 분류 섹션을 분리하고 교육연수 가설 기반 모델링 섹션을 추가한다."""

from pathlib import Path

import nbformat
from nbformat.v4 import new_code_cell, new_markdown_cell


PROJECT_ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_PATH = PROJECT_ROOT / "day2.ipynb"
TAG = "education-hypothesis-modeling"


notebook = nbformat.read(NOTEBOOK_PATH, as_version=4)
notebook.cells = [
    cell for cell in notebook.cells
    if TAG not in cell.get("metadata", {}).get("tags", [])
]

# 기존 소득 분류 End-to-End와 Day16 FE는 연구가설 모델과 Target이 다르므로 본문에서 제거한다.
income_starts = [
    index for index, cell in enumerate(notebook.cells)
    if cell.cell_type == "markdown" and "## 10. End-to-End 파이프라인" in "".join(cell.source)
]
if income_starts:
    income_start = income_starts[0]
    interpretation_limit = next(
        index for index, cell in enumerate(notebook.cells)
        if cell.cell_type == "markdown" and "### 해석 제한" in "".join(cell.source)
    )
    del notebook.cells[income_start:interpretation_limit]

interpretation_limit = next(
    index for index, cell in enumerate(notebook.cells)
    if cell.cell_type == "markdown" and "### 해석 제한" in "".join(cell.source)
)

new_cells = [
    new_markdown_cell(
        """## 10. 교육연수 가설 기반 모델링

### 모델링 목표

결과변수를 소득이 아니라 연구가설과 동일한 `education-num`으로 둔다.

- **M1 비보정 모델:** `교육연수 ~ 결혼 경험` — 주 가설의 표본 평균 차이를 회귀계수로 표현
- **M2 기본 보정 모델:** `+ 나이 + 나이² + 성별` — 관측된 연령·성별 구성 차이에 대한 민감도
- **M3 상호작용 모델:** `+ 결혼 경험×나이 + 결혼 경험×나이²` — 결혼 경험 차이가 연령에 따라 달라질 수 있도록 허용

OLS를 쓰는 이유는 가설이 평균 교육연수 차이에 관한 것이기 때문이다. `education-num`은 1~16의 이산값이지만 표본이 크고, 추론에는 이분산에 강한 HC3 표준오차를 사용한다. 모델 선택은 예측점수만이 아니라 가설 정합성, 상호작용 검정, 교차검증 오차를 함께 본다.
""",
        metadata={"tags": [TAG]},
    ),
    new_code_cell(
        r'''# 10-1. 동일한 5-fold×5회 분할에서 세 교육연수 모델의 일반화 오차 비교
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import RepeatedKFold

education_model_df = analysis_df[[
    'education-num', 'ever_married', 'age', 'sex'
]].copy()
education_model_df['male'] = education_model_df['sex'].eq('Male').astype(int)
education_model_df['age_sq'] = education_model_df['age']**2
education_model_df['marriage_age'] = (
    education_model_df['ever_married']*education_model_df['age']
)
education_model_df['marriage_age_sq'] = (
    education_model_df['ever_married']*education_model_df['age_sq']
)

education_model_features = {
    'M1 비보정': ['ever_married'],
    'M2 나이·성별 보정': ['ever_married', 'age', 'age_sq', 'male'],
    'M3 연령 상호작용': [
        'ever_married', 'age', 'age_sq', 'male',
        'marriage_age', 'marriage_age_sq',
    ],
}

splitter = RepeatedKFold(n_splits=5, n_repeats=5, random_state=42)
cv_rows = []
for split_number, (train_index, test_index) in enumerate(
    splitter.split(education_model_df), start=1
):
    train = education_model_df.iloc[train_index]
    test = education_model_df.iloc[test_index]
    for model_name, feature_names in education_model_features.items():
        model = LinearRegression()
        model.fit(train[feature_names], train['education-num'])
        prediction = model.predict(test[feature_names])
        cv_rows.append({
            '분할': split_number,
            '모델': model_name,
            'RMSE': mean_squared_error(test['education-num'], prediction)**0.5,
            'MAE': mean_absolute_error(test['education-num'], prediction),
            'R2': r2_score(test['education-num'], prediction),
        })

education_model_cv = pd.DataFrame(cv_rows)
education_model_comparison = (
    education_model_cv.groupby('모델', sort=False)
    .agg(
        평균_RMSE=('RMSE', 'mean'), RMSE_표준편차=('RMSE', 'std'),
        평균_MAE=('MAE', 'mean'), MAE_표준편차=('MAE', 'std'),
        평균_R2=('R2', 'mean'), R2_표준편차=('R2', 'std'),
    )
    .reset_index()
)
education_cv_pivot = education_model_cv.pivot(
    index='분할', columns='모델', values=['RMSE', 'MAE', 'R2']
)
m3_vs_m2_rmse = (
    education_cv_pivot[('RMSE', 'M3 연령 상호작용')]
    - education_cv_pivot[('RMSE', 'M2 나이·성별 보정')]
)
m3_vs_m2_mae = (
    education_cv_pivot[('MAE', 'M3 연령 상호작용')]
    - education_cv_pivot[('MAE', 'M2 나이·성별 보정')]
)
display(education_model_comparison.round(4))
print(
    f'M3−M2 평균 RMSE 변화: {m3_vs_m2_rmse.mean():+.4f} '
    f'(M3 우세 {int((m3_vs_m2_rmse < 0).sum())}/25 fold)'
)
print(
    f'M3−M2 평균 MAE 변화: {m3_vs_m2_mae.mean():+.4f} '
    f'(M3 우세 {int((m3_vs_m2_mae < 0).sum())}/25 fold)'
)

education_model_cv.to_csv(
    'artifacts/education_model_cv.csv', index=False, encoding='utf-8-sig'
)
education_model_comparison.to_csv(
    'artifacts/education_model_comparison.csv', index=False, encoding='utf-8-sig'
)

fig, ax = plt.subplots(figsize=(9, 4.8))
sns.boxplot(data=education_model_cv, x='모델', y='RMSE', color='#9ECAE1', ax=ax)
sns.stripplot(data=education_model_cv, x='모델', y='RMSE', color='#1F4E79',
              alpha=.45, size=3, ax=ax)
ax.set(title='교육연수 모델의 5-fold×5회 교차검증 RMSE', xlabel='', ylabel='RMSE(교육연수 년)')
plt.xticks(rotation=10)
plt.tight_layout()
plt.show()
''',
        metadata={"tags": [TAG]},
    ),
    new_markdown_cell(
        """### 모델 선택 기준

- M1은 연구가설과 직접 일치하지만 연령·성별 구성 차이를 고려하지 않은 주 분석이다.
- M2는 보정 민감도 모델이지만 결혼 경험 차이가 모든 연령에서 일정하다고 가정한다.
- M3는 공동 Wald 검정에서 확인된 연령 상호작용을 반영하며, 교차검증 RMSE도 가장 낮다.
- 다만 R²가 낮다는 것은 교육연수를 잘 예측하는 것이 연구 목적이 아니며, 이 변수들만으로 개인의 교육연수를 설명하기 어렵다는 뜻이다.
""",
        metadata={"tags": [TAG]},
    ),
    new_code_cell(
        r'''# 10-2. 최종 교육연수 모델과 추론 결과 저장
final_education_model = interaction_result.copy()
final_education_model['역할'] = [
    '기준 평균', '기준 연령에서 집단 차이', '미혼 집단 연령 기울기',
    '미혼 집단 연령 곡률', '성별 보정', '집단별 연령 기울기 차이',
    '집단별 연령 곡률 차이',
]
final_education_model.to_csv(
    'artifacts/education_model_final_coefficients.csv',
    index=False,
    encoding='utf-8-sig',
)

model_selection = pd.DataFrame({
    '항목': ['주 가설 모델', '최종 보정 민감도 모델', '상호작용 공동검정',
           '최종 표준화 보정 차이', '해석 범위'],
    '선택/결과': [
        'Welch t-test가 주 검정; M1 비보정 OLS는 같은 평균 차이의 회귀 표현',
        'M3 결혼 경험×나이·나이² 상호작용 OLS(HC3)',
        f'chi-square={interaction_wald:.3f}, p={interaction_p:.3e}',
        f'{adjusted_diff:.3f}년, 95% CI [{adjusted_ci_low:.3f}, {adjusted_ci_high:.3f}]',
        '관측자료의 연관성; 결혼 경험의 인과효과 아님',
    ],
    '이유': [
        '귀무가설이 두 집단 평균의 동일성에 관한 것이기 때문',
        f'연령별 집단 차이가 일정하지 않고, M2 대비 CV RMSE {m3_vs_m2_rmse.mean():+.4f}·MAE {m3_vs_m2_mae.mean():+.4f}',
        'M2의 일정한 결혼경험 계수 가정을 기각',
        '관측된 나이·성별 분포에 평균 표준화한 보정 민감도',
        '무작위 배정이 아니며 미측정 교란 가능성이 존재',
    ],
})
model_selection.to_csv(
    'artifacts/education_model_selection.csv', index=False, encoding='utf-8-sig'
)
display(model_selection)
display(final_education_model.round(6))
''',
        metadata={"tags": [TAG]},
    ),
    new_markdown_cell(
        """### 최종 모델링 결론

- **주 가설 결론:** 결혼 경험 있음 집단의 비보정 평균 교육연수는 약 `0.176년` 높지만 효과크기는 매우 작다.
- **최종 보정 모델:** 결혼 경험×연령·나이² 상호작용을 포함한 OLS(HC3)를 사용한다.
- **보정 민감도:** 관측된 나이·성별 분포에 표준화하면 결혼 경험 있음 집단이 약 `0.391년` 낮은 연관성을 보인다.
- **해석:** 비보정과 보정 결과의 부호 차이는 두 집단의 연령 구성이 크게 다르기 때문이다. 어느 결과도 결혼 경험이 교육연수를 변화시킨 인과효과로 해석하지 않는다.
- **예측 한계:** 최종 모델의 교차검증 R²가 낮으므로 개인별 교육연수 예측 모델로 사용하지 않는다.
""",
        metadata={"tags": [TAG]},
    ),
]

notebook.cells[interpretation_limit:interpretation_limit] = new_cells
nbformat.validate(notebook)
nbformat.write(notebook, NOTEBOOK_PATH)
print(f"Replaced income modeling with education modeling in {NOTEBOOK_PATH}")
