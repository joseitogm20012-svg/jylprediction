#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Extrae estadísticas misceláneas por jugador (tarjetas, faltas, etc.)
desde caché soccerdata (players_INT-World Cup_2022_misc.html).
Añade a player_stats.json bajo clave 'misc'.
"""
import json, sys, io
from pathlib import Path
from bs4 import BeautifulSoup, Comment

if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE_DIR = Path(__file__).parent
PLAYER_STATS_PATH = BASE_DIR / "player_stats.json"
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

def parse_val(s):
    if not s or s.strip() == "":
        return 0.0
    s = s.strip().replace(",", "")
    try:
        return float(s)
    except:
        return 0.0

def find_table_in_comments(soup, table_id):
    for comment in soup.find_all(string=lambda s: isinstance(s, Comment) and table_id in s):
        inner = BeautifulSoup(str(comment), "html.parser")
        tbl = inner.find("table", id=table_id)
        if tbl:
            return tbl
    return soup.find("table", id=table_id)

def parse_misc_table(filepath):
    if not filepath.exists():
        print(f"  Caché no encontrado: {filepath.name}")
        return []
    html = filepath.read_text(encoding="utf-8", errors="replace")
    soup = BeautifulSoup(html, "html.parser")
    table = find_table_in_comments(soup, "stats_misc")
    if not table:
        print(f"  No se encontró tabla stats_misc en {filepath.name}")
        return []
    tbody = table.find("tbody")
    if not tbody:
        return []
    rows = []
    for tr in tbody.find_all("tr"):
        player_el = tr.find("td", {"data-stat": "player"})
        if not player_el:
            continue
        player = player_el.get_text(strip=True)
        team_el = tr.find("td", {"data-stat": "team"})
        if not team_el:
            continue
        raw = team_el.get_text(strip=True)
        team = raw[2:] if (len(raw) >= 3 and raw[:2].isalpha()) else raw
        slug = FBREF_NAME_TO_SLUG.get(team)
        if not slug:
            continue
        def g(stat):
            el = tr.find("td", {"data-stat": stat})
            if el is None:
                el = tr.find("th", {"data-stat": stat})
            return el.get_text(strip=True) if el else "0"
        rows.append({
            "player": player,
            "team_slug": slug,
            "cards_yellow": int(parse_val(g("cards_yellow"))),
            "cards_red": int(parse_val(g("cards_red"))),
            "cards_yellow_red": int(parse_val(g("cards_yellow_red"))),
            "fouls": int(parse_val(g("fouls"))),
            "fouled": int(parse_val(g("fouled"))),
            "offsides": int(parse_val(g("offsides"))),
            "crosses": int(parse_val(g("crosses"))),
            "interceptions": int(parse_val(g("interceptions"))),
            "tackles_won": int(parse_val(g("tackles_won"))),
            "pens_won": int(parse_val(g("pens_won"))),
            "pens_conceded": int(parse_val(g("pens_conceded"))),
            "own_goals": int(parse_val(g("own_goals"))),
            "minutes_90s": parse_val(g("minutes_90s")),
        })
    return rows

def main():
    print("=" * 60)
    print("  FBref Player Misc Stats (desde caché)")
    print("=" * 60)
    all_data = {}
    if PLAYER_STATS_PATH.exists():
        try:
            all_data = json.loads(PLAYER_STATS_PATH.read_text(encoding="utf-8"))
            print(f"Datos existentes: {len(all_data)} equipos")
        except:
            all_data = {}
    for suffix in ["2022", "2026"]:
        fname = f"players_INT-World Cup_{suffix}_misc.html"
        fpath = SOCCERDATA_CACHE / fname
        print(f"\n--- {fname} ---")
        rows = parse_misc_table(fpath)
        for row in rows:
            slug = row.pop("team_slug")
            if slug not in all_data:
                all_data[slug] = {}
            if "misc" not in all_data[slug]:
                all_data[slug]["misc"] = []
            all_data[slug]["misc"].append(row)
        print(f"  {len(rows)} jugadores")
    PLAYER_STATS_PATH.write_text(json.dumps(all_data, ensure_ascii=False, indent=2), encoding="utf-8")
    total = sum(len(v.get("misc",[])) for v in all_data.values())
    print(f"\nTotal equipos: {len(all_data)}, jugadores misc: {total}")

if __name__ == "__main__":
    main()
