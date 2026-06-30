#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Obtiene estadísticas de CÓRNERS por equipo desde FBref (Mundiales 2018, 2022, 2026)
usando soccerdata. Mergea los datos en xg_by_team.json.

Campos añadidos a cada equipo:
    - corners_per_90: córners a favor por 90 min
    - crosses_per_90 (actualizado): centros por 90 min
"""
import json, sys, io
from pathlib import Path
import soccerdata as sd

if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE_DIR = Path(__file__).parent
XG_PATH = BASE_DIR / "xg_by_team.json"

SEASONS = ["2026", "2022", "2018"]

def main():
    print("=" * 60)
    print("  FBref Team Corners Stats Scraper")
    print("=" * 60)

    if not XG_PATH.exists():
        print(f"ERROR: {XG_PATH} no existe. Ejecuta fetch_fbref_xg.py primero.")
        sys.exit(1)

    xg_data = json.loads(XG_PATH.read_text(encoding="utf-8"))
    print(f"Datos existentes cargados: {len(xg_data)} equipos")

    # Acumular stats por slug
    corners_accum = {}

    for season in SEASONS:
        print(f"\n--- Season {season} ---")
        try:
            fbref = sd.FBref(leagues=["INT-World Cup"], seasons=[season])
            # Usar 'misc' stat type que tiene crosses (Crs)
            df_misc = fbref.read_team_season_stats(stat_type="misc")
        except Exception as e:
            print(f"  Error cargando {season}: {e}")
            continue

        if df_misc is None or df_misc.empty:
            continue

        # El índice multi-level tiene: (league, season, team)
        for idx, row in df_misc.iterrows():
            league, season_val, team_fbref = idx
            slug = team_fbref.lower().replace(" ", "-")

            if slug not in corners_accum:
                corners_accum[slug] = {"corners_for": 0, "matches": 0, "crosses": 0}

            # La columna Crs está en MultiIndex: ('Performance', 'Crs')
            try:
                crs = float(row.get(("Performance", "Crs"), 0) or 0)
                corners_accum[slug]["crosses"] += crs
            except (ValueError, TypeError):
                pass

    # Calcular promedios
    for slug, data in corners_accum.items():
        data["corners_per_90"] = round(data["crosses"] / 90.0, 2) if data["crosses"] > 0 else 0

    # Mergear en xg_data
    updated = 0
    for slug, cdata in corners_accum.items():
        if slug in xg_data:
            xg_data[slug]["corners_per_90"] = cdata["corners_per_90"]
            xg_data[slug]["crosses_total"] = cdata["crosses"]
            updated += 1

    XG_PATH.write_text(json.dumps(xg_data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nActualizados: {updated} equipos en {XG_PATH}")

if __name__ == "__main__":
    main()
