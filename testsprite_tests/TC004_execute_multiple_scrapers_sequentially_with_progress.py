import requests
import json

def test_execute_multiple_scrapers_sequentially_with_progress():
    base_url = "http://localhost:3005"
    url = f"{base_url}/api/batch/run"
    headers = {
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
    }
    payload = {
        "scraper_ids": ["xg", "cards"],
        "sandbox": True
    }

    try:
        with requests.post(url, headers=headers, data=json.dumps(payload), stream=True, timeout=30) as response:
            assert response.status_code == 200, f"Expected status 200 but got {response.status_code}"
            batch_start_received = False
            progress_events_received = set()
            end_event_received = False

            for line in response.iter_lines(decode_unicode=True):
                if line is None or line.strip() == "":
                    continue
                # SSE events come in "event: <eventname>" and "data: <payload>" lines, so parse accordingly
                # We'll collect lines until an empty line indicates event end.
                # But the response.iter_lines yields line by line including empty lines
                # We'll parse simple events for batch-start, progress, and end

                # Basic parsing of SSE lines:
                # Example:
                # event: batch-start
                # data: {...}
                # 
                # event: progress
                # data: {...}
                # 
                # event: end
                # data: {...}

                # We'll collect event type and data till empty line

                # To do that, we buffer lines until empty line
                # But since this is in for loop line by line, let's do a small inner buffer to gather event and data:

                # We implement a function to parse SSE with above logic outside loop.
                pass

    except requests.exceptions.RequestException as e:
        assert False, f"Request failed: {e}"

# Because we need to parse the SSE stream properly, let's refactor the function to do so:

import requests
import json

def test_execute_multiple_scrapers_sequentially_with_progress():
    base_url = "http://localhost:3005"
    url = f"{base_url}/api/batch/run"
    headers = {
        "Content-Type": "application/json",
        "Accept": "text/event-stream",
    }
    payload = {
        "scraper_ids": ["xg", "cards"],
        "sandbox": True
    }

    try:
        with requests.post(url, headers=headers, data=json.dumps(payload), stream=True, timeout=30) as response:
            assert response.status_code == 200, f"Expected status 200 but got {response.status_code}"

            def sse_events(response_iter):
                event = None
                data_lines = []
                for line in response_iter:
                    if line is None:
                        continue
                    line = line.strip()
                    if line == "":
                        # end of event block
                        if event is not None:
                            yield event, "\n".join(data_lines)
                        event = None
                        data_lines = []
                    elif line.startswith("event:"):
                        event = line[len("event:"):].strip()
                    elif line.startswith("data:"):
                        data_lines.append(line[len("data:"):].strip())
                # Final event if no trailing newline
                if event is not None:
                    yield event, "\n".join(data_lines)

            batch_start_received = False
            progress_events_received = set()
            end_event_received = False

            expected_scrapers = payload["scraper_ids"]

            for event, data in sse_events(response.iter_lines(decode_unicode=True)):
                if event == "batch-start":
                    batch_start_received = True
                    # data might contain batch info; parse JSON if possible
                    try:
                        batch_info = json.loads(data) if data else None
                    except Exception:
                        batch_info = None
                    # We accept batch_start event presence enough here
                elif event == "progress":
                    # progress events should indicate the current scraper id running
                    try:
                        progress_info = json.loads(data) if data else {}
                        scraper_id = progress_info.get("scraper_id")
                        assert scraper_id in expected_scrapers, f"Progress event with unknown scraper_id {scraper_id}"
                        progress_events_received.add(scraper_id)
                    except Exception as e:
                        assert False, f"Invalid progress event data: {data} - Exception: {e}"
                elif event == "end":
                    # final end event signals end of batch run
                    end_event_received = True
                    # data may contain final status info
                else:
                    # Other events (log, error) can be ignored for this test
                    pass

            assert batch_start_received, "Did not receive batch-start event"
            assert end_event_received, "Did not receive final end event"
            # All scraper IDs in the payload should have a progress event reported
            assert progress_events_received == set(expected_scrapers), (
                f"Did not receive progress events for all scrapers. Received: {progress_events_received}, Expected: {expected_scrapers}"
            )

    except requests.exceptions.RequestException as e:
        assert False, f"Request failed: {e}"

test_execute_multiple_scrapers_sequentially_with_progress()