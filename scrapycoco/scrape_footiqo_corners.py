"""Scraper for Footiqo.com World Cup corner stats (Second-Half).

Uses static HTML parsing since the data is present in the initial page load.
Tries to map the tables based on the order of regions and subtabs.
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

import requests
from bs4 import BeautifulSoup

# Project root
BASE_DIR = Path(__file__).parent.parent
CORNERS_JSON_PATH = BASE_DIR / "data" / "corners_stats.json"
URL = "https://footiqo.com/statistics/teams/corners/second-half-world-cup/"

# Map Footiqo display names to project slugs
NAME_MAP = {
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

def normalize_team_name(name: str) -> str:
    name = name.strip().lower()
    if name in NAME_MAP:
        return NAME_MAP[name]
    return re.sub(r"[^a-z0-9-]", "", name.replace(" ", "-").replace("'", "")).strip("-")

def extract_table_data(table) -> List[Dict[str, Any]]:
    """Parse a single wpDataTable."""
    rows = table.find_all("tr")
    data = []
    for row in rows:
        cols = row.find_all("td")
        if len(cols) < 10:
            continue
        
        team_name = cols[0].get_text(strip=True)
        slug = normalize_team_name(team_name)
        
        try:
            data.append({
                "slug": slug,
                "team": team_name,
                "matches": int(cols[1].get_text(strip=True)),
                "taken": float(cols[2].get_text(strip=True)),
                "conceded": float(cols[3].get_text(strip=True)),
                "over35": int(cols[4].get_text(strip=True).replace("%", "")),
                "over45": int(cols[6].get_text(strip=True).replace("%", "")),
                "over55": int(cols[8].get_text(strip=True).replace("%", "")),
            })
        except (ValueError, IndexError):
            continue
    return data

def main():
    print(f"Fetching {URL} ...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }
    try:
        resp = requests.get(URL, headers=headers, timeout=30)
        resp.raise_for_status()
        html = resp.text
    except Exception as e:
        print(f"Error fetching HTML: {e}")
        return

    soup = BeautifulSoup(html, "html.parser")
    tables = soup.find_all("table", class_="wpDataTable")
    
    if not tables:
        print("ERROR: No wpDataTable tables found")
        return

    print(f"Found {len(tables)} tables. Mapping to regions...")
    
    regions = [
        ("Final phase", ["Overall"]),
        ("South America", ["Overall", "Home", "Away"]),
        ("Africa", ["Overall", "Home", "Away"]),
        ("Europe", ["Overall", "Home", "Away"]),
        ("Asia", ["Overall", "Home", "Away"]),
        ("North & Central America", ["Overall", "Home", "Away"]),
    ]
    
    all_results = {}
    table_idx = 0
    
    for region_name, subtabs in regions:
        if table_idx >= len(tables):
            break
            
        for subtab in subtabs:
            if table_idx >= len(tables):
                break
                
            print(f"Processing {region_name} - {subtab} (Table {table_idx+1})")
            table_data = extract_table_data(tables[table_idx])
            
            for entry in table_data:
                slug = entry["slug"]
                if slug not in all_results:
                    all_results[slug] = {}
                
                # We store 2nd half data specifically
                all_results[slug]["second_half"] = all_results[slug].get("second_half", {})
                all_results[slug]["second_half"][subtab.lower()] = {
                    "taken": entry["taken"],
                    "conceded": entry["conceded"],
                    "over35": entry["over35"],
                    "over45": entry["over45"],
                    "over55": entry["over55"],
                    "matches": entry["matches"]
                }
            table_idx += 1

    # Merge into corners_stats.json
    if CORNERS_JSON_PATH.exists():
        with open(CORNERS_JSON_PATH, "r", encoding="utf-8") as f:
            existing = json.load(f)
    else:
        existing = {}

    updated_count = 0
    for slug, data in all_results.items():
        if slug not in existing:
            existing[slug] = {}
        
        existing[slug]["second_half"] = data["second_half"]
        updated_count += 1
        
    existing["_meta"] = existing.get("_meta", {})
    existing["_meta"]["footiqo_second_half_updated"] = datetime.now().isoformat()
    
    with open(CORNERS_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2, ensure_ascii=False)
    
    print(f"\nSuccessfully updated {updated_count} teams with second-half data in {CORNERS_JSON_PATH}")

if __name__ == "__main__":
    main()
