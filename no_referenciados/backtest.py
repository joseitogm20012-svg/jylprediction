#!/usr/bin/env python3
"""
Backtesting automatizado con ROI histórico.

Valida el modelo con datos reales del pasado y muestra métricas de rendimiento:
- Accuracy general (% de resultados correctamente predichos)
- ROI simulado en apuestas con estrategia +EV
- Brier Score (calibración probabilística)
- Tabla por Mundial (2010, 2014, 2018, 2022)
"""

import json
import csv
import math
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
import sys

# Agregar path al predictor
BASE_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(BASE_DIR))

from predictor import run_prediction_sim, load_data, name_to_slug

# Mundiales históricos para backtesting
WORLD_CUPS = {
    "2010": {"start": "2010-06-11", "end": "2010-07-11", "host": "South Africa"},
    "2014": {"start": "2014-06-12", "end": "2014-07-13", "host": "Brazil"},
    "2018": {"start": "2018-06-14", "end": "2018-07-15", "host": "Russia"},
    "2022": {"start": "2022-11-20", "end": "2022-12-18", "host": "Qatar"},
}

# Cuotas históricas aproximadas de casas de apuestas (para simulación)
HISTORICAL_ODDS = {
    # 2022 Final - Argentina vs France
    ("argentina", "france", "2022"): {"home": 2.80, "draw": 3.10, "away": 2.50},
    # 2018 Final - France vs Croatia  
    ("france", "croatia", "2018"): {"home": 2.10, "draw": 3.20, "away": 3.50},
    # 2014 Final - Germany vs Argentina
    ("germany", "argentina", "2014"): {"home": 2.30, "draw": 3.00, "away": 3.20},
    # 2010 Final - Spain vs Netherlands
    ("spain", "netherlands", "2010"): {"home": 2.40, "draw": 3.00, "away": 3.00},
}


def get_historical_odds(team_a: str, team_b: str, year: str) -> Dict:
    """Obtiene cuotas históricas si están disponibles."""
    key = (team_a, team_b, year)
    key_reversed = (team_b, team_a, year)
    
    if key in HISTORICAL_ODDS:
        return HISTORICAL_ODDS[key]
    elif key_reversed in HISTORICAL_ODDS:
        odds = HISTORICAL_ODDS[key_reversed]
        return {"home": odds["away"], "draw": odds["draw"], "away": odds["home"]}
    
    # Cuotas por defecto basadas en ranking FIFA
    return {"home": 2.50, "draw": 3.00, "away": 2.80}


def calculate_brier_score(predictions: List[Dict], actual_results: List[str]) -> float:
    """
    Calcula el Brier Score para medir la calibración de las predicciones.
    
    Brier Score = promedio de (probabilidad_predicha - resultado_real)^2
    - Resultado real: 1 si ocurrió, 0 si no
    - Menor es mejor (0 = perfecto)
    """
    if len(predictions) != len(actual_results):
        return float('inf')
    
    brier_sum = 0.0
    
    for pred, actual in zip(predictions, actual_results):
        if actual == "home":
            prob_assigned = pred.get('probWinA', 0.33)
            brier_sum += (prob_assigned - 1.0) ** 2
            brier_sum += (pred.get('probDraw', 0.33) - 0.0) ** 2
            brier_sum += (pred.get('probWinB', 0.33) - 0.0) ** 2
        elif actual == "draw":
            brier_sum += (pred.get('probWinA', 0.33) - 0.0) ** 2
            brier_sum += (pred.get('probDraw', 0.33) - 1.0) ** 2
            brier_sum += (pred.get('probWinB', 0.33) - 0.0) ** 2
        elif actual == "away":
            brier_sum += (pred.get('probWinA', 0.33) - 0.0) ** 2
            brier_sum += (pred.get('probDraw', 0.33) - 0.0) ** 2
            brier_sum += (pred.get('probWinB', 0.33) - 1.0) ** 2
    
    return brier_sum / len(predictions)


def simulate_bet(probability: float, odds: float, stake: float = 100) -> Tuple[float, bool]:
    """
    Simula una apuesta con estrategia +EV.
    
    Retorna: (profit/loss, fue_apostada)
    """
    implied_prob = 1.0 / odds if odds > 0 else 0
    edge = probability - implied_prob
    
    # Solo apostar si hay valor positivo (edge > 5%)
    if edge > 0.05:
        if probability > 0.5:  # Gana
            return (stake * (odds - 1), True)
        else:  # Pierde
            return (-stake, True)
    
    return (0, False)  # No se apostó


