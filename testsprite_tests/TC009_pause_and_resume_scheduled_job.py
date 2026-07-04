import requests

BASE_URL = "http://localhost:3005"
TIMEOUT = 30


def test_pause_and_resume_scheduled_job():
    headers = {"Content-Type": "application/json"}
    schedule_id = None

    # Step 1: Create a new schedule (needed to have a schedule_id)
    try:
        add_payload = {
            "scraper_id": "xg",
            "cron_expression": "0 6 * * *",
            "params": {"sandbox": True}
        }
        add_resp = requests.post(
            f"{BASE_URL}/api/scheduler/add",
            json=add_payload,
            headers=headers,
            timeout=TIMEOUT
        )
        assert add_resp.status_code == 200, f"Failed to add schedule, status: {add_resp.status_code}"
        add_data = add_resp.json()
        assert "id" in add_data, "Schedule ID not returned on add"
        schedule_id = add_data["id"]

        # Step 2: Pause the schedule
        pause_resp = requests.post(
            f"{BASE_URL}/api/scheduler/{schedule_id}/pause",
            headers=headers,
            timeout=TIMEOUT
        )
        assert pause_resp.status_code == 200, f"Pause request failed with status {pause_resp.status_code}"
        pause_data = pause_resp.json()
        assert pause_data.get("message") == "Tarea pausada", f"Pause message unexpected: {pause_data}"

        # Step 3: Resume the schedule
        resume_resp = requests.post(
            f"{BASE_URL}/api/scheduler/{schedule_id}/resume",
            headers=headers,
            timeout=TIMEOUT
        )
        assert resume_resp.status_code == 200, f"Resume request failed with status {resume_resp.status_code}"
        resume_data = resume_resp.json()
        assert resume_data.get("message") == "Tarea reanudada", f"Resume message unexpected: {resume_data}"

    finally:
        # Cleanup: delete the schedule if created
        if schedule_id:
            delete_resp = requests.delete(
                f"{BASE_URL}/api/scheduler/{schedule_id}",
                headers=headers,
                timeout=TIMEOUT
            )
            if delete_resp.status_code != 200:
                print(f"Warning: Failed to delete schedule {schedule_id}, status {delete_resp.status_code}")


test_pause_and_resume_scheduled_job()