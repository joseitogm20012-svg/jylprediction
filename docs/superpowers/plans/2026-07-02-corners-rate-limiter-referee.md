# Corners, Rate Limiter & Referee Stats — Implementation Plan

> **For agentic workers:** Use subagent-driven-development or executing-plans to implement task-by-task.

**Goal:** Integrate real corner stats, add domain-based rate limiter for scrapers, and add referee intensity slider.

**Architecture:** Three independent tasks: (1) modify predictor.py to load `corners_stats.json` and use it with capped opponent adjustment, (2) create `scrapycoco/rate_limiter.py` with per-domain async rate limiter, (3) add `refereeIntensity` param through the full stack (main.py → predictor.py → index.html → app.js).

**Tech Stack:** Python 3.12+, FastAPI, asyncio, Playwright, NumPy

## Global Constraints

- No new dependencies
- `corners_stats.json` path: `project_root/data/corners_stats.json` (keyed by team slug)
- Team slugs are identical between frontend, predictor, and corners JSON (no mapping needed)
- Rate limiter uses `asyncio.sleep` (no threading)
- `refereeIntensity` defaults to 1.0 (no change in behavior when absent)

---

### Task 1: Rate Limiter por Dominio

**Files:**
- Create: `scrapycoco/rate_limiter.py`
- Modify: `scrapycoco/scrape_injuries_v5.py`

**Interfaces:**
- Produces: `RateLimiter` class with `set_delay(domain, seconds)` and `async wait(domain)`

- [ ] **Step 1: Create rate_limiter.py**

```python
"""Per-domain async rate limiter for Playwright scrapers."""
import asyncio
import time


class RateLimiter:
    def __init__(self, defaults: dict = None):
        self._last_hit: dict[str, float] = {}
        self._delays: dict[str, float] = defaults or {}

    def set_delay(self, domain: str, seconds: float):
        self._delays[domain] = seconds

    async def wait(self, domain: str):
        now = time.time()
        last = self._last_hit.get(domain, 0.0)
        elapsed = now - last
        needed = self._delays.get(domain, 1.0)
        if elapsed < needed:
            await asyncio.sleep(needed - elapsed)
        self._last_hit[domain] = time.time()
```

- [ ] **Step 2: Create test**

`scrapycoco/test_rate_limiter.py`:

```python
import asyncio, time
from rate_limiter import RateLimiter

async def test():
    rl = RateLimiter({"slow.com": 3.0, "fast.com": 0.5})
    t0 = time.time()
    await rl.wait("slow.com")
    t1 = time.time()
    assert t1 - t0 < 0.1, "first call should not wait"
    await rl.wait("slow.com")
    t2 = time.time()
    assert t2 - t1 >= 2.9, "second call should wait ~3s"
    t3 = time.time()
    await rl.wait("fast.com")
    t4 = time.time()
    assert t4 - t3 < 0.1, "different domain should not wait"
    print("ALL PASS")

asyncio.run(test())
```

Run: `python scrapycoco/test_rate_limiter.py`

- [ ] **Step 3: Integrate into scrape_injuries_v5.py**

Add import:
```python
from rate_limiter import RateLimiter
_limiter = RateLimiter({"transfermarkt.com": 2.5})
```

In `scrape_squad_page`, before each `page.goto(...)`, add:
```python
await _limiter.wait("transfermarkt.com")
```

In `scrape_staff_page`, same. Remove all standalone `await asyncio.sleep(2-3)` calls immediately after goto.

- [ ] **Step 4: Run test**

Run: `python scrapycoco/test_rate_limiter.py`

Expected: `ALL PASS`

- [ ] **Step 5: Commit**

```bash
git add scrapycoco/rate_limiter.py scrapycoco/test_rate_limiter.py scrapycoco/scrape_injuries_v5.py
git commit -m "feat: add per-domain rate limiter for scrapers"
```

---

### Task 2: Integrar corners_stats.json al predictor

**Files:**
- Modify: `backend/predictor.py`

**Interfaces:**
- Consumes: `run_prediction_sim()` signature unchanged
- Produces: `load_corners_data()` module-level function

- [ ] **Step 1: Add corner stats loading function**

Add near the top of `predictor.py`, after `_cached_goalscorers`:

```python
_cached_corners = None

def load_corners_data():
    global _cached_corners
    if _cached_corners is not None:
        return _cached_corners
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "corners_stats.json")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                _cached_corners = json.load(f)
        except Exception:
            _cached_corners = {}
    else:
        _cached_corners = {}
    return _cached_corners
```

- [ ] **Step 2: Replace the corners lambda calculation**

In `run_prediction_sim`, locate the block starting at line ~1395:
```python
    # Expected corners lambda using corners_for_per_90 if available (Fase 1)
    corners_for_a = entry_a.get("corners_for_per_90")
    ...
    lambda_corners_b = max(1.5, min(9.5, expected_corners_base_b * concession_a))
```

Replace the entire block with:

