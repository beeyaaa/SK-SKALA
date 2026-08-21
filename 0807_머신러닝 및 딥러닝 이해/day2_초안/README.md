# Day 2 종합실습 — 결혼 경험에 따른 평균 교육연수 비교

Adult 데이터에서 결혼 경험이 있는 집단과 없는 집단의 평균 교육연수(`education-num`) 차이를 분석합니다.

## 연구 가설

- H0: 결혼 경험이 있는 집단과 없는 집단의 평균 교육연수는 같다.
- H1: 결혼 경험이 있는 집단과 없는 집단의 평균 교육연수는 다르다.
- 유의수준: 0.05, 양측검정

## 집단 정의

- 결혼 경험 있음: 현재 기혼, 이혼, 별거, 사별
- 결혼 경험 없음: `Never-married`

분석 집단 명칭은 현재 혼인 상태와 구분하기 위해 `결혼 경험 있음/없음`으로 통일합니다.

## 분석 방법

1. 데이터 로딩과 결측·중복 점검
2. 원래 혼인 상태를 결혼 경험 있음/없음으로 재분류
3. 집단별 표본 수·평균·분포 확인
4. 분산 및 Q-Q plot 점검
5. Welch 독립표본 t-test로 비보정 평균 차이 검정
6. 나이·나이 제곱·성별을 통제한 OLS(HC3) 회귀분석
7. 결혼 경험×나이·나이² 상호작용 검증과 평균 표준화
8. 부트스트랩·`fnlwgt` 가중 기술통계·Mann–Whitney 보조 검토
9. 교육연수 M1/M2/M3 모델의 5-fold×5회 교차검증
10. 주 가설과 보정 민감도를 분리한 최종 결론

노트북의 모델링 Target은 연구가설과 동일한 `education-num`입니다. 이전에 작성한
소득 분류 Logistic Regression과 Day16 Feature Engineering 코드는
`day2_pipeline.py`와 기존 산출물에 남아 있지만 현재 노트북 본문에서는 실행하지
않으며, 교육연수 가설의 근거로 사용하지 않습니다.

Welch t-test는 실제 두 집단의 전체 평균을 비교합니다. 보정 회귀분석은 나이와 성별 분포를 동일하게 고려했을 때의 모델 기반 평균 차이를 추정합니다. 보정 분석은 실제로 동일한 사람을 일대일 매칭한 결과가 아닙니다.

## 실행 방법

```bash
cd day2
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
curl -L \
  https://archive.ics.uci.edu/ml/machine-learning-databases/adult/adult.data \
  -o adult.data
.venv/bin/jupyter lab day2.ipynb
```

JupyterLab에서 `Restart Kernel and Run All Cells`를 실행합니다. 원본 데이터인
`adult.data`는 Git에 포함하지 않으며, 위 명령으로 내려받아 `day2.ipynb`와 같은
폴더에 둡니다.

기존 소득 분류 파이프라인은 참고용으로만 별도 실행할 수 있습니다.

```bash
.venv/bin/python day2_pipeline.py
```

교육연수 모델링 결과는 `artifacts/`에 저장됩니다.

- `hypothesis_validation.csv`: Welch·효과크기·가중 민감도·연령 상호작용 검증 요약
- `education_model_cv.csv`: M1/M2/M3의 5-fold×5회 교차검증 원결과
- `education_model_comparison.csv`: 모델별 RMSE·MAE·R² 평균과 표준편차
- `education_model_selection.csv`: 주 가설 모델과 최종 보정 민감도 모델 선택 근거
- `education_model_final_coefficients.csv`: 최종 상호작용 OLS(HC3) 계수·신뢰구간

아래 파일들은 이전 소득 분류 실험의 참고 산출물이며 현재 교육연수 모델링의 결론에는 사용하지 않습니다.

