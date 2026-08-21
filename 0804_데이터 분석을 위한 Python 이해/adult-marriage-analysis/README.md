# Adult Census 혼인 경험 확률 분석

## 프로젝트 질문

1994년 미국 Adult Census 표본에서 나이·학력·직업 등 여러 특성을 함께 사용하면, 최적 단일 특성만 사용했을 때보다 조사 시점까지의 혼인 경험 여부를 더 정확하게 예측할 수 있는가?

이 프로젝트가 출력하는 값은 **미래에 결혼할 확률**이 아니라 **입력 특성을 가진 사람이 조사 시점까지 한 번 이상 혼인했을 추정 확률**이다.

## 가설

- H0: 다변수 모델은 최적 단일 특성 모델보다 혼인 경험 여부의 예측 성능을 실질적으로 개선하지 못한다.
- H1: 다변수 모델은 최적 단일 특성 모델보다 혼인 경험 여부의 예측 성능을 실질적으로 개선한다.

주 평가지표는 ROC-AUC로 두고, `다변수 AUC - 단일 특성 AUC > 0.02`를 실질적 개선 기준으로 사용한다. Accuracy와 F1-score는 과제 필수 지표로 함께 보고하고, 확률 품질은 Brier score와 calibration curve로 확인한다.

## 왜 로지스틱 회귀인가

1. 타깃 `ever_married`가 0/1인 이진 분류 문제다.
2. `predict_proba()`로 혼인 경험의 추정 확률을 직접 출력할 수 있다.
3. 표준화된 숫자형 변수의 계수와 범주형 더미 계수를 통해 방향과 상대적 기여를 설명할 수 있다.
4. 단일 특성 모델과 다변수 모델에 같은 알고리즘을 사용하면 알고리즘 차이가 아니라 **추가 특성이 제공하는 정보**를 비교할 수 있다.
5. One-Hot Encoding된 범주형 변수가 많은 Adult 데이터에서도 빠르고 안정적인 기준 모델이다.

로지스틱 회귀는 log-odds가 특성의 선형 결합이라는 제약이 있다. 따라서 최종 단계에서 Random Forest 또는 Gradient Boosting을 보조 모델로 비교해 비선형 관계와 상호작용의 추가 이득을 확인한다. 보조 모델이 더 좋더라도 확률 보정 여부를 반드시 점검한다.

## 디렉터리 구조

```text
adult-marriage-analysis/
├── README.md                    # 프로젝트 개요와 실행 안내
├── requirements.txt             # 실행 패키지
├── .gitignore
├── config/
│   └── project.yaml             # 데이터 URL, 타깃, 평가 기준
├── data/
│   ├── raw/                     # 원본 데이터(버전 관리 제외)
│   └── processed/               # 정제 데이터(버전 관리 제외)
├── notebooks/
│   ├── 01_data_quality.ipynb        # Pandas/Polars 비교와 품질 점검
│   ├── 02_target_and_features.ipynb # Target 생성과 입력 특성 정책
│   ├── 03_eda_statistics.ipynb      # EDA, 시각화, 통계검정, MI
│   └── 04_modeling.ipynb            # 전처리와 단일/다변수 모델 비교
├── src/
│   ├── __init__.py
│   ├── config.py                # 공통 상수와 컬럼 정의
│   ├── data.py                  # 로딩, 문자열 정리, 타깃 생성
│   ├── features.py              # 전처리 Pipeline과 MI 준비
│   ├── modeling.py              # 단일 특성 선택과 모델 학습
│   ├── evaluation.py            # 지표, 신뢰구간, calibration
│   └── reporting.py             # report.md 자동 생성
├── models/                      # joblib 모델
├── reports/
│   ├── figures/                 # PNG 등 정적 그림
│   ├── interactive/             # Plotly HTML
│   ├── tables/                  # CSV/Markdown 결과표
│   └── report.md                # 자동 생성 최종 보고서
├── tests/                       # 타깃/누수/Pipeline 테스트
└── run_analysis.py              # 전체 분석 실행 진입점
```

전체 분석 Pipeline이 구현되어 있다. 세부 진행 순서와 채점 기준 연결은 [docs/analysis_plan.md](docs/analysis_plan.md)를 따른다.

## 핵심 변수 원칙

- 타깃: `Never-married=0`, 나머지 혼인·이혼·별거·사별 상태 `=1`
- 반드시 제외: `marital-status`, `relationship`, `fnlwgt`
- 중복 방지: `education`과 `education-num` 중 기본 모델은 `education-num`만 사용
- 기본 모델 제외·공정성 점검용: `race`, `sex`, `native-country`
- `income`은 현재 시점 정보이므로 기본 모델과 확장 모델을 나눠 비교
- 중복 행은 개인 식별자가 없으므로 자동 삭제하지 않고 개수만 점검

## 실행 방법

```bash
../.venv/bin/python -m pip install -r requirements.txt
../.venv/bin/python run_analysis.py
```

최종 실행 결과는 `models/`, `reports/figures/`, `reports/interactive/`, `reports/tables/`, `reports/report.md`에 저장한다.
