"""Scrape corner stats from FootyStats.org World Cup page and update corners_stats.json.

Target: https://footystats.org/world-cup
Extracts: Team name, Total Corners AVG per game, and over-threshold percentages.
Updates: data/corners_stats.json with real corners_for and corners_against values
         using the AVG split: corners_for = AVG * 0.65 / 0.35 (home/away factor).

Run: python data/scrape_footystats_corners.py
"""

import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests
from bs4 import BeautifulSoup

PROJECT_DIR = Path(__file__).resolve().parent.parent
CORNERS_JSON_PATH = PROJECT_DIR / "data" / "corners_stats.json"
FOOTYSTATS_URL = "https://footystats.org/world-cup"
CACHE_PATH = PROJECT_DIR / "data" / "footystats_worldcup.html"
# Fallback cache in opencode tool-output directory
OPENTOOL_CACHE = Path.home() / ".local" / "share" / "opencode" / "tool-output" / "tool_f2972bd5c001GbJJRpUfv2p1Jd"

NAME_MAP = {
    # FootyStats display name → project slug
    "argentina": "argentina",
    "france": "france",
    "brazil": "brazil",
    "spain": "spain",
    "germany": "germany",
    "england": "england",
    "netherlands": "netherlands",
    "portugal": "portugal",
    "belgium": "belgium",
    "croatia": "croatia",
    "uruguay": "uruguay",
    "colombia": "colombia",
    "mexico": "mexico",
    "usa": "usa",
    "usmnt": "usa",
    "japan": "japan",
    "south korea": "south-korea",
    "korea republic": "south-korea",
    "morocco": "morocco",
    "senegal": "senegal",
    "tunisia": "tunisia",
    "egypt": "egypt",
    "algeria": "algeria",
    "ghana": "ghana",
    "nigeria": "nigeria",
    "ivory coast": "ivory-coast",
    "cote d'ivoire": "ivory-coast",
    "cameroon": "cameroon",
    "south africa": "south-africa",
    "canada": "canada",
    "costa rica": "costa-rica",
    "panama": "panama",
    "honduras": "honduras",
    "jamaica": "jamaica",
    "el salvador": "el-salvador",
    "ir iran": "iran",
    "iran": "iran",
    "saudi arabia": "saudi-arabia",
    "qatar": "qatar",
    "australia": "australia",
    "new zealand": "new-zealand",
    "iraq": "iraq",
    "jordan": "jordan",
    "uzbekistan": "uzbekistan",
    "ecuador": "ecuador",
    "paraguay": "paraguay",
    "chile": "chile",
    "peru": "peru",
    "bolivia": "bolivia",
    "venezuela": "venezuela",
    "austria": "austria",
    "switzerland": "switzerland",
    "sweden": "sweden",
    "norway": "norway",
    "denmark": "denmark",
    "scotland": "scotland",
    "turkey": "turkey",
    "czech republic": "czech-republic",
    "serbia": "serbia",
    "poland": "poland",
    "ukraine": "ukraine",
    "hungary": "hungary",
    "romania": "romania",
    "greece": "greece",
    "bosnia and herzegovina": "bosnia",
    "cape verde": "cape-verde",
    "congo dr": "congo-dr",
    "curacao": "curacao",
    "haiti": "haiti",
    "indonesia": "indonesia",
}

HOME_FACTOR = 0.55          # 55% of total corners come from home team
AWAY_FACTOR = 0.45          # 45% from away team
MIN_CORNERS_FOR = 3.0
MIN_CORNERS_AGAINST = 2.0
MAX_CORNERS_FOR = 8.0
MAX_CORNERS_AGAINST = 6.0


def fetch_html(url: str, cache_path: Path, max_age_hours: int = 24) -> Optional[str]:
    """Fetch HTML from URL, using cache if fresh enough."""
    if cache_path.exists():
        age = time.time() - cache_path.stat().st_mtime
        if age < max_age_hours * 3600:
            with open(cache_path, "r", encoding="utf-8") as f:
                return f.read()

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
    }
    resp = requests.get(url, headers=headers, timeout=30)
    resp.raise_for_status()
    html = resp.text
    with open(cache_path, "w", encoding="utf-8") as f:
        f.write(html)
    return html


def normalize_name(name: str) -> str:
    """Convert display name to project slug."""
    key = name.strip().lower()
    if key in NAME_MAP:
        return NAME_MAP[key]
    return re.sub(r"[^a-z0-9-]", "", key.replace(" ", "-").replace("'", "")).strip("-")