- `pandas_polars_comparison.csv`: 로딩 결과·성능 비교
- `cleaning_summary.csv`: 결측치·중복 처리 전후
- `descriptive_statistics.csv`: 분위수를 포함한 기술통계
- `correlation_matrix.csv`: 수치형 상관행렬
- `seaborn_eda.png`: 정적 EDA 차트
- `plotly_income_by_education.html`: 인터랙티브 차트
- `model_metrics.json`: 정확도·F1 및 상세 평가 결과
- `adult_income_pipeline.joblib`: 저장된 전처리·모델 Pipeline
- `report.md`: 자동 생성 분석 보고서
- `adult_outlier_audit.csv`: Train 기준 범위·왜도·0 비율·IQR 후보 감사표
- `log_transform_audit.csv`: 로그 변환 전후 왜도·P99·최댓값 비교
- `preprocessing_provenance.csv`: 기존·개선·신규 전처리와 선택 근거
- `data_hygiene_audit.csv`: 공백·결측 토큰·라벨·중복 정리 변경 건수
- `existing_preprocessing_ablation.csv`: One-Hot·Scaler·결측 대치·희소 범주·중복 처리 성능 비교
- `rare_category_repeated_cv.csv`: 희소 범주 2건·1% 기준의 5×5 반복 교차검증 원결과
- `rare_category_cv_summary.csv`: 희소 범주 기준별 반복 교차검증 평균·표준편차
- `model_convergence_audit.csv`: LogisticRegression 반복 상한별 수렴 횟수·경고·성능
- `selected_feature_details.csv`: 최종 log·capital·bins 블록의 변수·계산식·선택 근거
- `feature_engineering_experiments.csv`: Baseline부터 IQR 처리까지 단계별 성능
- `feature_engineering_comparison.png`: F1·ROC-AUC·PR-AUC 비교 차트
- `adult_income_feature_engineered_pipeline.joblib`: F1·PR-AUC 비하락 규칙으로 선택한 최종 모델
- `feature_engineering_report.md`: Day16 방식 Feature Engineering 비교 보고서

## 교육연수 모델 구성

- M1: `education-num ~ 결혼 경험`
- M2: `M1 + 나이 + 나이² + 성별`
- M3: `M2 + 결혼 경험×나이 + 결혼 경험×나이²`

주 가설은 Welch t-test로 검정합니다. M1은 같은 비보정 평균 차이의 회귀 표현이고,
M2와 M3는 관측된 공변량 구성에 대한 보정 민감도입니다. 연령 상호작용 공동검정이
유의하고 M3가 반복 교차검증 RMSE·MAE에서도 일관되게 소폭 낮아 최종 보정
민감도 모델로 사용합니다. 다만 교차검증 R²가 약 0.034이므로 개인별 교육연수
예측 모델로 사용하지 않습니다.

## 연령 범위 변경

기본 분석 범위는 Adult 데이터의 전체 연령입니다. 연령 민감도 분석은 노트북 3번 코드 셀의 `MIN_AGE`, `MAX_AGE`로 설정합니다.

```python
MIN_AGE = 25
MAX_AGE = None
```

30~54세만 분석하려면 다음처럼 변경합니다.

```python
MIN_AGE = 30
MAX_AGE = 54
```

## 파일 구성

- `day2.ipynb`: 전체 분석 노트북
- `day2_pipeline.py`: End-to-End 분석 파이프라인
- `requirements.txt`: 실행 패키지 목록
- `README.md`: 연구 정의와 실행 안내
- `artifacts/`: 차트·모델·평가 결과·자동 생성 보고서

원본 `adult.data`, 강의 PDF, 가상환경과 캐시는 `.gitignore`로 제외합니다.

## 해석 제한

이 결과는 1994년 미국 Adult 데이터에서 관찰된 집단 간 연관성입니다. 결혼 경험이 교육연수를 변화시켰다는 인과관계로 해석할 수 없습니다. 표본이 크면 작은 차이도 유의할 수 있으므로 p-value뿐 아니라 평균 차이, 95% 신뢰구간, 효과크기를 함께 확인해야 합니다.

주 가설의 비보정 평균 차이는 약 `+0.176년`이고 Hedges g는 약 `0.068`로 매우
작습니다. 결혼 경험 있음 집단의 평균 나이가 약 15.5세 높아 보정 후 부호가
바뀌며, 결혼 경험×연령 상호작용도 유의하므로 일정한 OLS 계수 하나보다
상호작용을 허용한 평균 표준화 차이를 보정 민감도로 제시합니다.
`fnlwgt` 가중 평균도 비보정 결과와 같은 방향이지만, 제공된 파일만으로는 층화·군집
등 전체 표본설계를 복원할 수 없어 설계기반 p-value로 해석하지 않습니다.
