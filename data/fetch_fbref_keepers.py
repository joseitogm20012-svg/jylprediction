#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Obtiene estadísticas de PORTEROS por jugador desde FBref (Mundiales 2018, 2022, 2026)
usando soccerdata (stat_type='keeper'). Escribe en data/player_stats.json bajo 'keepers'.

Campos: player, clean_sheets, saves, goals_against, saves_per_90, save_pct
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
    print("  FBref Goalkeeper Stats Scraper")
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
            df = fbref.read_player_season_stats(stat_type="keeper")
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

            entry = {
                "player": player,
                "clean_sheets": int(row.get("Performance_CS", 0) or 0),
                "saves": int(row.get("Performance_Saves", 0) or 0),
                "goals_against": int(row.get("Performance_GA", 0) or 0),
                "goals_against_per_90": round(float(row.get("Performance_GA90", 0) or 0), 2),
                "shots_on_target_against": int(row.get("Performance_SoTA", 0) or 0),
                "save_pct": round(float(row.get("Performance_Save%", 0) or 0), 1),
                "matches_played": int(row.get("Playing Time_MP", 0) or 0),
                "minutes": int(row.get("Playing Time_Min", 0) or 0),
            }

            if slug not in all_data:
                all_data[slug] = {}
            if "keepers" not in all_data[slug]:
                all_data[slug]["keepers"] = []
            all_data[slug]["keepers"].append(entry)

    PLAYER_STATS_PATH.write_text(json.dumps(all_data, ensure_ascii=False, indent=2), encoding="utf-8")
    total_keepers = sum(len(d.get("keepers", [])) for d in all_data.values())
    print(f"\nTotal equipos: {len(all_data)}, total porteros: {total_keepers}")
    print(f"Datos guardados en {PLAYER_STATS_PATH}")

if __name__ == "__main__":
    main()
