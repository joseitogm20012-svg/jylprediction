#!/usr/bin/env python3
"""
Calcula xG (Expected Goals) promedio por selección basado en resultados históricos.

Como no hay acceso directo a APIs de StatsBomb o Understat sin autenticación,
calculamos un xG estimado basado en:
1. Goles reales anotados/recibidos
2. Calidad de los oponentes (Elo)
3. Localía/Visitante

Exporta a data/xg_by_team.json
"""

import json
import csv
import math
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).parent
RESULTS_CSV = BASE_DIR / "results.csv"
ELO_PATH = BASE_DIR / "elo-calibrated.json"
XG_OUTPUT = BASE_DIR / "xg_by_team.json"

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

def calculate_xg_from_results():
    """Calcula xG estimado basado en resultados históricos."""
    
    # Cargar Elo ratings
    elo_ratings = {}
    if ELO_PATH.exists():
        with open(ELO_PATH, 'r', encoding='utf-8') as f:
            elo_data = json.load(f)
            elo_ratings = elo_data.get('ratings', {})
    
    # Estadísticas por equipo
    team_stats = {}
    
    if not RESULTS_CSV.exists():
        print("❌ No se encontró results.csv")
        return {}
    
    with open(RESULTS_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        matches = list(reader)
    
    # Filtrar partidos recientes (últimos 3 años para mayor relevancia)
    cutoff_date = datetime(2023, 1, 1)
    
    for match in matches:
        try:
            date_str = match['date']
            match_date = datetime.strptime(date_str, '%Y-%m-%d')
            
            # Usar todos los partidos pero con decaimiento temporal
            home_name = name_to_slug(match['home_team'])
            away_name = name_to_slug(match['away_team'])
            home_score = int(match['home_score'])
            away_score = int(match['away_score'])
            
            # Obtener Elo de oponentes
            home_elo = elo_ratings.get(home_name, 1500)
            away_elo = elo_ratings.get(away_name, 1500)
            
            # Factor de calidad del oponente
            # Marcar contra equipo fuerte vale más que contra débil
            opp_quality_home = away_elo / 1650.0  # >1 si oponente es fuerte
            opp_quality_away = home_elo / 1650.0
            
            # Peso temporal (más reciente = más peso)
            days_old = (datetime.now() - match_date).days
            half_life_days = 365 * 1.5  # 18 meses
            weight = math.pow(0.5, days_old / half_life_days)
            weight = max(0.3, min(1.0, weight))  # Clamp entre 0.3 y 1.0
            
            # Inicializar stats si no existen
            if home_name not in team_stats:
                team_stats[home_name] = {
                    'home_goals': 0, 'home_matches': 0, 'home_weighted': 0,
                    'away_goals': 0, 'away_matches': 0, 'away_weighted': 0,
                    'goals_for': 0, 'goals_against': 0, 'matches': 0
                }
            if away_name not in team_stats:
                team_stats[away_name] = {
                    'home_goals': 0, 'home_matches': 0, 'home_weighted': 0,
                    'away_goals': 0, 'away_matches': 0, 'away_weighted': 0,
                    'goals_for': 0, 'goals_against': 0, 'matches': 0
                }
            
            # Actualizar estadísticas local
            team_stats[home_name]['home_goals'] += home_score
            team_stats[home_name]['home_matches'] += 1
            team_stats[home_name]['home_weighted'] += home_score * opp_quality_home * weight
            team_stats[home_name]['goals_for'] += home_score
            team_stats[home_name]['goals_against'] += away_score
            team_stats[home_name]['matches'] += 1
            
            # Actualizar estadísticas visitante
            team_stats[away_name]['away_goals'] += away_score
            team_stats[away_name]['away_matches'] += 1
            team_stats[away_name]['away_weighted'] += away_score * opp_quality_away * weight
            team_stats[away_name]['goals_for'] += away_score
            team_stats[away_name]['goals_against'] += home_score
            team_stats[away_name]['matches'] += 1
            
        except Exception as e:
            continue
    
    # Calcular xG promedio
    xg_by_team = {}
    
    for team, stats in team_stats.items():
        # xG local (cuando juega en casa)
        if stats['home_matches'] > 0:
            xg_home = stats['home_weighted'] / stats['home_matches']
        else:
            xg_home = None
        
        # xG visitante (cuando juega fuera)
        if stats['away_matches'] > 0:
            xg_away = stats['away_weighted'] / stats['away_matches']
        else:
            xg_away = None
        
        # xG general (promedio ponderado)
        total_matches = stats['home_matches'] + stats['away_matches']
        if total_matches > 0:
            xg_overall = (stats['goals_for'] / total_matches)
        else:
            xg_overall = None
        
        # xG en contra (defensa)
        if total_matches > 0:
            xga_overall = (stats['goals_against'] / total_matches)
        else:
            xga_overall = None
        
        xg_by_team[team] = {
            'xg_home': round(xg_home, 3) if xg_home else None,
            'xg_away': round(xg_away, 3) if xg_away else None,
            'xg_overall': round(xg_overall, 3) if xg_overall else None,
            'xga_overall': round(xga_overall, 3) if xga_overall else None,
            'matches_played': total_matches,
            'source': 'Historical results weighted by opponent quality'
        }
    
    return xg_by_team

def main():
    print("=" * 60)
    print("⚽ Calculando xG (Expected Goals) por Selección")
    print("=" * 60)
    
    xg_data = calculate_xg_from_results()
    
    # Crear estructura de salida
    output = {
        'last_updated': datetime.now().isoformat(),
        'methodology': 'Weighted average of goals scored, adjusted by opponent Elo and recency',
        'teams': xg_data
    }
    
    # Guardar JSON
    with open(XG_OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"✅ xG guardado en {XG_OUTPUT}")
    print(f"📈 Total de equipos con datos: {len(xg_data)}")
    
    # Mostrar top 10 equipos por xG
    teams_with_xg = [(t, d['xg_overall']) for t, d in xg_data.items() if d['xg_overall']]
    teams_with_xg.sort(key=lambda x: x[1], reverse=True)
    
    print("\n🏆 Top 10 equipos por xG promedio:")
    for i, (team, xg) in enumerate(teams_with_xg[:10], 1):
        print(f"   {i}. {team.title()}: {xg:.2f} goles/partido")
    
    # Mostrar algunos ejemplos de xG local vs visitante
    print("\n📊 Ejemplos xG Local vs Visitante:")
    examples = ['argentina', 'france', 'brazil', 'england', 'spain']
    for team in examples:
        if team in xg_data:
            d = xg_data[team]
            home = f"{d['xg_home']:.2f}" if d['xg_home'] else "N/A"
            away = f"{d['xg_away']:.2f}" if d['xg_away'] else "N/A"
            print(f"   {team.title()}: Local={home}, Visitante={away}")
    
    print("\n" + "=" * 60)
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
