# 분석 진행 순서 및 과제 요건

## 0. 분석 규칙 고정

- 관측 단위: Adult Census의 성인 1개 관측 행
- 타깃: 조사 시점까지 혼인 경험 여부 `ever_married`
- 주 비교: 최적 단일 특성 로지스틱 회귀 vs 다변수 로지스틱 회귀
- 주 지표: ROC-AUC
- 실질적 개선 기준: AUC 0.02 초과
- 필수 보조 지표: Accuracy, F1-score
- 확률 품질: Brier score, calibration curve
- 데이터 분할: stratified holdout + 훈련 데이터 내부 5-fold CV

분석 전에 기준을 고정해 결과를 본 뒤 가설이나 지표를 바꾸는 일을 방지한다.

## 1. 데이터 준비 — Pandas와 Polars

### 작업

1. 동일 URL을 Pandas와 Polars로 각각 로딩한다.
2. 컬럼명, shape, dtype, 첫 5행을 비교한다.
3. `?`, 공백, 빈 문자열을 결측치로 통일한다.
4. 문자열 앞뒤 공백과 `adult.test` 사용 시 income의 마침표를 정리한다.
5. 다음 품질 정보를 표로 저장한다.
   - 컬럼별 결측치 수와 비율
   - 완전 중복 행 수와 비율
   - 숫자형 min/max 및 분위수
   - 범주형 고유값과 빈도
6. 중복 행은 동일인 중복이라는 근거가 없으므로 자동 삭제하지 않는다.

### 과제 요건 연결

- [ ] Pandas와 Polars 모두 사용
- [ ] 두 로딩 결과 비교
- [ ] 결측치·중복 처리 근거 제시
- [ ] 기본 EDA 결과 출력

### 산출물

- `reports/tables/pandas_polars_comparison.csv`
- `reports/tables/data_quality.csv`

## 2. 타깃 생성과 누수 차단

### 타깃 정의

- 0: `Never-married`
- 1: `Married-civ-spouse`, `Married-spouse-absent`, `Married-AF-spouse`, `Divorced`, `Separated`, `Widowed`

### 변수 처리

- `marital-status`: 타깃 생성 후 제거
- `relationship`: Husband/Wife/Unmarried 등 정답 누수이므로 제거
- `fnlwgt`: 개인 특성이 아닌 표본 가중치이므로 입력에서 제거
- `education`: `education-num`과 중복되어 기본 모델에서 제거
- `race`, `sex`, `native-country`: 기본 모델에서 제외하고 공정성 점검에만 활용
- `income`: 기본 모델 제외, 확장 모델에서 추가해 민감도 분석

### 자동 검증

- [ ] 타깃에 결측값이 없는지 확인
- [ ] 타깃 값이 `{0, 1}`인지 확인
- [ ] 모델 입력에 `marital-status`, `relationship`이 없는지 확인

## 3. 데이터 분할

1. 모델 선택 전에 train/test를 분리한다.
2. `stratify=y`, `random_state=42`를 고정한다.
3. 상관분석, MI, 단일 특성 선택은 train에서만 수행한다.
4. test는 최종 비교에 한 번 사용한다.

## 4. EDA와 시각화

### Seaborn 정적 차트

- 혼인 경험별 나이 분포 violin/box plot
- 연령대별 혼인 경험 비율 bar plot
- 제목, 축 이름, 단위, 범례를 포함
- `reports/figures/`에 PNG 저장

### Plotly 인터랙티브 차트

- 연령대·학력 수준별 혼인 경험 비율
- hover에 표본 수와 비율 포함
- 제목, 축 이름, 범례 포함
- `reports/interactive/`에 HTML 저장

### 과제 요건 연결

- [ ] Seaborn 정적 차트 1개 이상
- [ ] Plotly 인터랙티브 차트 1개 이상
- [ ] 모든 차트에 제목과 레이블 포함
- [ ] 분포·상관관계·그룹 비교 중 목적을 명시

## 5. 기술통계와 통계검정

### 숫자형 기술통계

- 평균, 표준편차, 분산, 중앙값, 분위수
- 혼인 경험 집단별 `age`, `education-num`, `hours-per-week` 요약

### 관련성 분석

- 숫자형 vs 이진 타깃: point-biserial correlation
- 숫자형 집단 비교: `scipy.stats.ttest_ind(..., equal_var=False)` Welch t-test
- 범주형 vs 타깃: chi-square, Cramer's V
- 숫자형·범주형 공통 순위: `mutual_info_classif`

### 해석 규칙

- p-value와 함께 평균 차이 및 Cohen's d를 보고한다.
- 범주형 변수에 임의 숫자를 붙여 Pearson 상관계수를 계산하지 않는다.
- MI는 방향·인과관계를 뜻하지 않으며 단일 특성 후보 탐색에만 사용한다.
- 여러 검정을 수행하면 다중비교 문제를 caveat로 명시한다.

### 과제 요건 연결

- [ ] 평균·표준편차·분산 산출
- [ ] 변수 간 상관계수 계산
- [ ] `scipy.stats.ttest_ind` 수행
- [ ] p-value를 문장으로 해석

## 6. 모델용 전처리 Pipeline

### 숫자형

- `age`, `education-num`, `hours-per-week`: median imputation → StandardScaler
- `capital-gain`, `capital-loss`: median imputation → `log1p` → StandardScaler

### 범주형

