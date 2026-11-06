#!/usr/bin/env python
"""Seed script for the equipos management module.

Inserta 8 equipos de demostración en MongoDB si la colección está vacía.
Uso: python scripts/seed_equipos.py
"""
import os
import sys
from pathlib import Path

# Añadir backend al path para imports
BACKEND_DIR = Path(__file__).resolve().parent.parent / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Cargar .env de la raíz igual que main.py
ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
if ENV_PATH.exists():
    with open(ENV_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                os.environ[key.strip()] = val.strip().strip('"').strip("'")


def main():
    import database
    from controllers.equipo_controller import EquipoRepository, crear_equipo

    try:
        col = database.get_equipos_collection()
        database.ensure_indexes(col)
    except database.MongoNoConfiguradoError as exc:
        print(f"ERROR: {exc}")
        sys.exit(1)

    repo = EquipoRepository(col)
    existentes = repo.listar()

    if existentes:
        print(f"Ya hay {len(existentes)} equipos, no se inserta nada")
        return

    equipos = [
        {"nombre": "Argentina", "confederacion": "CONMEBOL", "ranking_fifa": 1, "rating_elo": 2050.0},
        {"nombre": "Brasil", "confederacion": "CONMEBOL", "ranking_fifa": 5, "rating_elo": 1980.0},
        {"nombre": "Francia", "confederacion": "UEFA", "ranking_fifa": 2, "rating_elo": 2010.0},
        {"nombre": "España", "confederacion": "UEFA", "ranking_fifa": 3, "rating_elo": 1995.0},
        {"nombre": "México", "confederacion": "CONCACAF", "ranking_fifa": 15, "rating_elo": 1750.0},
        {"nombre": "Estados Unidos", "confederacion": "CONCACAF", "ranking_fifa": 16, "rating_elo": 1720.0},
        {"nombre": "Marruecos", "confederacion": "CAF", "ranking_fifa": 12, "rating_elo": 1780.0},
        {"nombre": "Japón", "confederacion": "AFC", "ranking_fifa": 18, "rating_elo": 1700.0},
    ]

    for eq in equipos:
        res = crear_equipo(repo, eq)
        if not res.ok:
            print(f"Error insertando {eq['nombre']}: {res.mensaje}")
            sys.exit(1)

    print("8 equipos insertados")


if __name__ == "__main__":
    main()