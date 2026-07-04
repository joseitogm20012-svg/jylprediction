#!/usr/bin/env python3
"""
Genera el archivo elo-calibrated.json con los ratings Elo actuales
de las selecciones nacionales basado en datos históricos.
"""

import json
import csv
import sys
import math
from pathlib import Path
from datetime import datetime

# Forzar salida UTF-8 en Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE_DIR = Path(__file__).parent
RESULTS_CSV = BASE_DIR / "results.csv"
ELO_OUTPUT = BASE_DIR / "elo-calibrated.json"

# Ratings Elo iniciales aproximados (basados en rankings actuales)
INITIAL_ELO = {
    "argentina": 1880,
    "france": 1860,
    "spain": 1850,
    "brazil": 1840,
    "england": 1830,
    "portugal": 1820,
    "netherlands": 1810,
    "germany": 1800,
    "belgium": 1790,
    "italy": 1780,
    "colombia": 1760,
    "croatia": 1750,
    "morocco": 1740,
    "usa": 1720,
    "switzerland": 1710,
    "uruguay": 1770,
    "japan": 1700,
    "mexico": 1730,
    "senegal": 1690,
    "denmark": 1705,
    "iran": 1650,
    "ecuador": 1680,
    "australia": 1660,
    "south-korea": 1670,
    "poland": 1695,
    "wales": 1640,
    "nigeria": 1655,
    "peru": 1665,
    "serbia": 1675,
    "qatar": 1600,
    "czech-republic": 1685,
    "egypt": 1645,
    "ivory-coast": 1670,
    "scotland": 1660,
    "canada": 1650,
    "tunisia": 1630,
    "chile": 1680,
    "algeria": 1640,
    "panama": 1590,
    "cameroon": 1635,
    "jamaica": 1610,
    "venezuela": 1620,
    "paraguay": 1655,
    "south-africa": 1615,
    "saudi-arabia": 1625,
    "ghana": 1645,
    "jordan": 1595,
    "bosnia-and-herzegovina": 1650,
    "honduras": 1580,
    "el-salvador": 1570,
    "new-zealand": 1590,
    "haiti": 1560,
    "trinidad-and-tobago": 1575,
    "guatemala": 1565,
    "bolivia": 1585,
    "costa-rica": 1620,
    "sweden": 1690,
    "norway": 1675,
    "austria": 1695,
    "turkey": 1685,
    "greece": 1670,
    "russia": 1660,
    "ukraine": 1665,
    "romania": 1655,
    "hungary": 1660,
    "slovakia": 1650,
    "slovenia": 1645,
    "finland": 1640,
    "iceland": 1635,
    "albania": 1625,
    "kosovo": 1610,
    "north-macedonia": 1615,
    "israel": 1630,
    "china": 1605,
    "india": 1570,
    "mali": 1620,
    "burkina-faso": 1615,
    "kenya": 1560,
    "zimbabwe": 1580,
    "zambia": 1590,
    "angola": 1575,
    "ireland": 1655,
    "northern-ireland": 1610,
    "georgia": 1625,
    "armenia": 1605,
    "azerbaijan": 1595,
    "kazakhstan": 1585,
    "uzbekistan": 1600,
    "cuba": 1550,
    "dominican-republic": 1540,
    "nicaragua": 1545,
    "guyana": 1535,
    "suriname": 1540,
    "libya": 1570,
    "dr-congo": 1585,
    "gabon": 1590,
    "rwanda": 1555,
    "guinea": 1580,
    "cape-verde": 1595,
    "mauritania": 1565,
    "comoros": 1550,
    "madagascar": 1560,
    "philippines": 1540,
    "malaysia": 1555,
    "singapore": 1545,
    "thailand": 1570,
    "vietnam": 1565,
    "indonesia": 1560,
    "nepal": 1520,
    "bangladesh": 1515,
    "pakistan": 1510,
    "afghanistan": 1505,
    "palestine": 1550,
    "lebanon": 1545,
    "syria": 1560,
    "yemen": 1525,
    "kuwait": 1575,
    "uae": 1590,
    "bahrain": 1570,
    "iraq": 1585,
    "oman": 1580,
    "myanmar": 1530,
    "hong-kong": 1540,
    "mongolia": 1510,
    "sri-lanka": 1515,
    "eswatini": 1520,
    "lesotho": 1510,
    "malawi": 1525,
    "botswana": 1530,
    "namibia": 1520,
    "cyprus": 1560,
    "malta": 1545,
    "luxembourg": 1575,
    "congo": 1560,
    "guinea-bissau": 1540,
    "sierra-leone": 1545,
    "benin": 1555,
    "togo": 1550,
    "niger": 1545,
    "liberia": 1530,
    "seychelles": 1505,
    "mauritius": 1515,
    "mozambique": 1535,
    "tanzania": 1540,
    "ethiopia": 1535,
    "uganda": 1545,
}

