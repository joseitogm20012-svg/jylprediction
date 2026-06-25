#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Obtiene estadisticas REALES de tiro del Mundial desde FBref (2018, 2022, 2026)
usando soccerdata, y calcula un proxy de xG basado en rendimiento real
en Copa del Mundo (goles/90min, precision de remate).

NOTA: FBref no publica xG oficial para el Mundial, pero si los goles reales,
tiros y precision de remate por equipo, que son datos mas fiables que las
estimaciones históricas del modelo anterior.

Uso:
    python data/fetch_fbref_xg.py

Requiere:
    pip install soccerdata pandas
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

# Mapeo nombre FBref -> slug proyecto
FBREF_NAME_TO_SLUG = {
    "United States": "usa",
    "Mexico": "mexico",
    "Canada": "canada",
    "Panama": "panama",
    "Honduras": "honduras",
    "Costa Rica": "costa-rica",
    "Jamaica": "jamaica",
    "Haiti": "haiti",
    "Trinidad and Tobago": "trinidad-and-tobago",
    "Guatemala": "guatemala",
    "El Salvador": "el-salvador",
    "Curacao": "curacao",
    "Curazao": "curacao",
    "Argentina": "argentina",
    "Brazil": "brazil",
    "Colombia": "colombia",
    "Ecuador": "ecuador",
    "Paraguay": "paraguay",
    "Uruguay": "uruguay",
    "Chile": "chile",
    "Peru": "peru",
    "Bolivia": "bolivia",
    "Venezuela": "venezuela",
    "Germany": "germany",
    "Austria": "austria",
    "Belgium": "belgium",
    "Bosnia and Herzegovina": "bosnia-and-herzegovina",
    "Croatia": "croatia",
    "Scotland": "scotland",
    "Spain": "spain",
    "France": "france",
    "England": "england",
    "Norway": "norway",
    "Netherlands": "netherlands",
    "Poland": "poland",
    "Portugal": "portugal",
    "Czech Republic": "czech-republic",
    "Czechia": "czech-republic",
    "Sweden": "sweden",
    "Switzerland": "switzerland",
    "Turkey": "turkey",
    "Serbia": "serbia",
    "Denmark": "denmark",
    "Iceland": "iceland",
    "Wales": "wales",
    "Russia": "russia",
    "Ukraine": "ukraine",
    "Slovakia": "slovakia",
    "Slovenia": "slovenia",
    "Hungary": "hungary",
    "Romania": "romania",
    "Greece": "greece",
    "Albania": "albania",
    "North Macedonia": "north-macedonia",
    "Finland": "finland",
    "Georgia": "georgia",
    "Kosovo": "kosovo",
    "Armenia": "armenia",
    "Azerbaijan": "azerbaijan",
    "Saudi Arabia": "saudi-arabia",
    "Australia": "australia",
    "Qatar": "qatar",
    "South Korea": "south-korea",
    "Korea Republic": "south-korea",
    "United Arab Emirates": "uae",
    "Iraq": "iraq",
    "IR Iran": "iran",
    "Iran": "iran",
    "Japan": "japan",
    "Jordan": "jordan",
    "China PR": "china",
    "Uzbekistan": "uzbekistan",
    "Kazakhstan": "kazakhstan",
    "Algeria": "algeria",
    "Cape Verde": "cape-verde",
    "Ivory Coast": "ivory-coast",
    "Cote d'Ivoire": "ivory-coast",
    "Egypt": "egypt",
    "Ghana": "ghana",
    "Morocco": "morocco",
    "DR Congo": "dr-congo",
    "Democratic Republic of the Congo": "dr-congo",
    "South Africa": "south-africa",
    "Tunisia": "tunisia",
    "Senegal": "senegal",
    "Cameroon": "cameroon",
    "Nigeria": "nigeria",
    "Mali": "mali",
    "Burkina Faso": "burkina-faso",
    "New Zealand": "new-zealand",
}


def to_slug(name: str) -> str:
    clean = name.replace("\u00e7", "c").replace("\u00f4", "o").replace("\u2019", "'")
    if clean in FBREF_NAME_TO_SLUG:
        return FBREF_NAME_TO_SLUG[clean]
    if name in FBREF_NAME_TO_SLUG:
        return FBREF_NAME_TO_SLUG[name]
    return name.lower().replace(" ", "-").replace("'", "").replace(".", "")


