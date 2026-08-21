"""day2.ipynb에 Day16 방식 Feature Engineering 실험 섹션을 추가한다."""

from pathlib import Path

import nbformat
from nbformat.v4 import new_code_cell, new_markdown_cell


PROJECT_ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_PATH = PROJECT_ROOT / "day2.ipynb"
TAG = "day16-feature-engineering"


def tagged(cell):
    return TAG in cell.get("metadata", {}).get("tags", [])


notebook = nbformat.read(NOTEBOOK_PATH, as_version=4)
notebook.cells = [cell for cell in notebook.cells if not tagged(cell)]

new_cells = [
    new_markdown_cell(
        """## 11. Day16 방식 Feature Engineering 실험

### Goal

Day16의 `Baseline → 로그 변환 → 파생변수 → 이상치 처리 → 성능 비교` 흐름을 Adult Census 소득 분류에 적용한다.

> **가설 분석과의 구분:** 이 절의 Target은 소득(`>50K`)이다. 본 프로젝트의 연구가설인 “결혼 경험 유무에 따른 평균 교육연수 차이”를 검정하는 Welch t-test·보정 OLS와는 별도의 예측 실험이다. 여기서 채택된 로그·자본·연령/근무시간 구간 feature를 가설 검정에 넣었다는 뜻이 아니다.

### Key Assumptions

- 모든 실험은 동일한 80:20 계층화 분할(`random_state=42`)을 사용한다.
- 결측 대체, 스케일링, 인코딩, IQR clip 경계는 Train에서만 학습한다.
- 이진 Target인 소득 라벨에는 로그 변환을 적용하지 않는다.
- IQR 후보는 오류가 아닐 수 있으므로 `none`, `clip`, `remove`를 성능으로 비교한다.
- 채택 조건은 현재 조합보다 F1과 PR-AUC가 모두 비하락하고, 둘 중 하나 이상 상승하는 것이다.
""",
        metadata={"tags": [TAG]},
    ),
    new_markdown_cell(
        """### 11-1. 기존 처리와 이번 개선의 경계

현재 프로젝트에 원래 있던 전처리를 모두 새로 만든 것은 아니다. 아래 표는 `수정 전 기존 설정`과 `현재 설정`을 구분하고, 각 행에 `유지·변경 이유`와 실제 `검증 결과·최종 판단`을 함께 적는다. 즉 표시만 보고 판단하지 않고 근거 수치까지 같은 행에서 확인한다.
""",
        metadata={"tags": [TAG]},
    ),
    new_code_cell(
        """from day2_pipeline import run_feature_engineering_experiments

feature_experiment = run_feature_engineering_experiments(
    data_path='adult.data',
    output_dir='artifacts',
)
display(feature_experiment.preprocessing_provenance)
""",
        metadata={"tags": [TAG]},
    ),
    new_markdown_cell(
        """### 11-2. 기존 데이터 정리 근거

문자열 공백 제거, `?` 결측 변환, 소득 라벨 정규화는 성능 튜닝보다 데이터 형식과 재현성을 위한 처리다. 따라서 성능 대신 실제 변경 건수와 목적을 확인한다.
""",
        metadata={"tags": [TAG]},
    ),
    new_code_cell(
        """display(feature_experiment.data_hygiene_audit)
""",
        metadata={"tags": [TAG]},
    ),
    new_markdown_cell(
        """### 11-3. 기존 전처리별 성능 기여

각 검증 항목 안에서 첫 행을 비교 기준으로 사용한다. 모든 모델은 같은 Train/Test 분할과 같은 L2 `liblinear` 로지스틱 회귀를 사용한다.

- **범주형 인코딩:** 수치형만 사용한 모델과 One-Hot을 추가한 모델 비교
- **스케일링:** 동일 변수에서 StandardScaler 적용 전후 비교
- **결측 처리:** 결측 컬럼 제외, 최빈값 대치, Unknown 대치 비교
- **희소 범주:** 기존 2건 기준과 1% 후보를 단일 Holdout 및 5×5 반복 교차검증으로 비교
- **완전 중복:** 유지와 Train 중복 제거 비교
""",
        metadata={"tags": [TAG]},
    ),
    new_code_cell(
        """existing_ablation_display = feature_experiment.existing_preprocessing_ablation.copy()
existing_metric_columns = [
    'Accuracy', 'Precision', 'Recall', 'F1', 'ROC-AUC', 'PR-AUC',
    '그룹 기준 F1 변화', '그룹 기준 PR-AUC 변화',
]
existing_ablation_display[existing_metric_columns] = existing_ablation_display[existing_metric_columns].round(4)
display(existing_ablation_display)

rare_cv_summary = (
    feature_experiment.rare_category_cv_audit.groupby('설정', sort=False)
    .agg(
        평균_Feature_수=('Feature 수', 'mean'),
        평균_F1=('F1', 'mean'),
        F1_표준편차=('F1', 'std'),
        평균_PR_AUC=('PR-AUC', 'mean'),
        PR_AUC_표준편차=('PR-AUC', 'std'),
    )
    .reset_index()
)
print('희소 범주 기준 5-fold × 5회 반복 교차검증')
display(rare_cv_summary.round(4))

print('LogisticRegression max_iter 수렴 검사')
display(feature_experiment.model_convergence_audit.round(4))
""",
        metadata={"tags": [TAG]},
    ),
    new_markdown_cell(
        """### 11-4. 기존 전처리 결과 해석

- **One-Hot Encoding:** 수치형만 사용했을 때보다 F1이 **0.5226→0.6725**, PR-AUC가 **0.6645→0.7733**으로 크게 개선된다. 범주형 정보 사용의 근거가 충분하다.
- **StandardScaler:** 미적용보다 F1이 **0.3928→0.6725**, PR-AUC가 **0.4750→0.7733**으로 개선된다. `fnlwgt`와 자본 변수처럼 범위가 큰 값이 있는 L2 로지스틱 회귀에서 필수에 가깝다. 이 개선 폭은 현재 solver와 규제 설정에 대한 결과다.
- **결측치 대치:** 결측이 있는 세 컬럼을 제외한 모델보다 최빈값 대치는 F1 **+0.0269**, PR-AUC **+0.0179**이고, `Unknown` 대치는 F1 **+0.0292**, PR-AUC **+0.0218**이다. 행이나 변수를 버리는 것보다 정보를 보존하는 편이 낫다.
- **Feature를 줄인다고 자동으로 좋아지는 것은 아니다.** 차원이 줄면 계산량과 희소계수 분산이 감소할 수 있지만, 유용한 소수 범주 정보도 함께 사라질 수 있다.
- **단일 Holdout만 보면:** 1% 기준은 Feature를 **105→63**으로 줄이고 F1 **+0.0007**, PR-AUC **+0.0009**였지만 차이가 너무 작다.
- **5-fold×5회 반복 교차검증:** 1%−2건 평균은 F1 약 **-0.0014**, PR-AUC 약 **-0.0001**이며, F1이 좋아진 fold도 **8/25**뿐이다. 개선이 일관되지 않으므로 1%를 제외하고 기존 `min_frequency=2`를 유지한다.
- **Train 중복 제거:** 17행을 제거했지만 F1 **-0.0005**, PR-AUC **-0.0000**으로 개선되지 않는다. 개인 식별자가 없는 Census에서는 자동 삭제 근거가 부족하다.
- **문자열·라벨 정규화:** 현재 단일 파일 성능보다는 결측 인식과 `adult.test` 호환성을 위한 필수 데이터 품질 처리다.
""",
        metadata={"tags": [TAG]},
    ),
    new_markdown_cell(
        """### 11-5. IQR와 도메인 검사를 분리한 이상치 감사

IQR은 ‘분포에서 드문 값’을 찾지만 오류 여부를 판단하지 않는다. 따라서 IQR 후보 수와 함께 사전에 정의한 유효 범위 위반 수를 확인한다.

- [UCI Adult 공식 설명](https://archive.ics.uci.edu/dataset/2/adult)의 추출 조건인 `age>16`, `fnlwgt>1`, `hours-per-week>0`을 하한 검사의 근거로 사용한다.
- 도메인 위반이 0이면 관측값은 허용 범위 안에 있다.
- `capital-gain/loss`는 Q1=Q3=0이라 IQR=0이므로 IQR 삭제 기준이 부적합하다.
- IQR 후보의 고소득률도 확인해 단순 노이즈가 아니라 다른 특성을 가진 집단인지 점검한다.
- 공식 설명이 상한을 제공하지 않는 변수는 높은 값의 진위를 이 검사만으로 확정할 수 없다.
""",
        metadata={"tags": [TAG]},
    ),
    new_code_cell(
        """audit_display = feature_experiment.outlier_audit.copy()
ratio_columns = [
    '0 비율', 'IQR 후보 비율', 'IQR 후보 고소득률', 'IQR 정상범위 고소득률',
]
for column in ratio_columns:
    audit_display[column] = audit_display[column].map(
        lambda value: '' if pd.isna(value) else f'{value:.2%}'
    )
audit_display['왜도'] = audit_display['왜도'].round(3)
display(audit_display)
""",
        metadata={"tags": [TAG]},
    ),
    new_markdown_cell(
        """### 11-6. 로그 변환 전후 왜도 근거

`capital-gain`, `capital-loss`, `fnlwgt`에 대해 Train 데이터에서 `log1p` 전후 왜도와 범위 압축을 비교한다. 왜도가 줄어도 예측 성능이 낮아지면 자동으로 채택하지 않는다.
""",
        metadata={"tags": [TAG]},
    ),
    new_code_cell(
        """log_audit_display = feature_experiment.log_transform_audit.copy()
log_audit_display['0 비율'] = log_audit_display['0 비율'].map(lambda value: f'{value:.2%}')
numeric_log_columns = [
    '왜도 전', '왜도 후', '절대왜도 변화', 'P99 전', 'P99 후', '최댓값 전', '최댓값 후',
]
log_audit_display[numeric_log_columns] = log_audit_display[numeric_log_columns].round(3)
display(log_audit_display)
""",
        metadata={"tags": [TAG]},
    ),
    new_markdown_cell(
        """### 11-7. 신규 Feature Engineering forward selection

#### Baseline 구분

- **수정 전 기존 모델:** 전체 데이터에서 `Unknown` 대치와 중복 24행 제거 → 80:20 분할 → StandardScaler → One-Hot(`min_frequency=2`) → 로지스틱 회귀
- **이번 01 개선 Baseline:** 80:20 분할을 먼저 수행 → Train에서만 수치 중앙값·범주 `Unknown` 대치·StandardScaler·One-Hot(`min_frequency=2`) fit → 중복 유지
- 따라서 01은 누수 방지와 결측 처리 순서를 개선했지만, 희소 범주 기준은 반복 교차검증 결과에 따라 기존 2건을 유지한다.

#### 선택 방식

1. **Baseline:** 원본 수치형 + 범주형 전처리
2. **+ log1p:** 원본 열은 유지하고 `capital-gain`, `capital-loss`, `fnlwgt`의 로그 열 추가
3. **+ 자본 파생:** 순자본소득, 자본 활동 여부, 시간당 자본이익
4. **+ 구간화:** 연령대, 주당 근무시간 구간
5. **+ 상호작용:** 교육×직업, 나이×근로시간
6. **+ IQR clip:** Train IQR 경계로 `age`, `fnlwgt`, `hours-per-week` clip
7. **+ IQR remove:** 같은 경계 밖의 Train 행 제거, Test 유지

- 각 후보는 **현재까지 채택된 최적 조합 + 후보 하나**로 시험한다.
- 후보의 F1과 PR-AUC가 모두 현재 조합보다 낮아지지 않고, 둘 중 하나 이상 높아질 때만 채택한다.
- 성능이 하락한 후보는 즉시 제외하며 다음 후보 조합에도 남기지 않는다.
- 06과 07은 feature 선택이 끝난 같은 조합에서 `none` 대비 `clip`, `remove`를 각각 비교한다.
- `비교 기준 대비`는 표의 `비교 기준` 조합과의 차이이고, `Baseline 대비`는 01과의 총 차이다.
""",
        metadata={"tags": [TAG]},
    ),
    new_code_cell(
        """comparison_display = feature_experiment.comparison.copy()
metric_columns = [
    'Accuracy', 'Precision', 'Recall', 'F1', 'ROC-AUC', 'PR-AUC',
    '비교 기준 대비 F1', '비교 기준 대비 PR-AUC',
    'Baseline 대비 F1', 'Baseline 대비 PR-AUC',
]
comparison_display[metric_columns] = comparison_display[metric_columns].round(4)
display(comparison_display)

print('최종 채택 블록의 실제 변수·계산·선택 근거')
display(feature_experiment.selected_feature_details)

print('채택 규칙으로 선택한 최종 조합:', feature_experiment.best_experiment)
print('저장 모델:', feature_experiment.model_path)
print('상세 보고서:', feature_experiment.report_path)

from IPython.display import Image
display(Image(filename=str(feature_experiment.chart_path)))
""",
        metadata={"tags": [TAG]},
    ),
    new_markdown_cell(
        """### 11-8. 결과 해석 원칙

- 표의 `채택 결과=제외`인 전처리는 최종 모델에 들어가지 않는다.
- `log + capital + bins`는 모델에 들어가는 단일 변수명이 아니라 세 feature 묶음의 코드명이다. 바로 위 상세 표에서 생성 변수·계산식·추가 이유·성능 근거를 확인한다.
- `시험 조합`은 해당 후보를 평가할 때만 사용한 조합이고, `비교 기준`은 그 직전의 실제 최적 조합이다.
- 연령·근무시간 구간화의 `채택`은 소득 분류 성능 기준이다. 결혼 경험별 평균 교육연수 가설에는 적용하지 않는다.
- 완전 중복은 개인 식별자가 없어 서로 다른 사람이 같은 응답을 했을 가능성이 있으며, Train 중복 제거 실험에서도 성능이 개선되지 않아 유지한다.
- 도메인 위반이 0건이라는 사실과 IQR 후보 비율을 함께 봐서, IQR 밖이라는 이유만으로 유효 응답을 오류로 단정하지 않는다.
- 로그 변환은 왜도 감소와 예측 성능을 별도로 본다. 왜도가 줄어도 F1·PR-AUC 채택 조건을 통과하지 못하면 제외한다.
- `fnlwgt`는 Census 표본 가중치이므로 개인 특성처럼 해석하지 않는다.

아래 셀의 표가 이 실행에서의 최종 채택·제외 결과다. 작은 Holdout 차이는 이후 교차검증으로 재확인해야 한다.
""",
        metadata={"tags": [TAG]},
    ),
]

insert_at = len(notebook.cells)
for index, cell in enumerate(notebook.cells):
    if cell.cell_type == "markdown" and "### 해석 제한" in "".join(cell.source):
        insert_at = index
        break

notebook.cells[insert_at:insert_at] = new_cells
nbformat.validate(notebook)
nbformat.write(notebook, NOTEBOOK_PATH)
print(f"Updated {NOTEBOOK_PATH} with {len(new_cells)} tagged cells")
