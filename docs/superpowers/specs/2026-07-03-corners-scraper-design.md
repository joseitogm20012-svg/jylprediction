# Design – Corners Scraper (Hybrid: Soccerway + FlashScore)

**Date:** 2026‑07‑03
**Author:** OpenCode

---

## 1. Goal
Create an automated pipeline that gathers **corner‑kick statistics** for every World Cup 2026 match (including qualifiers) and stores them in `data/per_match_corners.json` using a **hybrid approach**:

1. **Primary source – Soccerway** (fast HTTP + BeautifulSoup). 
2. **Fallback source – FlashScore** (Playwright headless browser). 

The pipeline must be callable from `update_corners.bat --update` and respect rate limits for each domain.

---

## 2. Data Model (output file)
```json
{
  "matches": [
    {
      "id": "123456",
      "date": "2026-06-12",
      "home_team": "argentina",
      "away_team": "mexico",
      "home_corners": 5,
      "away_corners": 3,
      "competition": "WC2026 Qualifiers",
      "type": "international",
      "_fetched_at": "2026-07-03T14:22:31.123456"
    }
    // ... more matches
  ],
  "last_updated": "2026-07-03T14:22:31.123456",
  "teams_processed": 68,
  "total_matches": 342
}
```
The schema matches the existing `scrape_corners_per_match.py` format so the predictor can consume it without changes.

---

## 3. Architecture Overview
```
┌─────────────────────┐   ┌─────────────────────┐
│   Existing Repo     │   │   New Scraper       │
│   update_corners.bat│──▶│   scrape_corners_hybrid.py
│                     │   │                     │
└─────────────────────┘   └─────────────────────┘
        │                         │
        ▼                         ▼
  data/per_match_corners.json   └─► predictor (load_per_match_corners())
```
* `scrape_corners_hybrid.py` implements the pipeline described below.
* It imports the shared `RateLimiter` from `scrapycoco/rate_limiter.py`.
* All logging is printed to stdout; errors are appended to `logs/corners_scraper.log`.

---

## 4. Pipeline Steps
1. **Load existing JSON** (`load_existing`). If `--update` is passed, keep a set of processed fixture IDs to skip.
2. **Obtain fixture list**
   - **Soccerway**: request the public calendar page for 2026. Parse each match link to extract:
     - fixture URL (contains a numeric ID we keep as our internal `id`).
     - home/away team names.
     - date.
   - For any match not found on Soccerway (or where the statistics table lacks a *Corners* row), collect its URL for the FlashScore fallback.
3. **Process each fixture**
   - **Soccerway path**: `requests.get` → `BeautifulSoup` → locate the `<table>` with a row where the first cell contains "Corners". Extract both columns as integers.
   - **FlashScore fallback**: launch Playwright (`async_playwright`).
     - Open the match URL (`https://www.flashscore.com/match/<id>/`).
     - Accept the cookie banner (if present). 
     - Click the "Statistics" tab (by searching for a link containing "statistics").
     - Wait for network idle, then parse the rendered DOM for a row with text "Corners" and read the two cells.
   - **Normalization** – `slugify` team names (`lower`, replace spaces with hyphens, strip punctuation) to match the predictor's slugs.
   - Append a dict (as per the data model) to a list `new_matches`.
4. **Rate limiting** – before every HTTP request (`requests.get`) and before each Playwright navigation, invoke `RateLimiter.wait("soccerway.com")` or `RateLimiter.wait("flashscore.com")` respectively (default delay 1 s).
5. **Persist** – merge `new_matches` into the loaded JSON, recompute `teams_processed` (unique slugs), update `last_updated`, write back to `data/per_match_corners.json`.
6. **Logging** – write a line to `logs/corners_scraper.log` for each processed fixture (success/failure, source used).

---

## 5. Error handling & retries
* Each HTTP call has up to **3 retries** with exponential back‑off (1 s → 2 s → 4 s).
* Playwright navigation also retries on timeout (max 2 attempts).
* If a fixture still lacks corner data after both sources, it is **skipped** and logged as a warning.
* The script never raises an uncaught exception – it always completes and reports a summary.

---

## 6. Rate Limiter (shared)
The existing `scrapycoco/rate_limiter.py` provides:
```python
_limiter = RateLimiter({"soccerway.com": 1.0, "flashscore.com": 1.0})
```
`_limiter.wait(domain)` blocks until at least one second has elapsed since the previous request to that domain.

---

## 7. Integration with the predictor
`backend/predictor.py` already contains:
```python
PER_MATCH_CORNERS_PATH = os.path.join(PROJECT_DIR, "data", "per_match_corners.json")
```
and `load_per_match_corners()` loads the file at runtime. Once the scraper populates the JSON, the predictor will automatically start using the **rolling corner averages** for its corner‑kick market predictions (no code changes required).

---

## 8. Execution flow (via batch file)
1. User runs `update_corners.bat`.
2. The batch file activates the virtual env and executes:
   ```
   python scrapycoco\scrape_corners_hybrid.py --update
   ```
3. The script prints progress to the console; on success it displays:
   `✅ Guardados X partidos en data/per_match_corners.json`.
4. The predictor cache is cleared automatically on server restart (as per existing workflow).

---

## 9. Future extensibility
* **Additional sources** – adding a new parser only requires a function that returns `(home_corners, away_corners)` for a given fixture ID and plugging it into the fallback chain.
* **Parallelism** – the current implementation runs fixtures sequentially to keep the rate‑limit logic simple. If performance becomes a bottleneck, we can parallelise the Soccerway HTTP fetches using `concurrent.futures` while preserving per‑domain throttling.

---

**Next step**: review this design doc. If you need any changes, let me know. Once approved I will generate an implementation plan (writing‑plans) and then proceed with the code.
