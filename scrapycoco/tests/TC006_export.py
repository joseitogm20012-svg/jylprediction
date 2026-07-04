import os
import requests

BASE_URL = os.environ.get("TARGET_URL", "http://localhost:3006")

def test_export_unknown_scraper():
    resp = requests.post(
        f"{BASE_URL}/api/export",
        json={"scraper_id": "fake", "format": "csv"},
        timeout=5
    )
    assert resp.status_code == 404

def test_export_without_data():
    resp = requests.post(
        f"{BASE_URL}/api/export",
        json={"scraper_id": "results", "format": "csv"},
        timeout=5
    )
    assert resp.status_code in (400, 404)

if __name__ == "__main__":
    test_export_unknown_scraper()
    test_export_without_data()
    print("TC006 PASSED")
