#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sincroniza xg_by_team.json + player_stats.json a Supabase.
Actualiza public.team_metrics con datos de tarjetas, tiros, centros.
"""
import json, os, sys, io
from pathlib import Path

if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE_DIR = Path(__file__).parent
RAW_DIR = BASE_DIR / "raw"
XG_PATH = RAW_DIR / "xg_by_team.json"
ENV_PATH = BASE_DIR.parent / ".env"

def load_env():
    env = {}
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env

def main():
    env = load_env()
    db_url = env.get("DATABASE_URL")
    if not db_url:
        print("ERROR: DATABASE_URL no encontrada en .env")
        return

    import psycopg2

    print("Conectando a Supabase PostgreSQL...")
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()

    print(f"Leyendo {XG_PATH}...")
    xg_data = json.loads(XG_PATH.read_text(encoding="utf-8"))
    teams = xg_data.get("teams", {})
    print(f"  {len(teams)} equipos en JSON")

    upserted = 0
    for slug, stats in teams.items():
        xg_home = stats.get("xg_home")
        xg_overall = stats.get("xg_overall")
        shots_per_90 = stats.get("shots_per_90")
        crosses_per_90 = stats.get("crosses_per_90")
        shots_blocked_per_90 = stats.get("shots_blocked_per_90")
        shots_off_target_per_90 = stats.get("shots_off_target_per_90")
        yc = stats.get("yellow_cards_per_90")
        rc = stats.get("red_cards_per_90")
        disc = stats.get("discipline_index")
        source = stats.get("source", "fbref_world_cup")

        cur.execute("""
            INSERT INTO public.team_metrics
                (team_slug, xg_home, xg_overall, shots_per_90,
                 crosses_per_90, shots_blocked_per_90,
                 shots_off_target_per_90,
                 yellow_cards_per_90, red_cards_per_90,
                 discipline_index, source)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
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
        """, (slug, xg_home, xg_overall, shots_per_90,
              crosses_per_90, shots_blocked_per_90,
              shots_off_target_per_90,
              yc, rc, disc, source))
        upserted += 1
        if upserted % 50 == 0:
            print(f"  {upserted}/{len(teams)} upserted...")
            conn.commit()

    conn.commit()
    cur.close()
    conn.close()
    print(f"\nSync completo: {upserted} equipos actualizados en public.team_metrics")

if __name__ == "__main__":
    main()
