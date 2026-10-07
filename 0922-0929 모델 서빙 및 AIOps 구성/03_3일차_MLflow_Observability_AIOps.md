# 3일차 - MLflow, Observability와 AIOps

> 원본 범위: PDF 252~388쪽  
> 학습 흐름: **모델 이력 관리 → 시스템 관측 → 개발·모델·LLM 운영 → AIOps → 전체 연결**

---

## 0. 오늘 무엇을 배우는가

모델을 API로 배포했다고 운영이 끝나는 것은 아니다.

- 어떤 데이터와 코드로 만든 모델인지 알아야 한다.
- 현재 운영 중인 모델 버전을 추적해야 한다.
- 오류가 발생하면 어느 서비스와 요청에서 시작됐는지 찾아야 한다.
- 모델 성능이 떨어지면 원인을 분석하고 재학습 또는 롤백해야 한다.
- LLM은 Prompt, Token, 응답 품질, 비용, 안전성까지 관리해야 한다.

3일차는 모델을 지속적으로 운영하기 위한 관리와 관측 체계를 다룬다.

```text
실험과 모델 이력 관리
→ MLflow

Metrics·Logs·Traces 수집과 분석
→ Observability / LGTM

코드·모델·LLM의 개발과 운영 자동화
→ DevOps / MLOps / LLMOps

운영 데이터를 이용한 이상 탐지와 대응
→ AIOps
```

---

## 1. MLflow

> 원본 PDF 252~279쪽

### 1.1 왜 MLflow가 필요한가

모델을 한 번만 학습할 때는 파일 이름으로 관리할 수도 있다.

```text
model.pkl
model_final.pkl
model_final_v2.pkl
model_really_final.pkl
```

하지만 실험이 반복되면 다음 정보를 파일 이름만으로 관리할 수 없다.

- 어떤 코드와 데이터로 학습했는가?
- Hyperparameter는 무엇이었는가?
- 평가 지표는 얼마였는가?
- 생성된 모델 파일은 어디에 있는가?
- 어떤 버전이 운영 중인가?
- 문제가 생겼을 때 어느 버전으로 돌아가야 하는가?

**MLflow**는 머신러닝 실험, 모델 파일, 모델 버전과 배포 이력을 관리하는 Open Source MLOps Platform이다.

### 1.2 Experiment, Run, Parameter, Metric

#### Experiment

관련된 여러 학습 시도를 묶는 논리적 그룹이다. 예를 들어 `iris-classification`이라는 Experiment 안에 여러 알고리즘과 Hyperparameter 실험을 저장할 수 있다.

#### Run

한 번의 학습 실행을 뜻한다. Run마다 고유한 Run ID가 생성된다.

#### Parameter

학습 전에 정한 설정값이다.

예:

- Learning Rate
- Batch Size
- Epoch 수
- Random Forest의 `n_estimators`

#### Metric

학습 또는 평가 과정에서 측정한 숫자다.

예:

- Training Loss
- Validation Loss
- Accuracy
- F1 Score
- Latency

Parameter는 입력 설정이고 Metric은 실행 결과라는 차이가 있다.

### 1.3 MLflow Tracking

**MLflow Tracking**은 Run의 Parameter, Metric, Tag, Artifact를 기록하고 조회하는 기능이다.

```python
with mlflow.start_run():
    mlflow.log_param("n_estimators", 100)
    mlflow.log_metric("accuracy", 0.95)
    mlflow.log_artifact("confusion_matrix.png")
```

**Tag**는 Run을 분류하거나 설명하기 위한 문자열 메타데이터다. 예를 들어 담당 팀, 데이터 버전, 실행 환경을 기록할 수 있다.

### 1.4 MLflow의 저장 구조

MLflow는 메타데이터와 큰 파일을 분리해 저장한다.

#### Backend Store

Run, Parameter, Metric, Tag, Model Registry 메타데이터를 저장한다. 실습이나 소규모 환경에서는 SQLite를 사용할 수 있고, 운영 환경에서는 PostgreSQL 같은 Database를 사용할 수 있다.

#### Artifact Store

모델 파일, 이미지, 평가 결과처럼 크기가 큰 Artifact를 저장한다. Local File System, Amazon S3, Google Cloud Storage, Azure Blob Storage 등을 사용할 수 있다.

```text
MLflow Client
   ↓ 기록 요청
Tracking Server
   ├→ Backend Store: Parameter, Metric, Run Metadata
   └→ Artifact Store: Model, Image, Report, File
```

### 1.5 MLflow 주요 구성 요소

| 구성 요소 | 역할 |
|---|---|
| MLflow Client / SDK | 사용자 코드에서 Run과 모델 정보를 기록한다. |
| Tracking Server | 기록과 조회를 위한 중앙 REST API를 제공한다. |
| Backend Store | Run 메타데이터, Parameter, Metric, Tag를 저장한다. |
| Artifact Store | 모델 파일과 기타 Artifact를 저장한다. |
| Model Registry | 등록된 모델의 이름, 버전, 상태, 설명을 관리한다. |
| MLflow Models | 여러 ML Framework 모델을 공통 형식으로 패키징한다. |
| MLflow Projects | 코드, 환경, 실행 Entry Point를 재현 가능한 단위로 정의한다. |

