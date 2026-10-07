"""6단계: 실제 LangSmith 웹 화면을 캡처한다.

smith.langchain.com 대시보드 자체는 로그인(OAuth)이 필요해 API 키만으로는 로그인된
화면을 그대로 캡처할 수 없다(실제로 조직 스코프 URL — /o/<id>/... — 을 headless로 열면
로그인 페이지로 리다이렉트되는 것을 확인함). 대신 client.share_run()이 실제로 만들어주는
"공개 트레이스 링크"(/public/<id>/r, 로그인 불필요, curl 200 확인함)를 headless Chrome으로
열어 진짜 화면을 캡처한다.

주의(실제로 겪은 문제): client.share_dataset()이 반환하는 /public/<token>/d 링크는
curl로는 200이 오지만 headless Chrome이 렌더링을 끝내지 못하고 무한정 멈춘다(2분
타임아웃 후 강제 종료해야 했음) — 원인 미상. 이 스크립트는 그 경로는 시도하지 않고,
실제로 안정적으로 동작을 확인한 /public/<id>/r 트레이스 링크만 캡처한다.
"""
import json
import subprocess
from pathlib import Path
from langsmith import Client

CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
SCREENSHOT_DIR = Path("screenshots")
SCREENSHOT_DIR.mkdir(exist_ok=True)


def get_or_create_share_url(client: Client, run_id: str) -> str:
    try:
        return client.share_run(run_id)
    except Exception:
        # 이미 공유된 Run을 다시 share_run()하면 실제로 409 Conflict가 발생한다.
        return client.read_run_shared_link(run_id)


def capture(url: str, out_file: str, width=1600, height=1000, wait_ms=4000):
    subprocess.run([
        CHROME, "--headless", "--disable-gpu",
        f"--screenshot={SCREENSHOT_DIR / out_file}",
        f"--window-size={width},{height}",
        f"--virtual-time-budget={wait_ms}",
        url,
    ], check=True, capture_output=True, timeout=30)
    print(f"캡처 완료: {out_file}  <-  {url}")


if __name__ == "__main__":
    client = Client()

    with open("run_ids.json") as f:
        run_ids = json.load(f)

    urls = {}
    for idx, label in [(0, "rag"), (2, "vector_db")]:
        url = get_or_create_share_url(client, run_ids[idx])
        urls[label] = url
        print(f"[{label}] 공개 공유 링크: {url}")

    with open("share_urls.json", "w") as f:
        json.dump(urls, f, indent=2)

    capture(urls["rag"], "01_public_trace_detail.png")
    capture(urls["vector_db"], "02_public_trace_detail_vector_db.png")