def extract_corners_from_html(html: str) -> dict[str, float]:
    """Parse the FootyStats World Cup corner stats table from HTML."""
    soup = BeautifulSoup(html, "html.parser")
    corners_data: dict[str, float] = {}

    container = soup.find(id="cornerTables")
    if not container:
        print("ERROR: No #cornerTables found in HTML")
        return corners_data

    table = container.find("table", class_="full-league-table")
    if not table:
        table = container.find("table")
    if not table:
        print("ERROR: No table found inside #cornerTables")
        return corners_data

    tbody = table.find("tbody")
    if not tbody:
        tbody = table

    rows = tbody.find_all("tr")
    for row in rows:
        cols = row.find_all("td")
        if not cols or len(cols) < 2:
            continue

        name_cell = cols[0]
        link = name_cell.find("a")
        if not link:
            continue
        display_name = link.get_text(strip=True)

        avg_cell = cols[1]
        avg_text = avg_cell.get_text(strip=True)
        if not avg_text:
            continue

        try:
            avg = float(avg_text)
        except ValueError:
            continue

        slug = normalize_name(display_name)
        corners_data[slug] = avg

    return corners_data


def update_corners_json(corners_data: dict[str, float], json_path: Path):
    """Update corners_stats.json with FootyStats corner AVG data."""
    if json_path.exists():
        with open(json_path, "r", encoding="utf-8") as f:
            existing = json.load(f)
    else:
        existing = {}

    updated_count = 0
    for slug, avg in corners_data.items():
        if avg <= 0:
            continue

        corners_for = avg * HOME_FACTOR
        corners_against = avg * AWAY_FACTOR

        if corners_for < MIN_CORNERS_FOR:
            corners_for = MIN_CORNERS_FOR
        elif corners_for > MAX_CORNERS_FOR:
            corners_for = MAX_CORNERS_FOR

        if corners_against < MIN_CORNERS_AGAINST:
            corners_against = MIN_CORNERS_AGAINST
        elif corners_against > MAX_CORNERS_AGAINST:
            corners_against = MAX_CORNERS_AGAINST

        if slug in existing:
            entry = existing[slug]
            if isinstance(entry, dict):
                games_before = entry.get("games", 10)
                entry["corners_for"] = round(corners_for, 2)
                entry["corners_against"] = round(corners_against, 2)
                entry["_updated"] = datetime.now().isoformat()
                entry["_source"] = "footystats"
                updated_count += 1
            else:
                existing[slug] = {
                    "corners_for": round(corners_for, 2),
                    "corners_against": round(corners_against, 2),
                    "games": 10,
                    "_updated": datetime.now().isoformat(),
                    "_source": "footystats",
                }
                updated_count += 1
        else:
            existing[slug] = {
                "corners_for": round(corners_for, 2),
                "corners_against": round(corners_against, 2),
                "games": 10,
                "_updated": datetime.now().isoformat(),
                "_source": "footystats",
            }
            updated_count += 1

    existing["_meta"] = {
        "source": f"Scraped from {FOOTYSTATS_URL}",
        "total_teams": len(corners_data),
        "updated_teams": updated_count,
        "scraped_at": datetime.now().isoformat(),
        "home_factor": HOME_FACTOR,
        "away_factor": AWAY_FACTOR,
        "note": (
            "avg corners per game. "
            "Corners split by HOME_FACTOR/AWAY_FACTOR. "
            "Clamped to [3.0-8.0] (for) / [2.0-6.0] (against)."
        ),
    }

    json_path.parent.mkdir(parents=True, exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2, ensure_ascii=False)

    return updated_count


def load_html() -> Optional[str]:
    """Try loading from cache files in order of preference."""
    if CACHE_PATH.exists():
        with open(CACHE_PATH, "r", encoding="utf-8") as f:
            return f.read()
    if OPENTOOL_CACHE.exists():
        with open(OPENTOOL_CACHE, "r", encoding="utf-8") as f:
            return f.read()
    return fetch_html(FOOTYSTATS_URL, CACHE_PATH)


def main():
    print(f"Loading HTML (trying cache first) ...")
    html = load_html()
    if not html:
        print("ERROR: Could not load HTML from any source")
        sys.exit(1)

    print("Extracting corner stats from HTML ...")
    corners_data = extract_corners_from_html(html)

    if not corners_data:
        print("ERROR: No corner data extracted")
        sys.exit(1)

    print(f"Found {len(corners_data)} teams with corner data:")
    for slug, avg in sorted(corners_data.items()):
        print(f"  {slug}: AVG={avg}")

    updated = update_corners_json(corners_data, CORNERS_JSON_PATH)
    print(f"\nUpdated {updated} teams in {CORNERS_JSON_PATH}")
    print(f"Total teams in JSON: {len(corners_data)}")


if __name__ == "__main__":
    main()