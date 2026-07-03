"""Hybrid corners scraper – Soccerway primary, FlashScore fallback.

Provides a CLI entry point `main` that can be invoked as
`python scrapycoco/scrape_corners_hybrid.py --update`.
"""
import argparse, json, time, sys
from pathlib import Path
from datetime import datetime
import requests
from bs4 import BeautifulSoup

# Project root and output file
BASE_DIR = Path(__file__).parent.parent
OUTPUT_PATH = BASE_DIR / "data" / "per_match_corners.json"

# Rate limiter – use shared implementation if available
try:
    from scrapycoco.rate_limiter import RateLimiter
    _limiter = RateLimiter({"soccerway.com": 1.0, "flashscore.com": 1.0})
except Exception:
    # Fallback – simple sleep based limiter
    class _DummyLimiter:
        def wait(self, domain: str):
            time.sleep(1.0)
    _limiter = _DummyLimiter()

# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------

def slugify(name: str) -> str:
    """Normalize a team name into the slug used throughout the project.
    Lower‑case, spaces become hyphens, periods and apostrophes are removed.
    """
    return name.lower().replace(" ", "-").replace(".", "").replace("'", "")


def load_existing():
    """Load the existing per‑match corners JSON if present.
    Returns a dict with keys: matches (list), last_updated, teams_processed,
    total_matches. If the file does not exist or is malformed, returns the
    default empty structure.
    """
    if OUTPUT_PATH.is_file():
        try:
            with open(OUTPUT_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"matches": [], "last_updated": None, "teams_processed": 0, "total_matches": 0}


def save_data(data):
    """Persist `data` to ``OUTPUT_PATH``.
    Adds/updates the ``last_updated`` timestamp and ``total_matches`` count.
    """
    data["last_updated"] = datetime.now().isoformat()
    data["total_matches"] = len(data.get("matches", []))
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✅ Guardados {data['total_matches']} partidos en {OUTPUT_PATH}")

# ---------------------------------------------------------------------------
# Placeholder scraper functions – real implementations will replace these.
# ---------------------------------------------------------------------------

def fetch_soccerway_fixtures():
    """Fetch fixture list from Soccerway for 2026 matches."""
    _limiter.wait_sync("soccerway.com")
    calendar_url = "https://int.soccerway.com/matches/2026/"
    try:
        resp = requests.get(calendar_url, timeout=15)
        resp.raise_for_status()
        html = resp.text
    except Exception as e:
        print(f"⚠️ Error fetching Soccerway fixtures: {e}")
        return []
    soup = BeautifulSoup(html, "html.parser")
    fixtures = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/match/" in href and href.rstrip("/").split("/")[-1].isdigit():
            match_id = href.rstrip("/").split("/")[-1]
            match_url = f"https://int.soccerway.com{href}"
            # Attempt to infer team names from URL segment after '/match/'
            parts = href.split("/")
            try:
                name_seg = next(p for p in parts if p and p != "match")
                teams = name_seg.split("-")
                home = teams[0].replace("-", " ").title()
                away = teams[1].replace("-", " ").title()
            except Exception:
                home = away = ""
            fixtures.append({
                "id": match_id,
                "url": match_url,
                "home": home,
                "away": away,
                "date": "",
                "competition": ""
            })
    return fixtures


def extract_corners_soccerway(url):
    """Extract (home_corners, away_corners) from a Soccerway match page."""
    _limiter.wait_sync("soccerway.com")
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
        html = resp.text
    except Exception as e:
        print(f"⚠️ Error fetching Soccerway match page: {e}")
        return None
    soup = BeautifulSoup(html, "html.parser")
    for row in soup.find_all("tr"):
        cells = [c.get_text(strip=True) for c in row.find_all(["th", "td"])]
        if cells and cells[0].lower() == "corners":
            if len(cells) >= 3:
                try:
                    home_corners = int(cells[1])
                    away_corners = int(cells[2])
                    return (home_corners, away_corners)
                except Exception:
                    return None
    return None


def extract_corners_flashscore(url):
    """Attempt to extract corners using Playwright on FlashScore.
    Stub implementation – returns ``None``.
    """
    _limiter.wait_sync("flashscore.com")
    return None

# ---------------------------------------------------------------------------
# Main driver
# ---------------------------------------------------------------------------

def main(update: bool = False):
    parser = argparse.ArgumentParser(description="Hybrid corners scraper (Soccerway + FlashScore)")
    parser.add_argument("--update", action="store_true", help="Only process new fixtures")
    args = parser.parse_args()
    update = args.update

    existing = load_existing()
    processed_ids = {m["id"] for m in existing.get("matches", [])} if update else set()

    fixtures = fetch_soccerway_fixtures()
    new_matches = []
    for fix in fixtures:
        fid = fix.get("id")
        if not fid:
            continue
        if update and fid in processed_ids:
            continue
        # Try primary source
        corners = extract_corners_soccerway(fix.get("url", ""))
        if not corners:
            corners = extract_corners_flashscore(fix.get("url", ""))
        if not corners:
            # No data – skip
            continue
        home_corners, away_corners = corners
        new_matches.append({
            "id": fid,
            "date": fix.get("date", ""),
            "home_team": slugify(fix.get("home", "")),
            "away_team": slugify(fix.get("away", "")),
            "home_corners": home_corners,
            "away_corners": away_corners,
            "competition": fix.get("competition", ""),
            "type": "international",
        })
    if new_matches:
        existing.setdefault("matches", []).extend(new_matches)
        # recompute teams_processed
        teams = {m["home_team"] for m in existing["matches"]}.union({m["away_team"] for m in existing["matches"]})
        existing["teams_processed"] = len(teams)
        save_data(existing)
        print(f"🟢 Añadidos {len(new_matches)} partidos nuevos.")
    else:
        print("ℹ️ No se encontraron partidos nuevos para añadir.")

if __name__ == "__main__":
    main()