### 1.6 Model Registry

**Model Registry(모델 레지스트리)**는 배포 가능한 모델 버전을 중앙에서 관리한다.

```text
Run에서 모델 생성
→ Registry에 모델 등록
→ Version 1 생성
→ 새 모델 등록
→ Version 2 생성
→ 평가와 승인
→ 운영 Alias 또는 상태 변경
```

모델 버전에는 다음 정보를 연결해야 한다.

- 모델이 생성된 Run
- 학습 데이터와 코드 버전
- 평가 지표
- 설명과 Tag
- 승인 및 배포 이력

단순히 `v1`, `v2`만 기록하는 것은 충분하지 않다. 어떤 변경 때문에 버전이 올라갔는지를 추적할 수 있어야 한다.

### 1.7 MLflow Model과 Flavor

**MLflow Model**은 모델과 모델을 읽는 방법, 의존성 정보를 함께 묶는 표준 패키징 형식이다.

**Flavor**는 같은 모델을 특정 Framework 또는 공통 Interface로 읽는 방법을 정의한다.

예:

- `sklearn` Flavor: scikit-learn 객체로 로드
- `pytorch` Flavor: PyTorch 모델로 로드
- `python_function(pyfunc)` Flavor: Framework와 무관한 `predict()` Interface로 로드

```text
하나의 MLflow Model
├→ sklearn Flavor
└→ pyfunc Flavor
```

Flavor는 모델 자체를 여러 번 저장한다는 뜻이 아니라, 같은 모델을 어떤 방식으로 불러오고 실행할지에 대한 규칙을 제공한다.

### 1.8 Model Signature와 Input Example

**Model Signature**는 모델 입력과 출력의 Schema를 기록한다. 컬럼 이름, 자료형, Shape 등을 명시해 잘못된 입력을 조기에 발견할 수 있다.

**Input Example**은 모델이 기대하는 입력의 실제 예시다. 사용자가 호출 형식을 이해하고 배포 전 검증하는 데 도움이 된다.

### 1.9 Local Serving과 Kubernetes Serving

로컬에서는 MLflow CLI로 모델 서버를 실행해 빠르게 검증할 수 있다.

운영에서는 Container Image를 만들고 Kubernetes Deployment, KServe 또는 Cloud의 Managed Serving에 배포할 수 있다.

중요한 점은 MLflow가 모든 배포 환경을 직접 대체하는 도구가 아니라, 실험과 모델 이력을 일관되게 연결하는 중심 역할을 한다는 것이다.

### MLflow 실습에서 확인할 것

- 학습 Run이 Tracking Server에 기록되는가?
- Parameter와 Metric의 역할을 구분했는가?
- Model Artifact가 Artifact Store에 저장되는가?
- 모델을 Registry에 등록하면 Version이 생성되는가?
- 등록된 모델을 다시 로드해 같은 예측을 재현할 수 있는가?

### 이 장에서 기억할 것

- Experiment는 관련 Run의 그룹이고, Run은 한 번의 실행이다.
- Parameter는 입력 설정이고 Metric은 측정 결과다.
- Backend Store는 메타데이터, Artifact Store는 파일을 저장한다.
- Model Registry는 배포 가능한 모델의 버전과 이력을 관리한다.
- MLflow는 서빙 도구 하나가 아니라 실험부터 모델 등록까지 연결하는 MLOps Platform이다.

---

## 2. Observability

> 원본 PDF 281~298쪽

### 2.1 Monitoring과 Observability

**Monitoring(모니터링)**은 미리 정한 지표와 조건을 관찰해 알려진 문제를 감지하는 활동이다.

예:

- CPU 사용률이 90%를 넘었는가?
- 5xx 오류율이 5%를 넘었는가?
- 모델 서버가 응답하지 않는가?

**Observability(관측 가능성)**는 시스템 외부로 나타나는 신호를 이용해 내부 상태와 예상하지 못한 문제의 원인을 파악할 수 있는 능력이다.

Monitoring이 “문제가 있는가?”에 집중한다면 Observability는 “왜 문제가 발생했는가?”까지 탐색할 수 있어야 한다.

### 2.2 세 가지 핵심 신호

#### Metrics

시간에 따라 측정한 숫자다.

예:

- 초당 요청 수
- 오류율
- p95 Latency
- CPU와 Memory 사용률
- Model Prediction Class 분포

집계와 Alert에 적합하지만 개별 사건의 상세 정보는 부족하다.

#### Logs

특정 시점에 발생한 Event의 상세 기록이다.

예:

```text
2026-09-28T10:00:00Z ERROR model=fraud-v3 request_id=abc timeout
```

오류 메시지, 사용자 동작, 처리 결과를 자세히 확인할 수 있지만 양이 많고 구조가 제각각이면 검색이 어렵다.

#### Traces

하나의 요청이 여러 Service를 통과한 전체 경로를 기록한다.

```text
API Gateway 20ms
└→ Feature Service 40ms
   └→ Model Server 120ms
      └→ Database 30ms
```

각 작업 단위를 **Span**이라고 하며, 여러 Span이 모여 하나의 Trace가 된다.

### 2.3 Correlation

