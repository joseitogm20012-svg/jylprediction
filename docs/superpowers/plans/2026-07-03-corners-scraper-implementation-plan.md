# Corners Scraper Implementation Plan

> **For agentic workers:** REQUIRED SUB‑SKILL: Use `superpowers:subagent-driven-development` (recommended) or `superpowers:executing-plans` to implement this plan task‑by‑task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a hybrid scraper that collects corner‑kick statistics for all 2026 World Cup matches (including qualifiers) using Soccerway as the primary source and FlashScore via Playwright as a fallback, storing results in `data/per_match_corners.json`.

**Architecture:** A new script `scrapycoco/scrape_corners_hybrid.py`
- Loads existing JSON (or creates a fresh structure).
- Retrieves a list of fixtures for 2026 from Soccerway (HTML calendar) and extracts match URLs.
- For each fixture:
  1. Tries to scrape corners from Soccerway (fast HTTP + BeautifulSoup).
  2. If Soccerway lacks the data, falls back to Playwright‑FlashScore to render the statistics tab and extract corners.
- Normalizes team names to slugs (same algorithm used elsewhere).
- Respects a per‑domain rate limit (1 req / s) via the shared `RateLimiter`.
- Logs progress and errors to `logs/corners_scraper.log`.
- Writes the unified JSON file (`data/per_match_corners.json`) in the format already consumed by `backend/predictor.py`.

**Tech Stack:** Python 3.12, `requests`, `beautifulsoup4`, `playwright` (headless Chromium), standard library (`json`, `datetime`, `pathlib`), existing `scrapycoco/rate_limiter.py`.

**Global Constraints:**
- Must respect a 1 req / second limit per domain (`soccerway.com`, `flashscore.com`).
- No new external dependencies beyond what is already in the repo (`playwright`).
- Output file path exactly `data/per_match_corners.json`.
- Maintain backward compatibility with `load_per_match_corners()` in `backend/predictor.py`.

---

## Task 1: Create script skeleton
**Files:**
- Create: `scrapycoco/scrape_corners_hybrid.py`

**Step 1:** Write failing test.
```python
def test_script_exists():
    import importlib, sys, pathlib
    sys.path.append('scrapycoco')
    mod = importlib.import_module('scrape_corners_hybrid')
    assert hasattr(mod, 'main')
```
**Step 2:** Run test – it will fail because the module does not exist.
**Step 3:** Create the file with a minimal `main` placeholder and the required imports (`argparse`, `json`, `pathlib`, `datetime`).
```python
"""Hybrid corners scraper – Soccerway primary, FlashScore fallback."""
import argparse, json, time
from pathlib import Path
from datetime import datetime

def main():
    print("scrape_corners_hybrid placeholder")

if __name__ == "__main__":
    main()
```
**Step 4:** Run test – it should now pass.
**Step 5:** Commit.

- [ ] Write the failing test (`tests/scrape_corners_hybrid/test_import.py`).
- [ ] Run test to confirm failure.
- [ ] Add skeleton script.
- [ ] Run test to confirm pass.
- [ ] Commit.

---

## Task 2: Implement utility helpers (slugify, load/save)
**Files:**
- Modify: `scrapycoco/scrape_corners_hybrid.py`

**Step 1:** Write tests for `slugify` and JSON load/save.
```python
from scrape_corners_hybrid import slugify, load_existing, save_data

def test_slugify():
    assert slugify("United States") == "united-states"
    assert slugify("Côte d'Ivoire") == "côte-divoire"

def test_load_save(tmp_path):
    # Write a temporary JSON file
    path = tmp_path / "per_match_corners.json"
    data = {"matches": [], "last_updated": None, "teams_processed": 0, "total_matches": 0}
    path.write_text(json.dumps(data))
    # Monkey‑patch OUTPUT_PATH inside the module
    import importlib
    import scrape_corners_hybrid as mod
    mod.OUTPUT_PATH = path
    loaded = mod.load_existing()
    assert loaded == data
    # Modify and save
    loaded["matches"].append({"id": "1"})
    mod.save_data(loaded)
    reloaded = json.loads(path.read_text())
    assert reloaded["matches"][0]["id"] == "1"
```
**Step 2:** Run test → failure (helpers missing).
**Step 3:** Implement `slugify(name)`, `load_existing()`, `save_data(data)` using `Path` and `json`.
**Step 4:** Run test → pass.
**Step 5:** Commit.

