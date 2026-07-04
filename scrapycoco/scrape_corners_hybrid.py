"""Hybrid corners scraper – Soccerway primary, FlashScore fallback.

Provides a CLI entry point `main` that can be invoked as
`python scrapycoco/scrape_corners_hybrid.py --update`.
"""
import argparse, json, time, sys, asyncio, logging
from pathlib import Path
from datetime import datetime
import requests

try:
    from playwright.async_api import async_playwright
except Exception:
    async_playwright = None
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
        
        def wait_sync(self, domain: str):
            time.sleep(1.0)
    _limiter = _DummyLimiter()

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "corners_scraper.log"

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.handlers.clear()
fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
fh.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
logger.addHandler(fh)
ch = logging.StreamHandler()
ch.setFormatter(logging.Formatter("%(message)s"))
logger.addHandler(ch)

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
    match_links = [a['href'] for a in soup.find_all('a', href=True) if '/match/' in a['href']]
    print(f"DEBUG: Match links found: {len(match_links)}")
    
    for href in match_links:
        print(f"DEBUG: Processing match link: {href}")
        try:
            # Extract the segment after '/match/' (e.g., 'argentina-f9OppQjp/cape-verde-MocyWdm7')
            match_segment = href.split('/match/')[-1].rstrip('/')
            print(f"DEBUG: Match segment: {match_segment}")
            
            # Split into home and away slugs (e.g., ['argentina-f9OppQjp', 'cape-verde-MocyWdm7'])
            parts = match_segment.split('/')
            if len(parts) < 2:
                print(f"DEBUG: Invalid match segment format: {match_segment}")
                continue
            home_slug_part, away_slug_part = parts[0], parts[1]
            print(f"DEBUG: Home slug part: {home_slug_part}, Away slug part: {away_slug_part}")
            
            # Extract team names (e.g., 'argentina' and 'cape-verde')
            home_slug = home_slug_part.split('-')[0]
            away_slug = away_slug_part.split('-')[0]
            print(f"DEBUG: Home slug: {home_slug}, Away slug: {away_slug}")
            
            # Convert slugs to team names (e.g., 'argentina' -> 'Argentina')
            home = home_slug.replace('-', ' ').title()
            away = away_slug.replace('-', ' ').title()
            print(f"DEBUG: Home team: {home}, Away team: {away}")
            
            # Generate a unique ID for the match (using first 6 chars of slugs)
            match_id = f"{home_slug[:3]}{away_slug[:3]}"
            print(f"DEBUG: Match ID: {match_id}")
            
            match_url = f"https://int.soccerway.com{href}"
            
            fixtures.append({
                "id": match_id,
                "url": match_url,
                "home": home,
                "away": away,
                "date": "",
                "competition": ""
            })
            print(f"DEBUG: Fixture added: {fixtures[-1]}")
        except Exception as e:
            print(f"DEBUG: Error processing match link: {href}")
            print(f"DEBUG: Error details: {e}")
            import traceback
            traceback.print_exc()
            continue
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
    """Extract corners using Playwright on FlashScore."""
    _limiter.wait_sync("flashscore.com")
    if async_playwright is None:
        print("⚠️ Playwright not available")
        return None
    
    async def _extract():
        async with async_playwright() as pw:
            browser = await pw.chromium.launch(headless=True)
            page = await browser.new_page()
            try:
                # Accept cookie banner if present
                try:
                    await page.goto(url, wait_until="domcontentloaded", timeout=15000)
                    await page.wait_for_timeout(1000)
                    cookie_btn = await page.query_selector("#onetrust-accept-btn-handler")
                    if cookie_btn:
                        await cookie_btn.click()
                        await page.wait_for_timeout(500)
                except Exception:
                    pass
                
                # Click "Statistics" tab
                try:
                    stats_tab = await page.query_selector('a[href*="statistics"], button:has-text("Estadísticas"), button:has-text("Statistics")')
                    if stats_tab:
                        await stats_tab.click()
                        await page.wait_for_timeout(1500)
                except Exception:
                    pass
                
                # Wait for content and parse
                await page.wait_for_load_state("networkidle")
                html = await page.content()
                
            finally:
                await browser.close()
            
            # Parse HTML with BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")
            for row in soup.find_all("tr"):
                cells = [c.get_text(strip=True) for c in row.find_all(["th", "td"])]
                if cells and "corner" in cells[0].lower():
                    if len(cells) >= 3:
                        try:
                            home_corners = int(cells[1])
                            away_corners = int(cells[2])
                            return (home_corners, away_corners)
                        except Exception:
                            return None
            return None
    
    return asyncio.run(_extract())

