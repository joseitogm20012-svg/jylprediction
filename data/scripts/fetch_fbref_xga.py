#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Obtiene estadísticas de xGA (Expected Goals Against / Goles Esperados en Contra)
desde FBref (Mundiales 2018, 2022, 2026) y las consolida en xg_by_team.json.

Uso:
    python data/fetch_fbref_xga.py
"""

import json
import sys
import io
import os
from pathlib import Path
from datetime import datetime
from bs4 import BeautifulSoup

# Forzar salida UTF-8 en Windows
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE_DIR = Path(__file__).parent
XG_OUTPUT = BASE_DIR / "xg_by_team.json"

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

def to_slug(name: str) -> str:
    clean = name.replace("\u00e7", "c").replace("\u00f4", "o").replace("\u2019", "'")
    if clean in FBREF_NAME_TO_SLUG:
        return FBREF_NAME_TO_SLUG[clean]
    if name in FBREF_NAME_TO_SLUG:
        return FBREF_NAME_TO_SLUG[name]
    return name.lower().replace(" ", "-").replace("'", "").replace(".", "")

def fetch_xga_for_season(fbref, season: str, weight: float) -> dict:
    result = {}
    filename = fbref.data_dir / f"teams_INT-World Cup_{season}_shooting.html"
    
    try:
        # Check if the soccerdata cached shooting file exists
        if filename.exists():
            print(f"  [{season}] Leyendo archivo de caché local: {filename.name}")
            with open(filename, "r", encoding="utf-8") as f:
                html_content = f.read()
            soup = BeautifulSoup(html_content, "html.parser")
        else:
            # Fallback to download if cache is missing
            url = f"https://fbref.com/en/comps/1/{season}/shooting/{season}-World-Cup-Stats"
            alt_filename = fbref.data_dir / f"tournament_shooting_{season}.html"
            print(f"  [{season}] Descargando desde FBref...")
            reader = fbref.get(url, alt_filename)
            soup = BeautifulSoup(reader.read(), "html.parser")
            
        table = soup.find("table", id="stats_squads_shooting_against")
        
        if not table:
            print(f"  [{season}] No se encontró la tabla de disparos en contra (stats_squads_shooting_against).")
            return result
            
        tbody = table.find("tbody")
        rows_ok = 0
        for tr in tbody.find_all("tr"):
            th = tr.find("th", {"data-stat": "team"})
            if not th:
                continue
                
            team_name = th.get_text().strip()
            if not team_name:
                continue
                
            # Clean "vs " prefix from team name in the against table
            if "vs " in team_name:
                team_name = team_name.split("vs ")[-1].strip()
                
            slug = to_slug(team_name)
            
            td_goals = tr.find("td", {"data-stat": "goals"})
            td_shots = tr.find("td", {"data-stat": "shots"})
            td_90s = tr.find("td", {"data-stat": "minutes_90s"})
            
            try:
                nineties = float(td_90s.get_text().strip()) if td_90s and td_90s.get_text().strip() else 1.0
                goals_val = float(td_goals.get_text().strip()) if td_goals and td_goals.get_text().strip() else 0.0
                shots_val = float(td_shots.get_text().strip()) if td_shots and td_shots.get_text().strip() else 0.0
                
                if nineties <= 0:
                    continue
                    
                # Calculate xGA proxy using goals and shots against (consistent with fetch_fbref_xg.py)
                goals_per_90 = goals_val / nineties
                shot_based_xga = (shots_val / nineties) * 0.096 if shots_val > 0 else goals_per_90
                xga_proxy = 0.60 * goals_per_90 + 0.40 * shot_based_xga
                
                result[slug] = {
                    "xga_per_90": xga_proxy,
                    "nineties": nineties,
                    "weight": weight
                }
                rows_ok += 1
            except Exception:
                continue
                
        print(f"  [{season}] xGA OK → {rows_ok} equipos")
        return result
    except Exception as e:
        print(f"  [{season}] Error descargando xGA: {e}")
        return result

def fetch_fbref_xga() -> dict:
    try:
        import soccerdata as sd
    except ImportError:
        print("ERROR: soccerdata no instalado.")
        return {}

    print("=" * 60)
    print("  FBref xGA Fetcher — JLY Predictor")
    print("  Mundiales: 2018, 2022, 2026")
    print("=" * 60)

    SEASON_WEIGHT = {"2026": 1.0, "2022": 0.85, "2018": 0.65}
    acc = {}

    for season, weight in SEASON_WEIGHT.items():
        print(f"\n[{season}] Descargando xGA (peso={weight})...")
        try:
            fbref = sd.FBref(leagues=["INT-World Cup"], seasons=[season])
            season_data = fetch_xga_for_season(fbref, season, weight)
            
            for slug, vals in season_data.items():
                if slug not in acc:
                    acc[slug] = {
                        "xga_sum": 0.0,
                        "weight_sum": 0.0,
                        "seasons": []
                    }
                acc[slug]["xga_sum"] += vals["xga_per_90"] * vals["weight"]
                acc[slug]["weight_sum"] += vals["weight"]
                if season not in acc[slug]["seasons"]:
                    acc[slug]["seasons"].append(season)
        except Exception as e:
            print(f"  [{season}] Error general: {e}")
            continue

    result = {}
    for slug, data in acc.items():
        w_total = data["weight_sum"]
        if w_total <= 0:
            continue
        xga_avg = data["xga_sum"] / w_total
        result[slug] = {
            "xga_overall": round(xga_avg, 3),
            "xga_seasons": data["seasons"]
        }
        
    print(f"\nEquipos con datos de xGA: {len(result)}")
    return result

def merge_xga_into_existing(xga_data: dict) -> dict:
    if not XG_OUTPUT.exists():
        print(f"\nERROR: No existe {XG_OUTPUT}")
        return {}

    with open(XG_OUTPUT, "r", encoding="utf-8") as f:
        existing = json.load(f)

    teams = existing.get("teams", {})
    updated = 0

    for slug, xga_stats in xga_data.items():
        if slug in teams:
            teams[slug]["xga_overall"] = xga_stats["xga_overall"]
            teams[slug]["xga_seasons"] = xga_stats["xga_seasons"]
            updated += 1
        else:
            # Equipo nuevo
            teams[slug] = {
                "xg_overall": None,
                "xg_home": None,
                "xg_away": None,
                "xga_overall": xga_stats["xga_overall"],
                "xga_seasons": xga_stats["xga_seasons"],
                "shots_per_90": None,
                "crosses_per_90": None,
                "corners_for_per_90": None,
                "corners_against_per_90": None,
                "shots_blocked_per_90": None,
                "shots_off_target_per_90": None,
                "source": "xga_only"
            }

    print(f"\nEquipos actualizados con xGA: {updated}")
    existing["teams"] = teams
    existing["last_updated"] = datetime.now().isoformat()
    return existing

def main():
    cards_data = fetch_fbref_xga()
    if not cards_data:
        print("\nNo se obtuvieron datos de xGA.")
        return 1

    print("\nFusionando con xg_by_team.json...")
    merged = merge_xga_into_existing(cards_data)
    if not merged:
        return 1

    with open(XG_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Datos de xGA guardados con éxito en: {XG_OUTPUT}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
