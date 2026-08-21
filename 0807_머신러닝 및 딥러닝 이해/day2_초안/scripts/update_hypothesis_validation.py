"""day2.ipynb의 EDA 이후 가설검정·보정·강건성 셀을 검증 결과로 갱신한다."""

from pathlib import Path

import nbformat
from nbformat.v4 import new_markdown_cell


PROJECT_ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_PATH = PROJECT_ROOT / "day2.ipynb"
TAG = "hypothesis-validation"


def starts_with(cell, prefix: str) -> bool:
    return cell.cell_type == "code" and "".join(cell.source).lstrip().startswith(prefix)


notebook = nbformat.read(NOTEBOOK_PATH, as_version=4)
notebook.cells = [
    cell for cell in notebook.cells
    if TAG not in cell.get("metadata", {}).get("tags", [])
]

cell5 = next(cell for cell in notebook.cells if starts_with(cell, "# 5."))
cell5.source = cell5.source.split("\n# VALIDATION NOTES", 1)[0]
cell5.source = cell5.source.replace(
    "# 5. 분산과 분포 점검 — 등분산을 가정하지 않는 Welch 검정을 선택합니다.",
    "# 5. 가정 점검 — 분산 사전검정에 의존하지 않고 Welch 검정을 주 분석으로 사용합니다.",
)
cell5.source += r'''
# VALIDATION NOTES
# education-num은 1~16의 이산값이라 정규분포와 완전히 같지 않지만,
# 두 집단 표본이 모두 1만 이상이므로 평균의 표본분포에는 중심극한정리를 적용할 수 있습니다.
# Welch 검정은 등분산 여부에 따른 사후 선택이 아니라, 표본 수와 분산이 다른 두 집단에
# 기본적으로 안전한 평균 비교 방법으로 사전에 사용합니다.
assumption_judgement = pd.DataFrame({
    '가정/점검': ['관측 독립성', '결과변수 범위', '표본 크기', '등분산', '검정 선택'],
    '확인 결과': [
        '개인 ID가 없어 직접 검증 불가; Census 행을 서로 다른 응답자로 가정',
        f"education-num {analysis_df['education-num'].min()}~{analysis_df['education-num'].max()}",
        f'결혼 경험 있음 {len(ever):,}, 없음 {len(never):,}',
        f'Levene p={levene_p:.3e}; 분산 차이 존재',
        'Levene 결과와 무관하게 Welch를 주 분석으로 사전 지정',
    ],
    '영향': [
        '중복 24행은 동일인인지 판별할 수 없어 제한으로 기록',
        '유효 코드 범위; 평균·효과크기 해석 가능',
        '비정규·이산 분포에 대한 평균 검정의 근사 안정성 확보',
        'Student 등분산 t-test보다 Welch가 적절',
        '분산 사전검정에 따른 검정 선택 편향 방지',
    ],
})
display(assumption_judgement)
'''