def get_val(row, key_tuple, default=None):
    """Obtiene valor de fila con clave MultiIndex o simple."""
    if key_tuple in row.index:
        try:
            v = row[key_tuple]
            return float(v) if v is not None else default
        except (ValueError, TypeError):
            return default
    return default


def fetch_sofascore_team_stats(team_slug):
    """
    Intenta descargar estadísticas de SofaScore para una selección.
    Retorna (corners_for, corners_against, shots, blocked_shots, crosses) si tiene éxito,
    sino (None, None, None, None, None).
    """
    import requests
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.sofascore.com/",
        "Origin": "https://www.sofascore.com"
    }
    
    # Mapeos de slug a nombres comunes de búsqueda si es necesario
    search_name = team_slug.replace("-", " ").title()
    if team_slug == "usa":
        search_name = "USA"
    elif team_slug == "dr-congo":
        search_name = "DR Congo"
        
    search_url = f"https://api.sofascore.com/api/v1/search/all?q={search_name}"
    try:
        r = requests.get(search_url, headers=headers, timeout=5)
        if r.status_code == 200:
            data = r.json()
            for res in data.get("results", []):
                if res.get("type") == "team" and res.get("entity", {}).get("sport", {}).get("name") == "Football":
                    team_id = res["entity"]["id"]
                    # Obtener estadísticas del Mundial 2022 (tournament=1, season=41087)
                    stats_url = f"https://api.sofascore.com/api/v1/team/{team_id}/unique-tournament/1/season/41087/statistics/overall"
                    r_stats = requests.get(stats_url, headers=headers, timeout=5)
                    if r_stats.status_code == 200:
                        stats_data = r_stats.json().get("statistics", {})
                        matches = float(stats_data.get("matches", 1))
                        if matches > 0:
                            corners_for = float(stats_data.get("corners", 0)) / matches
                            shots = float(stats_data.get("shots", 0)) / matches
                            blocked = float(stats_data.get("blockedShots", 0)) / matches
                            crosses = float(stats_data.get("crosses", 0)) / matches
                            return corners_for, None, shots, blocked, crosses
    except Exception:
        pass
    return None, None, None, None, None