Metrics, Logs, Traces를 서로 연결해야 원인 분석 속도가 빨라진다.

```text
Metric: 오류율 급증 발견
→ Trace: 느린 요청의 경로 확인
→ Log: 실패한 Span의 상세 오류 확인
```

요청마다 `trace_id`, `span_id`, `request_id` 같은 식별자를 기록하면 신호를 연결할 수 있다.

### 2.4 RED와 USE

#### RED Method

서비스 요청을 관찰할 때 사용하는 기본 관점이다.

- **Rate**: 단위 시간당 요청 수
- **Errors**: 실패한 요청 수 또는 비율
- **Duration**: 요청 처리 시간 분포

#### USE Method

CPU, Memory, Disk 같은 Resource를 관찰할 때 사용하는 관점이다.

- **Utilization**: Resource가 사용 중인 비율
- **Saturation**: 처리 능력을 넘어 대기하는 정도
- **Errors**: Resource 관련 오류 수

### 2.5 SLI, SLO, SLA

#### SLI

**SLI(Service Level Indicator)**는 서비스 수준을 측정하는 실제 지표다.

예: 성공한 요청의 비율, p95 Latency

#### SLO

**SLO(Service Level Objective)**는 SLI에 대해 내부적으로 설정한 목표다.

예: 월간 요청의 99.9%가 성공해야 한다.

#### SLA

**SLA(Service Level Agreement)**는 고객과 합의한 서비스 수준 계약이다. 위반 시 보상 등 사업적 조건이 포함될 수 있다.

```text
SLI = 측정값
SLO = 내부 목표
SLA = 외부 계약
```

### 2.6 High Cardinality

**Cardinality(카디널리티)**는 Label 조합의 고유한 개수다.

Prometheus 같은 Time Series Database에서 `user_id`, 전체 URL, `request_id`를 Label로 사용하면 시계열 수가 폭발해 Memory와 저장 비용이 급격히 증가한다.

Metric Label에 적합한 값:

- HTTP Method
- Status Code Class
- 미리 정한 Route Template
- Region
- Model Version

Log나 Trace에 적합한 값:

- User ID
- Request ID
- 원본 URL과 Query String
- Error Message 원문
- Trace ID와 Span ID

### 이 장에서 기억할 것

- Monitoring은 알려진 상태를 감시하고, Observability는 내부 원인을 탐색할 수 있는 능력이다.
- Metrics는 집계, Logs는 사건의 상세 내용, Traces는 요청 경로를 보여준다.
- RED는 서비스, USE는 Resource를 관찰하는 기본 관점이다.
- SLI는 측정값, SLO는 내부 목표, SLA는 외부 계약이다.
- 값의 종류가 무한히 늘어날 수 있는 정보는 Metric Label로 사용하지 않는다.

---

## 3. LGTM Observability Stack

> 원본 PDF 299~334쪽

### 3.1 LGTM이란 무엇인가

이 강의에서 **LGTM**은 다음 Grafana Labs 관측 도구의 조합을 뜻한다.

- **Loki**: Logs 저장과 검색
- **Grafana**: Dashboard와 탐색, Alert 시각화
- **Tempo**: Distributed Traces 저장과 검색
- **Mimir**: Prometheus-compatible Metrics 장기 저장

신호 수집과 전달에는 **Grafana Alloy**를 사용할 수 있다.

```text
Application / Infrastructure
          ↓
      Grafana Alloy
      ├→ Metrics → Prometheus / Mimir
      ├→ Logs    → Loki
      └→ Traces  → Tempo
                   ↓
                Grafana
```

### 3.2 Prometheus

**Prometheus**는 Metrics를 수집하고 Time Series로 저장하며 **PromQL**로 조회하는 Monitoring System이다.

#### Pull 방식

Prometheus Server가 대상의 `/metrics` Endpoint를 정기적으로 호출해 값을 가져온다. 이 과정을 **Scraping(스크레이핑)**이라고 한다.

```text
Application /metrics
        ↑ scrape
Prometheus Server
```

#### 주요 구성 요소

| 구성 요소 | 역할 |
|---|---|
| Exporter / Instrumented Target | `/metrics`에 Metric을 노출한다. |
| Service Discovery / scrape_configs | 어떤 대상을 얼마나 자주 Scrape할지 정의한다. |
| Prometheus Server | Scraping, Rule 평가, Query를 수행한다. |
| TSDB | 수집한 Time Series를 Local Disk에 저장한다. |
| PromQL | Time Series를 선택·집계하는 Query Language다. |
| Alertmanager | Alert을 Grouping하고 Email, Slack 등으로 전달한다. |
| Remote Write | 장기 저장 시스템으로 Metric을 전송한다. |

#### Metric 구조

```text
http_requests_total{method="POST", route="/predict", status="200"} 1520
```

- Metric Name: `http_requests_total`
- Label: `method`, `route`, `status`
- Sample Value: `1520`
- Timestamp: 값이 수집된 시간

### 3.3 Grafana

**Grafana**는 Metrics, Logs, Traces 등 여러 Data Source를 조회하고 Dashboard로 시각화하는 도구다.

주요 기능:

