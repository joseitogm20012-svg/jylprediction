#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Obtiene estadísticas de TARJETAS (amarillas y rojas) del Mundial desde FBref
(2018, 2022, 2026) y las añade al archivo xg_by_team.json existente.

Nuevos campos que añade a cada equipo en xg_by_team.json:
    - yellow_cards_per_90    : Tarjetas amarillas por 90 min (a favor del rival = recibidas)
    - red_cards_per_90       : Tarjetas rojas por 90 min
    - fouls_committed_per_90 : Faltas cometidas por 90 min
    - fouls_drawn_per_90     : Faltas recibidas por 90 min
    - discipline_index       : Índice de agresividad 0-10 (amarilla=1pt, roja=3pts por 90min)

Uso:
    python data/fetch_fbref_cards.py

Requisitos (ya los tienes):
    pip install soccerdata beautifulsoup4
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

# ── Mismo mapeo que fetch_fbref_xg.py ────────────────────────────────────────
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


# ── Lógica principal de scraping ──────────────────────────────────────────────

def fetch_cards_from_misc(fbref, season: str, weight: float) -> dict:
    """
    Descarga la tabla 'misc' (miscellaneous) de FBref para un Mundial.
    Contiene: tarjetas amarillas, rojas, faltas cometidas y recibidas.

    La tabla tiene dos secciones: 'for' (lo que hace el equipo) y 'against'
    (lo que hace el rival contra ese equipo). Usamos 'for' para las faltas
    cometidas y tarjetas recibidas.

    Retorna dict: { team_slug: { yellow, red, fouls_committed, fouls_drawn, nineties } }
    """
    # Columnas de la tabla misc en FBref
    # data-stat names: CrdY, CrdR, Fls, Fld, 90s
    result = {}

    try:
        # soccerdata descarga la tabla misc completa
        df_misc = fbref.read_team_season_stats(stat_type="misc")

        if df_misc is None or df_misc.empty:
            print(f"  [{season}] Sin tabla misc disponible.")
            return result

        df = df_misc.reset_index()

        # Buscar las columnas con nombres tipo MultiIndex
        # FBref misc tiene: ('Performance', 'CrdY'), ('Performance', 'CrdR'),
        #                   ('Performance', 'Fls'), ('Performance', 'Fld')
        COL_TEAM  = ('team', '')
        COL_90S   = ('90s', '')
        COL_CRDY  = ('Performance', 'CrdY')   # Tarjetas amarillas
        COL_CRDR  = ('Performance', 'CrdR')   # Tarjetas rojas
        COL_FLS   = ('Performance', 'Fls')    # Faltas cometidas
        COL_FLD   = ('Performance', 'Fld')    # Faltas recibidas

        rows_ok = 0
        for _, row in df.iterrows():
            try:
                team_name = str(row.get(COL_TEAM, "")).strip()
                if not team_name or team_name == "nan":
                    continue

                slug = to_slug(team_name)

                def safe_float(col, default=0.0):
                    val = row.get(col)
                    if val is None:
                        return default
                    try:
                        return float(val)
                    except (ValueError, TypeError):
                        return default

                nineties        = safe_float(COL_90S, 1.0)
                yellow_cards    = safe_float(COL_CRDY)
                red_cards       = safe_float(COL_CRDR)
                fouls_committed = safe_float(COL_FLS)
                fouls_drawn     = safe_float(COL_FLD)

                if nineties <= 0:
                    continue

                result[slug] = {
                    "yellow_per_90":   yellow_cards    / nineties,
                    "red_per_90":      red_cards       / nineties,
                    "fouls_comm_per_90": fouls_committed / nineties,
                    "fouls_drawn_per_90": fouls_drawn    / nineties,
                    "weight":          weight,
                    "nineties":        nineties,
                }
                rows_ok += 1

            except Exception:
                continue

        print(f"  [{season}] Tarjetas OK → {rows_ok} equipos")
        return result

    except Exception as e:
        print(f"  [{season}] Error descargando misc: {e}")
        return result