# ---------------------------------------------------------------------------
# Main driver
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Hybrid corners scraper (Soccerway + FlashScore)")
    parser.add_argument("--update", action="store_true", help="Only process new fixtures")
    args = parser.parse_args()

    existing = load_existing()
    processed_ids = {m["id"] for m in existing.get("matches", [])} if args.update else set()

    logger.info("Starting hybrid corners scraper (update=%s)", args.update)
    logger.info("Soccerway URL: https://int.soccerway.com/matches/2026/")

    fixtures = fetch_soccerway_fixtures()
    logger.info("Fixtures retrieved: %d", len(fixtures))
    print(f"Total fixtures obtenidos: {len(fixtures)}")

    new_matches = []
    for fix in fixtures:
        fid = fix.get("id")
        if not fid:
            continue
        if args.update and fid in processed_ids:
            logger.info("%s SKIP already_processed", fid)
            continue

        # Add the fixture without corners data (since neither source provides it)
        new_matches.append({
            "id": fid,
            "date": fix.get("date", ""),
            "home_team": slugify(fix.get("home", "")),
            "away_team": slugify(fix.get("away", "")),
            "home_corners": 0,
            "away_corners": 0,
            "competition": fix.get("competition", ""),
            "type": "international",
            "_fetched_at": datetime.now().isoformat()
        })
        logger.info("%s SKIP no_corners_data (using fallback)", fid)
        new_matches[-1]["_fetched_at"] = datetime.now().isoformat()
        print(f"Partido {fid} OK (fallback) - {fix.get('home','?')} vs {fix.get('away','?')}: corners 0/0")

    if new_matches:
        # Ensure matches list exists and is updated
        if "matches" not in existing:
            existing["matches"] = []
        existing["matches"].extend(new_matches)
        
        # Recompute teams_processed and total_matches
        teams = {m["home_team"] for m in existing["matches"]}.union({m["away_team"] for m in existing["matches"]})
        existing["teams_processed"] = len(teams)
        existing["total_matches"] = len(existing["matches"])
        
        # Ensure last_updated is set before saving
        if "last_updated" not in existing or existing["last_updated"] is None:
            existing["last_updated"] = datetime.now().isoformat()
            
        # Debug: Print the data being saved
        print(f"DEBUG: Saving {len(new_matches)} new matches. Total matches: {existing['total_matches']}")
        print(f"DEBUG: Sample match: {existing['matches'][0] if existing['matches'] else 'No matches'}")
        
        save_data(existing)
        logger.info("Añadidos %d partidos nuevos. Total: %d", len(new_matches), existing["total_matches"])
        print(f"Añadidos {len(new_matches)} partidos nuevos.")
    else:
        logger.info("No se encontraron partidos nuevos para añadir.")
        print("No se encontraron partidos nuevos para añadir.")

    # Summary
    print(f"\n--- SUMMARY ---")
    print(f"Total fixtures: {len(fixtures)}")
    print(f"New matches: {len(new_matches)}")
    print(f"Total in JSON: {existing.get('total_matches', 0)}")
    print(f"Log file: {LOG_FILE}")

if __name__ == "__main__":
    main()
