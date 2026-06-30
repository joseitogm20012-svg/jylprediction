#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Obtiene estadísticas de ASISTENCIAS y PASES CLAVE por jugador desde FBref
usando soccerdata (stat_type='standard'). Escribe en data/player_stats.json bajo 'passing'.

Campos: player, assists, key_passes, passes_completed, passes_attempted, pass_pct, assists_per_90
"""
import json, sys, io
from pathlib import Path
import soccerdata as sd

if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE_DIR = Path(__file__).parent
PLAYER_STATS_PATH = BASE_DIR / "player_stats.json"

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
    "Burkina Faso": "burkina-faso", "New Zealand": "new-zealand",
    "Indonesia": "indonesia",
}

SEASONS = ["2026", "2022", "2018"]

def slug_for_fbref_name(name: str) -> str | None:
    clean = name.replace("\u00e7", "c").replace("\u00f4", "o").replace("\u2019", "'")
    if clean in FBREF_NAME_TO_SLUG:
        return FBREF_NAME_TO_SLUG[clean]
    if name in FBREF_NAME_TO_SLUG:
        return FBREF_NAME_TO_SLUG[name]
    return None

def main():
    print("=" * 60)
    print("  FBref Player Passing/Assist Stats Scraper")
    print("=" * 60)

    all_data = {}
    if PLAYER_STATS_PATH.exists():
        try:
            all_data = json.loads(PLAYER_STATS_PATH.read_text(encoding="utf-8"))
            print(f"Datos existentes cargados: {len(all_data)} equipos")
        except Exception:
            all_data = {}

    for season in SEASONS:
        print(f"\n--- Season {season} ---")
        try:
            fbref = sd.FBref(leagues=["INT-World Cup"], seasons=[season])
            df = fbref.read_player_season_stats(stat_type="standard")
        except Exception as e:
            print(f"  Error cargando {season}: {e}")
            continue

        if df is None or df.empty:
            print(f"  Sin datos para {season}")
            continue

        df.columns = ['_'.join(c).strip('_') for c in df.columns]

        for (league, season_val, team_fbref, player), row in df.iterrows():
            slug = slug_for_fbref_name(team_fbref)
            if not slug:
                continue

            mp = int(row.get("Playing Time_MP", 0) or 0)
            mins = int(row.get("Playing Time_Min", 0) or 0)
            n90s = max(mins / 90.0, 0.1)
            assists = int(row.get("Performance_Ast", 0) or 0)

            entry = {
                "player": player,
                "assists": assists,
                "assists_per_90": round(assists / n90s, 2),
                "matches_played": mp,
                "minutes": mins,
                "goals": int(row.get("Performance_Gls", 0) or 0),
                "g_plus_a": int(row.get("Performance_G+A", 0) or 0),
                "yellow_cards": int(row.get("Performance_CrdY", 0) or 0),
                "red_cards": int(row.get("Performance_CrdR", 0) or 0),
            }

            if slug not in all_data:
                all_data[slug] = {}
            if "passing" not in all_data[slug]:
                all_data[slug]["passing"] = []
            all_data[slug]["passing"].append(entry)

    PLAYER_STATS_PATH.write_text(json.dumps(all_data, ensure_ascii=False, indent=2), encoding="utf-8")
    total_players = sum(len(d.get("passing", [])) for d in all_data.values())
    print(f"\nTotal equipos: {len(all_data)}, total jugadores: {total_players}")
    print(f"Datos guardados en {PLAYER_STATS_PATH}")

if __name__ == "__main__":
    main()