- `workclass`, `occupation`: `Unknown` 대치 → OneHotEncoder
- `handle_unknown="ignore"`로 새 범주 오류 방지

### 주의

- imputer, scaler, encoder는 `sklearn.pipeline.Pipeline` 안에서 train에만 fit한다.
- 전체 데이터에 `pd.get_dummies()`를 먼저 적용하지 않는다.
- 확률 보존을 위해 SMOTE와 `class_weight="balanced"`는 기본 모델에 사용하지 않는다.

## 7. 최적 단일 특성 모델 선정

1. 모든 허용 특성에 대해 특성 하나만 사용하는 LogisticRegression Pipeline을 만든다.
2. 동일한 `StratifiedKFold(n_splits=5, shuffle=True, random_state=42)`를 사용한다.
3. 평균 ROC-AUC가 가장 높은 특성을 선택한다.
4. 동률에 가까우면 Brier score와 모델 단순성을 보조 기준으로 사용한다.
5. test 성능을 보고 특성을 다시 선택하지 않는다.

MI 1위가 자동으로 최적 단일 특성이 되는 것은 아니다. MI는 후보 설명용이고 최종 선택은 교차검증 성능으로 한다.

## 8. 다변수 모델 학습과 특성 기여도

### 기준 모델

- 동일한 LogisticRegression을 사용해 단일/다변수 비교에서 알고리즘 효과를 통제한다.
- L2 regularization으로 계수 불안정을 완화한다.

### 특성 해석

- 표준화 로지스틱 계수: 관계의 방향과 모델 가중치
- odds ratio: 계수를 오즈 변화로 표현
- permutation importance: 원본 컬럼을 섞었을 때 ROC-AUC 감소량

계수와 중요도는 예측 기여도이며 결혼의 원인이나 인과효과가 아니다.

### 보조 모델

- Random Forest 또는 Gradient Boosting으로 비선형·상호작용의 추가 이득 확인
- impurity 기반 `feature_importances_`보다 permutation importance 우선
- 필요 시 `CalibratedClassifierCV`로 확률 보정

## 9. 모델 평가와 가설 판단

### 필수 평가

- Accuracy
- F1-score
- confusion matrix

### 확장 평가

- ROC-AUC
- Brier score
- calibration curve
- 교차검증 fold별 성능과 평균·표준편차
- 가능하면 성능 차이의 bootstrap 95% 신뢰구간

### 판단

- `AUC_multi - AUC_single > 0.02`이고 불확실성 범위도 개선 방향이면 H0 기각 근거로 사용한다.
- 기준을 넘지 못하면 H0를 "채택"하기보다 "기각할 충분한 근거가 없다"고 쓴다.
- Accuracy/F1만 좋아지고 calibration이 나빠진 경우 확률 모델로서의 한계를 별도 기술한다.

### 과제 요건 연결

- [ ] sklearn Pipeline 객체로 전처리+모델 구성
- [ ] 모델 학습 수행
- [ ] Accuracy와 F1-score 출력
- [ ] 예측 확률 및 calibration 품질 추가 평가

## 10. 저장과 자동 보고서

### 저장 파일

- `models/single_feature_logistic.joblib`
- `models/multivariable_logistic.joblib`
- `reports/tables/model_metrics.csv`
- `reports/tables/feature_importance.csv`
- `reports/report.md`

### report.md 자동 생성 내용

1. 연구 질문과 데이터 설명
2. 타깃·변수·전처리 정의
3. Pandas/Polars 비교
4. EDA 핵심 결과와 차트 링크
5. 통계검정 결과와 p-value 해석
6. 단일 특성 선정 과정
7. 단일/다변수 성능 비교
8. 가설 판단
9. 한계·윤리·인과 해석 주의

### 과제 요건 연결

- [ ] `joblib`으로 모델 저장
- [ ] `report.md` 자동 생성
- [ ] 누락 파일과 예외에 대한 오류 메시지 처리
- [ ] 주요 함수에 주석 또는 docstring 작성

## 11. 5분 발표 구성

1. 30초: 문제 정의와 정확한 확률 의미
2. 40초: 데이터 및 타깃 정의
3. 50초: EDA·통계검정·MI 핵심 결과
4. 50초: 누수 차단과 전처리 Pipeline
5. 70초: 최적 단일 특성 선정과 다변수 비교
6. 50초: 특성 중요도와 개인 확률 예시
7. 50초: 결론, 한계, 미래 혼인 확률이 아니라는 주의

## 제출 전 체크리스트

- [ ] 깨끗한 환경에서 `run_analysis.py`가 처음부터 끝까지 실행된다.
- [ ] 정적 차트와 Plotly HTML이 모두 생성된다.
- [ ] Accuracy와 F1-score가 콘솔 및 보고서에 모두 표시된다.
- [ ] 모델 joblib 파일이 생성되고 다시 로드할 수 있다.
- [ ] `report.md`가 코드 실행으로 자동 생성된다.
- [ ] 차트 제목, 축 레이블, 단위, 범례가 누락되지 않았다.
- [ ] p-value를 기각/기각 실패 언어로 정확히 해석했다.
- [ ] `relationship`이 모델 입력에 포함되지 않았다.
- [ ] 결과를 인과관계나 개인의 미래 결혼 가능성으로 과장하지 않았다.
- [ ] 5분 발표 시간에 맞춰 리허설했다.