| 메뉴 | 역할 |
|---|---|
| Dashboards | Panel을 구성해 지표와 상태를 지속적으로 표시한다. |
| Explore | Dashboard를 만들기 전에 Query를 즉석에서 탐색한다. |
| Connections | Prometheus, Loki, Tempo 등 Data Source를 연결한다. |
| Alerting | Alert Rule, Contact Point, Notification Policy를 관리한다. |
| Administration | 사용자, Team, 권한, Authentication을 관리한다. |

Dashboard는 그래프를 많이 넣는 것이 목적이 아니다. 사용자가 판단하고 행동하는 데 필요한 정보가 한 화면에 있어야 한다.

### 3.4 Grafana Alloy

**Grafana Alloy**는 OpenTelemetry Collector와 Prometheus 생태계를 기반으로 Metrics, Logs, Traces를 수집·처리·전송하는 배포 가능한 Collector다.

Application이 각각의 Backend로 직접 전송하는 대신 Alloy를 사이에 두면 다음 장점이 있다.

- Application은 하나의 OTLP Endpoint만 알면 된다.
- Backend 변경 시 Application을 수정할 필요가 줄어든다.
- Batch, Retry, Buffering, Sampling, Label 추가, 민감정보 제거를 중앙에서 제어할 수 있다.
- Node Log, System Metric처럼 Application 밖의 신호도 수집할 수 있다.

**OTLP(OpenTelemetry Protocol)**는 Telemetry Data를 전달하기 위한 OpenTelemetry 표준 Protocol이다.

Alloy 자체의 배포, Resource, 설정을 운영해야 한다는 비용도 있다. 작은 실습 환경에서는 Application이 Backend로 직접 전송하는 편이 단순할 수 있다.

### 3.5 Loki

**Loki**는 Log를 저장하고 **LogQL**로 검색하는 시스템이다.

Loki는 Log 본문 전체를 Indexing하지 않고 Label을 중심으로 Index를 만든다. 실제 Log 본문은 압축된 **Chunk**로 Object Storage 등에 저장한다.

```text
Log Agent
→ Label 부여
→ Loki
   ├→ Index: Label 조합
   └→ Chunk: 실제 Log 본문
```

주요 구성 요소:

| 구성 요소 | 역할 |
|---|---|
| Fluent Bit / Alloy | Container Log를 수집하고 Label을 붙여 전송한다. |
| Index | Log Stream의 Label 조합을 색인한다. |
| Chunk | 압축된 실제 Log 본문을 저장한다. |
| Limits | Stream 수와 Label Cardinality 등을 제한한다. |
| LogQL | Log Stream을 선택하고 Filter·집계한다. |

Log에 고유한 값을 Label로 계속 추가하면 Stream 수가 폭발한다. `request_id`나 `user_id`는 Log 본문 Field로 두고 필요한 시점에 검색하는 편이 낫다.

### 3.6 Tempo

**Tempo**는 Distributed Trace를 저장하고 **TraceQL**로 검색하는 시스템이다.

주요 구성 요소:

| 구성 요소 | 역할 |
|---|---|
| Distributor | OTLP, Jaeger, Zipkin 등으로 들어온 Span을 검증하고 전달한다. |
| Ingester | 최근 Span을 Memory에 모아 Block으로 만든 뒤 저장한다. |
| Query Frontend | TraceQL Query를 분할하고 병렬 실행을 조정한다. |
| Querier | 최근 데이터와 장기 저장소에서 Trace를 조회한다. |
| Compactor | 저장된 Block을 압축하고 보존 기간을 관리한다. |
| Metrics Generator | Span에서 RED Metric과 Service Graph를 생성한다. |
| Object Storage | Trace Block을 장기 보관한다. |

Trace는 단순한 호출 목록이 아니다. 어느 Span에서 시간이 오래 걸렸는지, 오류가 어디서 시작됐는지를 보여준다.

### 3.7 Mimir

**Grafana Mimir**는 Prometheus와 호환되는 확장형 장기 Metrics 저장 시스템이다.

단일 Prometheus의 Local TSDB는 장기 보관, 고가용성, 수평 확장에 한계가 있다. Prometheus의 `remote_write`로 Mimir에 Metric을 전송하면 여러 Prometheus Server의 데이터를 중앙에서 장기 보관할 수 있다.

주요 구성 요소:

| 구성 요소 | 역할 |
|---|---|
| Distributor | Remote Write 요청을 검증하고 적합한 Ingester로 전달한다. |
| Ingester | 최근 데이터를 Memory와 WAL에 저장하고 Block으로 만들어 Object Storage에 기록한다. |
| Store Gateway | Object Storage에 있는 과거 Block을 Query 가능하게 제공한다. |
| Querier | 최근 데이터와 과거 데이터를 조회해 결과를 병합한다. |
| Object Storage | 장기 보관용 Metric Block을 저장한다. |

**WAL(Write-Ahead Log)**은 데이터 변경 내용을 본 저장소에 반영하기 전에 먼저 기록해 장애 시 복구할 수 있게 하는 로그다.

### 3.8 Signal 선택 기준

