import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

failures = []

def ok(msg): print(f"  [OK]  {msg}")
def fail(msg): print(f"  [FAIL] {msg}"); failures.append(msg)

# ==============================
# TEST 1: predictor.py imports
# ==============================
print("\n=== TEST 1: Import predictor.py ===")
try:
    from predictor import load_data, run_prediction_sim, get_team_history, get_h2h_stats
    ok("Importado correctamente")
except Exception as e:
    fail(f"Error al importar predictor: {e}")
    sys.exit(1)

# ==============================
# TEST 2: LRU Cache in load_data
# ==============================
print("\n=== TEST 2: load_data + LRU Cache ===")
try:
    m, r = load_data()
    ok(f"Partidos cargados: {len(m)}")
    ok(f"Ratings cargados: {len(r)} equipos")
    m2, r2 = load_data()
    if m is m2:
        ok("LRU Cache activo (misma referencia de objeto en memoria)")
    else:
        fail("LRU Cache NO esta funcionando, devuelve objetos distintos")
except Exception as e:
    fail(f"Error en load_data: {e}")

# ==============================
# TEST 3: Full simulation Argentina vs Brazil
# ==============================
print("\n=== TEST 3: run_prediction_sim (Argentina vs Brasil) ===")
try:
    result = run_prediction_sim(
        team_a='argentina', team_b='brazil',
        rank_a=1, rank_b=6,
        fifa_weight_pct=30, h2h_weight_pct=20,
        half_life_months=18, num_sims=10000,
        odds_a=2.10, odds_draw=3.40, odds_b=3.20
    )
    ok(f"probWinA={result['probWinA']:.3f} probDraw={result['probDraw']:.3f} probWinB={result['probWinB']:.3f}")
    assert abs(result['probWinA'] + result['probDraw'] + result['probWinB'] - 1.0) < 0.01, "Probabilidades no suman 1"
    ok("Probabilidades suman ~1.0")
    ok(f"xG A={result['xgA']:.2f} B={result['xgB']:.2f} (fuente A={result['xgSourceA']} B={result['xgSourceB']})")
    ok(f"DC Rho={result['dcRho']}")
except Exception as e:
    fail(f"Error en simulacion basica: {e}")

# ==============================
# TEST 4: Asian Handicap (NEW)
# ==============================
print("\n=== TEST 4: Asian Handicap (NUEVO) ===")
try:
    gm = result['goalsMarkets']
    assert 'asianHandicap' in gm, "asianHandicap KEY FALTANTE en goalsMarkets"
    ah = gm['asianHandicap']
    for line in ['-1.5', '-0.5', '+0.5', '+1.5']:
        assert line in ah, f"Linea AH {line} faltante"
        assert 'teamA' in ah[line] and 'teamB' in ah[line], f"teamA/teamB faltante en AH {line}"
        total = ah[line]['teamA'] + ah[line]['teamB']
        assert abs(total - 1.0) < 0.001, f"AH {line} no suma 1.0 (suma={total})"
        ok(f"AH {line}: A={ah[line]['teamA']:.3f} B={ah[line]['teamB']:.3f} (suma={total:.4f})")
except Exception as e:
    fail(f"Error en Asian Handicap: {e}")

# ==============================
# TEST 5: Goals Markets (existing)
# ==============================
print("\n=== TEST 5: Mercados de Goles (existentes) ===")
try:
    gm = result['goalsMarkets']
    for key in ['btts', 'doubleChance', 'dnb', 'overUnder']:
        assert key in gm, f"Mercado {key} FALTANTE"
        ok(f"Mercado '{key}' presente")
    ou_lines = [ou['threshold'] for ou in gm['overUnder']]
    assert 0.5 in ou_lines and 1.5 in ou_lines and 2.5 in ou_lines and 3.5 in ou_lines
    ok(f"Over/Under tiene lineas: {ou_lines}")
except Exception as e:
    fail(f"Error en mercados de goles: {e}")

# ==============================
# TEST 6: Corners (improved)
# ==============================
print("\n=== TEST 6: Modelo de Corners (mejorado) ===")
try:
    cp = result['cornersPrediction']
    assert 'expectedA' in cp and 'expectedB' in cp and 'expectedTotal' in cp
    assert cp['expectedA'] > 0 and cp['expectedB'] > 0
    assert abs(cp['expectedTotal'] - (cp['expectedA'] + cp['expectedB'])) < 0.5
    ok(f"Corners: A={cp['expectedA']:.1f} B={cp['expectedB']:.1f} Total={cp['expectedTotal']:.1f}")
    ok(f"Prob. mas corners: A={cp['probMostA']:.3f} Draw={cp['probMostDraw']:.3f} B={cp['probMostB']:.3f}")
    ou_c = [ou['threshold'] for ou in cp['overUnder']]
    ok(f"Corners Over/Under lineas: {ou_c}")
except Exception as e:
    fail(f"Error en modelo de corners: {e}")

