import requests

BASE_URL = "http://localhost:3005"
TIMEOUT = 30

def test_handle_scraper_not_found_on_execution():
    invalid_scraper_id = "nonexistent_scraper_12345"
    url = f"{BASE_URL}/api/run/{invalid_scraper_id}"
    try:
        response = requests.get(url, timeout=TIMEOUT, stream=True)
    except requests.RequestException as e:
        assert False, f"Request failed with exception: {e}"

    assert response.status_code == 404, f"Expected status code 404, got {response.status_code}"

    content_type = response.headers.get('Content-Type', '')
    # Assert that response is not an SSE stream
    assert 'text/event-stream' not in content_type, "SSE stream opened unexpectedly on 404 response"

    # It is allowed for the 404 response to have some body content describing the error

test_handle_scraper_not_found_on_execution()