---

## Task 3: Soccerway fixture list & corner extraction
**Files:**
- Modify: `scrapycoco/scrape_corners_hybrid.py`

**Step 1:** Write tests for fixture URL parsing and corner extraction.
```python
from scrape_corners_hybrid import fetch_soccerway_fixtures, extract_corners_soccerway

def test_fetch_fixtures(monkeypatch, requests_mock):
    html = """<a href=\"/match/argentina-mexico-2026/1234567/\">Match</a>"""
    requests_mock.get('https://int.soccerway.com/matches/2026/', text=html)
    fixtures = fetch_soccerway_fixtures()
    assert fixtures == [{"url": "https://int.soccerway.com/match/argentina-mexico-2026/1234567/", "id": "1234567"}]

def test_extract_corners_soccerway(monkeypatch, requests_mock):
    html = """<table><tr><td>Corners</td><td>5</td><td>3</td></tr></table>"""
    requests_mock.get('https://int.soccerway.com/match/argentina-mexico-2026/1234567/', text=html)
    corners = extract_corners_soccerway('https://int.soccerway.com/match/argentina-mexico-2026/1234567/')
    assert corners == (5, 3)
```
**Step 2:** Run test – failure (functions missing).
**Step 3:** Implement:
- `fetch_soccerway_fixtures()` → HTTP GET calendar page (`https://int.soccerway.com/matches/2026/`), use BeautifulSoup to find `<a>` tags containing `/match/` and extract the numeric ID from the URL.
- `extract_corners_soccerway(url)` → HTTP GET match page, parse with BeautifulSoup, locate row where first `<td>` text (strip) equals "Corners" (case‑insensitive), then read the next two `<td>` values as ints.
- Use `_limiter.wait('soccerway.com')` before each request.
**Step 4:** Run test – pass.
**Step 5:** Commit.

---

## Task 4: FlashScore fallback via Playwright
**Files:**
- Modify: `scrapycoco/scrape_corners_hybrid.py`

**Step 1:** Write a test that uses Playwright’s sync API with a mocked page object.
```python
from scrape_corners_hybrid import extract_corners_flashscore

class DummyPage:
    async def goto(self, url, **kwargs):
        pass
    async def content(self):
        return """<table><tr><td>Corners</td><td>4</td><td>2</td></tr></table>"""
    async def query_selector(self, selector):
        return None

def test_extract_corners_flashscore(monkeypatch):
    # Patch async_playwright to return a dummy context/page
    async def mock_playwright():
        class DummyBrowser:
            async def new_page(self):
                return DummyPage()
            async def close(self):
                pass
        class DummyPlaywright:
            async def __aenter__(self):
                return self
            async def __aexit__(self, *exc):
                pass
            async def launch(self, **kw):
                return DummyBrowser()
        return DummyPlaywright()
    monkeypatch.setattr('scrapycoco.scrape_corners_hybrid.async_playwright', mock_playwright)
    corners = extract_corners_flashscore('https://www.flashscore.com/match/abc/')
    assert corners == (4, 2)
```
**Step 2:** Run test – failure (function missing).
**Step 3:** Implement `extract_corners_flashscore(url)`:
- Use `async_playwright` to launch headless Chromium.
- Open page, accept cookie banner (`#onetrust-accept-btn-handler`).
- Click the “Statistics” tab (search for a link containing "statistics" or a button). If not found, fallback to parsing the initial HTML.
- Wait for network idle, get page content, parse with BeautifulSoup, locate the row where first cell contains "Corners" (case‑insensitive) and read the two numeric cells.
- Apply `_limiter.wait('flashscore.com')` before navigation.
- Return a tuple `(home_corners, away_corners)`.
**Step 4:** Run test – pass.
**Step 5:** Commit.

---

## Task 5: Main driver logic & CLI
**Files:**
- Modify: `scrapycoco/scrape_corners_hybrid.py`

