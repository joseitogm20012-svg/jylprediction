import json
import math
import os
import csv
import numpy as np
from datetime import datetime

# Load base path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_CSV_PATH = os.path.join(BASE_DIR, "data", "results.csv")
ELO_PATH = os.path.join(BASE_DIR, "data", "elo-calibrated.json")
XG_PATH = os.path.join(BASE_DIR, "data", "xg_by_team.json")

# Core Dixon-Coles correlation adjustment
DC_RHO = -0.13

# Load xG data at module initialization
_cached_xg_data = None
def load_xg_data():
    """Carga datos de xG por equipo."""
    global _cached_xg_data
    if _cached_xg_data is not None:
        return _cached_xg_data
    if os.path.exists(XG_PATH):
        with open(XG_PATH, 'r', encoding='utf-8') as f:
            xg_json = json.load(f)
            _cached_xg_data = xg_json.get('teams', {})
    else:
        _cached_xg_data = {}
    return _cached_xg_data

# Team name to slug mapping
NAME_TO_SLUG = {
    "Argentina": "argentina",
    "France": "france",
    "Spain": "spain",
    "Brazil": "brazil",
    "England": "england",
    "Portugal": "portugal",
    "Netherlands": "netherlands",
    "Germany": "germany",
    "Belgium": "belgium",
    "Italy": "italy",
    "Colombia": "colombia",
    "Croatia": "croatia",
    "Morocco": "morocco",
    "United States": "usa",
    "USA": "usa",
    "Switzerland": "switzerland",
    "Uruguay": "uruguay",
    "Japan": "japan",
    "Mexico": "mexico",
    "Senegal": "senegal",
    "Denmark": "denmark",
    "Iran": "iran",
    "Ecuador": "ecuador",
    "Australia": "australia",
    "South Korea": "south-korea",
    "Poland": "poland",
    "Wales": "wales",
    "Nigeria": "nigeria",
    "Peru": "peru",
    "Serbia": "serbia",
    "Qatar": "qatar",
    "Czech Republic": "czech-republic",
    "Czechia": "czech-republic",
    "Egypt": "egypt",
    "Ivory Coast": "ivory-coast",
    "Scotland": "scotland",
    "Canada": "canada",
    "Tunisia": "tunisia",
    "Chile": "chile",
    "Algeria": "algeria",
    "Panama": "panama",
    "Cameroon": "cameroon",
    "Jamaica": "jamaica",
    "Venezuela": "venezuela",
    "Paraguay": "paraguay",
    "South Africa": "south-africa",
    "Saudi Arabia": "saudi-arabia",
    "Ghana": "ghana",
    "Jordan": "jordan",
    "Bosnia and Herzegovina": "bosnia-and-herzegovina",
    "Honduras": "honduras",
    "El Salvador": "el-salvador",
    "New Zealand": "new-zealand",
    "Haiti": "haiti",
    "Trinidad and Tobago": "trinidad-and-tobago",
    "Guatemala": "guatemala",
    "Bolivia": "bolivia",
    "Costa Rica": "costa-rica",
    "Sweden": "sweden",
    "Norway": "norway",
    "Austria": "austria",
    "Turkey": "turkey",
    "Greece": "greece",
    "Russia": "russia",
    "Ukraine": "ukraine",
    "Romania": "romania",
    "Hungary": "hungary",
    "Slovakia": "slovakia",
    "Slovenia": "slovenia",
    "Finland": "finland",
    "Iceland": "iceland",
    "Albania": "albania",
    "Kosovo": "kosovo",
    "North Macedonia": "north-macedonia",
    "Israel": "israel",
    "Kuwait": "kuwait",
    "United Arab Emirates": "uae",
    "Bahrain": "bahrain",
    "Iraq": "iraq",
    "Oman": "oman",
    "Indonesia": "indonesia",
    "Thailand": "thailand",
    "Vietnam": "vietnam",
    "China PR": "china",
    "China": "china",
    "India": "india",
    "Mali": "mali",
    "Senegal": "senegal",
    "Burkina Faso": "burkina-faso",
    "Kenya": "kenya",
    "Tanzania": "tanzania",
    "Ethiopia": "ethiopia",
    "Uganda": "uganda",
    "Zimbabwe": "zimbabwe",
    "Zambia": "zambia",
    "Angola": "angola",
    "Mozambique": "mozambique",
    "Democratic Republic of the Congo": "dr-congo",
    "Congo DR": "dr-congo",
    "Republic of Ireland": "ireland",
    "Northern Ireland": "northern-ireland",
    "Cyprus": "cyprus",
    "Malta": "malta",
    "Luxembourg": "luxembourg",
    "Georgia": "georgia",
    "Armenia": "armenia",
    "Azerbaijan": "azerbaijan",
    "Kazakhstan": "kazakhstan",
    "Uzbekistan": "uzbekistan",
    "Cuba": "cuba",
    "Dominican Republic": "dominican-republic",
    "Nicaragua": "nicaragua",
    "Belize": "belize",
    "Guyana": "guyana",
    "Suriname": "suriname",
    "Libya": "libya",
    "Sudan": "sudan",
    "Congo": "congo",
    "Gabon": "gabon",
    "Rwanda": "rwanda",
    "Guinea": "guinea",
    "Guinea-Bissau": "guinea-bissau",
    "Sierra Leone": "sierra-leone",
    "Benin": "benin",
    "Togo": "togo",
    "Niger": "niger",
    "Cape Verde": "cape-verde",
    "Liberia": "liberia",
    "Mauritania": "mauritania",
    "Comoros": "comoros",
    "Seychelles": "seychelles",
    "Mauritius": "mauritius",
    "Swaziland": "eswatini",
    "Eswatini": "eswatini",
    "Lesotho": "lesotho",
    "Malawi": "malawi",
    "Botswana": "botswana",
    "Namibia": "namibia",
    "Madagascar": "madagascar",
    "Philippines": "philippines",
    "Myanmar": "myanmar",
    "Malaysia": "malaysia",
    "Singapore": "singapore",
    "Hong Kong": "hong-kong",
    "Macao": "macao",
    "Mongolia": "mongolia",
    "Nepal": "nepal",
    "Sri Lanka": "sri-lanka",
    "Bangladesh": "bangladesh",
    "Pakistan": "pakistan",
    "Afghanistan": "afghanistan",
    "Palestine": "palestine",
    "Lebanon": "lebanon",
    "Syria": "syria",
    "Yemen": "yemen",
}