cell7 = next(cell for cell in notebook.cells if starts_with(cell, "# 7."))
cell7.source = r'''# 7. 보정 분석 검증: 기본 OLS와 연령 상호작용 허용 모델(HC3 강건 표준오차)
# 비보정 평균 차이의 부호가 보정 후 바뀌므로, '결혼 경험 효과가 모든 연령에서 일정하다'는
# 기본 OLS 가정을 결혼 경험×나이, 결혼 경험×나이² 공동 검정으로 확인합니다.
y = analysis_df['education-num'].to_numpy(dtype=float)
age = analysis_df['age'].to_numpy(dtype=float)
age_z = (age-age.mean())/age.std(ddof=0)
male = analysis_df['sex'].eq('Male').to_numpy(dtype=float)
group = analysis_df['ever_married'].to_numpy(dtype=float)

def fit_ols_hc3(design, outcome, terms):
    beta = np.linalg.lstsq(design, outcome, rcond=None)[0]
    residual = outcome-design@beta
    xtx_inv = np.linalg.pinv(design.T@design)
    leverage = np.sum((design@xtx_inv)*design, axis=1)
    hc3_weight = (residual/np.clip(1-leverage, 1e-8, None))**2
    covariance = xtx_inv @ (design.T @ (hc3_weight[:, None]*design)) @ xtx_inv
    standard_error = np.sqrt(np.diag(covariance))
    statistic = beta/standard_error
    p_values = 2*stats.norm.sf(np.abs(statistic))
    ci_low = beta-stats.norm.ppf(.975)*standard_error
    ci_high = beta+stats.norm.ppf(.975)*standard_error
    result = pd.DataFrame({
        '변수': terms, '계수': beta, 'HC3 표준오차': standard_error,
        'z': statistic, 'p-value': p_values,
        '95% CI 하한': ci_low, '95% CI 상한': ci_high,
    })
    return beta, covariance, result

# 참고용 기본 모델: 결혼 경험의 보정 차이가 연령에 관계없이 일정하다고 가정
X_base = np.column_stack([np.ones(len(y)), group, age_z, age_z**2, male])
base_terms = ['절편', '결혼 경험 있음', '나이(표준화)', '나이 제곱', '남성']
base_beta, base_cov, base_result = fit_ols_hc3(X_base, y, base_terms)
base_adjusted_diff = float(base_beta[1])
base_adjusted_se = float(np.sqrt(base_cov[1, 1]))
base_adjusted_ci = (
    base_adjusted_diff-stats.norm.ppf(.975)*base_adjusted_se,
    base_adjusted_diff+stats.norm.ppf(.975)*base_adjusted_se,
)

# 검증 모델: 결혼 경험과 연령의 선형·비선형 상호작용 허용
X_interaction = np.column_stack([
    np.ones(len(y)), group, age_z, age_z**2, male,
    group*age_z, group*(age_z**2),
])
interaction_terms = [
    '절편', '결혼 경험 있음', '나이(표준화)', '나이 제곱', '남성',
    '결혼 경험×나이', '결혼 경험×나이 제곱',
]
interaction_beta, interaction_cov, interaction_result = fit_ols_hc3(
    X_interaction, y, interaction_terms
)

# 두 상호작용 계수의 공동 Wald 검정
interaction_indices = [5, 6]
interaction_vector = interaction_beta[interaction_indices]
interaction_covariance = interaction_cov[np.ix_(interaction_indices, interaction_indices)]
interaction_wald = float(
    interaction_vector @ np.linalg.pinv(interaction_covariance) @ interaction_vector
)
interaction_p = float(stats.chi2.sf(interaction_wald, df=2))

# 같은 관측자의 나이·성별을 유지하고 결혼 경험만 0/1로 바꾸는 평균 표준화
# 상호작용 모델에서 평균 차이의 contrast는 group + mean(age_z)*group:age
# + mean(age_z²)*group:age²입니다.
contrast = np.array([0, 1, 0, 0, 0, age_z.mean(), (age_z**2).mean()])
adjusted_diff = float(contrast@interaction_beta)
adjusted_se = float(np.sqrt(contrast@interaction_cov@contrast))
adjusted_ci_low = adjusted_diff-stats.norm.ppf(.975)*adjusted_se
adjusted_ci_high = adjusted_diff+stats.norm.ppf(.975)*adjusted_se
adjusted_p = float(2*stats.norm.sf(abs(adjusted_diff/adjusted_se)))
adjusted_decision = '0과 다름' if adjusted_p < ALPHA else '0과 다르다고 보기 어려움'

X_never, X_ever = X_interaction.copy(), X_interaction.copy()
X_never[:, [1, 5, 6]] = 0
X_ever[:, 1] = 1
X_ever[:, 5] = age_z
X_ever[:, 6] = age_z**2
adjusted_mean_never = float((X_never@interaction_beta).mean())
adjusted_mean_ever = float((X_ever@interaction_beta).mean())

age_balance = analysis_df.groupby('marriage_experience', observed=False).agg(
    표본수=('age', 'size'), 평균나이=('age', 'mean'), 나이표준편차=('age', 'std'),
    평균교육연수=('education-num', 'mean'), 남성비율=('sex', lambda s: s.eq('Male').mean()),
).reset_index()
display(age_balance.round(4))

interaction_check = pd.DataFrame({
    '검증': ['기본 OLS의 일정한 결혼경험 계수', '결혼경험×연령 상호작용 공동검정',
           '상호작용 허용 후 평균 표준화 차이'],
    '추정/통계량': [base_adjusted_diff, interaction_wald, adjusted_diff],
    '95% CI 또는 자유도': [f'[{base_adjusted_ci[0]:.3f}, {base_adjusted_ci[1]:.3f}]',
                         'chi-square df=2',
                         f'[{adjusted_ci_low:.3f}, {adjusted_ci_high:.3f}]'],
    'p-value': [2*stats.norm.sf(abs(base_adjusted_diff/base_adjusted_se)), interaction_p, adjusted_p],
    '판단': ['참고용: 연령별 차이 일정 가정', '상호작용 존재—일정 효과 가정 부적절',
           '모델 기반 보정 연관성'],
})
interaction_check_display = interaction_check.copy()
interaction_check_display['추정/통계량'] = interaction_check_display['추정/통계량'].map(
    lambda value: f'{value:.6f}'
)
interaction_check_display['p-value'] = interaction_check_display['p-value'].map(
    lambda value: f'{value:.3e}'
)
display(interaction_check_display)

comparison = pd.DataFrame({
    '분석': ['비보정 Welch', '기본 OLS(일정 효과)', '상호작용 허용·평균 표준화'],
    '평균 차이': [raw_diff, base_adjusted_diff, adjusted_diff],
    'CI 하한': [raw_ci_low, base_adjusted_ci[0], adjusted_ci_low],
    'CI 상한': [raw_ci_high, base_adjusted_ci[1], adjusted_ci_high],
})
fig, ax = plt.subplots(figsize=(10, 5))
xerr = np.vstack([
    comparison['평균 차이']-comparison['CI 하한'],
    comparison['CI 상한']-comparison['평균 차이'],
])
ax.errorbar(comparison['평균 차이'], comparison['분석'], xerr=xerr, fmt='o',
            markersize=9, capsize=7, linewidth=2, color='#4C78A8')
ax.axvline(0, color='black', linestyle='--', linewidth=1)
ax.set(title='비보정 평균 차이와 연령·성별 보정 연관성',
       xlabel='교육연수 차이(결혼 경험 있음 - 없음, 년)', ylabel='')
plt.tight_layout()
plt.show()
'''

