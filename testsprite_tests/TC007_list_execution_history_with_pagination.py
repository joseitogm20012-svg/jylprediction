import requests

BASE_URL = "http://localhost:3005"
TIMEOUT = 30

def test_list_execution_history_with_pagination():
    url = f"{BASE_URL}/api/history"

    # Test without pagination params (default)
    try:
        resp = requests.get(url, timeout=TIMEOUT)
        resp.raise_for_status()
    except requests.RequestException as e:
        assert False, f"Request failed: {e}"

    assert resp.status_code == 200
    try:
        history_records = resp.json()
    except Exception as e:
        assert False, f"Response is not valid JSON: {e}"
    assert isinstance(history_records, list), "Response should be a list"

    # Validate each record has required fields with correct types
    for rec in history_records:
        assert isinstance(rec, dict), "Each history item should be a dict"
        # Check required keys existence
        for key in ["scraper_id", "status", "started_at", "duration_ms", "records_count", "sandbox"]:
            assert key in rec, f"Missing key '{key}' in history record"
        # Validate types
        assert isinstance(rec["scraper_id"], str), "'scraper_id' should be string"
        assert isinstance(rec["status"], str), "'status' should be string"
        assert isinstance(rec["started_at"], str), "'started_at' should be ISO datetime string"
        assert isinstance(rec["duration_ms"], (int, float)), "'duration_ms' should be number"
        assert isinstance(rec["records_count"], int), "'records_count' should be int"
        assert isinstance(rec["sandbox"], bool), "'sandbox' should be boolean"

    # Test pagination: limit and offset parameters
    params = {"limit": 5, "offset": 0}
    try:
        page_resp = requests.get(url, params=params, timeout=TIMEOUT)
        page_resp.raise_for_status()
    except requests.RequestException as e:
        assert False, f"Paginated request failed: {e}"
    assert page_resp.status_code == 200
    try:
        page_records = page_resp.json()
    except Exception as e:
        assert False, f"Paginated response is not valid JSON: {e}"
    assert isinstance(page_records, list), "Paginated response should be a list"
    assert len(page_records) <= 5, "Paginated response list size should be <= limit param"

    # Validate fields in paginated results as well
    for rec in page_records:
        assert isinstance(rec, dict), "Each paginated history item should be a dict"
        for key in ["scraper_id", "status", "started_at", "duration_ms", "records_count", "sandbox"]:
            assert key in rec, f"Missing key '{key}' in paginated history record"
        assert isinstance(rec["scraper_id"], str), "'scraper_id' should be string"
        assert isinstance(rec["status"], str), "'status' should be string"
        assert isinstance(rec["started_at"], str), "'started_at' should be ISO datetime string"
        assert isinstance(rec["duration_ms"], (int, float)), "'duration_ms' should be number"
        assert isinstance(rec["records_count"], int), "'records_count' should be int"
        assert isinstance(rec["sandbox"], bool), "'sandbox' should be boolean"

test_list_execution_history_with_pagination()