def name_to_slug(name):
    if name in NAME_TO_SLUG:
        return NAME_TO_SLUG[name]
    return name.lower().replace(" ", "-").replace("'", "").replace(".", "")

_cached_matches = None
_cached_ratings = None

def load_data():
    global _cached_matches, _cached_ratings
    if _cached_matches is not None and _cached_ratings is not None:
        return _cached_matches, _cached_ratings

    # Load ratings
    with open(ELO_PATH, "r", encoding="utf-8") as f:
        elo_data = json.load(f)
    ratings = elo_data["ratings"]

    # Parse results.csv
    matches = []
    if os.path.exists(RESULTS_CSV_PATH):
        with open(RESULTS_CSV_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            match_id = 1
            for row in reader:
                try:
                    date_str = row["date"]
                    hg_val = row["home_score"]
                    ag_val = row["away_score"]
                    if not hg_val or not ag_val:
                        continue
                    hg = int(hg_val)
                    ag = int(ag_val)
                    
                    home_name = row["home_team"]
                    away_name = row["away_team"]
                    
                    try:
                        dt = datetime.strptime(date_str, "%Y-%m-%d")
                        ts = int(dt.timestamp())
                    except:
                        ts = 0

                    matches.append({
                        "id": match_id,
                        "date": date_str,
                        "ts": ts,
                        "homeSlug": name_to_slug(home_name),
                        "awaySlug": name_to_slug(away_name),
                        "homeName": home_name,
                        "awayName": away_name,
                        "hg": hg,
                        "ag": ag,
                        "tournament": row["tournament"],
                        "neutral": row["neutral"].upper() == "TRUE",
                        "city": row.get("city", ""),
                        "country": row.get("country", "")
                    })
                    match_id += 1
                except Exception as e:
                    continue

    matches.sort(key=lambda x: x["ts"])
    _cached_matches = matches
    _cached_ratings = ratings
    return _cached_matches, _cached_ratings

def dc_tau(a, b, lambda_a, lambda_b, rho=DC_RHO):
    if a == 0 and b == 0:
        return 1.0 - lambda_a * lambda_b * rho
    if a == 0 and b == 1:
        return 1.0 + lambda_a * rho
    if a == 1 and b == 0:
        return 1.0 + lambda_b * rho
    if a == 1 and b == 1:
        return 1.0 - rho
    return 1.0

def poisson_pmf(k, lambda_):
    if lambda_ <= 0:
        return 1.0 if k == 0 else 0.0
    return (lambda_**k * math.exp(-lambda_)) / math.factorial(k)

def get_team_history(team_slug, matches, ratings, half_life_months=18):
    team_matches = [m for m in matches if m.get("homeSlug") == team_slug or m.get("awaySlug") == team_slug]
    if not team_matches:
        return []
        
    latest_ts = max(m["ts"] for m in matches) if matches else int(datetime.now().timestamp())
    half_life_sec = half_life_months * 30.44 * 86400
    
    history = []
    for m in team_matches:
        if m.get("hg") is None or m.get("ag") is None:
            continue
            
        dt = latest_ts - m["ts"]
        weight = math.pow(0.5, dt / half_life_sec)
        
        is_home = m["homeSlug"] == team_slug
        gs = m["hg"] if is_home else m["ag"]
        gc = m["ag"] if is_home else m["hg"]
        
        opp_slug = m["awaySlug"] if is_home else m["homeSlug"]
        opp_name = m["awayName"] if is_home else m["homeName"]
        opp_elo = ratings.get(opp_slug, 1500)
        
        # Difficulty category
        opp_lvl = "Normal"
        if opp_elo >= 1850:
            opp_lvl = "Top Nivel"
        elif opp_elo >= 1700:
            opp_lvl = "Nivel Alto"
            
        history.append({
            "id": m["id"],
            "date": m["date"],
            "opponentName": opp_name,
            "opponentElo": opp_elo,
            "opponentLevel": opp_lvl,
            "goalsScored": gs,
            "goalsConceded": gc,
            "weight": weight
        })
        
    # Sort newest first
    history.sort(key=lambda x: x["date"], reverse=True)
    return history

def get_team_form_stats(team_slug, matches, ratings, half_life_months=18):
    history = get_team_history(team_slug, matches, ratings, half_life_months)
    if not history:
        return 1.0, 1.0
        
    total_w = 0.0
    weighted_gs = 0.0
    weighted_gc = 0.0
    
    for h in history:
        w = h["weight"]
        gs = h["goalsScored"]
        gc = h["goalsConceded"]
        opp_elo = h["opponentElo"]
        
        # Opponent quality adjustments:
        # Scoring against top opponent counts more
        # Conceding against weak opponent counts more as weakness
        q_off = opp_elo / 1650.0
        q_def = 1650.0 / opp_elo
        
        total_w += w
        weighted_gs += gs * q_off * w
        weighted_gc += gc * q_def * w
        
    avg_gs = (weighted_gs / total_w) if total_w > 0 else 1.0
    avg_gc = (weighted_gc / total_w) if total_w > 0 else 1.0
    
    return avg_gs, avg_gc

def get_h2h_stats(team_a, team_b, matches):
    direct_matches = [
        m for m in matches 
        if (m.get("homeSlug") == team_a and m.get("awaySlug") == team_b) or
           (m.get("homeSlug") == team_b and m.get("awaySlug") == team_a)
    ]
    
    wins_a = 0
    wins_b = 0
    draws = 0
    total_gd = 0
    matches_list = []
    
    for m in direct_matches:
        is_a_home = m["homeSlug"] == team_a
        gs_a = m["hg"] if is_a_home else m["ag"]
        gs_b = m["ag"] if is_a_home else m["hg"]
        
        if gs_a > gs_b:
            wins_a += 1
        elif gs_a == gs_b:
            draws += 1
        else:
            wins_b += 1
            
        total_gd += (gs_a - gs_b)
        matches_list.append({
            "date": m["date"],
            "homeName": m["homeName"],
            "awayName": m["awayName"],
            "hg": m["hg"],
            "ag": m["ag"]
        })
        
    avg_gd = (total_gd / len(direct_matches)) if direct_matches else 0.0
    
    return {
        "count": len(direct_matches),
        "winsA": wins_a,
        "winsB": wins_b,
        "draws": draws,
        "avgGd": avg_gd,
        "matches": matches_list
    }

def estimate_rho_from_data(matches, ratings, sample_size=2000):
    """
    Mejora 3: Estima el parámetro rho de Dixon-Coles desde los datos históricos.
    
    El parámetro rho captura la correlación entre goles de ambos equipos:
    - rho < 0: Los equipos tienden a no marcar simultáneamente (correlación negativa)
    - rho > 0: Los equipos tienden a marcar juntos (partidos abiertos)
    
    Para fútbol internacional, típicamente rho ≈ -0.13
    """
    if len(matches) < 100:
        return DC_RHO  # Valor por defecto si no hay suficientes datos
    
    # Muestrear partidos recientes (sin recalcular history)
    recent_matches = [m for m in matches if m.get('ts', 0) > 0]
    recent_matches.sort(key=lambda x: x['ts'], reverse=True)
    
    sample = recent_matches[:min(sample_size, len(recent_matches))]
    
    # Calcular frecuencias observadas de resultados
    obs_00 = sum(1 for m in sample if m['hg'] == 0 and m['ag'] == 0)
    obs_01 = sum(1 for m in sample if m['hg'] == 0 and m['ag'] == 1)
    obs_10 = sum(1 for m in sample if m['hg'] == 1 and m['ag'] == 0)
    obs_11 = sum(1 for m in sample if m['hg'] == 1 and m['ag'] == 1)
    
    n = len(sample)
    if n == 0 or obs_00 == 0:
        return DC_RHO
    
    # Frecuencias observadas
    p_00 = obs_00 / n
    p_01 = obs_01 / n
    p_10 = obs_10 / n
    p_11 = obs_11 / n
    
    # Calcular lambdas promedio usando solo goles directos (más rápido)
    total_hg = sum(m['hg'] for m in sample)
    total_ag = sum(m['ag'] for m in sample)
    avg_lambda_h = total_hg / n if n > 0 else 1.4
    avg_lambda_a = total_ag / n if n > 0 else 1.4
    
    # Probabilidades Poisson esperadas sin corrección
    pois_00 = math.exp(-avg_lambda_h) * math.exp(-avg_lambda_a)
    pois_01 = math.exp(-avg_lambda_h) * (avg_lambda_a ** 1 * math.exp(-avg_lambda_a))
    pois_10 = (avg_lambda_h ** 1 * math.exp(-avg_lambda_h)) * math.exp(-avg_lambda_a)
    pois_11 = (avg_lambda_h ** 1 * math.exp(-avg_lambda_h)) * (avg_lambda_a ** 1 * math.exp(-avg_lambda_a))
    
    # Estimar rho usando método de momentos
    rho_estimates = []
    
    if pois_00 > 0 and avg_lambda_h * avg_lambda_a > 0:
        rho_00 = (1 - p_00 / pois_00) / (avg_lambda_h * avg_lambda_a)
        rho_estimates.append(rho_00)
    
    if pois_01 > 0 and avg_lambda_h > 0:
        rho_01 = (p_01 / pois_01 - 1) / avg_lambda_h
        rho_estimates.append(rho_01)
    
    if pois_10 > 0 and avg_lambda_a > 0:
        rho_10 = (p_10 / pois_10 - 1) / avg_lambda_a
        rho_estimates.append(rho_10)
    
    if pois_11 > 0:
        rho_11 = (1 - p_11 / pois_11)
        rho_estimates.append(rho_11)
    
    if not rho_estimates:
        return DC_RHO
    
    # Promediar estimaciones y aplicar clamp al rango válido [-0.5, 0.5]
    rho_hat = sum(rho_estimates) / len(rho_estimates)
    rho_hat = max(-0.5, min(0.5, rho_hat))
    
    # Suavizar hacia el valor teórico (-0.13)
    rho_final = 0.7 * rho_hat + 0.3 * DC_RHO
    
    return round(rho_final, 4)


def calculate_xg(team_a, team_b, rank_a, rank_b, fifa_weight, h2h_weight, half_life_months, matches, ratings):
    # Cargar datos de xG histórico real
    xg_data = load_xg_data()
    
    # 1. Obtener xG real si está disponible (Mejora 2)
    xg_real_a_home = None
    xg_real_b_away = None
    
    if team_a in xg_data:
        xg_real_a_home = xg_data[team_a].get('xg_home') or xg_data[team_a].get('xg_overall')
    if team_b in xg_data:
        xg_real_b_away = xg_data[team_b].get('xg_away') or xg_data[team_b].get('xg_overall')
    
    # Get form stats
    gs_a, gc_a = get_team_form_stats(team_a, matches, ratings, half_life_months)
    gs_b, gc_b = get_team_form_stats(team_b, matches, ratings, half_life_months)
    
    # 2. Base expected goals from historical forms
    xg_a = gs_a * gc_b
    xg_b = gs_b * gc_a
    
    # Elo fallbacks if forms are too low
    elo_a = ratings.get(team_a, 1500)
    elo_b = ratings.get(team_b, 1500)
    if xg_a <= 0.1:
        xg_a = max(0.3, 1.35 + (elo_a - elo_b) / 400.0)
    if xg_b <= 0.1:
        xg_b = max(0.3, 1.35 + (elo_b - elo_a) / 400.0)
    
    # 3. BLEND con xG real si está disponible (60% real, 40% modelo)
    xg_source_a = "modelo"
    xg_source_b = "modelo"
    
    if xg_real_a_home and xg_real_a_home > 0:
        xg_a = 0.6 * xg_real_a_home + 0.4 * xg_a
        xg_source_a = "real"
    
    if xg_real_b_away and xg_real_b_away > 0:
        xg_b = 0.6 * xg_real_b_away + 0.4 * xg_b
        xg_source_b = "real"
        
    # 4. FIFA Ranking adjust
    rank_diff = rank_b - rank_a # positive = A is higher ranked
    fifa_mult_a = 1.0 + (rank_diff / 100.0) * fifa_weight
    fifa_mult_b = 1.0 - (rank_diff / 100.0) * fifa_weight
    
    xg_a *= max(0.2, fifa_mult_a)
    xg_b *= max(0.2, fifa_mult_b)
    
    # 5. H2H adjust
    h2h = get_h2h_stats(team_a, team_b, matches)
    h2h_mult_a = 1.0
    h2h_mult_b = 1.0
    if h2h["count"] > 0:
        h2h_mult_a = 1.0 + (h2h["avgGd"] / 4.0) * h2h_weight
        h2h_mult_b = 1.0 - (h2h["avgGd"] / 4.0) * h2h_weight
        xg_a *= max(0.2, h2h_mult_a)
        xg_b *= max(0.2, h2h_mult_b)
        
    # Clamping
    xg_a = max(0.1, min(4.5, xg_a))
    xg_b = max(0.1, min(4.5, xg_b))
    
    return xg_a, xg_b, h2h_mult_a, h2h_mult_b, xg_source_a, xg_source_b

def run_prediction_sim(team_a, team_b, rank_a, rank_b, fifa_weight_pct, h2h_weight_pct, half_life_months, num_sims, odds_a=None, odds_draw=None, odds_b=None):
    matches, ratings = load_data()
    
    fifa_weight = fifa_weight_pct / 100.0
    h2h_weight = h2h_weight_pct / 100.0
    
    # Calculate expected goals
    xg_a, xg_b, h2h_mult_a, h2h_mult_b, xg_source_a, xg_source_b = calculate_xg(
        team_a, team_b, rank_a, rank_b, fifa_weight, h2h_weight, half_life_months, matches, ratings
    )
    
    # Calculate exact joint probabilities up to 10 goals
    joint_probs = {}
    win_a_prob = 0.0
    draw_prob = 0.0
    win_b_prob = 0.0
    
    for a in range(11):
        pa = poisson_pmf(a, xg_a)
        for b in range(11):
            tau = dc_tau(a, b, xg_a, xg_b, DC_RHO)
            p = max(0.0, pa * poisson_pmf(b, xg_b) * tau)
            joint_probs[(a, b)] = p
            if a > b:
                win_a_prob += p
            elif a == b:
                draw_prob += p
            else:
                win_b_prob += p
                
    # Normalize probabilities
    total_prob = sum(joint_probs.values())
    if total_prob > 0:
        for k in joint_probs:
            joint_probs[k] /= total_prob
        win_a_prob /= total_prob
        draw_prob /= total_prob
        win_b_prob /= total_prob
        
    # Set up CDF for NumPy simulation
    score_keys = list(joint_probs.keys())
    score_probs = [joint_probs[k] for k in score_keys]
    cdf = np.cumsum(score_probs)
    
    # NumPy Monte Carlo simulation - vector implementation
    random_floats = np.random.rand(num_sims)
    sim_indices = np.searchsorted(cdf, random_floats)
    
    # Count outcomes
    sim_scores = [score_keys[i] for i in sim_indices]
    unique_scores, counts = np.unique(sim_scores, axis=0, return_counts=True)
    
    sim_win_a = 0
    sim_draw = 0
    sim_win_b = 0
    score_counts_dict = {}
    
    for score_pair, count in zip(unique_scores, counts):
        a, b = int(score_pair[0]), int(score_pair[1])
        score_counts_dict[f"{a}-{b}"] = int(count)
        if a > b:
            sim_win_a += count
        elif a == b:
            sim_draw += count
        else:
            sim_win_b += count
            
    # Compute percentages from simulation
    sim_pct_a = float(sim_win_a) / num_sims
    sim_pct_draw = float(sim_draw) / num_sims
    sim_pct_b = float(sim_win_b) / num_sims
    
    # Sort scores to find top 5
    sorted_scores = sorted(score_counts_dict.items(), key=lambda x: x[1], reverse=True)
    top_scores = []
    for score_str, count in sorted_scores[:5]:
        a, b = map(int, score_str.split("-"))
        top_scores.append({
            "score": score_str,
            "goalsA": a,
            "goalsB": b,
            "probability": float(count) / num_sims
        })
        
    # Betting Edge (+EV) calculations
    betting_analysis = {
        "hasOdds": False,
        "edgeA": 0.0,
        "edgeDraw": 0.0,
        "edgeB": 0.0,
        "valuableA": False,
        "valuableDraw": False,
        "valuableB": False
    }
    
    if odds_a and odds_draw and odds_b:
        betting_analysis["hasOdds"] = True
        
        # Calculate EV: Probability * Odds - 1
        edge_a = (sim_pct_a * odds_a) - 1.0
        edge_draw = (sim_pct_draw * odds_draw) - 1.0
        edge_b = (sim_pct_b * odds_b) - 1.0
        
        betting_analysis["edgeA"] = edge_a
        betting_analysis["edgeDraw"] = edge_draw
        betting_analysis["edgeB"] = edge_b
        
        betting_analysis["valuableA"] = edge_a > 0.0
        betting_analysis["valuableDraw"] = edge_draw > 0.0
        betting_analysis["valuableB"] = edge_b > 0.0
        
    return {
        "xgA": xg_a,
        "xgB": xg_b,
        "xgSourceA": xg_source_a,
        "xgSourceB": xg_source_b,
        "probWinA": sim_pct_a,
        "probDraw": sim_pct_draw,
        "probWinB": sim_pct_b,
        "topScores": top_scores,
        "bettingAnalysis": betting_analysis,
        "dcRho": DC_RHO
    }
