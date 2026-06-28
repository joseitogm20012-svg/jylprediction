"""
Team Analytics Module for JLY Predictor
Funciones avanzadas de análisis de equipos para los modales de detalles y comparación.
"""

import csv
import os
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Any, Optional

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
RESULTS_CSV = os.path.join(DATA_DIR, 'results.csv')
GOALSCORERS_CSV = os.path.join(DATA_DIR, 'goalscorers.csv')


def load_results() -> List[Dict]:
    """Carga todos los resultados desde results.csv"""
    matches = []
    if not os.path.exists(RESULTS_CSV):
        return matches
    
    with open(RESULTS_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                match = {
                    'date': row.get('date', ''),
                    'home_team': row.get('home_team', '').lower().replace(' ', '-'),
                    'away_team': row.get('away_team', '').lower().replace(' ', '-'),
                    'home_score': int(row.get('home_score', 0)),
                    'away_score': int(row.get('away_score', 0)),
                    'tournament': row.get('tournament', ''),
                    'city': row.get('city', ''),
                    'country': row.get('country', ''),
                    'neutral': row.get('neutral', 'FALSE').upper() == 'TRUE'
                }
                matches.append(match)
            except (ValueError, KeyError):
                continue
    
    # Ordenar por fecha descendente
    matches.sort(key=lambda x: x['date'], reverse=True)
    return matches


def load_goalscorers() -> List[Dict]:
    """Carga los goleadores desde goalscorers.csv"""
    scorers = []
    if not os.path.exists(GOALSCORERS_CSV):
        return scorers
    
    with open(GOALSCORERS_CSV, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                scorer = {
                    'date': row.get('date', ''),
                    'home_team': row.get('home_team', '').lower().replace(' ', '-'),
                    'away_team': row.get('away_team', '').lower().replace(' ', '-'),
                    'team': row.get('team', '').lower().replace(' ', '-'),
                    'scorer': row.get('scorer', ''),
                    'minute': int(row.get('minute', 0)) if row.get('minute', '').isdigit() else 0,
                    'own_goal': row.get('own_goal', 'FALSE').upper() == 'TRUE',
                    'penalty': row.get('penalty', 'FALSE').upper() == 'TRUE'
                }
                scorers.append(scorer)
            except (ValueError, KeyError):
                continue
    
    return scorers


def normalize_team_name(team_name: str) -> str:
    """Normaliza el nombre del equipo al formato slug"""
    return team_name.lower().replace(' ', '-')


def get_team_recent_matches(team_slug: str, n: int = 10) -> List[Dict]:
    """
    Obtiene los últimos n partidos de un equipo específico.
    Retorna lista ordenada por fecha descendente.
    """
    matches = load_results()
    team_matches = []
    
    for m in matches:
        if m['home_team'] == team_slug or m['away_team'] == team_slug:
            is_home = m['home_team'] == team_slug
            goals_for = m['home_score'] if is_home else m['away_score']
            goals_against = m['away_score'] if is_home else m['home_score']
            opponent = m['away_team'] if is_home else m['home_team']
            
            # Determinar resultado
            if goals_for > goals_against:
                result = 'W'
            elif goals_for == goals_against:
                result = 'D'
            else:
                result = 'L'
            
            team_matches.append({
                'date': m['date'],
                'opponent': opponent,
                'is_home': is_home,
                'result': result,
                'score': f"{goals_for}-{goals_against}",
                'goals_for': goals_for,
                'goals_against': goals_against,
                'tournament': m['tournament'],
                'full_match': m
            })
            
            if len(team_matches) >= n:
                break
    
    return team_matches


def calculate_team_stats(matches: List[Dict]) -> Dict[str, Any]:
    """
    Calcula estadísticas avanzadas de forma reciente.
    """
    if not matches:
        return {
            'record': {'wins': 0, 'draws': 0, 'losses': 0},
            'goals_for': {'total': 0, 'avg': 0},
            'goals_against': {'total': 0, 'avg': 0},
            'goal_difference': 0,
            'clean_sheets_pct': 0,
            'btts_pct': 0,
            'over_2_5_pct': 0,
            'over_1_5_pct': 0
        }
    
    wins = sum(1 for m in matches if m['result'] == 'W')
    draws = sum(1 for m in matches if m['result'] == 'D')
    losses = sum(1 for m in matches if m['result'] == 'L')
    
    total_goals_for = sum(m['goals_for'] for m in matches)
    total_goals_against = sum(m['goals_against'] for m in matches)
    
    clean_sheets = sum(1 for m in matches if m['goals_against'] == 0)
    btts = sum(1 for m in matches if m['goals_for'] > 0 and m['goals_against'] > 0)
    over_2_5 = sum(1 for m in matches if m['goals_for'] + m['goals_against'] > 2.5)
    over_1_5 = sum(1 for m in matches if m['goals_for'] + m['goals_against'] > 1.5)
    
    n = len(matches)
    
    return {
        'record': {'wins': wins, 'draws': draws, 'losses': losses},
        'goals_for': {'total': total_goals_for, 'avg': round(total_goals_for / n, 2)},
        'goals_against': {'total': total_goals_against, 'avg': round(total_goals_against / n, 2)},
        'goal_difference': total_goals_for - total_goals_against,
        'clean_sheets_pct': round(clean_sheets / n * 100, 1),
        'btts_pct': round(btts / n * 100, 1),
        'over_2_5_pct': round(over_2_5 / n * 100, 1),
        'over_1_5_pct': round(over_1_5 / n * 100, 1)
    }


def get_performance_by_rival_level(team_slug: str, rankings_dict: Dict[str, int]) -> Dict[str, Any]:
    """
    Calcula el rendimiento del equipo contra rivales de diferentes niveles de ranking.
    Niveles: Top (1-10), High (11-30), Medium (31-60), Low (61+)
    """
    matches = load_results()
    
    levels = {
        'top': {'name': 'Top Nivel (1-10)', 'matches': [], 'record': {'wins': 0, 'draws': 0, 'losses': 0}},
        'high': {'name': 'Nivel Alto (11-30)', 'matches': [], 'record': {'wins': 0, 'draws': 0, 'losses': 0}},
        'medium': {'name': 'Nivel Medio (31-60)', 'matches': [], 'record': {'wins': 0, 'draws': 0, 'losses': 0}},
        'low': {'name': 'Nivel Bajo (61+)', 'matches': [], 'record': {'wins': 0, 'draws': 0, 'losses': 0}}
    }
    
    for m in matches:
        if m['home_team'] == team_slug or m['away_team'] == team_slug:
            is_home = m['home_team'] == team_slug
            opponent = m['away_team'] if is_home else m['home_team']
            opponent_rank = rankings_dict.get(opponent, 999)
            
            # Determinar nivel del rival
            if opponent_rank <= 10:
                level_key = 'top'
            elif opponent_rank <= 30:
                level_key = 'high'
            elif opponent_rank <= 60:
                level_key = 'medium'
            else:
                level_key = 'low'
            
            goals_for = m['home_score'] if is_home else m['away_score']
            goals_against = m['away_score'] if is_home else m['home_score']
            
            levels[level_key]['matches'].append(m)
            
            if goals_for > goals_against:
                levels[level_key]['record']['wins'] += 1
            elif goals_for == goals_against:
                levels[level_key]['record']['draws'] += 1
            else:
                levels[level_key]['record']['losses'] += 1
    
    return {
        key: {
            'name': data['name'],
            'record': data['record'],
            'matches_played': len(data['matches'])
        }
        for key, data in levels.items()
    }


def get_performance_by_competition(team_slug: str) -> Dict[str, Any]:
    """
    Calcula el rendimiento por tipo de competición.
    """
    matches = load_results()
    
    competitions = {
        'world_cup': {'name': 'Mundiales', 'keywords': ['world cup', 'copa del mundo'], 'record': {'wins': 0, 'draws': 0, 'losses': 0}},
        'qualifiers': {'name': 'Eliminatorias', 'keywords': ['qualification', 'eliminatorias', 'qualifier'], 'record': {'wins': 0, 'draws': 0, 'losses': 0}},
        'continental': {'name': 'Competiciones Continentales', 'keywords': ['copa america', 'euro', 'asian cup', 'afcon', 'concacaf'], 'record': {'wins': 0, 'draws': 0, 'losses': 0}},
        'friendly': {'name': 'Amistosos', 'keywords': ['friendly', 'amistoso'], 'record': {'wins': 0, 'draws': 0, 'losses': 0}}
    }
    
    for m in matches:
        if m['home_team'] == team_slug or m['away_team'] == team_slug:
            tournament = m['tournament'].lower()
            is_home = m['home_team'] == team_slug
            goals_for = m['home_score'] if is_home else m['away_score']
            goals_against = m['away_score'] if is_home else m['home_score']
            
            for comp_key, comp_data in competitions.items():
                if any(keyword in tournament for keyword in comp_data['keywords']):
                    if goals_for > goals_against:
                        comp_data['record']['wins'] += 1
                    elif goals_for == goals_against:
                        comp_data['record']['draws'] += 1
                    else:
                        comp_data['record']['losses'] += 1
                    break
    
    return {
        key: {
            'name': data['name'],
            'record': data['record']
        }
        for key, data in competitions.items()
    }


def get_home_away_stats(team_slug: str) -> Dict[str, Any]:
    """
    Calcula estadísticas separadas para local, visitante y campo neutral.
    """
    matches = load_results()
    
    stats = {
        'home': {'record': {'wins': 0, 'draws': 0, 'losses': 0}, 'goals_for': 0, 'goals_against': 0, 'matches': 0},
        'away': {'record': {'wins': 0, 'draws': 0, 'losses': 0}, 'goals_for': 0, 'goals_against': 0, 'matches': 0},
        'neutral': {'record': {'wins': 0, 'draws': 0, 'losses': 0}, 'goals_for': 0, 'goals_against': 0, 'matches': 0}
    }
    
    for m in matches:
        if m['home_team'] == team_slug:
            location = 'home'
            goals_for = m['home_score']
            goals_against = m['away_score']
        elif m['away_team'] == team_slug:
            if m['neutral']:
                location = 'neutral'
            else:
                location = 'away'
            goals_for = m['away_score']
            goals_against = m['home_score']
        else:
            continue
        
        stats[location]['matches'] += 1
        stats[location]['goals_for'] += goals_for
        stats[location]['goals_against'] += goals_against
        
        if goals_for > goals_against:
            stats[location]['record']['wins'] += 1
        elif goals_for == goals_against:
            stats[location]['record']['draws'] += 1
        else:
            stats[location]['record']['losses'] += 1
    
    return stats


def get_top_scorers(team_slug: str, years: int = 2) -> Dict[str, List[Dict]]:
    """
    Obtiene los principales goleadores del equipo en los últimos años.
    """
    scorers = load_goalscorers()
    
    # Filtrar por fecha (últimos años)
    cutoff_date = (datetime.now() - timedelta(days=years*365)).strftime('%Y-%m-%d')
    
    team_scorers = defaultdict(lambda: {'goals': 0, 'matches': set(), 'penalties': 0, 'own_goals': 0})
    
    for s in scorers:
        if s['team'] != team_slug:
            continue
        if s['date'] < cutoff_date:
            continue
        
        player_name = s['scorer']
        team_scorers[player_name]['goals'] += 1
        team_scorers[player_name]['matches'].add(s['date'])
        if s['penalty']:
            team_scorers[player_name]['penalties'] += 1
        if s['own_goal']:
            team_scorers[player_name]['own_goals'] += 1
    
    # Convertir a lista y ordenar
    scorers_list = []
    for name, data in team_scorers.items():
        matches_count = len(data['matches'])
        scorers_list.append({
            'name': name,
            'goals': data['goals'],
            'matches': matches_count,
            'avg_per_match': round(data['goals'] / matches_count, 2) if matches_count > 0 else 0,
            'penalties': data['penalties'],
            'own_goals': data['own_goals']
        })
    
    scorers_list.sort(key=lambda x: x['goals'], reverse=True)
    
    # Separar activos (últimos 2 años) e históricos
    recent_cutoff = (datetime.now() - timedelta(days=2*365)).strftime('%Y-%m-%d')
    active_scorers = [s for s in scorers_list]  # Ya filtrado por años
    
    return {
        'active': active_scorers[:5],
        'historical': scorers_list[:10]
    }


def calculate_goal_timing(team_slug: str) -> Dict[str, float]:
    """
    Calcula la distribución de goles por periodo de tiempo.
    """
    scorers = load_goalscorers()
    
    periods = {
        '0-15': 0,
        '16-30': 0,
        '31-45': 0,
        '46-60': 0,
        '61-75': 0,
        '76-90': 0
    }
    
    total_goals = 0
    
    for s in scorers:
        if s['team'] != team_slug:
            continue
        
        minute = s['minute']
        if minute <= 0:
            continue
        
        total_goals += 1
        
        if minute <= 15:
            periods['0-15'] += 1
        elif minute <= 30:
            periods['16-30'] += 1
        elif minute <= 45:
            periods['31-45'] += 1
        elif minute <= 60:
            periods['46-60'] += 1
        elif minute <= 75:
            periods['61-75'] += 1
        elif minute <= 90:
            periods['76-90'] += 1
    
    # Calcular porcentajes
    if total_goals > 0:
        return {k: round(v / total_goals * 100, 1) for k, v in periods.items()}
    else:
        return {k: 0.0 for k in periods.keys()}


def detect_current_streaks(team_slug: str) -> Dict[str, Any]:
    """
    Detecta las rachas actuales del equipo.
    """
    matches = get_team_recent_matches(team_slug, 20)
    
    if not matches:
        return {
            'unbeaten': 0,
            'losing': 0,
            'scoring': 0,
            'conceding': 0,
            'clean_sheets': 0,
            'home_unbeaten': 0
        }
    
    streaks = {
        'unbeaten': 0,
        'losing': 0,
        'scoring': 0,
        'conceding': 0,
        'clean_sheets': 0,
        'home_unbeaten': 0
    }
    
    # Racha de resultados (sin perder / perdiendo)
    for i, m in enumerate(matches):
        if m['result'] != 'L':
            streaks['unbeaten'] += 1
        else:
            break
    
    for i, m in enumerate(matches):
        if m['result'] == 'L':
            streaks['losing'] += 1
        else:
            break
    
    # Racha de goles anotados
    for i, m in enumerate(matches):
        if m['goals_for'] > 0:
            streaks['scoring'] += 1
        else:
            break
    
    # Racha de goles recibidos
    for i, m in enumerate(matches):
        if m['goals_against'] > 0:
            streaks['conceding'] += 1
        else:
            break
    
    # Racha de clean sheets
    for i, m in enumerate(matches):
        if m['goals_against'] == 0:
            streaks['clean_sheets'] += 1
        else:
            break
    
    # Racha como local sin perder
    home_matches = [m for m in matches if m['is_home']]
    for m in home_matches:
        if m['result'] != 'L':
            streaks['home_unbeaten'] += 1
        else:
            break
    
    return streaks


def get_frequent_scores(team_slug: str) -> List[Dict]:
    """
    Obtiene los marcadores más frecuentes en los últimos partidos.
    """
    matches = get_team_recent_matches(team_slug, 20)
    
    score_counts = defaultdict(int)
    for m in matches:
        score_counts[m['score']] += 1
    
    frequent = [{'score': score, 'count': count} for score, count in score_counts.items()]
    frequent.sort(key=lambda x: x['count'], reverse=True)
    
    return frequent[:5]


def get_team_details(team_slug: str, rankings_dict: Dict[str, int]) -> Dict[str, Any]:
    """
    Función principal que retorna todos los datos para el modal de detalles del equipo.
    """
    recent_matches = get_team_recent_matches(team_slug, 10)
    
    return {
        'recent_form': recent_matches,
        'stats': calculate_team_stats(recent_matches),
        'performance_by_rival_level': get_performance_by_rival_level(team_slug, rankings_dict),
        'performance_by_competition': get_performance_by_competition(team_slug),
        'home_away_stats': get_home_away_stats(team_slug),
        'top_scorers': get_top_scorers(team_slug),
        'goal_timing': calculate_goal_timing(team_slug),
        'current_streaks': detect_current_streaks(team_slug),
        'frequent_scores': get_frequent_scores(team_slug)
    }


def compare_teams(team_a_slug: str, team_b_slug: str, rankings_dict: Dict[str, int]) -> Dict[str, Any]:
    """
    Compara dos equipos y retorna datos para el modal de comparación.
    """
    stats_a = get_team_details(team_a_slug, rankings_dict)
    stats_b = get_team_details(team_b_slug, rankings_dict)
    
    # Comparación lado a lado
    comparison = {
        'goals_for_avg': {
            'team_a': stats_a['stats']['goals_for']['avg'],
            'team_b': stats_b['stats']['goals_for']['avg'],
            'better': 'a' if stats_a['stats']['goals_for']['avg'] > stats_b['stats']['goals_for']['avg'] else 'b'
        },
        'goals_against_avg': {
            'team_a': stats_a['stats']['goals_against']['avg'],
            'team_b': stats_b['stats']['goals_against']['avg'],
            'better': 'a' if stats_a['stats']['goals_against']['avg'] < stats_b['stats']['goals_against']['avg'] else 'b'
        },
        'clean_sheets_pct': {
            'team_a': stats_a['stats']['clean_sheets_pct'],
            'team_b': stats_b['stats']['clean_sheets_pct'],
            'better': 'a' if stats_a['stats']['clean_sheets_pct'] > stats_b['stats']['clean_sheets_pct'] else 'b'
        },
        'btts_pct': {
            'team_a': stats_a['stats']['btts_pct'],
            'team_b': stats_b['stats']['btts_pct'],
            'better': 'a' if stats_a['stats']['btts_pct'] < stats_b['stats']['btts_pct'] else 'b'
        },
        'win_rate_recent': {
            'team_a': stats_a['stats']['record']['wins'] / 10 if len(stats_a['recent_form']) >= 10 else 0,
            'team_b': stats_b['stats']['record']['wins'] / 10 if len(stats_b['recent_form']) >= 10 else 0,
            'better': 'a' if stats_a['stats']['record']['wins'] > stats_b['stats']['record']['wins'] else 'b'
        }
    }
    
    # Ventajas clave
    advantages_a = []
    advantages_b = []
    
    if comparison['goals_against_avg']['better'] == 'a':
        advantages_a.append(f"Mejor defensa ({stats_a['stats']['goals_against']['avg']} vs {stats_b['stats']['goals_against']['avg']} goles/partido)")
    else:
        advantages_b.append(f"Mejor defensa ({stats_b['stats']['goals_against']['avg']} vs {stats_a['stats']['goals_against']['avg']} goles/partido)")
    
    if comparison['goals_for_avg']['better'] == 'a':
        advantages_a.append(f"Mejor ataque ({stats_a['stats']['goals_for']['avg']} vs {stats_b['stats']['goals_for']['avg']} goles/partido)")
    else:
        advantages_b.append(f"Mejor ataque ({stats_b['stats']['goals_for']['avg']} vs {stats_a['stats']['goals_for']['avg']} goles/partido)")
    
    if comparison['clean_sheets_pct']['better'] == 'a':
        advantages_a.append(f"Más clean sheets ({stats_a['stats']['clean_sheets_pct']}% vs {stats_b['stats']['clean_sheets_pct']}%)")
    else:
        advantages_b.append(f"Más clean sheets ({stats_b['stats']['clean_sheets_pct']}% vs {stats_a['stats']['clean_sheets_pct']}%)")
    
    if stats_a['current_streaks']['unbeaten'] > stats_b['current_streaks']['unbeaten']:
        advantages_a.append(f"Mejor racha actual ({stats_a['current_streaks']['unbeaten']} partidos sin perder)")
    else:
        advantages_b.append(f"Mejor racha actual ({stats_b['current_streaks']['unbeaten']} partidos sin perder)")
    
    # Historial de enfrentamientos directos
    h2h_history = get_h2h_matches(team_a_slug, team_b_slug)
    
    return {
        'team_a_stats': stats_a,
        'team_b_stats': stats_b,
        'comparison': comparison,
        'advantages_a': advantages_a[:5],
        'advantages_b': advantages_b[:5],
        'h2h_history': h2h_history
    }


def get_h2h_matches(team_a_slug: str, team_b_slug: str) -> List[Dict]:
    """
    Obtiene el historial de enfrentamientos directos entre dos equipos.
    """
    matches = load_results()
    h2h = []
    
    for m in matches:
        if (m['home_team'] == team_a_slug and m['away_team'] == team_b_slug) or \
           (m['home_team'] == team_b_slug and m['away_team'] == team_a_slug):
            is_a_home = m['home_team'] == team_a_slug
            score_a = m['home_score'] if is_a_home else m['away_score']
            score_b = m['away_score'] if is_a_home else m['home_score']
            
            if score_a > score_b:
                winner = 'a'
            elif score_b > score_a:
                winner = 'b'
            else:
                winner = 'draw'
            
            h2h.append({
                'date': m['date'],
                'home_team': m['home_team'],
                'away_team': m['away_team'],
                'score': f"{m['home_score']}-{m['away_score']}",
                'tournament': m['tournament'],
                'winner': winner
            })
            
            if len(h2h) >= 10:
                break
    
    return h2h
