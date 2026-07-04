import requests
import time

BASE_URL = "http://localhost:3005"
TIMEOUT = 30

def test_run_html_structure_diagnostic_and_compare_snapshots():
    scraper_id = None
    created_snapshot_ids = []

    try:
        # Step 1: Get a scraper_id from the list of scrapers if none is given
        resp = requests.get(f"{BASE_URL}/api/scrapers", timeout=TIMEOUT)
        resp.raise_for_status()
        scrapers = resp.json()
        assert isinstance(scrapers, list) and len(scrapers) > 0
        # Pick a scraper that is valid for diagnostic (most likely any)
        scraper_id = scrapers[0].get("id")
        assert scraper_id is not None and isinstance(scraper_id, str)

        # Step 2: POST /api/diagnostic/run/{scraper_id} with url and optional page_source
        run_payload = {
            "url": "https://example.com",
            "page_source": "<html><body><p>Test Page Source</p></body></html>",
        }
        run_resp = requests.post(
            f"{BASE_URL}/api/diagnostic/run/{scraper_id}",
            json=run_payload,
            timeout=TIMEOUT,
        )
        run_resp.raise_for_status()
        run_data = run_resp.json()
        # Validate presence and type of required keys
        assert "has_changes" in run_data and isinstance(run_data["has_changes"], bool)
        assert "severity" in run_data and isinstance(run_data["severity"], (int, float))
        assert "changes" in run_data and isinstance(run_data["changes"], list)
        assert "snapshot" in run_data and isinstance(run_data["snapshot"], (dict, list, str))
        assert "tab_labels" in run_data and isinstance(run_data["tab_labels"], (list, type(None)))
        assert "table_count" in run_data and isinstance(run_data["table_count"], int)
        assert "class_hashes" in run_data and isinstance(run_data["class_hashes"], dict)

        # Extract the snapshot ID created (assumption: snapshot has an "id" field or else get history and find latest)
        snapshot_id = None
        if isinstance(run_data["snapshot"], dict) and "id" in run_data["snapshot"]:
            snapshot_id = run_data["snapshot"]["id"]
        if not snapshot_id:
            # fallback: get snapshots history and pick the latest snapshot id for this scraper
            history_resp = requests.get(
                f"{BASE_URL}/api/diagnostic/history/{scraper_id}", timeout=TIMEOUT
            )
            history_resp.raise_for_status()
            history = history_resp.json()
            assert isinstance(history, list) and len(history) > 0
            latest_snapshot = max(history, key=lambda x: x.get("created_at", ""))
            snapshot_id = latest_snapshot.get("id")
        assert snapshot_id is not None
        created_snapshot_ids.append(snapshot_id)

        # Step 3: Create at least one more snapshot to compare - call run again with different page_source
        run_payload_2 = {
            "url": "https://example.com",
            "page_source": "<html><body><p>Changed Page Source</p></body></html>",
        }
        run_resp_2 = requests.post(
            f"{BASE_URL}/api/diagnostic/run/{scraper_id}",
            json=run_payload_2,
            timeout=TIMEOUT,
        )
        run_resp_2.raise_for_status()
        run_data_2 = run_resp_2.json()
        # Validate keys again
        assert "has_changes" in run_data_2 and isinstance(run_data_2["has_changes"], bool)
        assert "severity" in run_data_2 and isinstance(run_data_2["severity"], (int, float))
        assert "changes" in run_data_2 and isinstance(run_data_2["changes"], list)
        assert "snapshot" in run_data_2
        snapshot_id_2 = None
        if isinstance(run_data_2["snapshot"], dict) and "id" in run_data_2["snapshot"]:
            snapshot_id_2 = run_data_2["snapshot"]["id"]
        if not snapshot_id_2:
            # fallback: get snapshots history and pick the latest snapshot id - may be same or newer
            history_resp = requests.get(
                f"{BASE_URL}/api/diagnostic/history/{scraper_id}", timeout=TIMEOUT
            )
            history_resp.raise_for_status()
            history = history_resp.json()
            ids = [snap.get("id") for snap in history if snap.get("id") not in created_snapshot_ids]
            if ids:
                snapshot_id_2 = max(ids)
        assert snapshot_id_2 is not None and snapshot_id_2 != snapshot_id
        created_snapshot_ids.append(snapshot_id_2)

        # Step 4: GET /api/diagnostic/compare/{id1}/{id2} to compare two snapshots
        compare_resp = requests.get(
            f"{BASE_URL}/api/diagnostic/compare/{snapshot_id}/{snapshot_id_2}", timeout=TIMEOUT
        )
        compare_resp.raise_for_status()
        compare_data = compare_resp.json()
        # Validate response fields
        assert "has_changes" in compare_data and isinstance(compare_data["has_changes"], bool)
        assert "severity" in compare_data and isinstance(compare_data["severity"], (int, float))
        assert "changes" in compare_data and isinstance(compare_data["changes"], list)
        assert "snapshot_old_id" in compare_data and compare_data["snapshot_old_id"] == snapshot_id
        assert "snapshot_new_id" in compare_data and compare_data["snapshot_new_id"] == snapshot_id_2

    except requests.RequestException as e:
        assert False, f"Request failed: {e}"
    except AssertionError as e:
        assert False, f"Assertion failed: {e}"