def fetch_fbref_wc_stats():
    """
    Descarga estadisticas reales del Mundial desde FBref.
    Calcula xG proxy basado en rendimiento y añade corners/tiros de resumen.
    """
    try:
        import soccerdata as sd
    except ImportError:
        print("ERROR: soccerdata no instalado.")
        return {}

    print("=" * 60)
    print("Descargando estadisticas del Mundial desde FBref")
    print("  Temporadas: 2018, 2022, 2026")
    print("  Fuente: FBref (datos reales de partidos)")
    print("=" * 60)

    # Columnas MultiIndex conocidas
    COL_TEAM  = ('team', '')
    COL_90S   = ('90s', '')
    COL_GLS   = ('Standard', 'Gls')
    COL_SH    = ('Standard', 'Sh')
    COL_SOT   = ('Standard', 'SoT')
    COL_GSH   = ('Standard', 'G/Sh')
    COL_GSOT  = ('Standard', 'G/SoT')
    COL_CRS   = ('Performance', 'Crs')

    # Peso por temporada (mas reciente = mas relevante)
    SEASON_WEIGHT = {"2026": 1.0, "2022": 0.85, "2018": 0.65}

    # Acumulador ponderado por equipo
    accumulator = {}

    for season in ["2026", "2022", "2018"]:
        sw = SEASON_WEIGHT[season]
        print(f"\n[{season}] Descargando (peso={sw})...")
        try:
            fbref = sd.FBref(leagues=["INT-World Cup"], seasons=[season])
            df_sh = fbref.read_team_season_stats(stat_type="shooting")
            df_misc = fbref.read_team_season_stats(stat_type="misc")

            if df_sh is None or df_sh.empty:
                print(f"  [{season}] Sin datos de tiro.")
                continue

            # Descargar tipos de pases y defensa a nivel torneo
            corners_for_map = {}
            corners_against_map = {}
            blocked_shots_map = {}
            
            try:
                url_passing = f"https://fbref.com/en/comps/1/{season}/passing_types/{season}-World-Cup-Stats"
                filepath_passing = fbref.data_dir / f"tournament_passing_types_{season}.html"
                reader_p = fbref.get(url_passing, filepath_passing)
                soup_p = BeautifulSoup(reader_p.read(), "html.parser")
                
                table_for = soup_p.find("table", id="stats_squads_passing_types_for")
                if table_for:
                    tbody = table_for.find("tbody")
                    if tbody:
                        for tr in tbody.find_all("tr"):
                            th = tr.find("th", {"data-stat": "team"})
                            if th:
                                tslug = to_slug(th.get_text().strip())
                                td_ck = tr.find("td", {"data-stat": "corner_kicks"})
                                td_90s = tr.find("td", {"data-stat": "minutes_90s"})
                                nineties = float(td_90s.get_text().strip()) if td_90s and td_90s.get_text().strip() else 1.0
                                ck_val = float(td_ck.get_text().strip()) if td_ck and td_ck.get_text().strip() else 0.0
                                corners_for_map[tslug] = ck_val / nineties
                                
                table_against = soup_p.find("table", id="stats_squads_passing_types_against")
                if table_against:
                    tbody = table_against.find("tbody")
                    if tbody:
                        for tr in tbody.find_all("tr"):
                            th = tr.find("th", {"data-stat": "team"})
                            if th:
                                tslug = to_slug(th.get_text().strip())
                                td_ck = tr.find("td", {"data-stat": "corner_kicks"})
                                td_90s = tr.find("td", {"data-stat": "minutes_90s"})
                                nineties = float(td_90s.get_text().strip()) if td_90s and td_90s.get_text().strip() else 1.0
                                ck_val = float(td_ck.get_text().strip()) if td_ck and td_ck.get_text().strip() else 0.0
                                corners_against_map[tslug] = ck_val / nineties
            except Exception as pe:
                print(f"  [{season}] Advertencia tipos de pase: {pe}")
                
            try:
                url_defense = f"https://fbref.com/en/comps/1/{season}/defense/{season}-World-Cup-Stats"
                filepath_defense = fbref.data_dir / f"tournament_defense_{season}.html"
                reader_d = fbref.get(url_defense, filepath_defense)
                soup_d = BeautifulSoup(reader_d.read(), "html.parser")
                
                table_def_against = soup_d.find("table", id="stats_squads_defense_against")
                if table_def_against:
                    tbody = table_def_against.find("tbody")
                    if tbody:
                        for tr in tbody.find_all("tr"):
                            th = tr.find("th", {"data-stat": "team"})
                            if th:
                                tslug = to_slug(th.get_text().strip().replace("vs ", ""))
                                td_blocked = tr.find("td", {"data-stat": "blocked_shots"})
                                td_90s = tr.find("td", {"data-stat": "minutes_90s"})
                                nineties = float(td_90s.get_text().strip()) if td_90s and td_90s.get_text().strip() else 1.0
                                blocked_val = float(td_blocked.get_text().strip()) if td_blocked and td_blocked.get_text().strip() else 0.0
                                blocked_shots_map[tslug] = blocked_val / nineties
            except Exception as de:
                print(f"  [{season}] Advertencia defensa: {de}")

            df = df_sh.copy()
            if df_misc is not None and not df_misc.empty:
                df[COL_CRS] = df_misc[COL_CRS]

            df = df.reset_index()
            rows_ok = 0

            for _, row in df.iterrows():
                try:
                    team_name = str(row.get(COL_TEAM, "")).strip()
                    if not team_name or team_name == "nan":
                        continue

                    team_slug = to_slug(team_name)

                    # Minutos jugados (en unidades de 90 min)
                    nineties = get_val(row, COL_90S, default=1.0)
                    if not nineties or nineties <= 0:
                        continue

                    gls    = get_val(row, COL_GLS, default=0.0)
                    sh     = get_val(row, COL_SH,  default=0.0)
                    sot    = get_val(row, COL_SOT, default=0.0)
                    crs    = get_val(row, COL_CRS, default=0.0)
                    
                    corners_for = corners_for_map.get(team_slug, 0.0)
                    corners_against = corners_against_map.get(team_slug, 0.0)
                    blocked_shots = blocked_shots_map.get(team_slug, 0.0)

                    # Proxy de xG
                    gls_per_90 = gls / nineties
                    avg_conv_rate = 0.096
                    if sh > 0:
                        shot_based_xg = (sh / nineties) * avg_conv_rate
                    else:
                        shot_based_xg = gls_per_90

                    xg_proxy = 0.60 * gls_per_90 + 0.40 * shot_based_xg

                    # Acumular
                    if team_slug not in accumulator:
                        accumulator[team_slug] = {
                            "xg_sum": 0.0,
                            "sh_sum": 0.0,
                            "sot_sum": 0.0,
                            "crs_sum": 0.0,
                            "corners_for_sum": 0.0,
                            "corners_against_sum": 0.0,
                            "blocked_shots_sum": 0.0,
                            "weight_sum": 0.0,
                            "match_count": 0,
                            "seasons": []
                        }

                    accumulator[team_slug]["xg_sum"] += xg_proxy * sw
                    accumulator[team_slug]["sh_sum"] += (sh / nineties) * sw
                    accumulator[team_slug]["sot_sum"] += (sot / nineties) * sw
                    accumulator[team_slug]["crs_sum"] += (crs / nineties) * sw
                    accumulator[team_slug]["corners_for_sum"] += corners_for * sw
                    accumulator[team_slug]["corners_against_sum"] += corners_against * sw
                    accumulator[team_slug]["blocked_shots_sum"] += blocked_shots * sw
                    accumulator[team_slug]["weight_sum"] += sw
                    accumulator[team_slug]["match_count"] += max(1, int(round(nineties)))
                    if season not in accumulator[team_slug]["seasons"]:
                        accumulator[team_slug]["seasons"].append(season)

                    rows_ok += 1

                except Exception:
                    continue

            print(f"  [{season}] OK -> {rows_ok} equipos")

        except Exception as e:
            print(f"  [{season}] Error: {e}")
            continue

    if not accumulator:
        print("\nERROR: No se obtuvieron datos de FBref.")
        return {}

    # Calcular xG y estadísticas de córner final ponderado
    result = {}
    for team_slug, acc in accumulator.items():
        if acc["weight_sum"] > 0:
            xg_final = acc["xg_sum"] / acc["weight_sum"]
            sh_final = acc["sh_sum"] / acc["weight_sum"]
            sot_final = acc["sot_sum"] / acc["weight_sum"]
            crs_final = acc["crs_sum"] / acc["weight_sum"]
            
            corners_for_final = acc["corners_for_sum"] / acc["weight_sum"]
            corners_against_final = acc["corners_against_sum"] / acc["weight_sum"]
            blocked_shots_final = acc["blocked_shots_sum"] / acc["weight_sum"]
            
            # Base off target calculation (Fase 1)
            off_target_final = max(0.0, sh_final - sot_final - blocked_shots_final)
            
            # Fallback Sofascore si corners son 0.0
            if corners_for_final == 0.0:
                sf_corners_for, _, sf_shots, sf_blocked, sf_crosses = fetch_sofascore_team_stats(team_slug)
                if sf_corners_for is not None:
                    corners_for_final = sf_corners_for
                    sh_final = sf_shots
                    crs_final = sf_crosses
                    blocked_shots_final = sf_blocked
                    # Estimate off target for fallback
                    off_target_final = max(0.0, sf_shots * 0.40)

            # Robust fallbacks if still 0.0 after all scraping attempts
            if corners_for_final == 0.0:
                cam = 0.4 * (sh_final / 11.5) + 0.6 * (crs_final / 13.0)
                corners_for_final = 4.5 * cam

            if corners_against_final == 0.0:
                corners_against_final = 4.5
            
            sh_blocked_val = round(blocked_shots_final, 3) if blocked_shots_final > 0 else None
            
            result[team_slug] = {
                "xg_overall": round(xg_final, 3),
                "xg_home":    round(xg_final * 1.08, 3),
                "xg_away":    round(xg_final * 0.92, 3),
                "xga_overall": None,
                "shots_per_90": round(sh_final, 3),
                "crosses_per_90": round(crs_final, 3),
                "corners_for_per_90": round(corners_for_final, 3) if corners_for_final > 0 else None,
                "corners_against_per_90": round(corners_against_final, 3) if corners_against_final > 0 else None,
                "shots_blocked_per_90": sh_blocked_val,
                "shots_off_target_per_90": round(off_target_final, 3) if off_target_final > 0 else None,
                "matches_played": acc["match_count"],
                "seasons": acc["seasons"],
                "source": "fbref_world_cup"
            }

    print(f"\nResultados obtenidos para {len(result)} selecciones:")
    for team, d in sorted(result.items(), key=lambda x: x[1]["xg_overall"], reverse=True)[:16]:
        seasons_str = "+".join(d["seasons"])
        print(f"  {team:<25}  xG/90={d['xg_overall']:.3f}  Sh/90={d['shots_per_90']:.2f}  Crs/90={d['crosses_per_90']:.2f}  [{seasons_str}]")

    return result