**Step 1:** Write integration‑style test that patches both Soccerway and FlashScore functions.
```python
from scrape_corners_hybrid import main

def test_main_flow(monkeypatch, capsys):
    # Mock fixture list to contain two matches
    fixtures = [
        {"id": "1", "home": "Argentina", "away": "Mexico", "date": "2026-06-12", "url": "soccerway://1"},
        {"id": "2", "home": "Brazil", "away": "Germany", "date": "2026-06-15", "url": "soccerway://2"},
    ]
    monkeypatch.setattr('scrapycoco.scrape_corners_hybrid.fetch_soccerway_fixtures', lambda: fixtures)
    # Soccerway works for first match, fails for second
    monkeypatch.setattr('scrapycoco.scrape_corners_hybrid.extract_corners_soccerway', lambda url: (5, 3) if "1" in url else None)
    # FlashScore fallback returns data for second match
    monkeypatch.setattr('scrapycoco.scrape_corners_hybrid.extract_corners_flashscore', lambda url: (4, 2))
    # Point OUTPUT_PATH to a temporary file
    import pathlib, json, tempfile
    tmp = tempfile.NamedTemporaryFile(delete=False)
    monkeypatch.setattr('scrapycoco.scrape_corners_hybrid.OUTPUT_PATH', Path(tmp.name))
    # Run main with --update flag
    main(update=True)
    # Verify the JSON file contains two entries with correct corners
    data = json.loads(Path(tmp.name).read_text())
    assert len(data["matches"]) == 2
    ids = {m["id"] for m in data["matches"]}
    assert ids == {"1", "2"}
    # Check values
    for m in data["matches"]:
        if m["id"] == "1":
            assert m["home_corners"] == 5 and m["away_corners"] == 3
        else:
            assert m["home_corners"] == 4 and m["away_corners"] == 2
```
**Step 2:** Run test – failure (main logic missing).
**Step 3:** Implement `main(update: bool = False)`:
- Load existing JSON via `load_existing()`.
- Build a set of processed IDs if `update`.
- Call `fetch_soccerway_fixtures()` to obtain a list of fixture dicts (`id`, `home`, `away`, `date`).
- For each fixture not in processed set:
  1. Attempt `extract_corners_soccerway(fixture_url)`.
  2. If result is `None` or missing, call `extract_corners_flashscore(fixture_url)`.
  3. If still `None`, log warning and skip.
  4. Build a result dict matching the schema, add `_fetched_at` timestamp.
- Append all new matches to the existing structure, recompute `teams_processed` (unique slugs across matches), and `save_data()`.
- Print a summary of how many new matches were added.
**Step 4:** Run test – pass.
**Step 5:** Commit.

---

## Task 6: Logging
**Files:**
- Modify: `scrapycoco/scrape_corners_hybrid.py`

**Step 1:** Add a simple logger that appends lines to `logs/corners_scraper.log` (create `logs/` if missing). Each line: `[TIMESTAMP] ID SOURCE STATUS` where SOURCE is `soccerway` or `flashscore` and STATUS is `OK` or `SKIP`.
**Step 2:** Write a test that runs `main` and asserts the log file exists and contains at least one line.
**Step 3:** Run test – pass.
**Step 4:** Commit.

---

## Task 7: Update batch file
**Files:**
- Modify: `update_corners.bat`

**Step 1:** Write a test (shell script execution is not unit‑tested; we’ll just verify the file contains the new command).
**Step 2:** Replace line `python scrapycoco\scrape_corners_per_match.py --update` with `python scrapycoco\scrape_corners_hybrid.py --update`.
**Step 3:** Commit.

---

## Task 8: Documentation & README update
**Files:**
- Modify: `README.md` (if present) or create a brief section in `docs/superpowers/plans/2026-07-03-corners-scraper-implementation-plan.md` describing how to run the scraper (`update_corners.bat`).
**Step 1:** Add a Markdown block:
```
## Updating corner statistics
Run the batch script:
```
update_corners.bat
```
which will execute the hybrid scraper and refresh `data/per_match_corners.json`.
**Step 2:** Commit.

---

## Task 9: Final verification
**Step 1:** Run the full test suite (`pytest -q`). Ensure all new tests pass and existing tests remain green.
**Step 2:** Manually execute `python scrapycoco/scrape_corners_hybrid.py --update` (on a small subset of fixtures – you can add a `--dry-run` flag for quick sanity, but not required for production).
**Step 3:** Verify `data/per_match_corners.json` now contains entries.
**Step 4:** Commit final changes.

---

## Execution Choice
After the plan is saved, you can choose how to run it:
1. **Sub‑agent‑driven (recommended)** – a fresh sub‑agent will be launched for each task, you’ll get incremental reviews, and the work proceeds safely.
2. **Inline execution** – I will run the tasks sequentially in this session using the `executing‑plans` skill.

Which execution method do you prefer?