```python
    # Expected corners base from real stats (corners_stats.json) or fallback
    corners_data = load_corners_data()
    real_a = corners_data.get(team_a, {})
    real_b = corners_data.get(team_b, {})

    if real_a.get("corners_for") and real_a["corners_for"] > 0:
        expected_corners_base_a = real_a["corners_for"]
    elif corners_for_a is not None and corners_for_a > 0:
        expected_corners_base_a = corners_for_a
    else:
        expected_corners_base_a = 5.0 * cam_a

    if real_b.get("corners_for") and real_b["corners_for"] > 0:
        expected_corners_base_b = real_b["corners_for"]
    elif corners_for_b is not None and corners_for_b > 0:
        expected_corners_base_b = corners_for_b
    else:
        expected_corners_base_b = 4.0 * cam_b

    # Capped opponent adjustment: max +/- 15%
    concession_a_capped = max(0.85, min(1.15, concession_a))
    concession_b_capped = max(0.85, min(1.15, concession_b))

    lambda_corners_a = max(1.5, min(9.5, expected_corners_base_a * concession_b_capped))
    lambda_corners_b = max(1.5, min(9.5, expected_corners_base_b * concession_a_capped))
```

- [ ] **Step 3: Start server and test prediction**

```bash
python backend/main.py
```

In another terminal:
```bash
curl -s -X POST http://localhost:3000/api/predict -H "Content-Type: application/json" -d '{"teamA":"argentina","teamB":"france","rankA":1,"rankB":3,"fifaWeight":0.3,"h2hWeight":0.2,"decayMonths":12,"numSims":10000}' | python -m json.tool | grep -A5 cornersPrediction
```

Expected: corners values between 1.5 and 9.5 with reasonable difference (not wild swings).

- [ ] **Step 4: Commit**

```bash
git add backend/predictor.py
git commit -m "feat: integrate real corner stats from corners_stats.json with capped opponent adjustment"
```

---

### Task 3: Referee Stats (simplificado)

**Files:**
- Modify: `backend/main.py`
- Modify: `backend/predictor.py`
- Modify: `frontend/index.html`
- Modify: `frontend/index.css`
- Modify: `frontend/app.js`

**Interfaces:**
- Produces: `refereeIntensity: Optional[float] = 1.0` on PredictionRequest
- Produces: `referee_intensity` parameter on `run_prediction_sim()`

- [ ] **Step 1: Add refereeIntensity to PredictionRequest**

In `backend/main.py`, add to the `PredictionRequest` class (after `hostCountry`):

```python
    refereeIntensity: Optional[float] = 1.0
```

And pass it to `run_prediction_sim`:

```python
            referee_intensity=req.refereeIntensity if req.refereeIntensity is not None else 1.0,
```

- [ ] **Step 2: Add referee_intensity parameter to run_prediction_sim**

In `predictor.py`, change the function signature (line 1146):

```python
def run_prediction_sim(team_a, team_b, rank_a, rank_b, fifa_weight_pct, h2h_weight_pct, half_life_months, num_sims, odds_a=None, odds_draw=None, odds_b=None, strength_override_a=1.0, strength_override_b=1.0, altitude=0, host_country=None, return_raw=False, referee_intensity=1.0):
```

- [ ] **Step 3: Apply multiplier to cards**

After line 1714, before the cards_markets is returned, insert:

```python
    cards_a *= referee_intensity
    cards_b *= referee_intensity
    total_cards = cards_a + cards_b
```

- [ ] **Step 4: Add slider to frontend**

In `frontend/index.html`, locate the parameter panel (around the altitude and host country inputs). Add after the host country input:

```html
          <div class="param-field">
            <label for="input-referee-intensity">
              <span class="param-label">Intensidad del Árbitro</span>
              <span class="param-value" id="referee-intensity-value">1.00x</span>
            </label>
            <div class="range-wrapper">
              <span class="range-label">Permisivo</span>
              <input type="range" id="input-referee-intensity" min="0.5" max="1.5" step="0.1" value="1.0">
              <span class="range-label">Estricto</span>
            </div>
          </div>
```

In `frontend/index.css`, add before `/* Odds inputs grid */`:

```css
/* Referee intensity label */
#referee-intensity-value {
  font-weight: 700;
  color: var(--color-accent);
}
```

- [ ] **Step 5: Wire up JavaScript**

In `frontend/app.js`:

A) At the top, add the DOM element reference:

```javascript
const inputRefereeIntensity = document.getElementById("input-referee-intensity");
const refereeIntensityValue = document.getElementById("referee-intensity-value");
```

B) In the predict payload (around line 2180), add:

```javascript
    refereeIntensity: inputRefereeIntensity ? parseFloat(inputRefereeIntensity.value) : 1.0,
```

C) Add a change listener (near other slider listeners):

```javascript
if (inputRefereeIntensity) {
  inputRefereeIntensity.addEventListener("input", function() {
    if (refereeIntensityValue) {
      refereeIntensityValue.textContent = parseFloat(this.value).toFixed(2) + "x";
    }
  });
}
```

- [ ] **Step 6: Start server and test**

```bash
python backend/main.py
```

Open `http://localhost:3000`, select two teams, adjust the referee intensity slider, click Simular, check if cards markets change accordingly.

- [ ] **Step 7: Commit**

```bash
git add backend/main.py backend/predictor.py frontend/index.html frontend/index.css frontend/app.js
git commit -m "feat: add referee intensity slider with multiplier for cards market"
```