def merge_with_existing(fbref_stats: dict) -> dict:
    existing = {}
    if XG_OUTPUT.exists():
        with open(XG_OUTPUT, "r", encoding="utf-8") as f:
            data = json.load(f)
            existing = data.get("teams", {})

    print(f"\nFusionando con datos existentes ({len(existing)} equipos)...")

    merged = dict(existing)
    upgraded = 0
    added = 0

    for team_slug, new_data in fbref_stats.items():
        if team_slug in merged:
            old_source = merged[team_slug].get("source", "estimated")
            old_xg = merged[team_slug].get("xg_overall") or new_data["xg_overall"]
            old_xga = merged[team_slug].get("xga_overall")

            if old_source == "fbref_world_cup":
                blended_xg = new_data["xg_overall"]
            else:
                blended_xg = round(0.70 * new_data["xg_overall"] + 0.30 * old_xg, 3)

            merged[team_slug] = {
                "xg_home":    round(blended_xg * 1.08, 3),
                "xg_away":    round(blended_xg * 0.92, 3),
                "xg_overall": blended_xg,
                "xga_overall": old_xga,  # conservar xGA existente
                "shots_per_90": new_data["shots_per_90"],
                "crosses_per_90": new_data["crosses_per_90"],
                "corners_for_per_90": new_data.get("corners_for_per_90"),
                "corners_against_per_90": new_data.get("corners_against_per_90"),
                "shots_blocked_per_90": new_data.get("shots_blocked_per_90"),
                "shots_off_target_per_90": new_data.get("shots_off_target_per_90"),
                "matches_played": new_data["matches_played"],
                "seasons": new_data["seasons"],
                "source": "fbref_world_cup"
            }
            upgraded += 1
        else:
            merged[team_slug] = new_data
            added += 1

    print(f"  Actualizados con datos FBref WC: {upgraded}")
    print(f"  Equipos nuevos:                  {added}")
    print(f"  Total en base de datos:          {len(merged)}")
    return merged


def main():
    print("\n" + "=" * 60)
    print("  FBref World Cup Stats Fetcher - Predictor Mundial 2026")
    print("=" * 60)

    fbref_stats = fetch_fbref_wc_stats()

    if not fbref_stats:
        print("\nNo se pudieron obtener datos de FBref.")
        print("El archivo xg_by_team.json no ha sido modificado.")
        return 1

    merged = merge_with_existing(fbref_stats)

    output = {
        "last_updated": datetime.now().isoformat(),
        "methodology": (
            "xG calculado a partir de datos reales del Mundial en FBref "
            "(goles/90min + eficiencia de remate), mezclado con historial estimado. "
            "source='fbref_world_cup' indica datos reales de Copa del Mundo."
        ),
        "fbref_teams_count": len(fbref_stats),
        "total_teams": len(merged),
        "teams": merged
    }

    with open(XG_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"\nDatos guardados en: {XG_OUTPUT}")
    print(f"  Equipos con datos FBref WC: {len(fbref_stats)}")
    print(f"  Total en base de datos:     {len(merged)}")
    print("\nListo! El predictor usa rendimiento real del Mundial para calcular xG.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
