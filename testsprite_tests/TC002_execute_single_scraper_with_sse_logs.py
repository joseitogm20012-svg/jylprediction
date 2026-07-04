import requests
import sseclient
import time

BASE_URL = "http://localhost:3005"
TIMEOUT = 30


def test_execute_single_scraper_with_sse_logs():
    # Step 1: Get list of scrapers to find a valid scraper_id
    try:
        resp = requests.get(f"{BASE_URL}/api/scrapers", timeout=TIMEOUT)
        resp.raise_for_status()
        scrapers = resp.json()
        assert isinstance(scrapers, list) and len(scrapers) > 0

        # Select a scraper_id from the list (prefer one with 'idle' or at least present)
        scraper_id = None
        for scraper in scrapers:
            if "id" in scraper and ("status" in scraper and scraper["status"] in ["idle", "success", "error"]):
                scraper_id = scraper["id"]
                break
        if scraper_id is None:
            scraper_id = scrapers[0]["id"]
    except Exception as e:
        raise AssertionError(f"Failed to get scraper list or select valid scraper_id: {e}")

    # Step 2: Prepare valid parameters for GET /api/run/{scraper_id}
    # According to PRD example, match_id, team_name, type, and sandbox are params
    # We'll provide plausible sample parameters (strings and bool)
    params = {
        "match_id": "12345",
        "team_name": "TeamA",
        "type": "full",
        "sandbox": "true"  # pass boolean as string to be safe (FastAPI usually accepts)
    }

    # Step 3: Call the SSE endpoint and consume the stream of events
    url = f"{BASE_URL}/api/run/{scraper_id}"
    headers = {
        "Accept": "text/event-stream"
    }

    try:
        with requests.get(url, headers=headers, params=params, stream=True, timeout=TIMEOUT) as response:
            assert response.status_code == 200, f"Expected status 200, got {response.status_code}"
            # Use sseclient to parse Server-Sent Events
            client = sseclient.SSEClient(response)

            event_types_received = set()
            exit_code_found = False
            final_status_found = False
            end_event_received = False
            max_wait_seconds = TIMEOUT
            start_time = time.time()

            for event in client.events():
                event_types_received.add(event.event)
                data = event.data.strip()
                # Some event data may be JSON, so try parse
                try:
                    import json
                    parsed_data = json.loads(data)
                except Exception:
                    parsed_data = None

                if event.event == "start":
                    # Start event: typically no exit_code or final status here
                    pass
                elif event.event == "log":
                    # Log event: data can be text lines, no exit_code expected
                    pass
                elif event.event == "end":
                    end_event_received = True
                    # End event should include exit_code and final status info in data
                    # Validate presence of exit_code and final status keys in JSON data
                    assert parsed_data is not None and isinstance(parsed_data, dict), "End event data must be JSON object"
                    assert "exit_code" in parsed_data, "End event missing exit_code"
                    assert "status" in parsed_data, "End event missing final status"
                    exit_code_found = True
                    final_status_found = True
                    break  # end event received, stop listening

                # Safety timeout to break if no end event after a while
                if time.time() - start_time > max_wait_seconds:
                    break

            assert "start" in event_types_received, "Did not receive 'start' event"
            assert "log" in event_types_received, "Did not receive any 'log' event"
            assert end_event_received, "Did not receive 'end' event"
            assert exit_code_found, "End event missing exit_code"
            assert final_status_found, "End event missing final status"

    except requests.exceptions.Timeout:
        raise AssertionError("Request timed out waiting for SSE events")
    except requests.exceptions.RequestException as e:
        raise AssertionError(f"Request failed: {e}")
    except Exception as ex:
        raise AssertionError(f"An error occurred during SSE stream processing: {ex}")


test_execute_single_scraper_with_sse_logs()