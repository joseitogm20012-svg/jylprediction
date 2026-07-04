import requests

BASE_URL = "http://localhost:3005"
TIMEOUT = 30

def test_preview_scraper_data_with_validation_warnings():
    try:
        # Step 1: Get the list of all scrapers to find one that supports preview
        scrapers_resp = requests.get(f"{BASE_URL}/api/scrapers", timeout=TIMEOUT)
        assert scrapers_resp.status_code == 200, f"Expected 200 from /api/scrapers, got {scrapers_resp.status_code}"
        scrapers = scrapers_resp.json()
        assert isinstance(scrapers, list), "Scrapers response should be a list"

        # Heuristic: choose a scraper known to support preview (from PRD: xg, cards, transfermarkt)
        # We'll try 'xg' first, fallback to others if not found
        preview_supported_ids = {"xg", "cards", "transfermarkt"}
        scraper_id = None
        for scraper in scrapers:
            if scraper.get("id") in preview_supported_ids:
                scraper_id = scraper["id"]
                break

        assert scraper_id is not None, "No scraper found that supports preview"

        # Step 2: GET /api/preview/{scraper_id}
        preview_resp = requests.get(f"{BASE_URL}/api/preview/{scraper_id}", timeout=TIMEOUT)
        assert preview_resp.status_code == 200, f"Expected 200 from /api/preview/{scraper_id}, got {preview_resp.status_code}"

        preview_data = preview_resp.json()
        assert isinstance(preview_data, dict), "Preview response should be a JSON object"

        # Validate required keys
        required_keys = {"columns", "rows", "total", "warnings"}
        for key in required_keys:
            assert key in preview_data, f"Key '{key}' missing in preview response"

        # Validate columns
        columns = preview_data["columns"]
        assert isinstance(columns, list), "'columns' should be a list"
        assert all(isinstance(col, str) for col in columns), "Each column should be a string"

        # Validate rows
        rows = preview_data["rows"]
        assert isinstance(rows, list), "'rows' should be a list"

        # Validate total
        total = preview_data["total"]
        assert isinstance(total, int), "'total' should be an integer"
        assert total >= 0, "'total' should be zero or positive"

        # Validate warnings array structure
        warnings = preview_data["warnings"]
        assert isinstance(warnings, list), "'warnings' should be a list"
        for warning in warnings:
            assert isinstance(warning, dict), "Each warning should be a dict"
            # Expected keys based on PRD: row, field, message, severity
            for wkey in ("row", "field", "message", "severity"):
                assert wkey in warning, f"Warning missing expected key '{wkey}'"
            assert isinstance(warning["row"], int), "'row' in warning should be int"
            assert isinstance(warning["field"], str), "'field' in warning should be str"
            assert isinstance(warning["message"], str), "'message' in warning should be str"
            assert isinstance(warning["severity"], str), "'severity' in warning should be str"

    except requests.RequestException as e:
        assert False, f"Request failed: {e}"

test_preview_scraper_data_with_validation_warnings()