import requests

BASE_URL = "http://localhost:3005"
TIMEOUT = 30

def test_add_new_scheduler_job_with_cron_expression():
    # Step 1: Get the list of scrapers to find a valid scraper_id
    try:
        resp_scrapers = requests.get(f"{BASE_URL}/api/scrapers", timeout=TIMEOUT)
        assert resp_scrapers.status_code == 200, f"Failed to get scrapers list: {resp_scrapers.text}"
        scrapers = resp_scrapers.json()
        assert isinstance(scrapers, list) and len(scrapers) > 0, "Scrapers list is empty or not a list"
        valid_scraper_id = scrapers[0].get("id")
        assert valid_scraper_id, "First scraper does not have an 'id'"
    except Exception as e:
        raise AssertionError(f"Setup failed: {e}")

    # Step 2: Add new scheduler job with a valid cron expression
    schedule_id = None
    add_url = f"{BASE_URL}/api/scheduler/add"
    payload = {
        "scraper_id": valid_scraper_id,
        "cron_expression": "0 6 * * *",
        "params": {
            "sandbox": True
        }
    }

    try:
        resp_add = requests.post(add_url, json=payload, timeout=TIMEOUT)
        assert resp_add.status_code == 200, f"Scheduler add failed: {resp_add.text}"
        data = resp_add.json()
        assert "id" in data and "message" in data, "Response missing 'id' or 'message'"
        schedule_id = data["id"]
        assert isinstance(schedule_id, (int, str)), "Schedule id is not int or str"
        assert isinstance(data["message"], str) and len(data["message"]) > 0, "Message is empty"
    finally:
        # Cleanup: delete the created schedule if schedule_id exists
        if schedule_id:
            try:
                del_resp = requests.delete(f"{BASE_URL}/api/scheduler/{schedule_id}", timeout=TIMEOUT)
                assert del_resp.status_code == 200, f"Failed to delete schedule {schedule_id}: {del_resp.text}"
                del_data = del_resp.json()
                assert "message" in del_data and isinstance(del_data["message"], str), "Delete response invalid"
            except Exception as cleanup_error:
                print(f"Cleanup failed for schedule {schedule_id}: {cleanup_error}")

test_add_new_scheduler_job_with_cron_expression()