cell8 = next(cell for cell in notebook.cells if starts_with(cell, "# 8."))
cell8.source = r'''# 8. 강건성 검토: 평균 차이 부트스트랩·가중 기술통계·분포 검정
BOOTSTRAPS = 5000
rng = np.random.default_rng(42)
bootstrap_differences = np.empty(BOOTSTRAPS)
for i in range(BOOTSTRAPS):
    bootstrap_differences[i] = (
        rng.choice(ever, size=len(ever), replace=True).mean()
        - rng.choice(never, size=len(never), replace=True).mean()
    )
boot_low, boot_high = np.quantile(bootstrap_differences, [.025, .975])

# Mann–Whitney는 평균 동일성 검정이 아니라 분포/순위 차이 검정이므로 보조 진단으로만 사용
u_stat, u_p = stats.mannwhitneyu(ever, never, alternative='two-sided')

# fnlwgt는 Census 표본 가중치다. 설계정보가 없어 설계기반 표준오차는 계산하지 않고,
# 가중 평균 차이가 비보정 표본 차이와 같은 방향인지 기술적 민감도만 확인한다.
never_rows = analysis_df['ever_married'].eq(0)
ever_rows = analysis_df['ever_married'].eq(1)
weighted_never = np.average(
    analysis_df.loc[never_rows, 'education-num'],
    weights=analysis_df.loc[never_rows, 'fnlwgt'],
)
weighted_ever = np.average(
    analysis_df.loc[ever_rows, 'education-num'],
    weights=analysis_df.loc[ever_rows, 'fnlwgt'],
)
weighted_diff = weighted_ever-weighted_never

robustness = pd.DataFrame({
    '방법': ['Welch t-test', '평균 차이 부트스트랩', 'fnlwgt 가중 평균(기술통계)',
           'Mann–Whitney U(분포/순위)'],
    '무엇을 검증하나': ['비보정 평균 차이', '비보정 평균 차이 CI', '모집단 가중 시 방향 민감도',
                  '평균이 아닌 분포/순위 차이'],
    '결과': [f'p={p_value:.3e}', f'95% CI [{boot_low:.3f}, {boot_high:.3f}]',
           f'가중 차이={weighted_diff:.3f}년', f'p={u_p:.3e}'],
    '해석': [welch_decision, '0 미포함' if not boot_low <= 0 <= boot_high else '0 포함',
           '비보정 차이와 같은 방향', '보조 결과—평균 가설의 대체 검정 아님'],
})
display(robustness)

fig, axes = plt.subplots(1, 2, figsize=(14, 4.8))
sns.histplot(bootstrap_differences, bins=40, kde=True, color='#72B7B2', ax=axes[0])
axes[0].axvline(0, color='black', linestyle=':', linewidth=2, label='차이 없음(H0)')
axes[0].axvline(raw_diff, color='#F58518', linewidth=2, label=f'관측 차이={raw_diff:.3f}')
axes[0].axvspan(boot_low, boot_high, color='#54A24B', alpha=.18, label='부트스트랩 95% CI')
axes[0].set(title='평균 교육연수 차이의 부트스트랩 분포', xlabel='평균 차이(년)', ylabel='빈도')
axes[0].legend()
sns.ecdfplot(data=analysis_df, x='education-num', hue='marriage_experience', linewidth=2, ax=axes[1])
axes[1].set(title='결혼 경험 여부별 교육연수 ECDF', xlabel='교육연수', ylabel='누적비율')
plt.tight_layout()
plt.show()
'''

