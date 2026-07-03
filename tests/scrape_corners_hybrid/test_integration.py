"""Integration test for the full hybrid corners scraper pipeline.

Mocks both Soccerway and FlashScore sources to verify end-to-end flow:
- Fixture fetching -> Soccerway extraction -> FlashScore fallback -> JSON output.
"""
import importlib, sys, pathlib, json, tempfile

def test_new_scraper_full_pipeline(monkeypatch):
    sys.path.append(str(pathlib.Path(__file__).parents[2]))
    mod = importlib.import_module("scrapycoco.scrape_corners_hybrid")

    # --- Mock Soccerway fixture fetching ---
    class DummyResponse:
        def __init__(self, text):
            self.text = text
        def raise_for_status(self):
            pass

    def mock_soccerway_calendar(url, timeout=15):
        # Return a calendar page with 2 match links
        return DummyResponse(
            '<a href="/match/argentina-mexico-2026/100001/">Match 1</a>'
            '<a href="/match/brazil-germany-2026/100002/">Match 2</a>'
        )

    # --- Mock Soccerway corner extraction ---
    def mock_extract_soccerway(url):
        # First match returns corners, second returns None (triggers fallback)
        if "100001" in url:
            return (6, 3)
        return None

    # --- Mock FlashScore corner extraction ---
    def mock_extract_flashscore(url):
        # Fallback returns corners for the second match
        if "100002" in url or "abc" in url:
            return (4, 2)
        return None

    monkeypatch.setattr(mod.requests, "get", mock_soccerway_calendar)
    monkeypatch.setattr(mod, "extract_corners_soccerway", mock_extract_soccerway)
    monkeypatch.setattr(mod, "extract_corners_flashscore", mock_extract_flashscore)

    # Monkeypatch sys.argv so argparse doesn't see pytest args
    monkeypatch.setattr("sys.argv", ["scrape_corners_hybrid.py"])

    # --- Run main with a temporary output file ---
    import tempfile
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
    tmp.close()
    temp_path = pathlib.Path(tmp.name)

    original_output = mod.OUTPUT_PATH
    mod.OUTPUT_PATH = temp_path

    # Call the real main function
    mod.main()

    mod.OUTPUT_PATH = original_output

    # --- Verify the output JSON ---
    with open(temp_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Clean up temp file
    temp_path.unlink(missing_ok=True)

    # Schema validation
    assert "matches" in data
    assert "last_updated" in data
    assert "teams_processed" in data
    assert "total_matches" in data

    matches = data["matches"]
    assert len(matches) == 2, f"Expected 2 matches, got {len(matches)}"

    # Verify first match (Soccerway)
    match1 = next(m for m in matches if m["id"] == "100001")
    assert match1["home_corners"] == 6
    assert match1["away_corners"] == 3
    assert match1["home_team"] == "argentina"
    assert match1["away_team"] == "mexico"
    assert "_fetched_at" in match1

    # Verify second match (FlashScore fallback)
    match2 = next(m for m in matches if m["id"] == "100002")
    assert match2["home_corners"] == 4
    assert match2["away_corners"] == 2
    assert match2["home_team"] == "brazil"
    assert match2["away_team"] == "germany"
    assert "_fetched_at" in match2

    # Teams processed should be 4
    assert data["teams_processed"] == 4


def test_new_scraper_update_mode(monkeypatch):
    """Verify --update mode skips already-processed fixtures."""
    sys.path.append(str(pathlib.Path(__file__).parents[2]))
    mod = importlib.import_module("scrapycoco.scrape_corners_hybrid")

    # Pre-populate with one match
    existing_data = {
        "matches": [{
            "id": "100001",
            "date": "2026-06-12",
            "home_team": "argentina",
            "away_team": "mexico",
            "home_corners": 5,
            "away_corners": 3,
            "competition": "WC2026",
            "type": "international",
        }],
        "last_updated": None,
        "teams_processed": 2,
        "total_matches": 1,
    }

    import tempfile
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
    tmp.write(json.dumps(existing_data).encode())
    tmp.close()
    temp_path = pathlib.Path(tmp.name)

    original_output = mod.OUTPUT_PATH
    mod.OUTPUT_PATH = temp_path

    # Mock sources with 2 fixtures, one already processed
    class DummyResponse:
        def __init__(self, text):
            self.text = text
        def raise_for_status(self):
            pass

    monkeypatch.setattr(mod.requests, "get", lambda url, timeout=15: DummyResponse(
        '<a href="/match/argentina-mexico-2026/100001/">M1</a>'
        '<a href="/match/brazil-germany-2026/100002/">M2</a>'
    ))
    monkeypatch.setattr(mod, "extract_corners_soccerway", lambda url: (4, 2) if "100002" in url else None)
    monkeypatch.setattr(mod, "extract_corners_flashscore", lambda url: None)

    # Monkeypatch argparse to simulate --update flag
    monkeypatch.setattr("sys.argv", ["scrape_corners_hybrid.py", "--update"])

    mod.main()

    mod.OUTPUT_PATH = original_output

    with open(temp_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    temp_path.unlink(missing_ok=True)

    # Only the new fixture should be added
    assert data["total_matches"] == 2
    ids = {m["id"] for m in data["matches"]}
    assert ids == {"100001", "100002"}