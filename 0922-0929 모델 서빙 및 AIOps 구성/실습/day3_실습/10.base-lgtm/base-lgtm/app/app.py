"""checkout 서비스 — LGTM 스택 실습용 샘플 앱.

이 앱 하나가 세 가지 시그널을 모두 실제로 만들어낸다:
  - 메트릭: /metrics 엔드포인트에 Prometheus 포맷으로 노출 (Prometheus가 스크레이핑)
  - 로그: OTel Logs SDK로 OTLP를 통해 Grafana Alloy로 직접 전송
  - 트레이스: OTel Traces SDK로 OTLP를 통해 Grafana Alloy로 직접 전송

app=checkout, env=demo 라벨을 로그·트레이스 리소스 속성에 공통으로 붙여, Grafana에서
같은 요청의 로그·트레이스·(메트릭)를 상관 확인할 수 있게 한다.
"""
import logging
import os
import random
import time

from fastapi import FastAPI, Response
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc._log_exporter import OTLPLogExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk._logs import LoggerProvider, LoggingHandler
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

OTLP_ENDPOINT = os.environ.get("OTLP_ENDPOINT", "alloy:4317")
SERVICE_NAME = "checkout"

resource = Resource.create({"service.name": SERVICE_NAME, "app": "checkout", "env": "demo"})

# --- 트레이스: OTLP로 Alloy에 직접 전송 ---
tracer_provider = TracerProvider(resource=resource)
tracer_provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=OTLP_ENDPOINT, insecure=True)))
trace.set_tracer_provider(tracer_provider)
tracer = trace.get_tracer(SERVICE_NAME)

# --- 로그: OTLP로 Alloy에 직접 전송(app·env 라벨은 리소스 속성으로 부착) ---
logger_provider = LoggerProvider(resource=resource)
logger_provider.add_log_record_processor(BatchLogRecordProcessor(OTLPLogExporter(endpoint=OTLP_ENDPOINT, insecure=True)))
otel_handler = LoggingHandler(level=logging.INFO, logger_provider=logger_provider)

log = logging.getLogger("checkout")
log.setLevel(logging.INFO)
log.addHandler(otel_handler)
log.addHandler(logging.StreamHandler())  # 컨테이너 stdout에도 남겨 docker logs로 확인 가능

# --- 메트릭: Prometheus가 직접 스크레이핑할 수 있게 /metrics로 노출 ---
REQS = Counter("http_requests_total", "총 요청 수", ["path", "status"])
LATENCY = Histogram("http_request_duration_seconds", "요청 처리 시간(초)", ["path"])

app = FastAPI(title="checkout")
FastAPIInstrumentor.instrument_app(app, tracer_provider=tracer_provider)


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get("/checkout")
def checkout(user_id: str = "u-1001", amount: float = 42.0):
    start = time.time()
    with tracer.start_as_current_span("process-checkout") as span:
        span.set_attribute("user_id", user_id)
        span.set_attribute("amount", amount)

        # 실제로 5xx가 섞여 나오도록 20% 확률로 실패시킨다(PromQL 5xx 비율 예시와 동일한 패턴)
        fail = random.random() < 0.2
        time.sleep(random.uniform(0.02, 0.15))

        if fail:
            log.error(f"checkout failed user_id={user_id} amount={amount} reason=payment_gateway_timeout")
            REQS.labels(path="/checkout", status="500").inc()
            LATENCY.labels(path="/checkout").observe(time.time() - start)
            span.set_attribute("http.status_code", 500)
            return Response(status_code=500, content="payment gateway timeout")

        log.info(f"checkout succeeded user_id={user_id} amount={amount}")
        REQS.labels(path="/checkout", status="200").inc()
        LATENCY.labels(path="/checkout").observe(time.time() - start)
        span.set_attribute("http.status_code", 200)
        return {"status": "success", "user_id": user_id, "amount": amount}