cell9 = next(cell for cell in notebook.cells if starts_with(cell, "# 9."))
cell9.source = r'''# 9. 검증된 결론 대시보드 — 주 가설과 보정 민감도를 구분합니다.
effect_magnitude = ('매우 작음' if abs(hedges_g) < .2 else '작음' if abs(hedges_g) < .5
                    else '중간' if abs(hedges_g) < .8 else '큼')
final_summary = pd.DataFrame({
    '분석 역할': ['주 가설', '보정 민감도(참고)', '보정 민감도(권장)'],
    '분석': ['Welch t-test(비보정 평균)', '기본 OLS(일정 효과)',
           '연령 상호작용 허용·평균 표준화'],
    '차이(년)': [raw_diff, base_adjusted_diff, adjusted_diff],
    '95% CI': [f'[{raw_ci_low:.3f}, {raw_ci_high:.3f}]',
              f'[{base_adjusted_ci[0]:.3f}, {base_adjusted_ci[1]:.3f}]',
              f'[{adjusted_ci_low:.3f}, {adjusted_ci_high:.3f}]'],
    'p-value': [p_value, 2*stats.norm.sf(abs(base_adjusted_diff/base_adjusted_se)), adjusted_p],
    '해석': ['H0 기각; 비보정 차이는 매우 작음', '상호작용 검정 때문에 단일 계수 해석 제한',
           '연령·성별 보정 후 모델 기반 연관성'],
})
final_display = final_summary.copy()
final_display['차이(년)'] = final_display['차이(년)'].map(lambda value: f'{value:.4f}')
final_display['p-value'] = final_display['p-value'].map(lambda value: f'{value:.3e}')
display(final_display)

validation_summary = pd.DataFrame({
    '항목': ['주 가설 비보정 차이', '비보정 효과크기', '부트스트랩 CI',
           '가중 평균 민감도', '연령 상호작용 공동검정', '상호작용 허용 보정 차이'],
    '결과': [f'{raw_diff:.6f}', f'{hedges_g:.6f}', f'[{boot_low:.6f}, {boot_high:.6f}]',
           f'{weighted_diff:.6f}', f'chi2={interaction_wald:.6f}, p={interaction_p:.6e}',
           f'{adjusted_diff:.6f}, 95% CI [{adjusted_ci_low:.6f}, {adjusted_ci_high:.6f}]'],
    '판단': ['통계적으로 0과 다르지만 약 0.176년', f'{effect_magnitude}', 'Welch CI와 일치',
           '비보정 결과와 같은 방향', '일정한 결혼경험 계수 가정 부적절',
           '보정 후 음의 연관성; 인과효과 아님'],
})
validation_summary.to_csv('artifacts/hypothesis_validation.csv', index=False, encoding='utf-8-sig')
display(validation_summary)

fig, ax = plt.subplots(figsize=(12, 5.6))
ax.axis('off')
ax.text(.5, .88, '결혼 경험 여부에 따른 평균 교육연수 검증 결과',
        ha='center', fontsize=21, weight='bold', transform=ax.transAxes)
ax.text(.5, .69,
        f'주 가설(비보정): +{raw_diff:.3f}년 · 95% CI [{raw_ci_low:.3f}, {raw_ci_high:.3f}] · g={hedges_g:.3f}',
        ha='center', fontsize=13.5, transform=ax.transAxes)
ax.text(.5, .51,
        f'연령 상호작용 검정: p={interaction_p:.2e} → 일정한 보정효과 가정 부적절',
        ha='center', fontsize=13.5, transform=ax.transAxes)
ax.text(.5, .34,
        f'상호작용 허용 표준화 차이: {adjusted_diff:.3f}년 · 95% CI [{adjusted_ci_low:.3f}, {adjusted_ci_high:.3f}]',
        ha='center', fontsize=13.5, transform=ax.transAxes)
ax.text(.5, .15,
        '통계적 유의성과 실질적 크기를 구분하며, 모든 결과는 단면자료의 연관성이지 인과효과가 아닙니다.',
        ha='center', fontsize=11.5, color='#555555', transform=ax.transAxes)
ax.add_patch(plt.Rectangle((.03, .04), .94, .91, fill=False, linewidth=2,
                           edgecolor='#4C78A8', transform=ax.transAxes))
plt.show()
'''

