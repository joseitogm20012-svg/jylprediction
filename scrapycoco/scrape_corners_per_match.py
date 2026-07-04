#!/usr/bin/env python3
"""
scrape_corners_per_match.py
----------------------------
Scraper de córners por partido para todos los equipos WC2026.

FUENTES DISPONIBLES:
  - SofaScore API  → api.sofascore.com  (actualmente BLOQUEADA, 403)
  - FBref          → fbref.com          (actualmente BLOQUEADO, 403)
  - FlashScore     → flashscore.com     (requiere Playwright)

ESTADO ACTUAL (Julio 2026):
  Todas las fuentes principales de datos de fútbol están bloqueando scraping
  automatizado (Cloudflare, rate limiting agresivo). Este script contiene la
  estructura y lógica para cuando una fuente esté disponible.

ARQUITECTURA (cuando funcione):
  1. Cargar sofascore_team_ids.json → mapeo slug → SofaScore ID
  2. Por cada equipo:
     a. GET /team/{id}/events/last/0  → partidos recientes
     b. Por cada partido completado:
        - GET /event/{event_id}/statistics → estadísticas
        - Extraer "corner kicks" / "corners"
        - Guardar en per_match_corners.json
  3. Deducir partidos duplicados por match_id

USO:
    python scrapycoco/scrape_corners_per_match.py [--update] [--source sofascore|flashscore]

SALIDA:
    data/per_match_corners.json
"""

import json
import sys
import time
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent.parent
TEAM_IDS_PATH = BASE_DIR / "data" / "sofascore_team_ids.json"
OUTPUT_PATH = BASE_DIR / "data" / "per_match_corners.json"

SOFA_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://www.sofascore.com/",
    "Origin": "https://www.sofascore.com",
}


def load_existing():
    if OUTPUT_PATH.exists():
        try:
            with open(OUTPUT_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"matches": [], "last_updated": None, "teams_processed": 0, "total_matches": 0}


def save_data(data):
    data["last_updated"] = datetime.now().isoformat()
    data["total_matches"] = len(data["matches"])
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Guardado: {data['total_matches']} partidos en {OUTPUT_PATH}")


def scrape_sofascore(team_ids, existing_ids=None, update_only=False):
    """
    Scrapea corners por partido desde SofaScore API.
    ACTUALMENTE BLOQUEADO (403 desde Julio 2026).
    """
    import requests

    session = requests.Session()
    session.headers.update(SOFA_HEADERS)

    # Obtener cookie de sesión visitando la página principal
    try:
        session.get("https://www.sofascore.com/", timeout=10, allow_redirects=True)
        time.sleep(1.0)
    except Exception:
        pass

    matches = []
    new_count = 0

    for slug, team_id in team_ids.items():
        if team_id is None:
            print(f"  [SKIP] {slug}: sin ID de SofaScore")
            continue

        print(f"  [FETCH] {slug} (id={team_id})...", end=" ")

        try:
            r = session.get(
                f"https://api.sofascore.com/api/v1/team/{team_id}/events/last/0",
                timeout=12,
            )
            if r.status_code != 200:
                print(f"HTTP {r.status_code}")
                continue

            events = r.json().get("events", [])
            print(f"{len(events)} eventos")

            for ev in events[:20]:
                event_id = str(ev.get("id"))
                if update_only and existing_ids and event_id in existing_ids:
                    continue

                home_team = ev.get("homeTeam", {})
                away_team = ev.get("awayTeam", {})
                status = ev.get("status", "")

                # Solo partidos terminados
                if status not in ("finished", "completed"):
                    continue

                time.sleep(0.5)

                try:
                    sr = session.get(
                        f"https://api.sofascore.com/api/v1/event/{event_id}/statistics",
                        timeout=10,
                    )
                    if sr.status_code != 200:
                        continue

                    groups = sr.json().get("statistics", [])
                    stat_map = {}
                    for g in groups:
                        for item in g.get("statisticsItems", []):
                            stat_map[item.get("name", "").lower()] = (
                                item.get("homeValue"),
                                item.get("awayValue"),
                            )

                    hc = stat_map.get("corner kicks", (None, None)) or stat_map.get(
                        "corners", (None, None)
                    )
                    if hc[0] is None:
                        continue

                    home_slug = _resolve_slug(home_team.get("name", ""), team_ids)
                    away_slug = _resolve_slug(away_team.get("name", ""), team_ids)

                    match_date = datetime.fromtimestamp(
                        ev.get("startTimestamp", 0)
                    ).strftime("%Y-%m-%d")

                    matches.append({
                        "id": event_id,
                        "date": match_date,
                        "home_team": home_slug,
                        "away_team": away_slug,
                        "home_corners": float(hc[0]),
                        "away_corners": float(hc[1]),
                        "competition": ev.get("tournament", {}).get("name", ""),
                        "type": "international",
                    })
                    new_count += 1

                except Exception:
                    continue

        except Exception as e:
            print(f"Error: {e}")
            continue

    return matches, new_count


def _resolve_slug(name, team_ids):
    """Intenta resolver un nombre de equipo a slug."""
    slug = name.lower().replace(" ", "-").replace(".", "").replace("'", "")
    if slug in team_ids:
        return slug
    reverse = {v: k for k, v in team_ids.items() if v is not None}
    return slug


def scrape_flashscore(team_ids, existing_ids=None, update_only=False):
    """
    Scrapea corners por partido desde FlashScore vía Playwright.
    Placeholder - requiere implementación cuando FlashScore API sea accesible.
    """
    print("FlashScore scraper no implementado - requiere análisis de XHR de FlashScore")
    return [], 0


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Scrapea corners por partido")
    parser.add_argument("--source", choices=["sofascore", "flashscore"], default="sofascore")
    parser.add_argument("--update", action="store_true", help="Solo partidos nuevos")
    args = parser.parse_args()

    print("=" * 60)
    print(f"  Corner Per-Match Scraper (source={args.source})")
    print("=" * 60)

    if not TEAM_IDS_PATH.exists():
        print(f"ERROR: No se encuentra {TEAM_IDS_PATH}")
        return 1

    with open(TEAM_IDS_PATH, "r", encoding="utf-8") as f:
        team_ids = json.load(f)

    data = load_existing()
    existing_ids = {m["id"] for m in data["matches"]} if args.update else None

    known = {k: v for k, v in team_ids.items() if v is not None}
    print(f"Equipos con ID conocido: {len(known)}/{len(team_ids)}")

    if args.source == "sofascore":
        matches, new_count = scrape_sofascore(team_ids, existing_ids, args.update)
    else:
        matches, new_count = scrape_flashscore(team_ids, existing_ids, args.update)

    if new_count > 0:
        data["matches"].extend(matches)
        data["teams_processed"] = len(known)
        save_data(data)
        print(f"  +{new_count} partidos nuevos")
    else:
        print("Sin partidos nuevos.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
