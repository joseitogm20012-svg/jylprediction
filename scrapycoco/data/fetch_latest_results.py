#!/usr/bin/env python3
"""
Script para descargar los últimos partidos de selecciones nacionales
y actualizar results.csv con los datos más recientes.
"""

import urllib.request
import shutil
import sys
import os
import csv
from datetime import datetime

# Forzar salida UTF-8 en Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# BASE_DIR es la carpeta del script (data/). RESULTS_CSV apunta a data/results.csv
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

FILES_TO_DOWNLOAD = {
    "results.csv": "https://raw.githubusercontent.com/martj42/international_results/master/results.csv",
    "shootouts.csv": "https://raw.githubusercontent.com/martj42/international_results/master/shootouts.csv",
    "goalscorers.csv": "https://raw.githubusercontent.com/martj42/international_results/master/goalscorers.csv"
}

def download_file(url, file_name):
    """Intenta descargar un archivo especifico."""
    try:
        print(f"  Descargando {file_name}...")
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as response:
            content = response.read().decode("utf-8")
        lines = content.strip().split("\n")
        if len(lines) < 10:
            print(f"  [ERROR] Datos insuficientes para {file_name}.")
            return None
        print(f"  OK - {file_name} ({len(lines)-1:,} registros)")
        return content
    except Exception as e:
        print(f"  [Fallo] al descargar {file_name}: {e}")
        return None

def save_with_backup(content, file_name):
    """Guarda el CSV creando un backup del anterior."""
    file_path = os.path.join(BASE_DIR, file_name)
    if os.path.exists(file_path):
        backup = file_path + ".bak"
        shutil.copy2(file_path, backup)

    with open(file_path, "w", encoding="utf-8", newline="") as f:
        f.write(content)
    print(f"  -> {file_name} guardado correctamente.")

def show_recent_matches(n=10):
    """Muestra los N partidos más recientes de results.csv."""
    results_path = os.path.join(BASE_DIR, "results.csv")
    with open(results_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    rows.sort(key=lambda x: x["date"], reverse=True)
    total = len(rows)
    latest_date = rows[0]["date"] if rows else "N/A"

    print(f"\n  Total de partidos en la base de datos: {total:,}")
    print(f"  Partido más reciente: {latest_date}")
    print()
    print(f"  {'Fecha':<12} {'Local':<22} {'Marcador':>8}  {'Visitante':<22} Torneo")
    print("  " + "-" * 85)

    for r in rows[:n]:
        home = r["home_team"][:21]
        away = r["away_team"][:21]
        score = f"{r['home_score']}-{r['away_score']}"
        tournament = r["tournament"][:25]
        print(f"  {r['date']:<12} {home:<22} {score:>8}  {away:<22} {tournament}")

    print("  " + "-" * 85)

def main():
    print("=" * 60)
    print("  Actualizando Partidos de Selecciones Nacionales")
    print("=" * 60)

    # --- Paso 1: Descargar archivos CSV ---
    print("\n[1/2] Descargando datos actualizados...")
    
    success = True
    for file_name, url in FILES_TO_DOWNLOAD.items():
        content = download_file(url, file_name)
        if content is None:
            success = False
        else:
            save_with_backup(content, file_name)

    if not success:
        print("\n[ADVERTENCIA] Hubo problemas descargando algunos archivos.")
        print("   Revisa tu conexion a internet e intentalo mas tarde.")
        # We don't return 1 here so Elo recalculation can still try to run on whatever data exists.

    # --- Paso 2: Mostrar partidos recientes ---
    print("\n[2/2] Partidos más recientes descargados:")
    show_recent_matches(10)

    print("\nDescarga completada. Los ratings Elo seran recalculados a continuacion.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
