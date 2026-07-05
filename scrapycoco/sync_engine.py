"""Sync Engine - Sincroniza datos scrapeados a Supabase PostgreSQL."""
import os
import sys
import json
import csv
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional

try:
    import psycopg2
    from psycopg2.extras import execute_values
except ImportError:
    print("psycopg2 no instalado. pip install psycopg2-binary")
    sys.exit(1)

BASE_DIR = Path(__file__).parent.parent
RAW_DIR = BASE_DIR / "data" / "raw"
DATA_DIR = BASE_DIR / "data"

ENV_PATH = BASE_DIR / ".env"


def load_env():
    """Carga variables de entorno desde .env"""
    env = {}
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env


def get_db_connection():
    """Obtiene conexión a Supabase PostgreSQL."""
    env = load_env()
    db_url = env.get("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL no encontrada en .env")
    return psycopg2.connect(db_url)


def get_logger(name: str = "sync_engine"):
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
        logger.addHandler(ch)
    return logger


class SyncEngine:
    def __init__(self, log_callback=None):
        self.log_callback = log_callback
        self.logger = get_logger()

    def _log(self, level: str, message: str):
        """Log a stdout y opcionalmente a callback (para SSE)."""
        msg = {"level": level, "message": message, "timestamp": datetime.now().isoformat()}
        std_level = level if level in ("info", "warning", "error", "debug") else "info"
        getattr(self.logger, std_level)(f"[{level.upper()}] {message}")
        if self.log_callback:
            self.log_callback(json.dumps(msg, ensure_ascii=False))

    def _info(self, msg): self._log("info", msg)
    def _warning(self, msg): self._log("warning", msg)
    def _error(self, msg): self._log("error", msg)
    def _success(self, msg): self._log("success", msg)

    # -----------------------------------------------------------
    # 1. Sincronizar Matches (results.csv -> public.matches)
    # -----------------------------------------------------------
    def sync_matches(self) -> int:
        csv_path = DATA_DIR / "results.csv"
        if not csv_path.exists():
            csv_path = RAW_DIR / "results.csv"
        if not csv_path.exists():
            self._warning(f"Archivo no encontrado: {csv_path}")
            return 0

        self._info(f"Leyendo {csv_path}...")
        matches = []
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    hs = row.get("home_score")
                    as_ = row.get("away_score")
                    if hs is None or as_ is None or hs == "NA" or as_ == "NA" or hs == "" or as_ == "":
                        continue # Skip unplayed matches
                        
                    def _safe_int(val, default=0):
                        try:
                            return int(val)
                        except (ValueError, TypeError):
                            return default

                    matches.append({
                        "date": row.get("date"),
                        "home_slug": row.get("home_team", "").lower().replace(" ", "-").replace(".", ""),
                        "away_slug": row.get("away_team", "").lower().replace(" ", "-").replace(".", ""),
                        "home_team": row.get("home_team"),
                        "away_team": row.get("away_team"),
                        "home_score": _safe_int(hs),
                        "away_score": _safe_int(as_),
                        "tournament": row.get("tournament"),
                        "neutral": row.get("neutral", "False").lower() == "true",
                        "city": row.get("city"),
                        "country": row.get("country"),
                    })
                except Exception as e:
                    self._warning(f"Error parseando fila: {e}")

        if not matches:
            self._warning("No hay partidos para sincronizar")
            return 0

        # Eliminar duplicados que causarían ON CONFLICT violation
        seen = set()
        unique_matches = []
        for m in matches:
            key = (m["date"], m["home_team"], m["away_team"])
            if key not in seen:
                seen.add(key)
                unique_matches.append(m)
        dup_count = len(matches) - len(unique_matches)
        if dup_count > 0:
            self._info(f"{dup_count} duplicados eliminados")

        self._info(f"Sincronizando {len(unique_matches)} partidos a public.matches...")
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            sql = """
            INSERT INTO public.matches (
                date, home_slug, away_slug, home_team, away_team,
                home_score, away_score, tournament, neutral, city, country
            ) VALUES %s
            ON CONFLICT (date, home_team, away_team) DO UPDATE SET
                home_score = EXCLUDED.home_score,
                away_score = EXCLUDED.away_score,
                tournament = EXCLUDED.tournament
            """
            data = [(
                m["date"], m["home_slug"], m["away_slug"], m["home_team"], m["away_team"],
                m["home_score"], m["away_score"], m["tournament"], m["neutral"], m["city"], m["country"]
            ) for m in unique_matches]
            execute_values(cur, sql, data, page_size=1000)
            conn.commit()
            self._success(f"{len(unique_matches)} partidos sincronizados")
            return len(unique_matches)
        finally:
            conn.close()

    # -----------------------------------------------------------
    # 2. Sincronizar Elo (elo-calibrated.json -> public.elo_ratings)
    # -----------------------------------------------------------
    def sync_elo(self) -> int:
        elo_path = DATA_DIR / "elo-calibrated.json"
        if not elo_path.exists():
            elo_path = RAW_DIR / "elo-calibrated.json"
        if not elo_path.exists():
            self._warning(f"Archivo no encontrado: {elo_path}")
            return 0

        self._info(f"Leyendo {elo_path}...")
        data = json.loads(elo_path.read_text(encoding="utf-8"))
        ratings = data.get("ratings", {}) if isinstance(data, dict) else data

        if not ratings:
            self._warning("No hay ratings Elo para sincronizar")
            return 0

        self._info(f"Sincronizando {len(ratings)} equipos a public.elo_ratings...")
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            sql = """
            INSERT INTO public.elo_ratings (team_slug, rating)
            VALUES %s
            ON CONFLICT (team_slug) DO UPDATE SET rating = EXCLUDED.rating
            """
            data = [(slug, float(rating)) for slug, rating in ratings.items()]
            execute_values(cur, sql, data, page_size=500)
            conn.commit()
            self._success(f"{len(ratings)} ratings Elo sincronizados")
            return len(ratings)
        finally:
            conn.close()

    # -----------------------------------------------------------
    # 3. Sincronizar Team Metrics (xg_by_team.json -> public.team_metrics)
    # -----------------------------------------------------------
    def sync_team_metrics(self) -> int:
        xg_path = DATA_DIR / "xg_by_team.json"
        if not xg_path.exists():
            xg_path = RAW_DIR / "xg_by_team.json"
        if not xg_path.exists():
            self._warning(f"Archivo no encontrado: {xg_path}")
            return 0

        self._info(f"Leyendo {xg_path}...")
        data = json.loads(xg_path.read_text(encoding="utf-8"))
        teams = data.get("teams", {}) if isinstance(data, dict) else data

        if not teams:
            self._warning("No hay métricas de equipos para sincronizar")
            return 0

        self._info(f"Sincronizando {len(teams)} equipos a public.team_metrics...")
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            sql = """
            INSERT INTO public.team_metrics (
                team_slug, xg_home, xg_overall, shots_per_90,
                crosses_per_90, shots_blocked_per_90,
                shots_off_target_per_90,
                yellow_cards_per_90, red_cards_per_90,
                discipline_index, source
            ) VALUES %s
            ON CONFLICT (team_slug) DO UPDATE SET
                xg_home = EXCLUDED.xg_home,
                xg_overall = EXCLUDED.xg_overall,
                shots_per_90 = EXCLUDED.shots_per_90,
                crosses_per_90 = EXCLUDED.crosses_per_90,
                shots_blocked_per_90 = EXCLUDED.shots_blocked_per_90,
                shots_off_target_per_90 = EXCLUDED.shots_off_target_per_90,
                yellow_cards_per_90 = EXCLUDED.yellow_cards_per_90,
                red_cards_per_90 = EXCLUDED.red_cards_per_90,
                discipline_index = EXCLUDED.discipline_index,
                source = EXCLUDED.source,
                updated_at = now()
            """
            rows = []
            for slug, stats in teams.items():
                rows.append((
                    slug,
                    stats.get("xg_home"),
                    stats.get("xg_overall"),
                    stats.get("shots_per_90"),
                    stats.get("crosses_per_90"),
                    stats.get("shots_blocked_per_90"),
                    stats.get("shots_off_target_per_90"),
                    stats.get("yellow_cards_per_90"),
                    stats.get("red_cards_per_90"),
                    stats.get("discipline_index"),
                    stats.get("source", "fbref_world_cup")
                ))
            execute_values(cur, sql, rows, page_size=500)
            conn.commit()
            self._success(f"{len(rows)} métricas de equipo sincronizadas")
            return len(rows)
        finally:
            conn.close()

    # -----------------------------------------------------------
    # 4. Sincronizar Corners Stats (corners_stats.json -> public.corners_stats)
    # -----------------------------------------------------------
    def sync_corners_stats(self) -> int:
        corners_path = DATA_DIR / "corners_stats.json"
        if not corners_path.exists():
            self._warning(f"Archivo no encontrado: {corners_path}")
            return 0

        self._info(f"Leyendo {corners_path}...")
        data = json.loads(corners_path.read_text(encoding="utf-8"))

        if not isinstance(data, dict):
            self._warning("Formato de corners_stats.json inesperado")
            return 0

        # Filtrar solo entradas de equipos (excluir _meta)
        teams = {k: v for k, v in data.items() if k != "_meta" and isinstance(v, dict)}

        if not teams:
            self._warning("No hay datos de corners para sincronizar")
            return 0

        self._info(f"Sincronizando {len(teams)} equipos a public.corners_stats...")
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            sql = """
            INSERT INTO public.corners_stats (
                team_slug, corners_for, corners_against, games,
                second_half_taken, second_half_conceded, second_half_matches, source
            ) VALUES %s
            ON CONFLICT (team_slug) DO UPDATE SET
                corners_for = EXCLUDED.corners_for,
                corners_against = EXCLUDED.corners_against,
                games = EXCLUDED.games,
                second_half_taken = EXCLUDED.second_half_taken,
                second_half_conceded = EXCLUDED.second_half_conceded,
                second_half_matches = EXCLUDED.second_half_matches,
                source = EXCLUDED.source,
                updated_at = now()
            """
            rows = []
            for slug, stats in teams.items():
                sh = stats.get("second_half", {}).get("overall", {})
                rows.append((
                    slug,
                    stats.get("corners_for"),
                    stats.get("corners_against"),
                    stats.get("games"),
                    sh.get("taken"),
                    sh.get("conceded"),
                    sh.get("matches"),
                    stats.get("_source", "footystats")
                ))
            execute_values(cur, sql, rows, page_size=500)
            conn.commit()
            self._success(f"{len(rows)} equipos con corners sincronizados")
            return len(rows)
        finally:
            conn.close()

    # -----------------------------------------------------------
    # 5. Sincronizar Match Corners (per_match_corners.json -> public.match_corners)
    # -----------------------------------------------------------
    def sync_match_corners(self) -> int:
        corners_path = DATA_DIR / "per_match_corners.json"
        if not corners_path.exists():
            self._warning(f"Archivo no encontrado: {corners_path}")
            return 0

        self._info(f"Leyendo {corners_path}...")
        data = json.loads(corners_path.read_text(encoding="utf-8"))
        matches = data.get("matches", []) if isinstance(data, dict) else []

        if not matches:
            self._warning("No hay partidos de corners para sincronizar")
            return 0

        # Eliminar duplicados por ID
        seen = set()
        unique = []
        for m in matches:
            mid = m.get("id")
            if mid and mid not in seen:
                seen.add(mid)
                unique.append(m)
        dup_count = len(matches) - len(unique)
        if dup_count > 0:
            self._info(f"{dup_count} partidos duplicados eliminados")

        self._info(f"Sincronizando {len(unique)} partidos a public.match_corners...")
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            sql = """
            INSERT INTO public.match_corners (
                id, date, home_team, away_team, home_corners, away_corners, competition
            ) VALUES %s
            ON CONFLICT (id) DO UPDATE SET
                date = EXCLUDED.date,
                home_team = EXCLUDED.home_team,
                away_team = EXCLUDED.away_team,
                home_corners = EXCLUDED.home_corners,
                away_corners = EXCLUDED.away_corners,
                competition = EXCLUDED.competition,
                updated_at = now()
            """
            rows = []
            for m in unique:
                rows.append((
                    m.get("id"),
                    m.get("date") or None,
                    m.get("home_team"),
                    m.get("away_team"),
                    m.get("home_corners"),
                    m.get("away_corners"),
                    m.get("competition")
                ))
            execute_values(cur, sql, rows, page_size=500)
            conn.commit()
            self._success(f"{len(unique)} partidos con corners sincronizados")
            return len(unique)
        finally:
            conn.close()

    # -----------------------------------------------------------
    # Sync All - ejecuta todo en orden
    # -----------------------------------------------------------
    def sync_all(self) -> dict:
        """Ejecuta todas las sincronizaciones en orden de dependencia."""
        self._info("=" * 50)
        self._info("INICIANDO SINCRONIZACIÓN COMPLETA A SUPABASE")
        self._info("=" * 50)

        results = {}

        # 1. Matches (base para todo)
        results["matches"] = self.sync_matches()

        # 2. Elo (depende de matches idealmente, pero independiente)
        results["elo"] = self.sync_elo()

        # 3. Team Metrics (xG, shots, cards)
        results["team_metrics"] = self.sync_team_metrics()

        # 4. Corners Stats (promedios por equipo)
        results["corners_stats"] = self.sync_corners_stats()

        # 5. Match Corners (por partido)
        results["match_corners"] = self.sync_match_corners()

        self._info("=" * 50)
        self._info("SINCRONIZACIÓN COMPLETADA")
        self._info("=" * 50)
        for key, count in results.items():
            self._info(f"  {key}: {count} registros")
        return results


def main():
    """CLI entry point."""
    import argparse
    parser = argparse.ArgumentParser(description="Sync scraped data to Supabase")
    parser.add_argument("--all", action="store_true", help="Run all syncs")
    parser.add_argument("--matches", action="store_true", help="Sync matches only")
    parser.add_argument("--elo", action="store_true", help="Sync elo only")
    parser.add_argument("--metrics", action="store_true", help="Sync team metrics only")
    parser.add_argument("--corners", action="store_true", help="Sync corners stats only")
    parser.add_argument("--match-corners", action="store_true", help="Sync match corners only")
    args = parser.parse_args()

    engine = SyncEngine()

    if args.all or (not any([args.matches, args.elo, args.metrics, args.corners, args.match_corners])):
        engine.sync_all()
    else:
        if args.matches:
            engine.sync_matches()
        if args.elo:
            engine.sync_elo()
        if args.metrics:
            engine.sync_team_metrics()
        if args.corners:
            engine.sync_corners_stats()
        if args.match_corners:
            engine.sync_match_corners()


if __name__ == "__main__":
    main()