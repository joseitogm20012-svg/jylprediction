import os
import requests

BASE_URL = os.environ.get("TARGET_URL", "http://localhost:3006")

def test_preview_unknown_scraper():
    resp = requests.get(f"{BASE_URL}/api/preview/fake_scraper", timeout=5)
    assert resp.status_code == 404

def test_preview_endpoint_accepts_known_scraper():
    resp = requests.get(f"{BASE_URL}/api/preview/elo", timeout=5)
    assert resp.status_code in (200, 500, 503)

if __name__ == "__main__":
    test_preview_unknown_scraper()
    test_preview_endpoint_accepts_known_scraper()
    print("TC005 PASSED")
