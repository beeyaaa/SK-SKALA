"""
3단계: 실제로 떠 있는 FastAPI + TorchScript 서버에 부하를 걸어 성능을 측정한다.

ONNX/base_fastapi/perf_test.py와 완전히 동일한 설계를 그대로 재사용한다 — 이미
그쪽에서 세 번의 실패(fork 크래시 -> IPC 역전 -> spawn 편향)를 거쳐 검증된
방식이므로, 이 폴더에서 그 시행착오를 반복할 필요가 없다. 다른 점은 대상
서버(BASE_URL의 포트)뿐이다.

## 왜 같은 방식을 그대로 쓰는가
클라이언트가 ThreadPoolExecutor를 쓰면 클라이언트 자신의 GIL이 병목과 섞여
측정된다(배경은 _통합개념/GIL(GLOBAL INTERPRETER LOCK).md 참고). 그래서 동시성
개수만큼 별도 프로세스(자기만의 GIL)를 미리 띄워두고, 각 프로세스가 자기 몫의
요청을 순차로 다 보낸 뒤 결과를 한 번에 반환하게 한다 — 요청 1건마다 IPC를
타지 않고, 워커 1개당 IPC 왕복 1번으로 줄인다. 프로세스 풀은 최대 동시성
크기로 한 번만 만들어 예열해두고 이후 각 동시성 구간에서는 그중 일부만
재사용한다(spawn 비용이 특정 구간의 측정치에 섞이지 않도록).
"""

import json
import multiprocessing
import multiprocessing.pool
import statistics
import time
import urllib.request

BASE_URL = "http://127.0.0.1:8331"
MAX_CONCURRENCY = 50
REQUESTS_PER_WORKER = 40  # 워커(=동시성 한 단위)마다 순차로 보낼 요청 수

# ONNX/base_fastapi와 동일한 3개 실측 표본을 그대로 순환 사용 — 결과를 나란히
# 비교할 수 있도록 페이로드를 일치시킨다.
PAYLOADS = [
    {"sepal_length_cm": 5.1, "sepal_width_cm": 3.5, "petal_length_cm": 1.4, "petal_width_cm": 0.2},
    {"sepal_length_cm": 7.0, "sepal_width_cm": 3.2, "petal_length_cm": 4.7, "petal_width_cm": 1.4},
    {"sepal_length_cm": 6.3, "sepal_width_cm": 3.3, "petal_length_cm": 6.0, "petal_width_cm": 2.5},
]


def one_request(i: int) -> tuple[float, bool]:
    """/predict에 요청 1건을 보내고 (왕복 지연시간_ms, 성공여부)를 반환한다."""
    payload = json.dumps(PAYLOADS[i % len(PAYLOADS)]).encode("utf-8")
    req = urllib.request.Request(
        f"{BASE_URL}/predict",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            resp.read()
            ok = resp.status == 200
    except Exception:
        ok = False
    return (time.perf_counter() - t0) * 1000, ok


def worker_loop(n_requests: int) -> list[tuple[float, bool]]:
    """워커 프로세스 하나가 n_requests건을 자기 프로세스 안에서 순차로 보내고,
    (지연시간, 성공여부) 리스트를 한 번에 반환한다 — 부모-자식 간 IPC는 이
    함수 호출 1번(제출 1번 + 반환 1번)뿐이다."""
    return [one_request(i) for i in range(n_requests)]


def percentile(sorted_values: list, p: float) -> float:
    if not sorted_values:
        return float("nan")
    idx = min(len(sorted_values) - 1, int(len(sorted_values) * p))
    return sorted_values[idx]


def run_load(pool: multiprocessing.pool.Pool, concurrency: int, requests_per_worker: int) -> dict:
    """미리 예열해둔 풀(최대 동시성 크기로 고정)에서 `concurrency`개 워커만
    골라 쓴다 — 나머지 워커는 이번 구간에서 그냥 유휴 상태. 각 워커는 자기
    몫(requests_per_worker건)을 순차로 보내고 끝나면 결과를 한 번에 반환한다.
    총 요청 수는 concurrency * requests_per_worker."""
    total_requests = concurrency * requests_per_worker

    t_start = time.perf_counter()
    per_worker_results = pool.map(worker_loop, [requests_per_worker] * concurrency)
    wall_time = time.perf_counter() - t_start

    latencies = []
    errors = 0
    for worker_results in per_worker_results:
        for latency_ms, ok in worker_results:
            latencies.append(latency_ms)
            if not ok:
                errors += 1
    latencies.sort()

    return {
        "concurrency": concurrency,
        "total_requests": total_requests,
        "errors": errors,
        "wall_time_s": wall_time,
        "throughput_rps": total_requests / wall_time,
        "latency_mean_ms": statistics.mean(latencies),
        "latency_p50_ms": percentile(latencies, 0.50),
        "latency_p90_ms": percentile(latencies, 0.90),
        "latency_p95_ms": percentile(latencies, 0.95),
        "latency_p99_ms": percentile(latencies, 0.99),
        "latency_max_ms": latencies[-1],
    }


def main():
    with multiprocessing.Pool(processes=MAX_CONCURRENCY) as pool:
        # 웜업 — 풀이 워커 프로세스 MAX_CONCURRENCY개를 실제로 다 띄우기까지
        # 걸리는 spawn 비용을 여기서 한 번에 치르고, 이후 구간 측정에서는
        # 제외한다.
        print(f"[warmup] {MAX_CONCURRENCY}개 워커 예열 중...")
        run_load(pool, concurrency=MAX_CONCURRENCY, requests_per_worker=REQUESTS_PER_WORKER)

        print(f"\n{'동시성':>6} {'요청수':>6} {'실패':>4} {'처리량(req/s)':>14} {'평균(ms)':>9} {'p50(ms)':>9} {'p95(ms)':>9} {'p99(ms)':>9} {'최대(ms)':>9}")
        print("-" * 90)

        results = []
        for concurrency in [1, 5, 20, 50]:
            r = run_load(pool, concurrency, requests_per_worker=REQUESTS_PER_WORKER)
            results.append(r)
            print(
                f"{r['concurrency']:>6} {r['total_requests']:>6} {r['errors']:>4} "
                f"{r['throughput_rps']:>14.1f} {r['latency_mean_ms']:>9.2f} "
                f"{r['latency_p50_ms']:>9.2f} {r['latency_p95_ms']:>9.2f} "
                f"{r['latency_p99_ms']:>9.2f} {r['latency_max_ms']:>9.2f}"
            )

    print("\n[요약] 동시성 1 -> 50으로 올렸을 때:")
    r1, r50 = results[0], results[-1]
    print(f"  처리량: {r1['throughput_rps']:.1f} req/s -> {r50['throughput_rps']:.1f} req/s ({r50['throughput_rps'] / r1['throughput_rps']:.2f}배)")
    print(f"  p50 지연시간: {r1['latency_p50_ms']:.2f}ms -> {r50['latency_p50_ms']:.2f}ms")
    print(f"  p99 지연시간: {r1['latency_p99_ms']:.2f}ms -> {r50['latency_p99_ms']:.2f}ms")


if __name__ == "__main__":
    main()
