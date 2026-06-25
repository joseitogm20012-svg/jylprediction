#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
fetch_wc2026_missing.py  v2
---------------------------
Obtiene estadísticas de los 9 equipos WC2026 sin datos FBref.

Estrategia:
  1. SofaScore API con headers correctos
  2. Si falla, ClubElo / football-data.org (datos históricos recientes)
  3. Si todo falla, estimar desde resultados históricos de results.csv
     usando solo los últimos 4 años (2022-2026) para evitar el sesgo histórico.
"""
import json, sys, io, time, csv
from pathlib import Path
from datetime import datetime, date
import requests

if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE_DIR = Path(__file__).parent
XG_OUTPUT  = BASE_DIR / "xg_by_team.json"
RESULTS_CSV = BASE_DIR / "results.csv"

# ---- SofaScore Headers (browser-accurate) ----
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

MISSING_WC_TEAMS = {
    "venezuela": 7840,
    "hungary":   3165,
    "slovakia":  3168,
    "turkey":    3159,
    "honduras":  7839,
    "mali":      7848,
    "dr-congo":  36846,
    "indonesia": 7891,
    "ukraine":   3157,
}

# Slug -> how they appear in results.csv (home/away columns)
SLUG_TO_CSV_NAMES = {
    "venezuela": ["Venezuela"],
    "hungary":   ["Hungary"],
    "slovakia":  ["Slovakia"],
    "turkey":    ["Turkey"],
    "honduras":  ["Honduras"],
    "mali":      ["Mali"],
    "dr-congo":  ["DR Congo", "Congo DR", "Congo (DR)", "Democratic Republic of the Congo"],
    "indonesia": ["Indonesia"],
    "ukraine":   ["Ukraine"],
}

def try_sofascore(team_slug: str, team_id: int) -> dict | None:
    """Intenta obtener datos de SofaScore usando sesión de browser."""
    session = requests.Session()
    session.headers.update(SOFA_HEADERS)

    # First: get a cookie by visiting the team page
    try:
        landing = session.get(
            f"https://www.sofascore.com/team/football/{team_slug}/{team_id}",
            timeout=10,
            allow_redirects=True
        )
        print(f"    Landing page: {landing.status_code}")
    except Exception as e:
        print(f"    Error landing: {e}")

    time.sleep(1.0)

    try:
        url = f"https://api.sofascore.com/api/v1/team/{team_id}/events/last/0"
        r = session.get(url, timeout=12)
        print(f"    API response: {r.status_code}")
        if r.status_code == 200:
            data = r.json()
            events = data.get("events", [])
            if events:
                return _process_sofascore_events(team_slug, team_id, session, events)
    except Exception as e:
        print(f"    SofaScore error: {e}")

    return None


def _process_sofascore_events(team_slug, team_id, session, events):
    """Procesa los eventos de SofaScore y extrae estadísticas."""
    shots_list, corners_for_list, corners_against_list, crosses_list, sot_list = [], [], [], [], []

    for ev in events[:20]:
        event_id = ev.get("id")
        if not event_id:
            continue
        home_team_id = ev.get("homeTeam", {}).get("id")
        is_home = (home_team_id == team_id)

        time.sleep(0.5)
        try:
            sr = session.get(
                f"https://api.sofascore.com/api/v1/event/{event_id}/statistics",
                timeout=10
            )
            if sr.status_code != 200:
                continue

            groups = sr.json().get("statistics", [])
            stat_map = {}
            for g in groups:
                for item in g.get("statisticsItems", []):
                    stat_map[item.get("name", "").lower()] = (
                        item.get("homeValue"), item.get("awayValue")
                    )

            def gv(key):
                v = stat_map.get(key)
                if v is None:
                    return None
                return v[0] if is_home else v[1]

            def opp(key):
                v = stat_map.get(key)
                if v is None:
                    return None
                return v[1] if is_home else v[0]

            shots = gv("shots total") or gv("total shots")
            sot   = gv("shots on target") or gv("on target")
            cf    = gv("corner kicks") or gv("corners")
            ca    = opp("corner kicks") or opp("corners")
            crs   = gv("total crosses") or gv("crosses")

            if shots: shots_list.append(float(shots))
            if sot:   sot_list.append(float(sot))
            if cf:    corners_for_list.append(float(cf))
            if ca:    corners_against_list.append(float(ca))
            if crs:   crosses_list.append(float(crs))

        except Exception:
            continue

    def avg(lst):
        return round(sum(lst) / len(lst), 3) if lst else None

    avg_shots = avg(shots_list)
    avg_cf    = avg(corners_for_list)
    avg_ca    = avg(corners_against_list)
    avg_crs   = avg(crosses_list)
    avg_sot   = avg(sot_list)

    if avg_shots is None and avg_cf is None:
        return None

    xg = round((avg_sot or 0) * 0.11, 3) if avg_sot else (round(avg_shots * 0.033, 3) if avg_shots else 1.10)
    avg_cf  = avg_cf  or round(4.5 * (0.5 * (avg_shots or 11.5) / 11.5 + 0.5), 3)
    avg_ca  = avg_ca  or 4.5
    avg_crs = avg_crs or 13.0

    print(f"    Shots={avg_shots} CF={avg_cf} CA={avg_ca} Crs={avg_crs} xG={xg}")
    return {
        "xg_overall": xg,
        "xg_home": round(xg * 1.08, 3),
        "xg_away": round(xg * 0.92, 3),
        "xga_overall": None,
        "shots_per_90": avg_shots or 11.5,
        "crosses_per_90": avg_crs,
        "corners_for_per_90": avg_cf,
        "corners_against_per_90": avg_ca,
        "shots_blocked_per_90": None,
        "shots_off_target_per_90": None,
        "matches_played": len(shots_list) or len(corners_for_list),
        "seasons": ["2024-25", "2025-26"],
        "source": "sofascore_qualifiers"
    }


def estimate_from_csv(team_slug: str) -> dict | None:
    """
    Estima estadísticas usando solo partidos recientes (2022-2026)
    del archivo results.csv. Calcula goles promedio como proxy de xG.
    Asigna corners/tiros por defecto para selecciones activas.
    """
    csv_names = SLUG_TO_CSV_NAMES.get(team_slug)
    if not csv_names or not RESULTS_CSV.exists():
        return None

    cutoff_date = date(2022, 1, 1)

    gs_list, gc_list = [], []

    with open(RESULTS_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                row_date = datetime.strptime(row.get("date", ""), "%Y-%m-%d").date()
            except ValueError:
                continue
            if row_date < cutoff_date:
                continue

            home = row.get("home_team", "")
            away = row.get("away_team", "")
            hg   = row.get("home_score", "") or row.get("home_goals", "")
            ag   = row.get("away_score", "") or row.get("away_goals", "")

            try:
                hg, ag = int(hg), int(ag)
            except (ValueError, TypeError):
                continue

            if home in csv_names:
                gs_list.append(hg)
                gc_list.append(ag)
            elif away in csv_names:
                gs_list.append(ag)
                gc_list.append(hg)

    if len(gs_list) < 3:
        print(f"    Solo {len(gs_list)} partidos recientes en CSV — insuficiente")
        return None

    avg_gs = sum(gs_list) / len(gs_list)
    avg_gc = sum(gc_list) / len(gc_list)

    # xG proxy: goals scored + 0.3 * goals conceded (regression to mean)
    xg = round(avg_gs * 0.9 + 0.15, 3)
    xg = max(0.5, min(2.5, xg))

    # Corner estimation based on xG level (calibrated to WC averages)
    xg_ratio = xg / 1.35
    corners_for = round(4.5 * xg_ratio, 3)
    corners_against = round(4.5 / xg_ratio, 3) if xg_ratio > 0 else 4.5

    # Clamp to realistic ranges
    corners_for     = max(2.5, min(7.5, corners_for))
    corners_against = max(2.5, min(7.5, corners_against))

    shots_est = round(11.5 * xg_ratio, 2)

    print(f"    CSV ({len(gs_list)} partidos 2022-2026): xG={xg} CF={corners_for} CA={corners_against} Sh={shots_est}")
    return {
        "xg_overall": xg,
        "xg_home": round(xg * 1.08, 3),
        "xg_away": round(xg * 0.92, 3),
        "xga_overall": round(avg_gc, 3),
        "shots_per_90": shots_est,
        "crosses_per_90": 13.0,
        "corners_for_per_90": corners_for,
        "corners_against_per_90": corners_against,
        "shots_blocked_per_90": None,
        "shots_off_target_per_90": None,
        "matches_played": len(gs_list),
        "seasons": ["2022-2026"],
        "source": "csv_recent_4yr"
    }


def main():
    print("\n" + "=" * 60)
    print("  WC 2026 Missing Teams - Fetcher v2")
    print("=" * 60)

    existing = {}
    if XG_OUTPUT.exists():
        with open(XG_OUTPUT, "r", encoding="utf-8") as f:
            existing = json.load(f).get("teams", {})

    updated = 0
    results = {}

    for team_slug, team_id in MISSING_WC_TEAMS.items():
        cur_source = existing.get(team_slug, {}).get("source", "unknown")
        print(f"\n[{team_slug}] Fuente actual: {cur_source}")

        if cur_source == "fbref_world_cup":
            print("  -> Conservando datos FBref (no se degradan)")
            continue

        # Strategy 1: SofaScore
        print("  -> Intentando SofaScore...")
        stats = try_sofascore(team_slug, team_id)

        # Strategy 2: CSV recent
        if not stats:
            print("  -> Intentando CSV reciente (2022-2026)...")
            stats = estimate_from_csv(team_slug)

        if stats:
            existing[team_slug] = stats
            updated += 1
            print(f"  ✓ Actualizado con source={stats['source']}")
        else:
            print(f"  ✗ Sin cambios — se mantiene historial")

        time.sleep(1.5)

    print(f"\n{'='*60}")
    print(f"Actualizados: {updated}/{len(MISSING_WC_TEAMS)}")

    if updated > 0:
        fbref_count = len([t for t in existing.values() if t.get("source") == "fbref_world_cup"])
        sofascore_count = len([t for t in existing.values() if t.get("source") == "sofascore_qualifiers"])
        csv_count = len([t for t in existing.values() if t.get("source") == "csv_recent_4yr"])

        output = {
            "last_updated": datetime.now().isoformat(),
            "methodology": (
                "xG calculado desde datos reales del Mundial (FBref), eliminatorias (SofaScore) "
                "o partidos recientes 2022-2026 (CSV). "
                "source='fbref_world_cup'=datos Copa del Mundo reales. "
                "source='sofascore_qualifiers'=datos eliminatorias SofaScore. "
                "source='csv_recent_4yr'=estimación desde resultados 2022-2026."
            ),
            "fbref_teams_count": fbref_count,
            "sofascore_teams_count": sofascore_count,
            "csv_recent_teams_count": csv_count,
            "total_teams": len(existing),
            "teams": existing
        }
        with open(XG_OUTPUT, "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        print(f"✓ Guardado en {XG_OUTPUT}")
        print(f"  FBref WC:    {fbref_count}")
        print(f"  SofaScore:   {sofascore_count}")
        print(f"  CSV reciente:{csv_count}")
    else:
        print("Sin cambios.")

    return 0

if __name__ == "__main__":
    sys.exit(main())
