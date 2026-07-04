import os
import requests

BASE_URL = os.environ.get("TARGET_URL", "http://localhost:3006")

def test_diagnostic_history():
    resp = requests.get(f"{BASE_URL}/api/diagnostic/history/xg", timeout=10)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)

def test_diagnostic_compare_not_found():
    resp = requests.get(f"{BASE_URL}/api/diagnostic/compare/99999/99998", timeout=10)
    assert resp.status_code == 404

if __name__ == "__main__":
    test_diagnostic_history()
    test_diagnostic_compare_not_found()
    print("TC008 PASSED")
