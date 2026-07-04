import requests

BASE_URL = "http://localhost:3005"
TIMEOUT = 30

def test_export_scraper_data_in_supported_formats():
    try:
        # Step 1: Get scrapers to find a valid scraper_id that supports preview/export
        resp = requests.get(f"{BASE_URL}/api/scrapers", timeout=TIMEOUT)
        assert resp.status_code == 200, f"Failed to get scrapers, status: {resp.status_code}"
        scrapers = resp.json()
        assert isinstance(scrapers, list) and len(scrapers) > 0, "Scrapers list is empty or invalid"

        # Choose a scraper that likely supports preview/export based on known limitations (avoid legacy scrapers)
        # From PRD legacy scrapers: "results", "wc2026", "elo" do NOT support preview/export
        unsupported_ids = {"results", "wc2026", "elo"}
        valid_scraper = next((s for s in scrapers if s["id"] not in unsupported_ids), None)
        assert valid_scraper is not None, "No suitable scraper found for export testing"
        scraper_id = valid_scraper["id"]

        # Step 2: Get preview data to use in export request
        preview_resp = requests.get(f"{BASE_URL}/api/preview/{scraper_id}", timeout=TIMEOUT)
        assert preview_resp.status_code == 200, f"Preview failed for scraper {scraper_id}"
        preview_data_json = preview_resp.json()
        # preview_data format: {columns, rows, total, warnings}
        # Use 'rows' as preview_data to export
        preview_rows = preview_data_json.get("rows")
        assert isinstance(preview_rows, list), "Preview rows invalid or missing"

        # Step 3: Test POST /api/export with supported formats and optional empty transforms and preview_data
        supported_formats = ["csv", "json", "xlsx"]
        for fmt in supported_formats:
            export_payload = {
                "scraper_id": scraper_id,
                "format": fmt,
                "transforms": [],
                "preview_data": preview_rows
            }
            export_resp = requests.post(f"{BASE_URL}/api/export", json=export_payload, timeout=TIMEOUT)
            assert export_resp.status_code == 200, f"Export failed for format {fmt} with status {export_resp.status_code}"
            
            content_type = export_resp.headers.get("Content-Type", "").lower()
            content_disposition = export_resp.headers.get("Content-Disposition", "").lower()
            # Validate content type and disposition for a file download (basic checking)
            assert content_disposition.startswith("attachment"), \
                f"Content-Disposition header missing or not attachment for format {fmt}"
            assert len(export_resp.content) > 0, f"Exported file is empty for format {fmt}"

    except (requests.RequestException, AssertionError) as e:
        raise AssertionError(f"Test failed: {e}")

test_export_scraper_data_in_supported_formats()