import os
import requests

BASE_URL = os.environ.get("TARGET_URL", "http://localhost:3005")

def test_scheduler_list():
    resp = requests.get(f"{BASE_URL}/api/scheduler/list", timeout=10)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)

def test_scheduler_add_delete():
    new_job = requests.post(
        f"{BASE_URL}/api/scheduler/add",
        json={"scraper_id": "results", "cron_expression": "0 6 * * *"},
        timeout=10
    )
    assert new_job.status_code == 200
    job_id = new_job.json().get("id")
    if job_id:
        resp = requests.delete(f"{BASE_URL}/api/scheduler/{job_id}", timeout=10)
        assert resp.status_code == 200

if __name__ == "__main__":
    test_scheduler_list()
    test_scheduler_add_delete()
    print("TC007 PASSED")
