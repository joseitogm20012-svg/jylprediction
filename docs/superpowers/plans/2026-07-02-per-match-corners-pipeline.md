# Per-Match Corner Data Pipeline Implementation Plan

**Goal:** Build a pipeline for per-match corner data with rolling weighted averages and home/away split, integrated into the predictor for betting-grade accuracy.

**Architecture:** Scraper → `data/per_match_corners.json` → predictor rolling blend → Poisson simulation. Currently all public APIs (SofaScore, FBref, FlashScore) return 403; the framework is ready for when a data source becomes available.

**Tech Stack:** Python, NumPy, requests, BeautifulSoup (cache), Playwright (future)

## Global Constraints
- No new dependencies beyond what already exists
- Backward compatible: all existing predictions unchanged when per_match_corners.json is empty
- Home/away factors: 1.10 home, 0.90 away (empirical ~58/42 split)

---

### Task 1: SofaScore Team ID Mapping

**Files:**
- Create: `data/sofascore_team_ids.json`
- Create: `scrapycoco/map_sofascore_ids.py`

**Result:** 19 known IDs from existing codebase; 30 teams unmapped (SofaScore API blocked). File serves as ready mapping when API becomes accessible.

### Task 2: Per-Match Corner Data Framework

**Files:**
- Create: `data/per_match_corners.json` (empty skeleton with documented structure)
- Create: `scrapycoco/scrape_corners_per_match.py` (scraper framework with both SofaScore and FlashScore placeholders)

**Result:** Infrastructure ready. When a data source becomes available, `scrape_corners_per_match.py --update` populates the file.

### Task 3: Rolling Average + Home/Away Integration in Predictor

**Files:**
- Modify: `backend/predictor.py`
  - Line 25: Add `PER_MATCH_CORNERS_PATH` constant
  - Lines 100-151: Add `load_per_match_corners()`, `compute_rolling_corner_avg()`, `HOME_CORNER_FACTOR`, `AWAY_CORNER_FACTOR`
  - Lines 1487-1521: Blend rolling averages with base data + apply venue factor

**Test:** `compute_rolling_corner_avg('argentina', mock_data)` returns weighted average; `load_per_match_corners()` returns None when file empty

### Task 4: Maintenance Script

**Files:**
- Create: `update_corners.bat`

**Usage:** Runs `scrape_corners_per_match.py --update`, activates venv.
