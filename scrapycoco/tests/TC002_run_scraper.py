import os
import requests

BASE_URL = os.environ.get("TARGET_URL", "http://localhost:3006")

def test_run_scraper_returns_sse():
    resp = requests.get(f"{BASE_URL}/api/run/results", timeout=15, stream=True)
    assert resp.status_code == 200
    assert resp.headers.get("content-type", "").startswith("text/event-stream")
    lines_read = 0
    for _ in range(20):
        line = resp.raw.readline()
        if not line:
            break
        line = line.strip()
        if not line:
            continue
        if line.startswith(b"data:") or line.startswith(b"event:"):
            lines_read += 1
            if lines_read >= 2:
                break
    assert lines_read >= 2, f"Expected at least 2 SSE events, got {lines_read}"

def test_run_unknown_scraper_returns_404():
    resp = requests.get(f"{BASE_URL}/api/run/does_not_exist", timeout=10)
    assert resp.status_code == 404

if __name__ == "__main__":
    test_run_scraper_returns_sse()
    test_run_unknown_scraper_returns_404()
    print("TC002 PASSED")