| 확인하려는 것 | 적합한 Signal |
|---|---|
| 오류율이 임계값을 넘었는가? | Metrics |
| 특정 요청이 왜 실패했는가? | Logs와 Traces |
| 어떤 서비스가 느린가? | Traces |
| 오류의 상세 Stack Trace는 무엇인가? | Logs |
| 모델 v2의 p95 Latency 추세는 어떤가? | Metrics |
| 한 요청이 어떤 모델 버전을 거쳤는가? | Traces와 Structured Logs |

### LGTM 실습에서 확인할 것

- Application 또는 Exporter의 Metrics가 수집되는가?
- Grafana에서 Prometheus/Mimir Data Source를 조회할 수 있는가?
- Application Log가 Loki에 들어오고 LogQL로 검색되는가?
- Trace가 Tempo에 저장되고 Trace ID로 조회되는가?
- Dashboard에서 Metric에서 Trace와 Log로 이동할 수 있는가?
- Label Cardinality가 통제되고 있는가?

### 이 장에서 기억할 것

- LGTM은 Loki, Grafana, Tempo, Mimir의 조합이다.
- Prometheus는 Metric을 Scrape하고 PromQL로 조회한다.
- Alloy는 Telemetry를 수집·처리·분기하는 Collector다.
- Loki는 Label을 Indexing하고 Log 본문은 Chunk로 저장한다.
- Tempo는 Distributed Trace, Mimir는 장기 Metrics를 담당한다.
- 신호를 따로 보지 말고 공통 식별자로 연결해야 원인 분석이 빨라진다.

---

## 4. DevOps

> 원본 PDF 335~346쪽

### 4.1 DevOps란 무엇인가

**DevOps**는 Development와 Operations를 결합한 말이다. 특정 도구 하나가 아니라 개발과 운영이 공동 책임을 지고 소프트웨어를 빠르고 안정적으로 전달하기 위한 문화, 프로세스, 자동화의 집합이다.

```text
계획
→ 개발
→ Build
→ Test
→ Release
→ Deploy
→ Operate
→ Monitor
→ Feedback
→ 다시 계획
```

### 4.2 CI와 CD

#### Continuous Integration

**CI(Continuous Integration, 지속적 통합)**는 개발자의 변경 사항을 자주 통합하고 자동 Build와 Test로 문제를 빠르게 발견하는 방식이다.

#### Continuous Delivery

**Continuous Delivery(지속적 제공)**는 검증된 변경 사항을 언제든 운영에 배포할 수 있는 상태로 유지한다. 운영 배포에는 사람의 승인이 포함될 수 있다.

#### Continuous Deployment

**Continuous Deployment(지속적 배포)**는 자동 검증을 통과한 변경 사항을 사람의 수동 승인 없이 운영까지 자동 배포한다.

Continuous Delivery와 Continuous Deployment를 같은 의미로 사용하기도 하지만, 자동 운영 배포 여부에서 구분할 수 있다.

### 4.3 Infrastructure as Code

**IaC(Infrastructure as Code)**는 Server, Network, Kubernetes Resource 같은 Infrastructure를 수동 작업 대신 코드로 선언하고 버전 관리하는 방식이다.

장점:

- 같은 환경을 반복해서 만들 수 있다.
- 변경 이력을 Code Review할 수 있다.
- 개발, Staging, Production의 차이를 추적할 수 있다.

### 4.4 DORA Metrics

**DORA(DevOps Research and Assessment) Metrics**는 Software Delivery 성과를 측정하는 대표 지표다.

- Deployment Frequency: 얼마나 자주 배포하는가?
- Lead Time for Changes: 변경이 운영에 도달하기까지 얼마나 걸리는가?
- Change Failure Rate: 배포 중 장애나 롤백이 발생한 비율은 얼마인가?
- Time to Restore Service: 장애 후 서비스를 복구하는 데 얼마나 걸리는가?

배포 횟수만 늘리는 것이 목표가 아니다. 속도와 안정성을 함께 개선해야 한다.

### 이 장에서 기억할 것

- DevOps는 개발팀과 운영팀의 책임을 연결하는 방식이다.
- CI는 변경 통합과 자동 검증, CD는 배포 가능한 상태와 배포 자동화에 초점을 둔다.
- IaC는 Infrastructure를 재현 가능한 코드로 관리한다.
- DORA Metrics는 Software Delivery의 속도와 안정성을 함께 측정한다.

---

## 5. MLOps

> 원본 PDF 347~355쪽

### 5.1 DevOps만으로 부족한 이유

일반 소프트웨어는 주로 코드가 바뀌면 결과가 바뀐다. 머신러닝 시스템은 코드뿐 아니라 데이터와 모델도 결과에 영향을 준다.

```text
소프트웨어 결과 = 코드

머신러닝 결과 = 코드 + 데이터 + Feature + 모델 + 환경
```

따라서 Git으로 코드만 버전 관리하고 CI/CD만 구성해서는 모델을 완전히 재현하기 어렵다.

**MLOps(Machine Learning Operations)**는 머신러닝 모델의 개발, 학습, 검증, 배포, 모니터링, 재학습을 안정적으로 반복하기 위한 운영 체계다.

### 5.2 MLOps가 관리하는 대상

- Source Code Version
- Data Version과 Data Lineage
- Feature 정의와 전처리
- Experiment와 Hyperparameter
- Model Artifact와 Model Version
- 학습·추론 Environment
- 배포 상태와 Traffic
- Model Quality와 Drift

