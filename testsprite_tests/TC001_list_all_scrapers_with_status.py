import requests
from datetime import datetime

BASE_URL = "http://localhost:3005"
TIMEOUT = 30

def test_list_all_scrapers_with_status():
    url = f"{BASE_URL}/api/scrapers"
    try:
        response = requests.get(url, timeout=TIMEOUT)
    except requests.RequestException as e:
        assert False, f"Request failed: {e}"

    assert response.status_code == 200, f"Expected 200 OK, got {response.status_code}"

    try:
        scrapers = response.json()
    except ValueError:
        assert False, "Response is not valid JSON"

    assert isinstance(scrapers, list), "Response JSON is not a list"

    # Expected fields in each scraper object
    required_fields = {"id", "name", "description", "status", "last_run", "exit_code"}

    for scraper in scrapers:
        assert isinstance(scraper, dict), "Each scraper item should be a JSON object"
        keys = set(scraper.keys())
        assert required_fields.issubset(keys), f"Scraper missing required fields. Found: {keys}"

        # Validate specific fields types and values
        assert isinstance(scraper["id"], str) and scraper["id"], "Scraper id must be a non-empty string"
        assert isinstance(scraper["name"], str) and scraper["name"], "Scraper name must be a non-empty string"
        assert isinstance(scraper["description"], str), "Scraper description must be a string"
        assert scraper["status"] in ("idle", "running", "success", "error"), f"Invalid status value: {scraper['status']}"

        # last_run can be None or a datetime string, so validate if present
        last_run = scraper["last_run"]
        if last_run is not None:
            assert isinstance(last_run, str), "last_run should be a string null or ISO8601 datetime string"
            try:
                # Attempt to parse datetime to validate format
                datetime.fromisoformat(last_run.replace("Z", "+00:00"))
            except ValueError:
                assert False, f"last_run is not a valid ISO8601 datetime string: {last_run}"

        # exit_code can be None or int
        exit_code = scraper["exit_code"]
        assert (exit_code is None) or (isinstance(exit_code, int)), "exit_code must be int or None"

test_list_all_scrapers_with_status()