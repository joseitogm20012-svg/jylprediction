#!/usr/bin/env python3
"""
map_sofascore_ids.py
--------------------
Mapea todos los equipos WC2026 a IDs de SofaScore usando la API de búsqueda.
Guarda en data/sofascore_team_ids.json
"""
import json
import sys
import time
import requests
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
OUTPUT = BASE_DIR / "data" / "sofascore_team_ids.json"

SOFA_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://www.sofascore.com/",
    "Origin": "https://www.sofascore.com",
    "Cache-Control": "max-age=0",
    "sec-ch-ua": '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
}

KNOWN_IDS = {
    "argentina": 2571, "brazil": 2492, "france": 2484, "spain": 2486,
    "england": 2488, "portugal": 2490, "netherlands": 2491, "germany": 2485,
    "belgium": 2487, "italy": 2489, "colombia": 2500, "croatia": 2501,
    "morocco": 2502, "usa": 2503, "mexico": 2504, "canada": 2505,
    "venezuela": 7840, "hungary": 3165, "slovakia": 3168,
    "turkey": 3159, "honduras": 7839, "mali": 7848,
    "dr-congo": 36846, "indonesia": 7891, "ukraine": 3157,
}

SPECIAL_NAMES = {
    "usa": "USA",
    "dr-congo": "DR Congo",
    "costa-rica": "Costa Rica",
    "saudi-arabia": "Saudi Arabia",
    "new-zealand": "New Zealand",
    "south-korea": "South Korea",
    "south-africa": "South Africa",
    "czech-republic": "Czech Republic",
}

# 49 WC2026 teams from transfermarkt_stats.json
WC2026_SLUGS = [
    "algeria", "argentina", "australia", "belgium", "bolivia", "brazil",
    "cameroon", "canada", "chile", "colombia", "costa-rica", "croatia",
    "czech-republic", "denmark", "ecuador", "egypt", "england", "france",
    "germany", "ghana", "greece", "guatemala", "honduras", "indonesia",
    "iran", "italy", "jamaica", "japan", "mexico", "morocco",
    "netherlands", "new-zealand", "nigeria", "panama", "paraguay",
    "poland", "portugal", "qatar", "saudi-arabia", "senegal", "serbia",
    "south-africa", "south-korea", "spain", "switzerland", "tunisia",
    "turkey", "uruguay", "usa",
]


def make_session():
    """Create a session with proper headers and land on sofascore.com to get cookies."""
    session = requests.Session()
    session.headers.update(SOFA_HEADERS)
    try:
        landing = session.get("https://www.sofascore.com/", timeout=10, allow_redirects=True)
    except Exception:
        pass
    time.sleep(1.0)
    return session


def search_team_id(slug: str, session: requests.Session) -> int | None:
    name = SPECIAL_NAMES.get(slug, slug.replace("-", " ").title())
    url = f"https://api.sofascore.com/api/v1/search/all?q={name}"
    try:
        r = session.get(url, timeout=10)
        if r.status_code != 200:
            print(f"    HTTP {r.status_code}")
            return None
        data = r.json()
        for res in data.get("results", []):
            if res.get("type") == "team" and res.get("entity", {}).get("sport", {}).get("name") == "Football":
                team_id = res["entity"]["id"]
                return team_id
        print(f"    No football team found for '{name}'")
        return None
    except Exception as e:
        print(f"    Error: {e}")
        return None


def main():
    print("=" * 60)
    print("  SofaScore Team ID Mapper - WC2026")
    print("=" * 60)

    session = make_session()
    mapping = {}
    found, missing = 0, 0

    for slug in WC2026_SLUGS:
        if slug in KNOWN_IDS:
            mapping[slug] = KNOWN_IDS[slug]
            print(f"  [KNOWN] {slug:20s} -> {KNOWN_IDS[slug]}")
            found += 1
            continue

        print(f"  [SEARCH] {slug:20s} ...", end=" ")
        sys.stdout.flush()
        team_id = search_team_id(slug, session)
        if team_id:
            mapping[slug] = team_id
            found += 1
            print(f"-> {team_id}")
        else:
            mapping[slug] = None
            missing += 1
            print("-> NOT FOUND")

        time.sleep(1.5)

    print(f"\n{'=' * 60}")
    print(f"  Resultado: {found} encontrados, {missing} faltantes")

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(mapping, f, indent=2, ensure_ascii=False)
    print(f"  Guardado en {OUTPUT}")

    return 1 if missing > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