**Data Lineage(데이터 계보)**는 데이터가 어디서 생성되어 어떤 변환을 거쳐 모델 학습에 사용됐는지를 추적하는 정보다.

### 5.3 CT

DevOps의 CI/CD에 더해 MLOps에서는 **CT(Continuous Training, 지속적 학습)**가 중요하다.

```text
새 데이터 도착 또는 Drift 감지
→ Training Pipeline 실행
→ 후보 모델 생성
→ 자동 평가
→ 품질·안전 기준 통과
→ 승인
→ 점진적 배포
→ 운영 평가
```

Continuous Training은 새 데이터가 생길 때마다 무조건 운영 모델을 교체한다는 뜻이 아니다. 재학습과 배포 사이에는 검증과 승인 단계가 필요하다.

### 5.4 Training-serving Skew

**Training-serving Skew**는 학습 환경과 서빙 환경에서 Feature 계산이나 전처리가 달라지는 문제다.

예:

- 학습에서는 결측값을 평균으로 채웠지만 서빙에서는 0으로 채운다.
- 학습에서는 UTC를 사용했지만 서빙에서는 Local Time을 사용한다.
- 학습과 서빙에서 서로 다른 Scaler를 사용한다.

이 문제는 API가 정상 응답해도 모델 품질을 조용히 떨어뜨리므로 발견하기 어렵다. 공통 Feature Code, Feature Store, Pipeline Test, 입력 분포 모니터링 등으로 줄여야 한다.

### 5.5 Model Deployment Strategy

- Rolling Deployment: 인스턴스를 순차적으로 새 버전으로 교체한다.
- Blue-Green Deployment: 기존 환경과 새 환경을 함께 두고 Traffic을 전환한다.
- Canary Deployment: 새 버전에 일부 Traffic만 전달한다.
- Shadow Deployment: 실제 요청을 새 모델에도 복제하지만 사용자 응답에는 반영하지 않는다.
- A/B Test: 사용자 그룹을 나눠 업무 성과를 비교한다.

Canary는 안전한 점진 배포에 초점을 두고, A/B Test는 서로 다른 Variant가 사용자 행동과 Business Metric에 미치는 영향을 비교하는 실험이라는 차이가 있다.

### 이 장에서 기억할 것

- MLOps는 코드뿐 아니라 데이터, Feature, 모델, 환경의 버전을 함께 관리한다.
- CI/CD에 Continuous Training이 추가된다.
- 새 모델 생성과 운영 배포 사이에는 평가와 승인이 필요하다.
- Training-serving Skew는 API 오류 없이 모델 품질을 떨어뜨릴 수 있다.

---

## 6. LLMOps

> 원본 PDF 356~369쪽

### 6.1 LLMOps가 필요한 이유

**LLMOps(Large Language Model Operations)**는 LLM Application의 개발, 평가, 배포, 관측, 비용과 안전 관리를 위한 운영 체계다.

LLM Application은 전통적인 모델 API보다 구성 요소와 출력의 변동성이 크다.

```text
사용자 질문
→ Prompt Template
→ 선택적 Retrieval
→ LLM
→ 선택적 Tool 호출
→ 후처리와 Safety 검사
→ 응답
```

응답은 입력 문장, Model Version, Sampling Parameter, Prompt, 검색 문서, Tool 결과에 따라 달라질 수 있다.

### 6.2 Prompt Management

**Prompt**는 LLM에 제공하는 지시와 Context다. Prompt도 코드처럼 Version, 작성자, 변경 이유, 평가 결과를 관리해야 한다.

Prompt를 Application Code에 흩어놓으면 변경 이력과 영향 범위를 파악하기 어렵다. Prompt Template을 분리하고 Version별 평가 결과를 연결하는 편이 좋다.

### 6.3 RAG

**RAG(Retrieval-Augmented Generation, 검색 증강 생성)**는 질문과 관련된 문서를 먼저 검색하고 그 문서를 Context로 LLM에 전달해 답을 생성하는 구조다.

```text
질문
→ Embedding 생성
→ Vector Database에서 관련 문서 검색
→ 검색 문서 + 질문을 Prompt로 구성
→ LLM 응답 생성
```

RAG에서는 LLM만 평가하면 안 된다.

- Retrieval이 관련 문서를 찾았는가?
- 중요한 문서를 놓치지 않았는가?
- 검색 결과가 최종 답변에 근거로 사용됐는가?
- 답변이 제공된 Context와 일치하는가?

### 6.4 Agent와 Tool Calling

**AI Agent**는 목표를 달성하기 위해 LLM이 다음 행동이나 Tool 호출을 선택하는 구조다.

**Tool Calling**은 LLM이 정해진 Schema에 따라 외부 함수나 API 호출을 요청하는 기능이다.

Agent 운영에서는 다음 정보를 Trace로 남겨야 한다.

- 입력 Prompt와 Model Version
- 선택한 Tool과 Argument
- Tool 실행 결과와 오류
- 반복 횟수와 종료 이유
- Token 사용량과 전체 Latency

### 6.5 LLM 평가

LLM의 자연어 출력은 정답이 하나가 아닐 수 있어 단순 Accuracy만으로 평가하기 어렵다.