def name_to_slug(name):
    """Convierte nombre de equipo a slug."""
    name = name.lower().replace("'", "").replace(".", "")
    replacements = {
        "united states": "usa",
        "czech republic": "czech-republic",
        "south korea": "south-korea",
        "ivory coast": "ivory-coast",
        "bosnia and herzegovina": "bosnia-and-herzegovina",
        "el salvador": "el-salvador",
        "new zealand": "new-zealand",
        "trinidad and tobago": "trinidad-and-tobago",
        "costa rica": "costa-rica",
        "republic of ireland": "ireland",
        "northern ireland": "northern-ireland",
        "north macedonia": "north-macedonia",
        "united arab emirates": "uae",
        "china pr": "china",
        "democratic republic of the congo": "dr-congo",
        "congo dr": "dr-congo",
        "cape verde": "cape-verde",
        "burkina faso": "burkina-faso",
        "dominican republic": "dominican-republic",
    }
    if name in replacements:
        return replacements[name]
    return name.replace(" ", "-")

def calculate_elo_from_results():
    """Calcula ratings Elo basados en resultados históricos."""
    ratings = INITIAL_ELO.copy()
    
    # Parámetros Elo
    K_BASE = 30
    HOME_ADVANTAGE = 50
    
    if not RESULTS_CSV.exists():
        print("❌ No se encontró results.csv")
        return ratings
    
    with open(RESULTS_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        matches = list(reader)
    
    # Ordenar por fecha
    matches.sort(key=lambda x: x['date'])
    
    for match in matches:
        try:
            home_name = name_to_slug(match['home_team'])
            away_name = name_to_slug(match['away_team'])
            home_score = int(match['home_score'])
            away_score = int(match['away_score'])
            
            # Obtener Elo actual (o usar 1500 si no existe)
            elo_home = ratings.get(home_name, 1500)
            elo_away = ratings.get(away_name, 1500)
            
            # Calcular expectativa
            expected_home = 1 / (1 + 10 ** ((elo_away - elo_home) / 400))
            expected_away = 1 / (1 + 10 ** ((elo_home - elo_away) / 400))
            
            # Resultado real
            if home_score > away_score:
                result_home = 1.0
                result_away = 0.0
            elif home_score < away_score:
                result_home = 0.0
                result_away = 1.0
            else:
                result_home = 0.5
                result_away = 0.5
            
            # Factor K ajustado por importancia del torneo
            tournament = match.get('tournament', 'Friendly')
            if 'World Cup' in tournament:
                K = K_BASE * 1.5
            elif 'Copa América' in tournament or 'European Championship' in tournament:
                K = K_BASE * 1.3
            elif 'qualification' in tournament.lower():
                K = K_BASE * 1.2
            else:
                K = K_BASE
            
            # Actualizar Elo
            new_elohome = elo_home + K * (result_home - expected_home)
            new_eloaway = elo_away + K * (result_away - expected_away)
            
            ratings[home_name] = round(new_elohome, 2)
            ratings[away_name] = round(new_eloaway, 2)
            
        except Exception as e:
            continue
    
    return ratings

def main():
    print("=" * 60)
    print("  Generando Ratings Elo Calibrados")
    print("=" * 60)
    
    ratings = calculate_elo_from_results()
    
    # Crear estructura de salida
    output = {
        "last_updated": datetime.now().isoformat(),
        "source": "Historical results + Initial estimates",
        "ratings": ratings
    }
    
    # Guardar JSON
    with open(ELO_OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"OK - Ratings Elo guardados en {ELO_OUTPUT}")
    print(f"   Total de equipos: {len(ratings)}")
    
    # Mostrar top 10
    sorted_ratings = sorted(ratings.items(), key=lambda x: x[1], reverse=True)[:10]
    print("\nTop 10 equipos:")
    for i, (team, elo) in enumerate(sorted_ratings, 1):
        print(f"   {i}. {team.title()}: {elo:.0f}")
    
    print("\n" + "=" * 60)
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
