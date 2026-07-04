"""scrape_corners_apifootball.py
--------------------------------
Scraper de córners por partido usando la API gratuita de API‑FOOTBALL.

Este script:
- Lee la clave API de la variable de entorno `API_FOOTBALL_KEY`.
- Obtiene los fixtures del período 2026-01-01 a 2026-12-31 (cubre todas las fases del Mundial 2026 y sus clasificatorios).
- Para cada fixture finalizado solicita la estadística de corners vía `/fixtures/statistics`.
- Extrae los valores de corners para el equipo local y visitante.
- Guarda los resultados en `data/per_match_corners.json` en el mismo formato que usan los scrapers actuales.
- Soporta `--update` para añadir solo partidos nuevos (evita volver a descargar datos ya almacenados).
- Usa `RateLimiter` para respetar la cuota de 1 req/s de la API (free tier).
"""

import os, json, argparse, time
from pathlib import Path
from datetime import datetime
import requests

# Proyecto raíz y ruta de salida
BASE_DIR = Path(__file__).parent.parent
OUTPUT_PATH = BASE_DIR / "data" / "per_match_corners.json"

# Rate limiter (per dominio API‑FOOTBALL)
# Rate limiter import omitted; using simple time.sleep for rate limiting

API_BASE = "https://v3.football.api-sports.io"
API_KEY = os.getenv("API_FOOTBALL_KEY")
if not API_KEY:
    # Intentar cargar la clave desde .env si está presente
    env_path = BASE_DIR / ".env"
    if env_path.is_file():
        for line in env_path.read_text().splitlines():
            if line.startswith("API_FOOTBALL_KEY="):
                API_KEY = line.partition("=")[2].strip()
                break
    if not API_KEY:
        raise RuntimeError("API_FOOTBALL_KEY no está definida en el entorno ni en .env")

HEADERS = {"x-apisports-key": API_KEY}


def slugify(name: str) -> str:
    return name.lower().replace(" ", "-").replace(".", "").replace("'", "")


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
    data["total_matches"] = len(data.get("matches", []))
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"✅ Guardados {data['total_matches']} partidos en {OUTPUT_PATH}")


def fetch_fixtures():
    params = {
        "from": "2026-01-01",
        "to": "2026-12-31",
        "season": 2026,
        # la API gratuita no permite filtrar por liga sin ID; dejamos la búsqueda abierta.
    }
    resp = requests.get(f"{API_BASE}/fixtures", headers=HEADERS, params=params, timeout=15)
    resp.raise_for_status()
    payload = resp.json()
    return payload.get("response", [])


def fetch_statistics(fixture_id: int):
    params = {"fixture": fixture_id}
    resp = requests.get(f"{API_BASE}/fixtures/statistics", headers=HEADERS, params=params, timeout=15)
    resp.raise_for_status()
    return resp.json().get("response", [])


def extract_corners(stats):
    # stats: lista de 2 dicts (uno por equipo)
    corners = {}
    for entry in stats:
        team_name = entry.get("team", {}).get("name")
        for item in entry.get("statistics", []):
            if item.get("type", "").lower() == "corners":
                # El valor viene como string, lo convertimos a float (puede ser "0" o "5")
                try:
                    val = float(item.get("value", 0))
                except Exception:
                    val = 0.0
                corners[team_name] = val
    return corners


def main():
    parser = argparse.ArgumentParser(description="Scrape corners de partidos usando API‑FOOTBALL.")
    parser.add_argument("--update", action="store_true", help="Solo descargar partidos que no existan aún.")
    args = parser.parse_args()

    existing = load_existing()
    existing_ids = {m["id"] for m in existing.get("matches", [])} if args.update else set()

    print("Obteniendo fixtures del API-FOOTBALL ...")
    fixtures = fetch_fixtures()
    print(f"Total fixtures obtenidos: {len(fixtures)}")

    new_matches = []
    for f in fixtures:
        fid = str(f.get("fixture", {}).get("id"))
        if not fid:
            continue
        if args.update and fid in existing_ids:
            continue
        # Solo procesar partidos concluidos (status "FT", "AET", "PEN", etc.)
        status = f.get("fixture", {}).get("status", {}).get("short")
        if status not in ("FT", "AET", "PEN", "ET", "FT_PEN"):
            continue
        # Esperar entre peticiones para no superar la cuota (≈1 req/s)
        time.sleep(1.0)
        try:
            stats = fetch_statistics(int(fid))
        except Exception as e:
            print(f"⚠️ Error obteniendo stats de {fid}: {e}")
            continue
        corners = extract_corners(stats)
        if len(corners) != 2:
            # No hay datos de corners para ambos equipos
            continue
        home_name = f.get("teams", {}).get("home", {}).get("name")
        away_name = f.get("teams", {}).get("away", {}).get("name")
        if not home_name or not away_name:
            continue
        home_slug = slugify(home_name)
        away_slug = slugify(away_name)
        match_date = f.get("fixture", {}).get("date", "")[:10]
        competition = f.get("league", {}).get("name", "")
        new_matches.append({
            "id": fid,
            "date": match_date,
            "home_team": home_slug,
            "away_team": away_slug,
            "home_corners": corners.get(home_name, 0.0),
            "away_corners": corners.get(away_name, 0.0),
            "competition": competition,
            "type": "international",
        })
        new_matches[-1]["_fetched_at"] = datetime.now().isoformat()
        print(f"Partido {fid} – {home_name} vs {away_name} – corners {corners.get(home_name)} / {corners.get(away_name)}")

    if new_matches:
        existing.setdefault("matches", []).extend(new_matches)
        existing["teams_processed"] = len({m["home_team"] for m in existing["matches"]}.union({m["away_team"] for m in existing["matches"]}))
        save_data(existing)
        print(f"Añadidos {len(new_matches)} partidos nuevos.")
    else:
        print("No se encontraron partidos nuevos para añadir.")


if __name__ == "__main__":
    main()
