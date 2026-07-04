import os
import requests

BASE_URL = os.environ.get("TARGET_URL", "http://localhost:3005")

def test_batch_run_sse():
    resp = requests.post(
        f"{BASE_URL}/api/batch/run",
        json={"scraper_ids": ["results", "elo"], "sandbox": True},
        timeout=15,
        stream=True
    )
    assert resp.status_code == 200
    assert resp.headers.get("content-type", "").startswith("text/event-stream")

def test_batch_run_unknown_scraper():
    resp = requests.post(
        f"{BASE_URL}/api/batch/run",
        json={"scraper_ids": ["fake_scraper"]},
        timeout=10
    )
    assert resp.status_code == 404

if __name__ == "__main__":
    test_batch_run_sse()
    test_batch_run_unknown_scraper()
    print("TC003 PASSED")
