#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Scrapea estadisticas reales de corners desde FBref (passing_types -> corner_kicks)
para TODAS las competiciones internacionales principales, y guarda en corners_stats.json.

Competiciones scrapeadas:
  - Mundial (2018, 2022, 2026)
  - Eurocopa (2021, 2025)
  - Copa America (2021, 2024)
  - Africa Cup of Nations (2022, 2024)
  - Asian Cup (2024)
  - CONCACAF Gold Cup (2023, 2025)
  - UEFA Nations League (2023, 2025)
  - CONCACAF Nations League (2023, 2025)
  - Eliminatorias CONMEBOL (2022, 2026)
  - Eliminatorias CONCACAF (2022, 2026)

Uso:
    python data/fetch_all_corners.py
"""
import json, os, sys, io, time, re
from pathlib import Path
from bs4 import BeautifulSoup
import urllib.request, urllib.error

if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE_DIR = Path(__file__).parent
OUTPUT = BASE_DIR / "corners_stats.json"

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

# Competiciones a scrapear: (comp_id, season, url_slug)
TOURNAMENTS = [
    # Mundial
    (1, 2018, "World-Cup"),
    (1, 2022, "World-Cup"),
    (1, 2026, "World-Cup"),
    # Eurocopa
    (19, 2021, "European-Championship"),
    (19, 2025, "European-Championship"),
    # Copa America
    (17, 2021, "Copa-America"),
    (17, 2024, "Copa-America"),
    # Africa Cup of Nations
    (5, 2022, "Africa-Cup-of-Nations"),
    (5, 2024, "Africa-Cup-of-Nations"),
    # Asian Cup
    (3, 2024, "Asian-Cup"),
    # CONCACAF Gold Cup
    (7, 2023, "CONCACAF-Gold-Cup"),
    (7, 2025, "CONCACAF-Gold-Cup"),
    # UEFA Nations League
    (658, 2023, "UEFA-Nations-League"),
    (658, 2025, "UEFA-Nations-League"),
    # CONCACAF Nations League
    (714, 2023, "CONCACAF-Nations-League"),
    (714, 2025, "CONCACAF-Nations-League"),
    # Eliminatorias CONMEBOL
    (202, 2022, "CONMEBOL-World-Cup- Qualifiers"),
    (202, 2026, "CONMEBOL-World-Cup- Qualifiers"),
    # Eliminatorias CONCACAF
    (250, 2022, "CONCACAF-World-Cup- Qualifiers"),
    (250, 2026, "CONCACAF-World-Cup- Qualifiers"),
    # Eliminatorias UEFA
    (155, 2022, "UEFA-World-Cup- Qualifiers"),
    (155, 2026, "UEFA-World-Cup- Qualifiers"),
]

# Mapeo nombres FBref -> slugs del proyecto (de fetch_fbref_xg.py)
FBREF_TO_SLUG = {
    "United States": "usa", "Mexico": "mexico", "Canada": "canada",
    "Panama": "panama", "Honduras": "honduras", "Costa Rica": "costa-rica",
    "Jamaica": "jamaica", "Haiti": "haiti", "Trinidad and Tobago": "trinidad-and-tobago",
    "Guatemala": "guatemala", "El Salvador": "el-salvador", "Curacao": "curacao",
    "Curazao": "curacao", "Argentina": "argentina", "Brazil": "brazil",
    "Colombia": "colombia", "Ecuador": "ecuador", "Uruguay": "uruguay",
    "Paraguay": "paraguay", "Chile": "chile", "Bolivia": "bolivia",
    "Venezuela": "venezuela", "Peru": "peru", "France": "france",
    "England": "england", "Spain": "spain", "Italy": "italy",
    "Germany": "germany", "Netherlands": "netherlands", "Portugal": "portugal",
    "Belgium": "belgium", "Croatia": "croatia", "Switzerland": "switzerland",
    "Denmark": "denmark", "Serbia": "serbia", "Poland": "poland",
    "Austria": "austria", "Turkey": "turkey", "Turkey (Türkiye)": "turkey",
    "Wales": "wales", "Scotland": "scotland", "Norway": "norway",
    "Sweden": "sweden", "Czech Republic": "czech-republic",
    "Ukraine": "ukraine", "Hungary": "hungary", "Greece": "greece",
    "Romania": "romania", "Slovakia": "slovakia", "Slovenia": "slovenia",
    "Bosnia and Herzegovina": "bosnia-and-herzegovina",
    "Nigeria": "nigeria", "Senegal": "senegal", "Ghana": "ghana",
    "Cameroon": "cameroon", "Ivory Coast": "ivory-coast",
    "Côte d'Ivoire": "ivory-coast", "Algeria": "algeria",
    "Egypt": "egypt", "Morocco": "morocco", "Tunisia": "tunisia",
    "South Africa": "south-africa", "DR Congo": "dr-congo",
    "Burkina Faso": "burkina-faso", "Mali": "mali",
    "Japan": "japan", "South Korea": "south-korea",
    "Korea Republic": "south-korea", "Australia": "australia",
    "Iran": "iran", "Saudi Arabia": "saudi-arabia",
    "Qatar": "qatar", "Iraq": "iraq", "United Arab Emirates": "uae",
    "Jordan": "jordan", "Indonesia": "indonesia",
    "New Zealand": "new-zealand",
    "Cape Verde": "cape-verde",
}

def to_slug(name):
    name = name.strip()
    if name in FBREF_TO_SLUG:
        return FBREF_TO_SLUG[name]
    slug = name.lower().replace(" ", "-").replace(".", "").replace("'", "")
    slug = re.sub(r'[^a-z0-9-]', '', slug)
    return slug

def fetch_url(url, retries=3):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2)
            else:
                return None

def scrape_tournament(comp_id, season, comp_slug):
    url = f"https://fbref.com/en/comps/{comp_id}/{season}/passing_types/{season}-{comp_slug}-Stats"
    print(f"  {url}")
    html = fetch_url(url)
    if not html:
        print(f"    -> no data")
        return {}, {}

    soup = BeautifulSoup(html, "html.parser")
    corners_for = {}
    corners_against = {}

    # Tabla 'for'
    table = soup.find("table", id="stats_squads_passing_types_for")
    if table:
        tbody = table.find("tbody")
        if tbody:
            for tr in tbody.find_all("tr"):
                th = tr.find("th", {"data-stat": "team"})
                if not th:
                    continue
                slug = to_slug(th.get_text().strip())
                td_ck = tr.find("td", {"data-stat": "corner_kicks"})
                td_90s = tr.find("td", {"data-stat": "minutes_90s"})
                if td_ck and td_90s:
                    try:
                        ck = float(td_ck.get_text().strip())
                        mins = float(td_90s.get_text().strip())
                        if mins > 0:
                            corners_for[slug] = ck / mins
                    except:
                        pass

    # Tabla 'against'
    table2 = soup.find("table", id="stats_squads_passing_types_against")
    if table2:
        tbody = table2.find("tbody")
        if tbody:
            for tr in tbody.find_all("tr"):
                th = tr.find("th", {"data-stat": "team"})
                if not th:
                    continue
                slug = to_slug(th.get_text().strip())
                td_ck = tr.find("td", {"data-stat": "corner_kicks"})
                td_90s = tr.find("td", {"data-stat": "minutes_90s"})
                if td_ck and td_90s:
                    try:
                        ck = float(td_ck.get_text().strip())
                        mins = float(td_90s.get_text().strip())
                        if mins > 0:
                            corners_against[slug] = ck / mins
                    except:
                        pass

    n_for = len(corners_for)
    n_ag = len(corners_against)
    print(f"    -> {n_for} equipos for, {n_ag} equipos against")
    return corners_for, corners_against

def main():
    print("=" * 60)
    print("SCRAPEO CORNERS FBref — TODAS LAS COMPETICIONES")
    print("=" * 60)

    # Cargar datos existentes
    existing = {}
    if OUTPUT.exists():
        try:
            existing = json.loads(OUTPUT.read_text(encoding="utf-8"))
            print("Cargados %d equipos existentes" % len(existing))
        except:
            pass

    # Acumuladores: slug -> {sum_for, sum_against, count}
    agg = {}
    for slug, data in existing.items():
        if data.get("corners_for") and data["corners_for"] > 0:
            agg[slug] = {
                "sum_for": data["corners_for"] * data.get("games", 1),
                "sum_against": data["corners_against"] * data.get("games", 1),
                "count": data.get("games", 1)
            }

    total_tournaments = len(TOURNAMENTS)
    for idx, (comp_id, season, comp_slug) in enumerate(TOURNAMENTS, 1):
        print(f"[{idx}/{total_tournaments}] comp={comp_id} season={season} {comp_slug}")
        corners_for, corners_against = scrape_tournament(comp_id, season, comp_slug)

        for slug, val in corners_for.items():
            if slug not in agg:
                agg[slug] = {"sum_for": 0, "sum_against": 0, "count": 0}
            agg[slug]["sum_for"] += val
            agg[slug]["count"] += 1

        for slug, val in corners_against.items():
            if slug not in agg:
                agg[slug] = {"sum_for": 0, "sum_against": 0, "count": 0}
            agg[slug]["sum_against"] += val

        time.sleep(1.5)

    # Construir output
    output = {}
    for slug, data in agg.items():
        if data["count"] > 0:
            output[slug] = {
                "corners_for": round(data["sum_for"] / data["count"], 2),
                "corners_against": round(data["sum_against"] / data["count"], 2),
                "games": data["count"]
            }

    OUTPUT.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")

    print("=" * 60)
    print("COMPLETADO: %d equipos con datos de corners" % len(output))
    print("Output: %s" % OUTPUT)
    print("=" * 60)

if __name__ == "__main__":
    main()