# ==============================
# TEST 7: Betting Analysis (+EV)
# ==============================
print("\n=== TEST 7: Betting Analysis (+EV) ===")
try:
    ba = result['bettingAnalysis']
    assert ba['hasOdds'] == True, "hasOdds deberia ser True con odds dados"
    ok(f"EV A={ba['edgeA']:.3f} Draw={ba['edgeDraw']:.3f} B={ba['edgeB']:.3f}")
    ok(f"Valuable A={ba['valuableA']} Draw={ba['valuableDraw']} B={ba['valuableB']}")
except Exception as e:
    fail(f"Error en betting analysis: {e}")

# ==============================
# TEST 8: Top Scores (Correct Score)
# ==============================
print("\n=== TEST 8: Top Scores (Correct Score) ===")
try:
    ts = result['topScores']
    assert len(ts) > 0, "topScores vacio"
    ok(f"Top 5 marcadores: {[s['score'] for s in ts]}")
    ok(f"Probabilidades: {[round(s['probability']*100,1) for s in ts]}%")
except Exception as e:
    fail(f"Error en top scores: {e}")

# ==============================
# TEST 9: H2H and History
# ==============================
print("\n=== TEST 9: H2H y Historial ===")
try:
    m, r = load_data()
    history = get_team_history('argentina', m, r, 18)
    assert len(history) > 0, "Historial de Argentina vacio"
    ok(f"Historial Argentina: {len(history)} partidos")
    h2h = get_h2h_stats('argentina', 'brazil', m)
    ok(f"H2H Argentina vs Brasil: {h2h['count']} partidos, A wins={h2h['winsA']} B wins={h2h['winsB']} draws={h2h['draws']}")
except Exception as e:
    fail(f"Error en H2H/historial: {e}")

# ==============================
# TEST 11: Refactored calculate_xg (FASE 2)
# ==============================
print("\n=== TEST 11: calculate_xg load & compute refactoring ===")
try:
    from predictor import load_match_raw_data, compute_xg_from_raw_data, load_xg_data
    xg_data = load_xg_data()
    raw = load_match_raw_data('argentina', 'brazil', 18, m, r, xg_data)
    assert "gs_a" in raw and "gs_b" in raw and "elo_a" in raw
    ok("load_match_raw_data cargó datos de forma y Elo")
    
    xg_a, xg_b, _, _, _, _ = compute_xg_from_raw_data(raw, 1, 6, 0.3, 0.2)
    assert xg_a > 0 and xg_b > 0
    ok(f"compute_xg_from_raw_data calculó xG correctos: A={xg_a:.2f} B={xg_b:.2f}")
except Exception as e:
    fail(f"Error en refactorización calculate_xg: {e}")

# ==============================
# TEST 12: Overrides y Ajustes de Altitud (FASES 4 & 5)
# ==============================
print("\n=== TEST 12: Overrides y Ajustes de Altitud ===")
try:
    res_base = run_prediction_sim('argentina', 'brazil', 1, 6, 30, 20, 18, 1000)
    xg_base_a = res_base['xgA']
    xg_base_b = res_base['xgB']
    
    res_override = run_prediction_sim('argentina', 'brazil', 1, 6, 30, 20, 18, 1000, strength_override_a=0.5)
    assert res_override['xgA'] < xg_base_a
    ok(f"Override de fuerza aplicado: xG A base={xg_base_a:.2f} -> override={res_override['xgA']:.2f}")
    
    res_alt = run_prediction_sim('argentina', 'brazil', 1, 6, 30, 20, 18, 1000, altitude=3000)
    assert res_alt['xgA'] < xg_base_a
    assert res_alt['xgB'] < xg_base_b
    ok(f"Ajuste por altitud (3000m) aplicado a no aclimatados: xG A={res_alt['xgA']:.2f} (base={xg_base_a:.2f}) B={res_alt['xgB']:.2f} (base={xg_base_b:.2f})")
except Exception as e:
    fail(f"Error en overrides/altitud: {e}")

# ==============================
# TEST 10: main.py API routes (UPDATED FASE 6)
# ==============================
print("\n=== TEST 10: main.py (API Routes) ===")
try:
    from main import app
    routes = [r.path for r in app.routes]
    required = ['/api/teams', '/api/predict', '/api/history/{team_slug}', '/api/h2h/{team_a}/{team_b}', '/api/backtest-metrics', '/api/run-backtest', '/api/log-prediction', '/api/logged-predictions', '/api/update-prediction-results', '/api/resolve-prediction']
    for route in required:
        if route in routes:
            ok(f"Ruta presente: {route}")
        else:
            fail(f"Ruta FALTANTE: {route}")
except Exception as e:
    fail(f"Error al cargar main.py: {e}")

# ==============================
# FINAL SUMMARY
# ==============================
print("\n" + "="*50)
if failures:
    print(f"[FALLO] {len(failures)} fallo(s) detectados:")
    for f in failures:
        print(f"  - {f}")
    sys.exit(1)
else:
    print("[EXITO] TODOS LOS TESTS PASARON - El programa funciona correctamente")
    print("="*50)