평가 관점:

- Correctness: 사실과 문제 요구에 맞는가?
- Relevance: 질문에 관련된 답인가?
- Groundedness / Faithfulness: 제공된 Context에 근거하는가?
- Helpfulness: 사용자의 목적 달성에 도움이 되는가?
- Safety: 유해하거나 정책을 위반하는 내용이 없는가?
- Format Compliance: 요구한 JSON Schema나 형식을 지키는가?

평가 방법:

- Rule-based Evaluation
- Reference Answer와 비교
- 사람 평가
- LLM-as-a-Judge
- Online User Feedback과 Business Metric

**LLM-as-a-Judge**는 다른 LLM이 평가 기준에 따라 응답을 채점하는 방식이다. 빠르고 확장하기 쉽지만 평가 모델의 편향과 재현성 문제를 확인해야 한다.

### 6.6 LLM 운영 지표

#### 시스템 성능

- Request Rate
- Error Rate
- End-to-end Latency
- TTFT(Time to First Token)
- TPOT(Time per Output Token)
- Queue Time

#### 사용량과 비용

- Prompt Tokens
- Completion Tokens
- Total Tokens
- 요청별·사용자별·기능별 비용
- Cache Hit Rate

#### 품질과 안전

- Task Success Rate
- Groundedness
- Hallucination 관련 지표
- Safety Violation Rate
- Tool Call Success Rate
- User Feedback

### 6.7 Caching

LLM 추론 비용과 Latency를 줄이기 위해 여러 Cache를 사용할 수 있다.

- Exact Match Cache: 완전히 같은 요청의 응답을 재사용한다.
- Semantic Cache: 의미가 유사한 요청의 응답을 재사용한다.
- Prompt / Prefix Cache: 동일한 Prompt Prefix의 계산 결과를 재사용한다.
- KV Cache: 한 생성 요청 내부의 이전 Token 계산을 재사용한다.

Cache는 데이터 최신성, 사용자별 권한, 개인정보, 잘못된 응답 재사용 문제를 고려해야 한다.

### 6.8 Guardrails

**Guardrails**는 LLM 입력과 출력에 적용하는 제약과 검증 체계다.

- Prompt Injection 탐지
- 개인정보와 Secret 제거
- 금지 주제 또는 유해 콘텐츠 검사
- 출력 Schema 검증
- 허용된 Tool과 Argument 제한
- 근거 없는 답변의 거절 또는 검토 요청

Guardrails는 LLM의 정확성을 보장하는 단일 장치가 아니다. Model, Prompt, Retrieval, 권한, 검증, Human Review를 함께 사용하는 다층 방어가 필요하다.

### 이 장에서 기억할 것

- LLMOps는 Prompt, Retrieval, Model, Tool, 평가, 비용, 안전을 함께 관리한다.
- RAG는 검색과 생성을 결합하므로 Retrieval과 Generation을 각각 평가해야 한다.
- Agent는 Tool 선택과 반복 과정을 Trace로 남겨야 한다.
- LLM은 Request뿐 아니라 Token 단위 성능과 비용을 관찰해야 한다.
- 자동 평가만 믿지 말고 사람 평가와 실제 사용자 지표를 함께 사용한다.

---

## 7. AIOps

> 원본 PDF 370~388쪽

### 7.1 AIOps란 무엇인가

**AIOps(Artificial Intelligence for IT Operations)**는 Logs, Metrics, Traces, Events 등 운영 데이터를 분석해 이상을 탐지하고, 관련 Alert을 묶고, 원인을 추정하며, 대응을 지원하거나 자동화하는 접근이다.

MLOps와 이름이 비슷하지만 대상이 다르다.

| 구분 | 핵심 대상 |
|---|---|
| MLOps | 머신러닝 모델의 개발과 운영 |
| LLMOps | LLM Application의 개발과 운영 |
| AIOps | IT 시스템 운영 데이터를 AI로 분석하고 대응하는 활동 |

### 7.2 AIOps가 해결하려는 문제

- Alert가 너무 많아 중요한 문제를 찾기 어렵다.
- 동일한 장애에서 여러 시스템이 중복 Alert을 발생시킨다.
- 여러 도구의 데이터를 사람이 수동으로 연결해야 한다.
- 정상 상태가 시간대와 서비스마다 달라 고정 임계값만으로 탐지하기 어렵다.
- 장애 원인 파악과 복구가 담당자의 경험에 의존한다.

### 7.3 기본 처리 흐름

```text
Metrics·Logs·Traces·Events 수집
→ 형식 정규화와 Context 연결
→ 중복 제거와 Alert Grouping
→ Baseline 학습과 이상 탐지
→ 상관관계 분석
→ Root Cause 후보 제시
→ 담당자 알림 또는 Runbook 실행
→ 결과 Feedback
```

#### Baseline

**Baseline(기준선)**은 정상 상태에서 지표가 보이는 일반적인 패턴이다. 단일 고정값 대신 요일, 시간대, 계절성을 반영할 수 있다.

#### Anomaly Detection

**Anomaly Detection(이상 탐지)**은 정상 패턴과 크게 다른 상태를 찾는 과정이다. 이상은 곧 장애를 의미하지 않으므로 Business Context와 다른 Signal을 함께 확인해야 한다.