insert_at = notebook.cells.index(cell9) + 1
notebook.cells.insert(
    insert_at,
    new_markdown_cell(
        """### EDA 이후 검증 결론

- **주 가설:** Welch 검정은 결혼 경험 두 집단의 실제 표본 평균 차이를 검정한다. 차이는 약 `+0.176년`이고 통계적으로 유의하지만 Hedges g가 약 `0.068`이라 실질적 크기는 매우 작다.
- **부호 반전:** 결혼 경험 있음 집단이 평균 약 15.5세 더 나이가 많아 비보정 결과에 연령 구성 차이가 섞여 있다. 연령·성별 보정 후에는 음의 연관성이 나타난다.
- **모델 검증:** 결혼 경험과 연령의 상호작용이 유의하므로, 모든 연령에서 동일한 결혼경험 계수 하나를 해석하지 않는다. 상호작용을 허용한 모델의 평균 표준화 차이를 보정 민감도로 제시한다.
- **강건성:** 평균 차이 부트스트랩과 `fnlwgt` 가중 기술통계는 비보정 차이의 방향을 지지한다. Mann–Whitney U는 평균이 아닌 분포·순위 차이의 보조 결과다.
- **해석 한계:** 주 가설의 H0 기각은 인과효과를 뜻하지 않는다. 보정 결과도 관측된 나이·성별을 통제한 모델 기반 연관성이다.
- **가중치 한계:** `fnlwgt` 가중 평균도 비보정 차이와 같은 방향이지만, 층화·군집·복제 가중치 같은 표본설계 정보가 없어 설계기반 모집단 표준오차와 p-value는 계산하지 않았다.
""",
        metadata={"tags": [TAG]},
    ),
)

nbformat.validate(notebook)
nbformat.write(notebook, NOTEBOOK_PATH)
print(f"Updated hypothesis validation cells in {NOTEBOOK_PATH}")