def fetch_fbref_cards() -> dict:
    """
    Descarga tarjetas de los Mundiales 2018, 2022 y 2026.
    Devuelve dict ponderado por equipo: { slug: { yellow_cards_per_90, ... } }
    """
    try:
        import soccerdata as sd
    except ImportError:
        print("ERROR: soccerdata no instalado. Ejecuta: pip install soccerdata")
        return {}

    print("=" * 60)
    print("  FBref Cards Fetcher — JLY Predictor")
    print("  Mundiales: 2018, 2022, 2026")
    print("=" * 60)

    # Peso por temporada — mismo criterio que fetch_fbref_xg.py
    SEASON_WEIGHT = {"2026": 1.0, "2022": 0.85, "2018": 0.65}

    # Acumulador ponderado
    # { slug: { yellow_sum, red_sum, fouls_comm_sum, fouls_drawn_sum, weight_sum } }
    acc = {}

    for season, weight in SEASON_WEIGHT.items():
        print(f"\n[{season}] Descargando tarjetas (peso={weight})...")
        try:
            fbref = sd.FBref(leagues=["INT-World Cup"], seasons=[season])
            season_data = fetch_cards_from_misc(fbref, season, weight)

            for slug, vals in season_data.items():
                if slug not in acc:
                    acc[slug] = {
                        "yellow_sum":      0.0,
                        "red_sum":         0.0,
                        "fouls_comm_sum":  0.0,
                        "fouls_drawn_sum": 0.0,
                        "weight_sum":      0.0,
                        "seasons":         []
                    }

                w = vals["weight"]
                acc[slug]["yellow_sum"]      += vals["yellow_per_90"]    * w
                acc[slug]["red_sum"]         += vals["red_per_90"]       * w
                acc[slug]["fouls_comm_sum"]  += vals["fouls_comm_per_90"]  * w
                acc[slug]["fouls_drawn_sum"] += vals["fouls_drawn_per_90"] * w
                acc[slug]["weight_sum"]      += w
                if season not in acc[slug]["seasons"]:
                    acc[slug]["seasons"].append(season)

        except Exception as e:
            print(f"  [{season}] Error general: {e}")
            continue

    if not acc:
        print("\nERROR: No se obtuvieron datos de tarjetas.")
        return {}

    # Calcular promedios ponderados finales
    result = {}
    for slug, data in acc.items():
        w_total = data["weight_sum"]
        if w_total <= 0:
            continue

        yellow = data["yellow_sum"] / w_total
        red    = data["red_sum"]    / w_total
        fouls_comm  = data["fouls_comm_sum"]  / w_total
        fouls_drawn = data["fouls_drawn_sum"] / w_total

        # Índice de disciplina: amarilla=1pt, roja=3pts por 90min
        # Escala 0-10 (promedio mundial ≈ 2.5-3 puntos → índice ≈ 5)
        raw_index = (yellow * 1.0 + red * 3.0)
        discipline_index = round(min(10.0, raw_index / 0.7), 2)  # normalizado

        result[slug] = {
            "yellow_cards_per_90":    round(yellow,       3),
            "red_cards_per_90":       round(red,          3),
            "fouls_committed_per_90": round(fouls_comm,   3),
            "fouls_drawn_per_90":     round(fouls_drawn,  3),
            "discipline_index":       discipline_index,
            "card_seasons":           data["seasons"],
        }

    print(f"\nEquipos con datos de tarjetas: {len(result)}")

    # Preview top 10 más agresivos
    top = sorted(result.items(), key=lambda x: x[1]["discipline_index"], reverse=True)[:10]
    print("\nTop 10 más agresivos (discipline_index):")
    for slug, d in top:
        print(f"  {slug:<25}  🟨 {d['yellow_cards_per_90']:.2f}/90  "
              f"🟥 {d['red_cards_per_90']:.3f}/90  "
              f"Índice: {d['discipline_index']:.1f}")

    return result


# ── Integración con xg_by_team.json ──────────────────────────────────────────

def merge_cards_into_existing(cards_data: dict) -> dict:
    """
    Carga xg_by_team.json y añade/actualiza los campos de tarjetas.
    No toca ningún campo existente (xg, corners, shots...).
    """
    if not XG_OUTPUT.exists():
        print(f"\nERROR: No existe {XG_OUTPUT}")
        print("Ejecuta primero fetch_fbref_xg.py para crear el archivo base.")
        return {}

    with open(XG_OUTPUT, "r", encoding="utf-8") as f:
        existing = json.load(f)

    teams = existing.get("teams", {})

    updated  = 0
    added_to_new = 0

    for slug, card_stats in cards_data.items():
        if slug in teams:
            # Equipo ya existe: solo añadir campos de tarjetas
            teams[slug]["yellow_cards_per_90"]    = card_stats["yellow_cards_per_90"]
            teams[slug]["red_cards_per_90"]        = card_stats["red_cards_per_90"]
            teams[slug]["fouls_committed_per_90"]  = card_stats["fouls_committed_per_90"]
            teams[slug]["fouls_drawn_per_90"]       = card_stats["fouls_drawn_per_90"]
            teams[slug]["discipline_index"]         = card_stats["discipline_index"]
            teams[slug]["card_seasons"]             = card_stats["card_seasons"]
            updated += 1
        else:
            # Equipo nuevo (solo en misc, no en shooting) — añadir con campos vacíos
            teams[slug] = {
                "xg_overall": None,
                "xg_home": None,
                "xg_away": None,
                "xga_overall": None,
                "shots_per_90": None,
                "crosses_per_90": None,
                "corners_for_per_90": None,
                "corners_against_per_90": None,
                "shots_blocked_per_90": None,
                "shots_off_target_per_90": None,
                "source": "cards_only",
                **card_stats
            }
            added_to_new += 1

    print(f"\nEquipos actualizados con tarjetas: {updated}")
    print(f"Equipos nuevos (solo tarjetas):    {added_to_new}")
    print(f"Total equipos en base de datos:    {len(teams)}")

    existing["teams"] = teams
    existing["last_updated"] = datetime.now().isoformat()
    existing["cards_note"] = (
        "Tarjetas obtenidas de FBref misc stats (Mundiales 2018+2022+2026, "
        "ponderado por recencia). discipline_index = amarillas*1 + rojas*3 por 90min, normalizado 0-10."
    )

    return existing


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    print("\n" + "=" * 60)
    print("  fetch_fbref_cards.py — JLY Predictor")
    print("  Tarjetas, faltas e índice de disciplina del Mundial")
    print("=" * 60 + "\n")

    # 1. Descargar tarjetas
    cards_data = fetch_fbref_cards()

    if not cards_data:
        print("\nNo se obtuvieron datos. El archivo xg_by_team.json no ha sido modificado.")
        return 1

    # 2. Fusionar con xg_by_team.json existente
    print("\nFusionando con xg_by_team.json...")
    merged = merge_cards_into_existing(cards_data)

    if not merged:
        return 1

    # 3. Guardar
    with open(XG_OUTPUT, "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Datos guardados en: {XG_OUTPUT}")
    print("   Nuevos campos por equipo:")
    print("     • yellow_cards_per_90")
    print("     • red_cards_per_90")
    print("     • fouls_committed_per_90")
    print("     • fouls_drawn_per_90")
    print("     • discipline_index  (0-10)")
    print("\nPróximo paso: usar discipline_index en predictor.py")
    print("para ajustar la probabilidad de penaltis y faltas estratégicas.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
