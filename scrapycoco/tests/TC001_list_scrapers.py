import os
import requests

BASE_URL = os.environ.get("TARGET_URL", "http://localhost:3006")

def test_list_scrapers():
    resp = requests.get(f"{BASE_URL}/api/scrapers", timeout=10)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 8
    scraper_ids = {s["id"] for s in data}
    expected = {"results", "xg", "xga", "cards", "flashscore", "transfermarkt", "wc2026", "elo"}
    assert scraper_ids == expected, f"Missing scrapers: {expected - scraper_ids}"

def test_all_scrapers_have_names():
    resp = requests.get(f"{BASE_URL}/api/scrapers", timeout=10)
    for s in resp.json():
        assert s["name"], f"Scraper {s['id']} missing name"
        assert s["status"] in ("idle", "running")

if __name__ == "__main__":
    test_list_scrapers()
    test_all_scrapers_have_names()
    print("TC001 PASSED")