#### Event Correlation

**Event Correlation(이벤트 상관분석)**은 같은 원인에서 발생한 여러 Alert과 Event를 하나의 Incident로 묶는 과정이다.

#### Root Cause Analysis

**RCA(Root Cause Analysis, 근본 원인 분석)**는 장애의 최초 원인과 영향 경로를 찾는 활동이다. 상관관계가 발견됐다고 원인관계가 증명된 것은 아니므로 배포 이력, Service Dependency, Trace 등을 함께 사용해야 한다.

#### Runbook Automation

**Runbook**은 특정 장애를 진단하고 복구하기 위한 표준 절차다. 반복적이고 위험이 낮은 조치는 자동 실행할 수 있다.

### 7.4 AIOps 1.0의 현실적인 한계

강의자료는 초기 AIOps가 약속한 범위와 실제 도달점의 차이를 강조한다.

| 기대 | 현실적인 문제 |
|---|---|
| 여러 도구의 Signal 자동 상관분석 | 도구와 Schema가 제각각이라 데이터 정규화에 많은 비용이 든다. |
| 이상 탐지, RCA, 원격 조치까지 자동화 | 실제로는 Alert Noise 감소 수준에 머무르는 경우가 많다. |
| 사후 대응에서 예방 운영으로 전환 | 원인 분석과 대응을 사람이 수동으로 수행하는 경우가 많다. |
| 운영 비용 절감이라는 명확한 ROI | 효과를 금액과 시간으로 증명하기 어렵다. |

AIOps의 성패는 AI Model 자체보다 신뢰할 수 있는 Telemetry, 일관된 Service Metadata, 변경 이력, 소유자 정보, 대응 절차가 준비되어 있는지에 달려 있다.

### 7.5 자동화 수준을 단계적으로 높이기

처음부터 완전 자동 복구를 목표로 하면 위험하다.

1. Signal 수집과 품질 개선
2. Dashboard와 Search 표준화
3. Alert 중복 제거와 Grouping
4. 이상 탐지와 원인 후보 추천
5. 담당자 승인 후 Runbook 실행
6. 안전한 범위에서 자동 조치

자동 조치에는 다음 안전장치가 필요하다.

- 실행 조건과 허용 범위
- 승인 절차
- Rate Limit
- Dry Run
- Rollback
- Audit Log
- 실패 시 사람에게 Escalation

### 7.6 AIOps의 성공 지표

- Alert 수와 중복 Alert 비율
- 탐지 시간 MTTD(Mean Time to Detect)
- 확인 시간 MTTA(Mean Time to Acknowledge)
- 복구 시간 MTTR(Mean Time to Restore/Recover)
- 자동 조치 성공률
- 잘못된 Alert 비율
- 반복 장애 감소율
- 운영자가 절약한 시간

모델의 이상 탐지 정확도만으로는 AIOps의 Business Value를 설명하기 어렵다. 실제 장애 대응 시간과 운영 부담이 얼마나 줄었는지를 측정해야 한다.

### 이 장에서 기억할 것

- AIOps는 IT 운영 데이터를 AI로 분석해 탐지와 대응을 돕는 접근이다.
- MLOps는 ML Model 운영, AIOps는 IT Operations 개선이 중심이다.
- 신뢰할 수 있는 Telemetry와 Service Context가 없으면 AIOps도 제대로 동작하지 않는다.
- 상관관계는 근본 원인의 증명이 아니다.
- 자동화는 추천, 승인 실행, 제한적 자동 조치 순으로 단계적으로 확대한다.

---

## 8. 3일차 전체 연결

```text
학습 실험과 모델 이력을 기록
→ MLflow Tracking / Model Registry

운영 상태를 외부 Signal로 관찰
→ Metrics / Logs / Traces

Signal 저장과 분석
→ Prometheus·Mimir / Loki / Tempo / Grafana / Alloy

코드 배포 운영
→ DevOps

데이터·Feature·모델까지 확장
→ MLOps

Prompt·Retrieval·Tool·Token·안전까지 확장
→ LLMOps

운영 Signal을 AI로 분석하고 대응 지원
→ AIOps
```

3일차의 핵심은 운영 도구를 각각 외우는 것이 아니다. **모델의 생성 이력을 추적하고, 운영 Signal을 연결해 문제를 설명하며, 검증된 절차로 개선과 대응을 반복하는 체계**를 이해하는 것이다.

### 최종 체크

- MLflow의 Run, Artifact Store, Backend Store, Model Registry를 구분할 수 있는가?
- Monitoring과 Observability의 차이를 설명할 수 있는가?
- Metrics, Logs, Traces를 어떤 상황에 사용해야 하는지 설명할 수 있는가?
- Loki, Grafana, Tempo, Mimir, Alloy의 역할을 구분할 수 있는가?
- DevOps, MLOps, LLMOps, AIOps의 대상과 범위를 구분할 수 있는가?
- LLM Application에서 Prompt, Retrieval, Tool, Token 비용을 함께 관리해야 하는 이유를 설명할 수 있는가?
- AIOps 자동화를 단계적으로 적용해야 하는 이유를 설명할 수 있는가?