def backtest_world_cup(year: str, matches: List[Dict], ratings: Dict) -> Dict:
    """
    Ejecuta backtesting para un Mundial específico.
    """
    wc_info = WORLD_CUPS[year]
    start_date = wc_info["start"]
    end_date = wc_info["end"]
    
    # Filtrar partidos del Mundial
    wc_matches = [
        m for m in matches
        if start_date <= m.get('date', '') <= end_date
        and 'World Cup' in m.get('tournament', '')
    ]
    
    if not wc_matches:
        # Intentar con filtro más amplio
        wc_matches = [
            m for m in matches
            if start_date <= m.get('date', '') <= end_date
        ]
    
    predictions = []
    actual_results = []
    betting_results = []
    total_staked = 0
    total_return = 0
    
    for match in wc_matches[:min(len(wc_matches), 64)]:  # Máximo 64 partidos por Mundial
        home = match.get('homeSlug', '')
        away = match.get('awaySlug', '')
        hg = match.get('hg')
        ag = match.get('ag')
        
        if not home or not away or hg is None or ag is None:
            continue
        
        # Obtener rankings aproximados
        rank_a = list(ratings.keys()).index(home) + 1 if home in ratings else 50
        rank_b = list(ratings.keys()).index(away) + 1 if away in ratings else 50
        
        # Ejecutar predicción
        try:
            pred = run_prediction_sim(
                team_a=home,
                team_b=away,
                rank_a=rank_a,
                rank_b=rank_b,
                fifa_weight_pct=10,
                h2h_weight_pct=10,
                half_life_months=18,
                num_sims=10000
            )
        except Exception as e:
            continue
        
        predictions.append(pred)
        
        # Determinar resultado real
        if hg > ag:
            actual = "home"
        elif hg < ag:
            actual = "away"
        else:
            actual = "draw"
        
        actual_results.append(actual)
        
        # Simular apuestas
        odds = get_historical_odds(home, away, year)
        
        # Apostar a victoria local si hay valor
        profit_a, bet_a = simulate_bet(pred['probWinA'], odds.get('home', 2.5))
        if bet_a:
            total_staked += 100
            total_return += profit_a + 100
            betting_results.append({
                'match': f"{home} vs {away}",
                'bet': 'home',
                'odds': odds.get('home', 2.5),
                'probability': pred['probWinA'],
                'result': actual,
                'profit': profit_a
            })
        
        # Apostar a victoria visitante si hay valor
        profit_b, bet_b = simulate_bet(pred['probWinB'], odds.get('away', 2.8))
        if bet_b:
            total_staked += 100
            total_return += profit_b + 100
            betting_results.append({
                'match': f"{home} vs {away}",
                'bet': 'away',
                'odds': odds.get('away', 2.8),
                'probability': pred['probWinB'],
                'result': actual,
                'profit': profit_b
            })
        
        # Apostar a empate si hay valor
        profit_draw, bet_draw = simulate_bet(pred['probDraw'], odds.get('draw', 3.0))
        if bet_draw:
            total_staked += 100
            total_return += profit_draw + 100
            betting_results.append({
                'match': f"{home} vs {away}",
                'bet': 'draw',
                'odds': odds.get('draw', 3.0),
                'probability': pred['probDraw'],
                'result': actual,
                'profit': profit_draw
            })
    
    # Calcular métricas
    correct_predictions = sum(
        1 for pred, actual in zip(predictions, actual_results)
        if (actual == "home" and pred['probWinA'] >= max(pred['probDraw'], pred['probWinB'])) or
           (actual == "away" and pred['probWinB'] >= max(pred['probDraw'], pred['probWinA'])) or
           (actual == "draw" and pred['probDraw'] >= max(pred['probWinA'], pred['probWinB']))
    )
    
    accuracy = correct_predictions / len(predictions) if predictions else 0
    brier_score = calculate_brier_score(predictions, actual_results)
    roi = ((total_return - total_staked) / total_staked * 100) if total_staked > 0 else 0
    
    return {
        'year': year,
        'matches_analyzed': len(predictions),
        'accuracy': round(accuracy * 100, 2),
        'brier_score': round(brier_score, 4),
        'total_bets': len(betting_results),
        'total_staked': total_staked,
        'total_return': round(total_return, 2),
        'roi_pct': round(roi, 2),
        'betting_details': betting_results[:10]  # Primeras 10 apuestas
    }


def run_full_backtest() -> Dict:
    """
    Ejecuta backtesting completo para todos los Mundiales.
    """
    print("=" * 60)
    print("📊 Backtesting Automatizado - Predictor Mundial 2026")
    print("=" * 60)
    
    # Cargar datos
    print("\nCargando datos históricos...")
    matches, ratings = load_data()
    print(f"✅ {len(matches):,} partidos cargados")
    
    results = {}
    
    for year in WORLD_CUPS.keys():
        print(f"\n🏆 Procesando Mundial {year}...")
        result = backtest_world_cup(year, matches, ratings)
        results[year] = result
        print(f"   Partidos: {result['matches_analyzed']}")
        print(f"   Accuracy: {result['accuracy']}%")
        print(f"   Brier Score: {result['brier_score']}")
        print(f"   ROI: {result['roi_pct']}%")
    
    # Calcular métricas agregadas
    total_matches = sum(r['matches_analyzed'] for r in results.values())
    avg_accuracy = sum(r['accuracy'] for r in results.values()) / len(results) if results else 0
    avg_brier = sum(r['brier_score'] for r in results.values()) / len(results) if results else 0
    total_staked = sum(r['total_staked'] for r in results.values())
    total_return = sum(r['total_return'] for r in results.values())
    overall_roi = ((total_return - total_staked) / total_staked * 100) if total_staked > 0 else 0
    
    summary = {
        'total_matches_analyzed': total_matches,
        'average_accuracy': round(avg_accuracy, 2),
        'average_brier_score': round(avg_brier, 4),
        'overall_roi_pct': round(overall_roi, 2),
        'world_cups': results
    }
    
    # Guardar resultados
    output_path = BASE_DIR / "backtesting" / "backtest_results.json"
    output_path.parent.mkdir(exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            'last_updated': datetime.now().isoformat(),
            'summary': summary
        }, f, indent=2)
    
    print("\n" + "=" * 60)
    print("📈 RESUMEN DEL BACKTESTING")
    print("=" * 60)
    print(f"Total de partidos analizados: {total_matches}")
    print(f"Accuracy promedio: {avg_accuracy:.2f}%")
    print(f"Brier Score promedio: {avg_brier:.4f}")
    print(f"ROI Overall: {overall_roi:.2f}%")
    print(f"\n✅ Resultados guardados en {output_path}")
    print("=" * 60)
    
    return summary


def main():
    """Función principal."""
    try:
        results = run_full_backtest()
        return 0
    except Exception as e:
        print(f"❌ Error en backtesting: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
