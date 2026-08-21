# Adult Census 혼인 경험 여부와 교육 수준 분석

## 연구 가설

- H₀: 미혼 집단과 미혼 외 집단의 평균 교육 수준(`education-num`)은 같다.
- H₁: 두 집단의 평균 교육 수준은 다르다.

`Never-married`만 미혼(0)으로 정의하고, `Married-*`, `Divorced`, `Separated`, `Widowed`는 미혼 외, 즉 혼인 경험 있음(1)으로 정의한다.

## 노트북

1. `01_data_quality.ipynb`: Pandas/Polars 로딩과 품질 점검
2. `02_target_and_features.ipynb`: 전체 변수 프로파일, Target 정의, 입력 변수 정책
3. `03_eda_hypothesis.ipynb`: Train 전용 EDA, 상관관계, VIF, Welch t-test
4. `04_feature_engineering.ipynb`: Day16 자료 기반 결측·이상치·변환·파생변수·인코딩·스케일링 Pipeline

`04`에서는 처리 항목마다 관찰값, 적용 여부와 근거를 표로 남기며 모든 학습형 전처리는 Train에만 `fit`한다.

## 실행

```bash
cd /Users/beeyaaa/Workspace/SK-SKALA/day15_data/adult-marriage-education-analysis
bash scripts/start_jupyter.sh
```

JupyterLab이 열리면 커널이 `Adult Marriage (.venv)`인지 확인한다. 이 실행 스크립트는 프로젝트 전용 Python 3.14 가상환경과 로컬 kernelspec을 사용한다.

터미널에서 전체 노트북을 일괄 실행하려면 다음 명령을 사용한다.

```bash
bash scripts/run_notebooks.sh
```
