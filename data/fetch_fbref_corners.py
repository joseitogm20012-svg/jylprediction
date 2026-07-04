#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Obtiene estadísticas de CÓRNERS/CROSSES por equipo desde caché soccerdata.
Usa crosses (Crs) de tabla misc como proxy de córners.
Mergea en xg_by_team.json.
"""
import json, sys, io
from pathlib import Path
from bs4 import BeautifulSoup, Comment

if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE_DIR = Path(__file__).parent
XG_PATH = BASE_DIR / "xg_by_team.json"
SOCCERDATA_CACHE = Path.home() / "soccerdata" / "data" / "FBref"

FBREF_NAME_TO_SLUG = {
    "United States": "usa", "Mexico": "mexico", "Canada": "canada",
    "Panama": "panama", "Honduras": "honduras", "Costa Rica": "costa-rica",
    "Jamaica": "jamaica", "Haiti": "haiti", "Trinidad and Tobago": "trinidad-and-tobago",
    "Guatemala": "guatemala", "El Salvador": "el-salvador", "Curacao": "curacao",
    "Argentina": "argentina", "Brazil": "brazil", "Colombia": "colombia",
    "Ecuador": "ecuador", "Paraguay": "paraguay", "Uruguay": "uruguay",
    "Chile": "chile", "Peru": "peru", "Bolivia": "bolivia", "Venezuela": "venezuela",
    "Germany": "germany", "Austria": "austria", "Belgium": "belgium",
    "Bosnia and Herzegovina": "bosnia-and-herzegovina", "Croatia": "croatia",
    "Scotland": "scotland", "Spain": "spain", "France": "france",
    "England": "england", "Norway": "norway", "Netherlands": "netherlands",
    "Poland": "poland", "Portugal": "portugal", "Czech Republic": "czech-republic",
    "Czechia": "czech-republic", "Sweden": "sweden", "Switzerland": "switzerland",
    "Turkey": "turkey", "Serbia": "serbia", "Denmark": "denmark",
    "Iceland": "iceland", "Wales": "wales", "Russia": "russia",
    "Ukraine": "ukraine", "Slovakia": "slovakia", "Slovenia": "slovenia",
    "Hungary": "hungary", "Romania": "romania", "Greece": "greece",
    "Albania": "albania", "North Macedonia": "north-macedonia", "Finland": "finland",
    "Georgia": "georgia", "Kosovo": "kosovo",
    "Saudi Arabia": "saudi-arabia", "Australia": "australia", "Qatar": "qatar",
    "South Korea": "south-korea", "Korea Republic": "south-korea",
    "United Arab Emirates": "uae", "Iraq": "iraq", "IR Iran": "iran", "Iran": "iran",
    "Japan": "japan", "Jordan": "jordan", "China PR": "china",
    "Uzbekistan": "uzbekistan", "Kazakhstan": "kazakhstan",
    "Algeria": "algeria", "Cape Verde": "cape-verde", "Ivory Coast": "ivory-coast",
    "Cote d'Ivoire": "ivory-coast", "Egypt": "egypt", "Ghana": "ghana",
    "Morocco": "morocco", "DR Congo": "dr-congo",
    "Democratic Republic of the Congo": "dr-congo",
    "South Africa": "south-africa", "Tunisia": "tunisia", "Senegal": "senegal",
    "Cameroon": "cameroon", "Nigeria": "nigeria", "Mali": "mali",
    "Burkina Faso": "burkina-faso", "New Zealand": "new-zealand", "Indonesia": "indonesia",
}

CACHE_SOURCES = [
    ("2022", "teams_INT-World Cup_2022_misc.html", "stats_squads_misc_for"),
    ("2026", "teams_INT-World Cup_2026_misc.html", "stats_squads_misc_for"),
]

def parse_val(s):
    if not s or s == "":
        return 0.0
    s = s.strip().replace(",", "")
    try:
        return float(s)
    except:
        return 0.0

def extract_team_name(raw):
    if len(raw) >= 3 and raw[:2].isalpha() and raw[2:]:
        return raw[2:]
    return raw

def parse_squad_misc(filepath, table_id):
    if not filepath.exists():
        print(f"  Caché no encontrado: {filepath.name}")
        return {}
    html = filepath.read_text(encoding="utf-8", errors="replace")
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", id=table_id)
    if not table:
        print(f"  No se encontró tabla {table_id}")
        return {}
    tbody = table.find("tbody")
    if not tbody:
        return {}
    result = {}
    for tr in tbody.find_all("tr"):
        team_el = tr.find(["th", "td"], {"data-stat": "team"})
        if not team_el:
            continue
        team = extract_team_name(team_el.get_text(strip=True))
        slug = FBREF_NAME_TO_SLUG.get(team)
        if not slug:
            continue
        def g(stat):
            el = tr.find("td", {"data-stat": stat})
            return el.get_text(strip=True) if el else "0"
        crosses = int(parse_val(g("crosses")))
        mp = int(parse_val(g("games")))
        if mp == 0:
            mp = int(parse_val(g("minutes_90s")))
            mp = max(mp, 1)
        if slug not in result:
            result[slug] = {"crosses_for": 0, "matches": 0}
        result[slug]["crosses_for"] += crosses
        result[slug]["matches"] += max(mp, 1)
    return result

def main():
    print("=" * 60)
    print("  FBref Team Corners/Crosses Stats (desde caché)")
    print("=" * 60)
    if not XG_PATH.exists():
        print(f"ERROR: {XG_PATH} no existe")
        sys.exit(1)
    xg_data = json.loads(XG_PATH.read_text(encoding="utf-8"))
    teams = xg_data.get("teams", {})
    print(f"Datos existentes: {len(teams)} equipos")

    accum = {}
    for label, fname, tid in CACHE_SOURCES:
        print(f"\n--- {label}: {fname} [{tid}] ---")
        stats = parse_squad_misc(SOCCERDATA_CACHE / fname, tid)
        for slug, s in stats.items():
            if slug not in accum:
                accum[slug] = {"crosses_for": 0, "matches": 0}
            accum[slug]["crosses_for"] += s["crosses_for"]
            accum[slug]["matches"] += s["matches"]
        print(f"  {len(stats)} equipos")

    updated = 0
    for slug, cdata in accum.items():
        m = max(cdata["matches"], 1)
        cdata["crosses_per_90"] = round(cdata["crosses_for"] / m, 2)
        if slug in teams:
            teams[slug]["crosses_per_90"] = cdata["crosses_per_90"]
            teams[slug]["crosses_for"] = cdata["crosses_for"]
            updated += 1
    xg_data["teams"] = teams
    XG_PATH.write_text(json.dumps(xg_data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nActualizados: {updated} equipos")

if __name__ == "__main__":
    main()
