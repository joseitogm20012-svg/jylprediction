import os
import requests

BASE_URL = os.environ.get("TARGET_URL", "http://localhost:3005")

def test_history():
    resp = requests.get(f"{BASE_URL}/api/history", timeout=10)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)

def test_history_with_scraper_filter():
    resp = requests.get(f"{BASE_URL}/api/history?scraper_id=results&limit=5", timeout=10)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) <= 5

def test_history_metrics():
    resp = requests.get(f"{BASE_URL}/api/history/metrics", timeout=10)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, dict) or isinstance(data, list)

def test_history_stats():
    resp = requests.get(f"{BASE_URL}/api/history/stats", timeout=10)
    assert resp.status_code == 200

if __name__ == "__main__":
    test_history()
    test_history_with_scraper_filter()
    test_history_metrics()
    test_history_stats()
    print("TC004 PASSED")
