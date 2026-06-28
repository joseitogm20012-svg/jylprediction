import json
import math
import os
import csv
import numpy as np
from datetime import datetime
from functools import lru_cache

# Load base path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_CSV_PATH = os.path.join(BASE_DIR, "data", "results.csv")
ELO_PATH = os.path.join(BASE_DIR, "data", "elo-calibrated.json")
XG_PATH = os.path.join(BASE_DIR, "data", "xg_by_team.json")

# Core Dixon-Coles correlation adjustment
DC_RHO = -0.13

# Altitude acclimated teams (Fase 5)
ALTITUDE_ACCLIMATED_TEAMS = {"mexico", "ecuador", "colombia", "bolivia"}

# WC 2026 host countries and their home advantage for CONCACAF teams
WC2026_HOST_CONCACAF = {
    "usa":        {"usa": 0.08, "canada": 0.03, "mexico": 0.03},
    "canada":     {"canada": 0.08, "usa": 0.03, "mexico": 0.03},
    "mexico":     {"mexico": 0.08, "usa": 0.03, "canada": 0.03},
}
CONCACAF_TEAMS = {"usa", "mexico", "canada", "panama", "honduras", "costa-rica",
                   "jamaica", "haiti", "trinidad-and-tobago", "curacao", "el-salvador",
                   "guatemala", "nicaragua", "cuba"}

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

@lru_cache(maxsize=1)
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
                        parts = date_str.split("-")
                        dt = datetime(int(parts[0]), int(parts[1]), int(parts[2]))
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

_goalscorers_cache = None
_active_scorers_set = None

def load_goalscorers_data():
    global _goalscorers_cache, _active_scorers_set
    if _goalscorers_cache is not None:
        return _goalscorers_cache, _active_scorers_set
        
    _goalscorers_cache = {}
    _active_scorers_set = set()
    
    goalscorers_path = os.path.join(BASE_DIR, "data", "goalscorers.csv")
    if os.path.exists(goalscorers_path):
        with open(goalscorers_path, "r", encoding="utf-8", errors="replace") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    date_str = row.get("date", "")
                    home_team = row.get("home_team", "")
                    away_team = row.get("away_team", "")
                    team = row.get("team", "")
                    scorer = row.get("scorer", "")
                    minute_val = row.get("minute", "")
                    own_goal = row.get("own_goal", "").upper() == "TRUE"
                    penalty = row.get("penalty", "").upper() == "TRUE"
                    
                    if not date_str or not scorer:
                        continue
                        
                    minute = int(minute_val) if minute_val and minute_val.isdigit() else 0
                    
                    # Track active players (scored in 2021 or later)
                    parts = date_str.split("-")
                    if parts and int(parts[0]) >= 2021:
                        _active_scorers_set.add(scorer)
                        
                    # Index by team slugs
                    slug1 = name_to_slug(home_team)
                    slug2 = name_to_slug(away_team)
                    key = tuple(sorted([slug1, slug2]))
                    
                    if key not in _goalscorers_cache:
                        _goalscorers_cache[key] = []
                        
                    _goalscorers_cache[key].append({
                        "date": date_str,
                        "home_team": home_team,
                        "away_team": away_team,
                        "team": team,
                        "scorer": scorer,
                        "minute": minute,
                        "own_goal": own_goal,
                        "penalty": penalty
                    })
                except Exception as e:
                    continue
    return _goalscorers_cache, _active_scorers_set

def get_advanced_h2h_center_data(team_a, team_b):
    matches, ratings = load_data()
    
    name_a = team_a.replace("-", " ").title()
    name_b = team_b.replace("-", " ").title()
    for m in matches:
        if m["homeSlug"] == team_a:
            name_a = m["homeName"]
            break
        elif m["awaySlug"] == team_a:
            name_a = m["awayName"]
            break
            
    for m in matches:
        if m["homeSlug"] == team_b:
            name_b = m["homeName"]
            break
        elif m["awaySlug"] == team_b:
            name_b = m["awayName"]
            break

    # Direct Matches
    direct = [
        m for m in matches 
        if (m["homeSlug"] == team_a and m["awaySlug"] == team_b) or
           (m["homeSlug"] == team_b and m["awaySlug"] == team_a)
    ]
    
    count = len(direct)
    wins_a = 0
    wins_b = 0
    draws = 0
    total_goals = 0
    goals_a = 0
    goals_b = 0
    
    btts_count = 0
    over25_count = 0
    cs_a_count = 0
    cs_b_count = 0
    
    local_a_matches = 0
    local_a_wins = 0
    local_a_draws = 0
    local_a_losses = 0
    
    visit_a_matches = 0
    visit_a_wins = 0
    visit_a_draws = 0
    visit_a_losses = 0
    
    neutral_matches = 0
    neutral_wins_a = 0
    neutral_draws = 0
    neutral_wins_b = 0
    
    comp_records = {}
    score_counts = {}
    timeline_matches = []
    
    max_diff = -1
    biggest_win_str = "No registrado"
    
    for m in direct:
        is_a_home = m["homeSlug"] == team_a
        gs_a = m["hg"] if is_a_home else m["ag"]
        gs_b = m["ag"] if is_a_home else m["hg"]
        
        if gs_a > gs_b:
            wins_a += 1
            winner_slug = "A"
        elif gs_a < gs_b:
            wins_b += 1
            winner_slug = "B"
        else:
            draws += 1
            winner_slug = "Draw"
            
        total_goals += (gs_a + gs_b)
        goals_a += gs_a
        goals_b += gs_b
        
        if gs_a > 0 and gs_b > 0:
            btts_count += 1
        if (gs_a + gs_b) > 2.5:
            over25_count += 1
        if gs_b == 0:
            cs_a_count += 1
        if gs_a == 0:
            cs_b_count += 1
            
        if m["neutral"]:
            neutral_matches += 1
            if winner_slug == "A":
                neutral_wins_a += 1
            elif winner_slug == "B":
                neutral_wins_b += 1
            else:
                neutral_draws += 1
        elif is_a_home:
            local_a_matches += 1
            if winner_slug == "A":
                local_a_wins += 1
            elif winner_slug == "B":
                local_a_losses += 1
            else:
                local_a_draws += 1
        else:
            visit_a_matches += 1
            if winner_slug == "A":
                visit_a_wins += 1
            elif winner_slug == "B":
                visit_a_losses += 1
            else:
                visit_a_draws += 1
                
        comp = m["tournament"]
        if comp not in comp_records:
            comp_records[comp] = {"pj": 0, "winsA": 0, "draws": 0, "winsB": 0}
        comp_records[comp]["pj"] += 1
        if winner_slug == "A":
            comp_records[comp]["winsA"] += 1
        elif winner_slug == "B":
            comp_records[comp]["winsB"] += 1
        else:
            comp_records[comp]["draws"] += 1
            
        score_key = f"{gs_a}-{gs_b}"
        score_counts[score_key] = score_counts.get(score_key, 0) + 1
        
        diff = abs(gs_a - gs_b)
        if diff > max_diff:
            max_diff = diff
            if gs_a > gs_b:
                biggest_win_str = f"{name_a} {gs_a}-{gs_b} {name_b} ({m['date'].split('-')[0]})"
            elif gs_b > gs_a:
                biggest_win_str = f"{name_b} {gs_b}-{gs_a} {name_a} ({m['date'].split('-')[0]})"
            else:
                biggest_win_str = f"Empate {gs_a}-{gs_b} ({m['date'].split('-')[0]})"
                
        timeline_matches.append({
            "date": m["date"],
            "homeName": m["homeName"],
            "awayName": m["awayName"],
            "hg": m["hg"],
            "ag": m["ag"],
            "tournament": m["tournament"],
            "winner": winner_slug
        })
        
    avg_goals = (total_goals / count) if count > 0 else 0.0
    btts_pct = (btts_count / count * 100) if count > 0 else 0.0
    over25_pct = (over25_count / count * 100) if count > 0 else 0.0
    cs_a_pct = (cs_a_count / count * 100) if count > 0 else 0.0
    cs_b_pct = (cs_b_count / count * 100) if count > 0 else 0.0
    
    home_a_str = f"{local_a_wins}V-{local_a_draws}E-{local_a_losses}D" if local_a_matches > 0 else "0V-0E-0D"
    away_a_str = f"{visit_a_wins}V-{visit_a_draws}E-{visit_a_losses}D" if visit_a_matches > 0 else "0V-0E-0D"
    neutral_str = f"{neutral_wins_a}V-{neutral_draws}E-{neutral_wins_b}D" if neutral_matches > 0 else "0V-0E-0D"
    
    most_freq_scores = sorted(
        [{"score": k, "count": v} for k, v in score_counts.items()],
        key=lambda x: x["count"],
        reverse=True
    )[:5]
    
    last_winner_badge = "No hay partidos previos"
    if direct:
        last_m = direct[-1]
        last_yr = last_m["date"].split("-")[0]
        is_a_home = last_m["homeSlug"] == team_a
        winner_slug = "A" if last_m["hg"] > last_m["ag"] else ("B" if last_m["ag"] > last_m["hg"] else "Draw")
        if not is_a_home and winner_slug != "Draw":
            winner_slug = "B" if winner_slug == "A" else "A"
            
        if winner_slug == "A":
            last_winner_badge = f"🔥 {name_a} ganó el último H2H ({last_yr})"
        elif winner_slug == "B":
            last_winner_badge = f"🔥 {name_b} ganó el último H2H ({last_yr})"
        else:
            last_winner_badge = f"⚡ Vienen de empatar el último H2H ({last_yr})"
            
        win_a_years = [m["date"].split("-")[0] for m in direct if (m["hg"] > m["ag"] and m["homeSlug"] == team_a) or (m["ag"] > m["hg"] and m["awaySlug"] == team_a)]
        win_b_years = [m["date"].split("-")[0] for m in direct if (m["hg"] > m["ag"] and m["homeSlug"] == team_b) or (m["ag"] > m["hg"] and m["awaySlug"] == team_b)]
        
        last_win_yr_a = win_a_years[-1] if win_a_years else None
        last_win_yr_b = win_b_years[-1] if win_b_years else None
        
        current_year = 2026
        if last_win_yr_a and (current_year - int(last_win_yr_a)) >= 5:
            last_winner_badge = f"🔥 {name_a} no le gana a {name_b} desde {last_win_yr_a}"
        elif last_win_yr_b and (current_year - int(last_win_yr_b)) >= 5:
            last_winner_badge = f"🔥 {name_b} no le gana a {name_a} desde {last_win_yr_b}"
            
    scorers_cache, active_set = load_goalscorers_data()
    h2h_scorers = scorers_cache.get(tuple(sorted([team_a, team_b])), [])
    
    direct_dates = set(m["date"] for m in direct)
    matched_scorers = [s for s in h2h_scorers if s["date"] in direct_dates]
    
    scorer_counts = {}
    all_minutes = []
    penalties_count = 0
    own_goals_count = 0
    period_counts = {"0-15": 0, "16-30": 0, "31-45": 0, "46-60": 0, "61-75": 0, "76-90": 0}
    
    for s in matched_scorers:
        sname = s["scorer"]
        steam = name_to_slug(s["team"])
        steam_display = "ARG" if steam == "argentina" else ("URU" if steam == "uruguay" else steam[:3].upper())
        
        if sname not in scorer_counts:
            scorer_counts[sname] = {"goals": 0, "team": steam_display, "active": sname in active_set}
        scorer_counts[sname]["goals"] += 1
        
        min_val = s["minute"]
        if min_val > 0:
            all_minutes.append(min_val)
            if min_val <= 15:
                period_counts["0-15"] += 1
            elif min_val <= 30:
                period_counts["16-30"] += 1
            elif min_val <= 45:
                period_counts["31-45"] += 1
            elif min_val <= 60:
                period_counts["46-60"] += 1
            elif min_val <= 75:
                period_counts["61-75"] += 1
            else:
                period_counts["76-90"] += 1
                
        if s["penalty"]:
            penalties_count += 1
        if s["own_goal"]:
            own_goals_count += 1
            
    top_scorers_list = sorted(
        [{"name": k, "goals": v["goals"], "team": v["team"], "active": v["active"]} for k, v in scorer_counts.items()],
        key=lambda x: x["goals"],
        reverse=True
    )[:5]
    
    avg_goal_minute = int(np.mean(all_minutes)) if all_minutes else 0
    total_min_goals = len(all_minutes)
    period_pct = {}
    for k, v in period_counts.items():
        period_pct[k] = round(v / total_min_goals * 100) if total_min_goals > 0 else 0
        
    history_a = get_team_history(team_a, matches, ratings, 18)[:10]
    history_b = get_team_history(team_b, matches, ratings, 18)[:10]
    
    def analyze_form(history_list, team_slug):
        if not history_list:
            return {
                "record": "0V-0E-0D", "avg_gf": 0.0, "avg_gc": 0.0, "clean_sheets": 0, "btts": 0, "over25": 0,
                "streaks": {"unbeaten": 0, "losing": 0, "scoring": 0, "clean_sheet": 0},
                "by_rival": {"top": "0V-0E-0D", "high": "0V-0E-0D", "medium": "0V-0E-0D"}
            }
            
        wins = sum(1 for h in history_list if h["goalsScored"] > h["goalsConceded"])
        draws = sum(1 for h in history_list if h["goalsScored"] == h["goalsConceded"])
        losses = sum(1 for h in history_list if h["goalsScored"] < h["goalsConceded"])
        
        gf_total = sum(h["goalsScored"] for h in history_list)
        gc_total = sum(h["goalsConceded"] for h in history_list)
        n = len(history_list)
        
        cs = sum(1 for h in history_list if h["goalsConceded"] == 0)
        btts_c = sum(1 for h in history_list if h["goalsScored"] > 0 and h["goalsConceded"] > 0)
        o25 = sum(1 for h in history_list if h["goalsScored"] + h["goalsConceded"] > 2.5)
        
        unbeaten_streak = 0
        for h in history_list:
            if h["goalsScored"] >= h["goalsConceded"]:
                unbeaten_streak += 1
            else:
                break
                
        losing_streak = 0
        for h in history_list:
            if h["goalsScored"] < h["goalsConceded"]:
                losing_streak += 1
            else:
                break
                
        scoring_streak = 0
        for h in history_list:
            if h["goalsScored"] > 0:
                scoring_streak += 1
            else:
                break
                
        cs_streak = 0
        for h in history_list:
            if h["goalsConceded"] == 0:
                cs_streak += 1
            else:
                break
                
        rival_records = {
            "Top Nivel": {"w": 0, "d": 0, "l": 0},
            "Nivel Alto": {"w": 0, "d": 0, "l": 0},
            "Normal": {"w": 0, "d": 0, "l": 0}
        }
        for h in history_list:
            lvl = h["opponentLevel"]
            if h["goalsScored"] > h["goalsConceded"]:
                rival_records[lvl]["w"] += 1
            elif h["goalsScored"] == h["goalsConceded"]:
                rival_records[lvl]["d"] += 1
            else:
                rival_records[lvl]["l"] += 1
                
        def fmt_rec(rec):
            return f"{rec['w']}V-{rec['d']}E-{rec['l']}D"
            
        return {
            "record": f"{wins}V - {draws}E - {losses}D",
            "avg_gf": round(gf_total / n, 1) if n > 0 else 0.0,
            "avg_gc": round(gc_total / n, 1) if n > 0 else 0.0,
            "clean_sheets": round(cs / n * 100) if n > 0 else 0,
            "btts": round(btts_c / n * 100) if n > 0 else 0,
            "over25": round(o25 / n * 100) if n > 0 else 0,
            "streaks": {
                "unbeaten": unbeaten_streak,
                "losing": losing_streak,
                "scoring": scoring_streak,
                "clean_sheet": cs_streak
            },
            "by_rival": {
                "top": fmt_rec(rival_records["Top Nivel"]),
                "high": fmt_rec(rival_records["Nivel Alto"]),
                "medium": fmt_rec(rival_records["Normal"])
            }
        }
        
    form_stats_a = analyze_form(history_a, team_a)
    form_stats_b = analyze_form(history_b, team_b)
    
    detected_patterns = []
    if count > 0:
        if btts_pct >= 70:
            detected_patterns.append(f"✅ En {round(btts_pct)}% de los H2H, ambos equipos anotan.")
        if over25_pct >= 50:
            detected_patterns.append(f"✅ {round(over25_pct)}% de los partidos terminan con Over 2.5 goles.")
        if local_a_matches >= 2 and local_a_losses == 0:
            detected_patterns.append(f"✅ {name_a} no pierde como local en H2H ({home_a_str}).")
        if visit_a_matches >= 2 and visit_a_wins == 0:
            detected_patterns.append(f"⚠️ {name_b} no gana como visitante en H2H ({away_a_str.replace('D', 'V').replace('V', 'D')}).")
        detected_patterns.append(f"💡 El promedio de goles es {avg_goals:.1f}/partido.")
    else:
        detected_patterns.append("💡 Sin partidos previos registrados. Toda la predicción se basa en forma actual.")
        
    if form_stats_a["streaks"]["unbeaten"] >= 3:
        detected_patterns.append(f"🔥 {name_a}: {form_stats_a['streaks']['unbeaten']} partidos sin perder.")
    if form_stats_b["streaks"]["losing"] >= 2:
        detected_patterns.append(f"⚠️ {name_b}: {form_stats_b['streaks']['losing']} derrotas consecutivas.")
        
    comparative_matrix = {
        "avg_goals": {
            "h2h": f"{avg_goals:.1f}",
            "team_a": f"{form_stats_a['avg_gf'] + form_stats_a['avg_gc']:.1f}",
            "team_b": f"{form_stats_b['avg_gf'] + form_stats_b['avg_gc']:.1f}"
        },
        "btts": {
            "h2h": f"{round(btts_pct)}%",
            "team_a": f"{form_stats_a['btts']}%",
            "team_b": f"{form_stats_b['btts']}%"
        },
        "over25": {
            "h2h": f"{round(over25_pct)}%",
            "team_a": f"{form_stats_a['over25']}%",
            "team_b": f"{form_stats_b['over25']}%"
        },
        "clean_sheets": {
            "h2h": f"{round(cs_a_pct)}% (A) / {round(cs_b_pct)}% (B)",
            "team_a": f"{form_stats_a['clean_sheets']}%",
            "team_b": f"{form_stats_b['clean_sheets']}%"
        }
    }
    
    pred_res = "Empate"
    pred_prob = 33
    if count > 0:
        pct_a = wins_a / count * 100
        pct_b = wins_b / count * 100
        pct_d = draws / count * 100
        
        if pct_a > pct_b and pct_a > pct_d:
            pred_res = f"Victoria {name_a}"
            pred_prob = round(pct_a)
        elif pct_b > pct_a and pct_b > pct_d:
            pred_res = f"Victoria {name_b}"
            pred_prob = round(pct_b)
        else:
            pred_res = "Empate"
            pred_prob = round(pct_d)
            
    confidence = "MEDIA"
    if count >= 8:
        confidence = "ALTA"
    elif count < 4:
        confidence = "BAJA"
        
    most_freq_str = most_freq_scores[0]["score"] if most_freq_scores else "1-1"
    
    historical_prediction = {
        "outcome": pred_res,
        "probability": pred_prob,
        "freq_score": most_freq_str,
        "exp_goals": round(avg_goals, 1),
        "confidence": confidence,
        "sample_size": count
    }
    
    return {
        "h2h": {
            "count": count,
            "winsA": wins_a,
            "winsB": wins_b,
            "draws": draws,
            "goalsA": goals_a,
            "goalsB": goals_b,
            "avgGoals": avg_goals,
            "biggestWin": biggest_win_str,
            "patterns": {
                "btts": round(btts_pct),
                "over25": round(over25_pct),
                "csA": round(cs_a_pct),
                "csB": round(cs_b_pct)
            },
            "byCondition": {
                "homeA": home_a_str,
                "awayA": away_a_str,
                "neutral": neutral_str
            },
            "byCompetition": [{"competition": k, "pj": v["pj"], "winsA": v["winsA"], "draws": v["draws"], "winsB": v["winsB"]} for k, v in comp_records.items()],
            "mostFrequentScores": most_freq_scores,
            "lastWinner": last_winner_badge,
            "timeline": timeline_matches
        },
        "scorers": {
            "topScorers": top_scorers_list,
            "avgGoalMinute": avg_goal_minute,
            "periodDistribution": period_pct,
            "penaltiesCount": penalties_count,
            "ownGoalsCount": own_goals_count
        },
        "form": {
            "teamA": form_stats_a,
            "teamB": form_stats_b
        },
        "insights": {
            "detectedPatterns": detected_patterns,
            "comparativeMatrix": comparative_matrix,
            "historicalPrediction": historical_prediction
        }
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


def get_team_real_xg(team_slug, xg_data):
    """
    Obtiene el xG real de un equipo y su etiqueta de fuente desde xg_data.
    Responsabilidad única: Lectura y mapeo de datos reales.
    """
    if not xg_data or team_slug not in xg_data:
        return None, "modelo"
    entry = xg_data[team_slug]
    xg_real = entry.get('xg_home') or entry.get('xg_overall')
    source_tag = "fbref" if entry.get('source') == 'fbref_world_cup' else "real"
    return xg_real, source_tag

def get_team_corner_stats(team_slug, xg_data, avg_gs):
    """
    Obtiene estadísticas para el modelo de corners (disparos y centros).
    Si no hay datos en xg_data (p. ej. debutantes mundialistas), estima
    los valores dinámicamente según la forma ofensiva real del equipo.
    """
    entry = xg_data.get(team_slug, {}) if xg_data else {}
    
    if entry:
        sh = entry.get("shots_per_90") or 11.5
        crs = entry.get("crosses_per_90") or 13.0
        sh_blocked = entry.get("shots_blocked_per_90", 0)
        sh_off = entry.get("shots_off_target_per_90", 0)
        return sh, crs, sh_blocked, sh_off
        
    # Estimación basada en promedio de goles marcados (form factor)
    # Promedio global de goles es ~1.35
    form_factor = max(0.5, min(1.8, avg_gs / 1.35))
    sh = 11.5 * form_factor
    crs = 13.0 * form_factor
    sh_blocked = 1.5 * form_factor
    sh_off = 4.0 * form_factor
    return sh, crs, sh_blocked, sh_off

def load_match_raw_data(team_a, team_b, half_life_months, matches, ratings, xg_data):
    """
    Fase 2: Separación de responsabilidades - Carga de datos crudos.
    """
    xg_real_a_home, source_a_tag = get_team_real_xg(team_a, xg_data)
    xg_real_b_away, source_b_tag = get_team_real_xg(team_b, xg_data)

    gs_a, gc_a = get_team_form_stats(team_a, matches, ratings, half_life_months)
    gs_b, gc_b = get_team_form_stats(team_b, matches, ratings, half_life_months)
    
    elo_a = ratings.get(team_a, 1500)
    elo_b = ratings.get(team_b, 1500)
    
    h2h = get_h2h_stats(team_a, team_b, matches)
    
    matches_history_a = get_team_history(team_a, matches, ratings, half_life_months)
    matches_history_b = get_team_history(team_b, matches, ratings, half_life_months)
    
    return {
        "xg_real_a_home": xg_real_a_home,
        "source_a_tag": source_a_tag,
        "xg_real_b_away": xg_real_b_away,
        "source_b_tag": source_b_tag,
        "gs_a": gs_a,
        "gc_a": gc_a,
        "gs_b": gs_b,
        "gc_b": gc_b,
        "elo_a": elo_a,
        "elo_b": elo_b,
        "h2h_count": h2h["count"],
        "h2h_avg_gd": h2h["avgGd"],
        "matches_count_a": len(matches_history_a),
        "matches_count_b": len(matches_history_b)
    }

def compute_xg_from_raw_data(raw_data, rank_a, rank_b, fifa_weight, h2h_weight):
    """
    Fase 2: Cálculo matemático puro de xG utilizando promedio ponderado real de componentes.
    """
    gs_a = raw_data["gs_a"]
    gc_a = raw_data["gc_a"]
    gs_b = raw_data["gs_b"]
    gc_b = raw_data["gc_b"]
    
    # 1. Componente de Form (Historial reciente y xG de FBref)
    xg_form_a = gs_a * gc_b
    xg_form_b = gs_b * gc_a
    
    # Fallback si la forma calculada es casi nula
    elo_a = raw_data["elo_a"]
    elo_b = raw_data["elo_b"]
    if xg_form_a <= 0.1:
        xg_form_a = max(0.3, 1.35 + (elo_a - elo_b) / 400.0)
    if xg_form_b <= 0.1:
        xg_form_b = max(0.3, 1.35 + (elo_b - elo_a) / 400.0)
    
    # Blend con xG real de FBref si está disponible
    xg_real_a_home = raw_data["xg_real_a_home"]
    source_a_tag = raw_data["source_a_tag"]
    xg_real_b_away = raw_data["xg_real_b_away"]
    source_b_tag = raw_data["source_b_tag"]
    
    xg_source_a = "modelo"
    xg_source_b = "modelo"
    
    if xg_real_a_home and xg_real_a_home > 0:
        blend_w = 0.70 if source_a_tag == "fbref" else 0.60
        xg_form_a = blend_w * xg_real_a_home + (1.0 - blend_w) * xg_form_a
        xg_source_a = source_a_tag
    
    if xg_real_b_away and xg_real_b_away > 0:
        blend_w = 0.70 if source_b_tag == "fbref" else 0.60
        xg_form_b = blend_w * xg_real_b_away + (1.0 - blend_w) * xg_form_b
        xg_source_b = source_b_tag

    # 2. Componente de Ranking (FIFA & ELO)
    # Expected goals derived from ratings
    xg_elo_a = 1.35 + (elo_a - elo_b) / 400.0
    xg_elo_b = 1.35 + (elo_b - elo_a) / 400.0
    
    # FIFA rank difference
    rank_diff = rank_b - rank_a
    xg_fifa_a = 1.35 + (rank_diff / 50.0)
    xg_fifa_b = 1.35 - (rank_diff / 50.0)
    
    xg_ranking_a = 0.5 * xg_elo_a + 0.5 * xg_fifa_a
    xg_ranking_b = 0.5 * xg_elo_b + 0.5 * xg_fifa_b
    
    # Clamping of ranking components
    xg_ranking_a = max(0.3, min(3.5, xg_ranking_a))
    xg_ranking_b = max(0.3, min(3.5, xg_ranking_b))
    
    # 3. Componente H2H
    h2h_count = raw_data["h2h_count"]
    h2h_avg_gd = raw_data["h2h_avg_gd"]
    
    if h2h_count > 0:
        xg_h2h_a = 1.35 + h2h_avg_gd
        xg_h2h_b = 1.35 - h2h_avg_gd
    else:
        # Fallback to recent form if no H2H exists
        xg_h2h_a = xg_form_a
        xg_h2h_b = xg_form_b
        
    xg_h2h_a = max(0.3, min(3.5, xg_h2h_a))
    xg_h2h_b = max(0.3, min(3.5, xg_h2h_b))

    # --- Reglas de Oro ---
    # Regla 1: Si no hay H2H en tu CSV -> PON H2H EN 0%
    if h2h_count == 0:
        h2h_weight = 0.0
        
    # Regla 2: Si un equipo tiene <5 partidos en la base de datos reciente -> subir FIFA a 55%
    matches_count_a = raw_data.get("matches_count_a", 10)
    matches_count_b = raw_data.get("matches_count_b", 10)
    if matches_count_a < 5 or matches_count_b < 5:
        fifa_weight = max(fifa_weight, 0.55)

    # Asegurar que la suma de pesos no supere 1.0 (100%)
    total_w = fifa_weight + h2h_weight
    if total_w > 1.0:
        w_fifa = fifa_weight / total_w
        w_h2h = h2h_weight / total_w
        w_form = 0.0
    else:
        w_fifa = fifa_weight
        w_h2h = h2h_weight
        w_form = 1.0 - total_w

    # Promedio ponderado final
    xg_a = w_form * xg_form_a + w_fifa * xg_ranking_a + w_h2h * xg_h2h_a
    xg_b = w_form * xg_form_b + w_fifa * xg_ranking_b + w_h2h * xg_h2h_b
    
    # H2H multipliers for backward compatibility in API
    h2h_mult_a = 1.0
    h2h_mult_b = 1.0
    if h2h_count > 0:
        h2h_mult_a = 1.0 + (h2h_avg_gd / 4.0) * h2h_weight
        h2h_mult_b = 1.0 - (h2h_avg_gd / 4.0) * h2h_weight

    # Clamp final results
    xg_a = max(0.1, min(4.5, xg_a))
    xg_b = max(0.1, min(4.5, xg_b))
    
    return xg_a, xg_b, h2h_mult_a, h2h_mult_b, xg_source_a, xg_source_b

def calculate_xg(team_a, team_b, rank_a, rank_b, fifa_weight, h2h_weight, half_life_months, matches, ratings, xg_data):
    """
    Fase 2: Orquestador que mantiene compatibilidad hacia atrás.
    """
    raw_data = load_match_raw_data(team_a, team_b, half_life_months, matches, ratings, xg_data)
    return compute_xg_from_raw_data(raw_data, rank_a, rank_b, fifa_weight, h2h_weight)

def run_prediction_sim(team_a, team_b, rank_a, rank_b, fifa_weight_pct, h2h_weight_pct, half_life_months, num_sims, odds_a=None, odds_draw=None, odds_b=None, strength_override_a=1.0, strength_override_b=1.0, altitude=0, host_country=None):
    matches, ratings = load_data()
    
    fifa_weight = fifa_weight_pct / 100.0
    h2h_weight = h2h_weight_pct / 100.0
    
    # Calculate expected goals
    xg_data = load_xg_data()
    raw_data = load_match_raw_data(team_a, team_b, half_life_months, matches, ratings, xg_data)
    xg_a, xg_b, h2h_mult_a, h2h_mult_b, xg_source_a, xg_source_b = compute_xg_from_raw_data(
        raw_data, rank_a, rank_b, fifa_weight, h2h_weight
    )
    
    # Altitude adjustments (Fase 5)
    if altitude > 1500:
        if team_a not in ALTITUDE_ACCLIMATED_TEAMS:
            penalty_a = 1.0 - 0.08 * ((altitude - 1500) / 1000.0)
            penalty_a = max(0.70, penalty_a) # Cap penalty at 30%
            xg_a *= penalty_a
            
        if team_b not in ALTITUDE_ACCLIMATED_TEAMS:
            penalty_b = 1.0 - 0.08 * ((altitude - 1500) / 1000.0)
            penalty_b = max(0.70, penalty_b)
            xg_b *= penalty_b

    # WC 2026 Host Country Home Advantage (Componente 3)
    # CONCACAF teams playing in their own host country receive a boost.
    if host_country and host_country.lower() in WC2026_HOST_CONCACAF:
        host_boosts = WC2026_HOST_CONCACAF[host_country.lower()]
        if team_a in CONCACAF_TEAMS:
            boost_a = host_boosts.get(team_a, 0.0)
            xg_a *= (1.0 + boost_a)
        if team_b in CONCACAF_TEAMS:
            boost_b = host_boosts.get(team_b, 0.0)
            xg_b *= (1.0 + boost_b)

    # Strength overrides (Fase 4)
    xg_a *= strength_override_a
    xg_b *= strength_override_b

    # Re-clamp expected goals after modifications
    xg_a = max(0.1, min(4.5, xg_a))
    xg_b = max(0.1, min(4.5, xg_b))
    
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
        
    # --- CALCULATE GOALS MARKETS (BLOCK 1) ---
    prob_btts = 0.0
    prob_over_0_5 = 0.0
    prob_over_1_5 = 0.0
    prob_over_2_5 = 0.0
    prob_over_3_5 = 0.0

    for (a, b), p in joint_probs.items():
        if a >= 1 and b >= 1:
            prob_btts += p
        total_goals = a + b
        if total_goals > 0.5:
            prob_over_0_5 += p
        if total_goals > 1.5:
            prob_over_1_5 += p
        if total_goals > 2.5:
            prob_over_2_5 += p
        if total_goals > 3.5:
            prob_over_3_5 += p

    prob_under_0_5 = 1.0 - prob_over_0_5
    prob_under_1_5 = 1.0 - prob_over_1_5
    prob_under_2_5 = 1.0 - prob_over_2_5
    prob_under_3_5 = 1.0 - prob_over_3_5

    # Asian Handicaps (Team A perspective)
    prob_ah_minus_1_5_a = sum(p for (a, b), p in joint_probs.items() if a - b >= 2)
    prob_ah_minus_0_5_a = win_a_prob
    prob_ah_plus_0_5_a = win_a_prob + draw_prob
    prob_ah_plus_1_5_a = 1.0 - sum(p for (a, b), p in joint_probs.items() if b - a >= 2)

    goals_markets = {
        "btts": {
            "yes": round(prob_btts, 4),
            "no": round(1.0 - prob_btts, 4)
        },
        "doubleChance": {
            "1X": round(win_a_prob + draw_prob, 4),
            "12": round(win_a_prob + win_b_prob, 4),
            "X2": round(draw_prob + win_b_prob, 4)
        },
        "dnb": {
            "1": round(win_a_prob / (win_a_prob + win_b_prob) if (win_a_prob + win_b_prob) > 0 else 0.5, 4),
            "2": round(win_b_prob / (win_a_prob + win_b_prob) if (win_a_prob + win_b_prob) > 0 else 0.5, 4)
        },
        "overUnder": [
            {"threshold": 0.5, "over": round(prob_over_0_5, 4), "under": round(prob_under_0_5, 4)},
            {"threshold": 1.5, "over": round(prob_over_1_5, 4), "under": round(prob_under_1_5, 4)},
            {"threshold": 2.5, "over": round(prob_over_2_5, 4), "under": round(prob_under_2_5, 4)},
            {"threshold": 3.5, "over": round(prob_over_3_5, 4), "under": round(prob_under_3_5, 4)}
        ],
        "asianHandicap": {
            "-1.5": {"teamA": round(prob_ah_minus_1_5_a, 4), "teamB": round(1.0 - prob_ah_minus_1_5_a, 4)},
            "-0.5": {"teamA": round(prob_ah_minus_0_5_a, 4), "teamB": round(1.0 - prob_ah_minus_0_5_a, 4)},
            "+0.5": {"teamA": round(prob_ah_plus_0_5_a, 4), "teamB": round(1.0 - prob_ah_plus_0_5_a, 4)},
            "+1.5": {"teamA": round(prob_ah_plus_1_5_a, 4), "teamB": round(1.0 - prob_ah_plus_1_5_a, 4)}
        }
    }

    # --- CALCULATE CORNERS MODEL (BLOCK 2) ---
    xg_data = load_xg_data()
    entry_a = xg_data.get(team_a, {})
    entry_b = xg_data.get(team_b, {})

    # Smart Defaults per Team based on calculated expected goals (Fase 3)
    # Average xG is ~1.35. Proportional scaling factor.
    factor_a = xg_a / 1.35
    factor_b = xg_b / 1.35

    sh_a = entry_a.get("shots_per_90") or max(5.0, min(25.0, 11.5 * factor_a))
    crs_a = entry_a.get("crosses_per_90") or max(5.0, min(25.0, 13.0 * factor_a))
    
    # If the team has blocked/off-target shots data, use it. Otherwise, use scaled defaults.
    if "shots_blocked_per_90" in entry_a and entry_a["shots_blocked_per_90"] is not None:
        sh_blocked_a = entry_a["shots_blocked_per_90"]
    else:
        sh_blocked_a = 1.5 * factor_a

    if "shots_off_target_per_90" in entry_a and entry_a["shots_off_target_per_90"] is not None:
        sh_off_a = entry_a["shots_off_target_per_90"]
    else:
        sh_off_a = 4.0 * factor_a
        
    sh_b = entry_b.get("shots_per_90") or max(5.0, min(25.0, 11.5 * factor_b))
    crs_b = entry_b.get("crosses_per_90") or max(5.0, min(25.0, 13.0 * factor_b))
    
    if "shots_blocked_per_90" in entry_b and entry_b["shots_blocked_per_90"] is not None:
        sh_blocked_b = entry_b["shots_blocked_per_90"]
    else:
        sh_blocked_b = 1.5 * factor_b

    if "shots_off_target_per_90" in entry_b and entry_b["shots_off_target_per_90"] is not None:
        sh_off_b = entry_b["shots_off_target_per_90"]
    else:
        sh_off_b = 4.0 * factor_b

    # Corner Attack Multipliers (based on shots, blocked/off-target, and crosses)
    if sh_blocked_a + sh_off_a > 0:
        cam_a = 0.3 * (sh_a / 11.5) + 0.3 * ((sh_blocked_a + sh_off_a) / 5.0) + 0.4 * (crs_a / 13.0)
    else:
        cam_a = 0.4 * (sh_a / 11.5) + 0.6 * (crs_a / 13.0)
        
    if sh_blocked_b + sh_off_b > 0:
        cam_b = 0.3 * (sh_b / 11.5) + 0.3 * ((sh_blocked_b + sh_off_b) / 5.0) + 0.4 * (crs_b / 13.0)
    else:
        cam_b = 0.4 * (sh_b / 11.5) + 0.6 * (crs_b / 13.0)

    # Concession Multipliers (based on ELO difference and historical corners conceded)
    elo_a = ratings.get(team_a, 1500)
    elo_b = ratings.get(team_b, 1500)
    elo_diff = elo_a - elo_b

    concession_a_elo = 10 ** (-elo_diff / 800.0)
    concession_b_elo = 10 ** (elo_diff / 800.0)

    corners_against_a = entry_a.get("corners_against_per_90")
    if corners_against_a is not None and corners_against_a > 0:
        concession_real_a = corners_against_a / 4.5
        concession_a_mixed = 0.5 * concession_real_a + 0.5 * concession_a_elo
    else:
        concession_a_mixed = concession_a_elo

    corners_against_b = entry_b.get("corners_against_per_90")
    if corners_against_b is not None and corners_against_b > 0:
        concession_real_b = corners_against_b / 4.5
        concession_b_mixed = 0.5 * concession_real_b + 0.5 * concession_b_elo
    else:
        concession_b_mixed = concession_b_elo

    concession_a = max(0.5, min(1.8, concession_a_mixed))
    concession_b = max(0.5, min(1.8, concession_b_mixed))

    # Expected corners lambda using corners_for_per_90 if available (Fase 1)
    corners_for_a = entry_a.get("corners_for_per_90")
    if corners_for_a is not None and corners_for_a > 0:
        expected_corners_base_a = corners_for_a
    else:
        expected_corners_base_a = 5.0 * cam_a

    corners_for_b = entry_b.get("corners_for_per_90")
    if corners_for_b is not None and corners_for_b > 0:
        expected_corners_base_b = corners_for_b
    else:
        expected_corners_base_b = 4.0 * cam_b

    lambda_corners_a = max(1.5, min(9.5, expected_corners_base_a * concession_b))
    lambda_corners_b = max(1.5, min(9.5, expected_corners_base_b * concession_a))

    # Simulate Corners (Poisson distribution)
    sim_corners_a = np.random.poisson(lambda_corners_a, num_sims)
    sim_corners_b = np.random.poisson(lambda_corners_b, num_sims)
    sim_corners_total = sim_corners_a + sim_corners_b

    avg_corners_a = float(np.mean(sim_corners_a))
    avg_corners_b = float(np.mean(sim_corners_b))
    avg_corners_total = float(np.mean(sim_corners_total))

    prob_most_corners_a = float(np.mean(sim_corners_a > sim_corners_b))
    prob_most_corners_b = float(np.mean(sim_corners_b > sim_corners_a))
    prob_most_corners_draw = float(np.mean(sim_corners_a == sim_corners_b))

    prob_corners_over_7_5 = float(np.mean(sim_corners_total > 7.5))
    prob_corners_over_8_5 = float(np.mean(sim_corners_total > 8.5))
    prob_corners_over_9_5 = float(np.mean(sim_corners_total > 9.5))
    prob_corners_over_10_5 = float(np.mean(sim_corners_total > 10.5))

    corners_prediction = {
        "expectedA": round(avg_corners_a, 2),
        "expectedB": round(avg_corners_b, 2),
        "expectedTotal": round(avg_corners_total, 2),
        "probMostA": round(prob_most_corners_a, 4),
        "probMostB": round(prob_most_corners_b, 4),
        "probMostDraw": round(prob_most_corners_draw, 4),
        "overUnder": [
            {"threshold": 7.5, "over": round(prob_corners_over_7_5, 4), "under": round(1.0 - prob_corners_over_7_5, 4)},
            {"threshold": 8.5, "over": round(prob_corners_over_8_5, 4), "under": round(1.0 - prob_corners_over_8_5, 4)},
            {"threshold": 9.5, "over": round(prob_corners_over_9_5, 4), "under": round(1.0 - prob_corners_over_9_5, 4)},
            {"threshold": 10.5, "over": round(prob_corners_over_10_5, 4), "under": round(1.0 - prob_corners_over_10_5, 4)}
        ]
    }
        
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
        
    # Generate 5x5 score heatmap
    score_heatmap = []
    for a in range(5):
        row = []
        pa = poisson_pmf(a, xg_a)
        for b in range(5):
            tau = dc_tau(a, b, xg_a, xg_b, DC_RHO)
            p = max(0.0, pa * poisson_pmf(b, xg_b) * tau)
            if total_prob > 0:
                p /= total_prob
            row.append(round(p, 4))
        score_heatmap.append(row)

    # Generate comparison stats for radar chart
    comparison_stats = {
        "teamA": {
            "xg_overall": float(entry_a.get("xg_overall") or 1.35) if entry_a else 1.35,
            "xga_overall": float(entry_a.get("xga_overall") or 1.35) if entry_a else 1.35,
            "form_gs": float(raw_data["gs_a"]),
            "form_gc": float(raw_data["gc_a"]),
            "rank": int(rank_a),
            "elo": float(raw_data["elo_a"]),
            "match_xg": float(xg_a),
            "shots_per_90": float(sh_a),
            "crosses_per_90": float(crs_a)
        },
        "teamB": {
            "xg_overall": float(entry_b.get("xg_overall") or 1.35) if entry_b else 1.35,
            "xga_overall": float(entry_b.get("xga_overall") or 1.35) if entry_b else 1.35,
            "form_gs": float(raw_data["gs_b"]),
            "form_gc": float(raw_data["gc_b"]),
            "rank": int(rank_b),
            "elo": float(raw_data["elo_b"]),
            "match_xg": float(xg_b),
            "shots_per_90": float(sh_b),
            "crosses_per_90": float(crs_b)
        }
    }

    return {
        "xgA": xg_a,
        "xgB": xg_b,
        "xgSourceA": xg_source_a,
        "xgSourceB": xg_source_b,
        "probWinA": sim_pct_a,
        "probDraw": sim_pct_draw,
        "probWinB": sim_pct_b,
        "topScores": top_scores,
        "goalsMarkets": goals_markets,
        "cornersPrediction": corners_prediction,
        "bettingAnalysis": betting_analysis,
        "dcRho": DC_RHO,
        "scoreHeatmap": score_heatmap,
        "comparisonStats": comparison_stats
    }


def eval_leg(leg_key, g_a, g_b, c_a, c_b):
    """Evalúa si se cumple una selección (leg_key) en los arrays de simulación."""
    if leg_key == "win_a":
        return g_a > g_b
    elif leg_key == "draw":
        return g_a == g_b
    elif leg_key == "win_b":
        return g_a < g_b
    elif leg_key == "btts_yes":
        return (g_a >= 1) & (g_b >= 1)
    elif leg_key == "btts_no":
        return (g_a == 0) | (g_b == 0)
    elif leg_key == "over_0_5_goals":
        return (g_a + g_b) > 0.5
    elif leg_key == "under_0_5_goals":
        return (g_a + g_b) < 0.5
    elif leg_key == "over_1_5_goals":
        return (g_a + g_b) > 1.5
    elif leg_key == "under_1_5_goals":
        return (g_a + g_b) < 1.5
    elif leg_key == "over_2_5_goals":
        return (g_a + g_b) > 2.5
    elif leg_key == "under_2_5_goals":
        return (g_a + g_b) < 2.5
    elif leg_key == "over_3_5_goals":
        return (g_a + g_b) > 3.5
    elif leg_key == "under_3_5_goals":
        return (g_a + g_b) < 3.5
    elif leg_key == "corners_win_a":
        return c_a > c_b
    elif leg_key == "corners_draw":
        return c_a == c_b
    elif leg_key == "corners_win_b":
        return c_b > c_a
    elif leg_key == "corners_over_7_5":
        return (c_a + c_b) > 7.5
    elif leg_key == "corners_under_7_5":
        return (c_a + c_b) < 7.5
    elif leg_key == "corners_over_8_5":
        return (c_a + c_b) > 8.5
    elif leg_key == "corners_under_8_5":
        return (c_a + c_b) < 8.5
    elif leg_key == "corners_over_9_5":
        return (c_a + c_b) > 9.5
    elif leg_key == "corners_under_9_5":
        return (c_a + c_b) < 9.5
    elif leg_key == "corners_over_10_5":
        return (c_a + c_b) > 10.5
    elif leg_key == "corners_under_10_5":
        return (c_a + c_b) < 10.5
    elif leg_key == "handicap_minus_1_5_a":
        return (g_a - g_b) >= 2
    elif leg_key == "handicap_plus_1_5_b":
        return (g_a - g_b) < 2
    elif leg_key == "handicap_minus_1_5_b":
        return (g_b - g_a) >= 2
    elif leg_key == "handicap_plus_1_5_a":
        return (g_b - g_a) < 2
    elif leg_key == "double_chance_1X":
        return g_a >= g_b
    elif leg_key == "double_chance_12":
        return g_a != g_b
    elif leg_key == "double_chance_X2":
        return g_b >= g_a
    else:
        return np.ones(len(g_a), dtype=bool)


def simulate_bet_builder(team_a, team_b, rank_a, rank_b, fifa_weight_pct, h2h_weight_pct, half_life_months, num_sims=100000, strength_override_a=1.0, strength_override_b=1.0, altitude=0, host_country=None, legs=[]):
    """Realiza una simulación Monte Carlo de goles y córners correlacionados para evaluar un Bet Builder."""
    matches, ratings = load_data()
    
    fifa_weight = fifa_weight_pct / 100.0
    h2h_weight = h2h_weight_pct / 100.0
    
    # Calcular goles esperados
    xg_data = load_xg_data()
    raw_data = load_match_raw_data(team_a, team_b, half_life_months, matches, ratings, xg_data)
    xg_a, xg_b, h2h_mult_a, h2h_mult_b, xg_source_a, xg_source_b = compute_xg_from_raw_data(
        raw_data, rank_a, rank_b, fifa_weight, h2h_weight
    )
    
    # Ajuste por altitud
    if altitude > 1500:
        if team_a not in ALTITUDE_ACCLIMATED_TEAMS:
            penalty_a = 1.0 - 0.08 * ((altitude - 1500) / 1000.0)
            penalty_a = max(0.70, penalty_a)
            xg_a *= penalty_a
        if team_b not in ALTITUDE_ACCLIMATED_TEAMS:
            penalty_b = 1.0 - 0.08 * ((altitude - 1500) / 1000.0)
            penalty_b = max(0.70, penalty_b)
            xg_b *= penalty_b

    # Ajuste por país anfitrión
    if host_country and host_country.lower() in WC2026_HOST_CONCACAF:
        host_boosts = WC2026_HOST_CONCACAF[host_country.lower()]
        if team_a in CONCACAF_TEAMS:
            xg_a *= (1.0 + host_boosts.get(team_a, 0.0))
        if team_b in CONCACAF_TEAMS:
            xg_b *= (1.0 + host_boosts.get(team_b, 0.0))

    xg_a = max(0.1, min(4.5, xg_a * strength_override_a))
    xg_b = max(0.1, min(4.5, xg_b * strength_override_b))
    
    # Calcular distribución Dixon-Coles
    joint_probs = {}
    for a in range(11):
        pa = poisson_pmf(a, xg_a)
        for b in range(11):
            tau = dc_tau(a, b, xg_a, xg_b, DC_RHO)
            p = max(0.0, pa * poisson_pmf(b, xg_b) * tau)
            joint_probs[(a, b)] = p
                
    total_prob = sum(joint_probs.values())
    if total_prob > 0:
        for k in joint_probs:
            joint_probs[k] /= total_prob
            
    score_keys = list(joint_probs.keys())
    score_probs = [joint_probs[k] for k in score_keys]
    cdf = np.cumsum(score_probs)
    
    # Simulación goles
    random_floats = np.random.rand(num_sims)
    sim_indices = np.searchsorted(cdf, random_floats)
    
    sim_goals_a = np.array([score_keys[i][0] for i in sim_indices])
    sim_goals_b = np.array([score_keys[i][1] for i in sim_indices])

    # Calcular parámetros córners
    entry_a = xg_data.get(team_a, {})
    entry_b = xg_data.get(team_b, {})
    factor_a = xg_a / 1.35
    factor_b = xg_b / 1.35

    sh_a = entry_a.get("shots_per_90") or max(5.0, min(25.0, 11.5 * factor_a))
    crs_a = entry_a.get("crosses_per_90") or max(5.0, min(25.0, 13.0 * factor_a))
    sh_blocked_a = entry_a.get("shots_blocked_per_90") or (1.5 * factor_a)
    sh_off_a = entry_a.get("shots_off_target_per_90") or (4.0 * factor_a)

    sh_b = entry_b.get("shots_per_90") or max(5.0, min(25.0, 11.5 * factor_b))
    crs_b = entry_b.get("crosses_per_90") or max(5.0, min(25.0, 13.0 * factor_b))
    sh_blocked_b = entry_b.get("shots_blocked_per_90") or (1.5 * factor_b)
    sh_off_b = entry_b.get("shots_off_target_per_90") or (4.0 * factor_b)

    cam_a = 0.3 * (sh_a / 11.5) + 0.3 * ((sh_blocked_a + sh_off_a) / 5.0) + 0.4 * (crs_a / 13.0)
    cam_b = 0.3 * (sh_b / 11.5) + 0.3 * ((sh_blocked_b + sh_off_b) / 5.0) + 0.4 * (crs_b / 13.0)

    elo_a = ratings.get(team_a, 1500)
    elo_b = ratings.get(team_b, 1500)
    elo_diff = elo_a - elo_b
    concession_a_elo = 10 ** (-elo_diff / 800.0)
    concession_b_elo = 10 ** (elo_diff / 800.0)

    corners_against_a = entry_a.get("corners_against_per_90")
    concession_a_mixed = 0.5 * (corners_against_a / 4.5) + 0.5 * concession_a_elo if corners_against_a else concession_a_elo
    corners_against_b = entry_b.get("corners_against_per_90")
    concession_b_mixed = 0.5 * (corners_against_b / 4.5) + 0.5 * concession_b_elo if corners_against_b else concession_b_elo

    concession_a = max(0.5, min(1.8, concession_a_mixed))
    concession_b = max(0.5, min(1.8, concession_b_mixed))

    corners_for_a = entry_a.get("corners_for_per_90")
    expected_corners_base_a = corners_for_a if corners_for_a else 5.0 * cam_a
    corners_for_b = entry_b.get("corners_for_per_90")
    expected_corners_base_b = corners_for_b if corners_for_b else 4.0 * cam_b

    lambda_corners_a = max(1.5, min(9.5, expected_corners_base_a * concession_b))
    lambda_corners_b = max(1.5, min(9.5, expected_corners_base_b * concession_a))

    # Simulación córners con correlación a goles marcados
    lambdas_a = np.clip(lambda_corners_a * (1.0 + 0.12 * (sim_goals_a - xg_a)), 1.5, 15.0)
    lambdas_b = np.clip(lambda_corners_b * (1.0 + 0.12 * (sim_goals_b - xg_b)), 1.5, 15.0)

    sim_corners_a = np.random.poisson(lambdas_a)
    sim_corners_b = np.random.poisson(lambdas_b)

    # Evaluar selecciones
    leg_vectors = {}
    individual_probs = {}
    for leg in legs:
        v = eval_leg(leg, sim_goals_a, sim_goals_b, sim_corners_a, sim_corners_b)
        leg_vectors[leg] = v
        individual_probs[leg] = float(np.mean(v))

    # Probabilidad combinada real
    if legs:
        all_true = np.ones(num_sims, dtype=bool)
        for leg in legs:
            all_true &= leg_vectors[leg]
        combined_prob = float(np.mean(all_true))
    else:
        combined_prob = 1.0

    # Calcular correlaciones de Pearson
    correlations = []
    num_legs = len(legs)
    for i in range(num_legs):
        for j in range(i + 1, num_legs):
            v_i = leg_vectors[legs[i]].astype(float)
            v_j = leg_vectors[legs[j]].astype(float)
            std_i = np.std(v_i)
            std_j = np.std(v_j)
            if std_i > 0 and std_j > 0:
                corr = float(np.cov(v_i, v_j)[0, 1] / (std_i * std_j))
            else:
                corr = 0.0
            correlations.append({
                "legA": legs[i],
                "legB": legs[j],
                "coefficient": round(corr, 4)
            })

    # Generate 6x6 score heatmap
    score_heatmap = []
    for a in range(6):
        row = []
        pa = poisson_pmf(a, xg_a)
        for b in range(6):
            tau = dc_tau(a, b, xg_a, xg_b, DC_RHO)
            p = max(0.0, pa * poisson_pmf(b, xg_b) * tau)
            if total_prob > 0:
                p /= total_prob
            row.append(round(p, 4))
        score_heatmap.append(row)

    # Calculate advanced metrics
    prob_win_a = float(np.mean(sim_goals_a > sim_goals_b))
    prob_draw = float(np.mean(sim_goals_a == sim_goals_b))
    prob_win_b = float(np.mean(sim_goals_b > sim_goals_a))

    xpts_a = prob_win_a * 3 + prob_draw * 1
    xpts_b = prob_win_b * 3 + prob_draw * 1

    cs_a = float(np.mean(sim_goals_b == 0))
    cs_b = float(np.mean(sim_goals_a == 0))

    w2n_a = float(np.mean((sim_goals_a > sim_goals_b) & (sim_goals_b == 0)))
    w2n_b = float(np.mean((sim_goals_b > sim_goals_a) & (sim_goals_a == 0)))

    ah_minus_1_5_a = float(np.mean((sim_goals_a - sim_goals_b) >= 2))
    ah_minus_1_0_a = float(np.mean((sim_goals_a - sim_goals_b) > 1)) + 0.5 * float(np.mean((sim_goals_a - sim_goals_b) == 1))
    ah_plus_0_5_b = float(np.mean((sim_goals_b - sim_goals_a) >= 0))
    ah_plus_1_5_b = float(np.mean((sim_goals_b - sim_goals_a) >= -1))

    band_0_1 = float(np.mean((sim_goals_a + sim_goals_b) <= 1))
    band_2_3 = float(np.mean(((sim_goals_a + sim_goals_b) >= 2) & ((sim_goals_a + sim_goals_b) <= 3)))
    band_4_5 = float(np.mean(((sim_goals_a + sim_goals_b) >= 4) & ((sim_goals_a + sim_goals_b) <= 5)))
    band_6_plus = float(np.mean((sim_goals_a + sim_goals_b) >= 6))

    ht_goals_a = np.random.binomial(sim_goals_a, 0.45)
    ht_goals_b = np.random.binomial(sim_goals_b, 0.45)
    ht_win_a = ht_goals_a > ht_goals_b
    ht_draw = ht_goals_a == ht_goals_b
    ht_win_b = ht_goals_b > ht_goals_a
    ft_win_a = sim_goals_a > sim_goals_b
    ft_draw = sim_goals_a == sim_goals_b
    ft_win_b = sim_goals_b > sim_goals_a

    htft = {
        "AA": round(float(np.mean(ht_win_a & ft_win_a)), 4),
        "DA": round(float(np.mean(ht_draw & ft_win_a)), 4),
        "BA": round(float(np.mean(ht_win_b & ft_win_a)), 4),
        "AD": round(float(np.mean(ht_win_a & ft_draw)), 4),
        "DD": round(float(np.mean(ht_draw & ft_draw)), 4),
        "BD": round(float(np.mean(ht_win_b & ft_draw)), 4),
        "AB": round(float(np.mean(ht_win_a & ft_win_b)), 4),
        "DB": round(float(np.mean(ht_draw & ft_win_b)), 4),
        "BB": round(float(np.mean(ht_win_b & ft_win_b)), 4),
    }

    ttg_a = {
        "over0_5": round(float(np.mean(sim_goals_a > 0.5)), 4),
        "over1_5": round(float(np.mean(sim_goals_a > 1.5)), 4),
        "over2_5": round(float(np.mean(sim_goals_a > 2.5)), 4)
    }
    ttg_b = {
        "over0_5": round(float(np.mean(sim_goals_b > 0.5)), 4),
        "over1_5": round(float(np.mean(sim_goals_b > 1.5)), 4),
        "over2_5": round(float(np.mean(sim_goals_b > 2.5)), 4)
    }

    form_a = 5.0 + 2.5 * (xg_a - 1.35)
    form_b = 5.0 + 2.5 * (xg_b - 1.35)
    form_a = max(1.0, min(9.9, form_a))
    form_b = max(1.0, min(9.9, form_b))

    conf_win_a = 1.96 * np.sqrt(prob_win_a * (1.0 - prob_win_a) / num_sims)
    conf_draw = 1.96 * np.sqrt(prob_draw * (1.0 - prob_draw) / num_sims)
    conf_win_b = 1.96 * np.sqrt(prob_win_b * (1.0 - prob_win_b) / num_sims)

    timing_dist = [12.5, 15.3, 18.7, 16.2, 19.8, 17.5]

    corners_expected_a = float(np.mean(sim_corners_a))
    corners_expected_b = float(np.mean(sim_corners_b))

    shots_expected_a = float(sh_a * concession_b)
    shots_expected_b = float(sh_b * concession_a)

    possession_a = elo_a / (elo_a + elo_b) * 100
    possession_a = max(35.0, min(65.0, possession_a))
    possession_b = 100.0 - possession_a

    return {
        "xgA": round(xg_a, 4),
        "xgB": round(xg_b, 4),
        "combinedProb": round(combined_prob, 4),
        "individualProbs": {k: round(v, 4) for k, v in individual_probs.items()},
        "correlations": correlations,
        "scoreHeatmap": score_heatmap,
        "advanced": {
            "probWinA": round(prob_win_a, 4),
            "probDraw": round(prob_draw, 4),
            "probWinB": round(prob_win_b, 4),
            "xptsA": round(xpts_a, 2),
            "xptsB": round(xpts_b, 2),
            "csA": round(cs_a, 4),
            "csB": round(cs_b, 4),
            "w2nA": round(w2n_a, 4),
            "w2nB": round(w2n_b, 4),
            "ahMinus1_5A": round(ah_minus_1_5_a, 4),
            "ahMinus1_0A": round(ah_minus_1_0_a, 4),
            "ahPlus0_5B": round(ah_plus_0_5_b, 4),
            "ahPlus1_5B": round(ah_plus_1_5_b, 4),
            "band_0_1": round(band_0_1, 4),
            "band_2_3": round(band_2_3, 4),
            "band_4_5": round(band_4_5, 4),
            "band_6_plus": round(band_6_plus, 4),
            "htft": htft,
            "ttgA": ttg_a,
            "ttgB": ttg_b,
            "formA": round(form_a, 1),
            "formB": round(form_b, 1),
            "confWinA": round(conf_win_a, 4),
            "confDraw": round(conf_draw, 4),
            "confWinB": round(conf_win_b, 4),
            "timingDist": timing_dist,
            "cornersA": round(corners_expected_a, 1),
            "cornersB": round(corners_expected_b, 1),
            "shotsA": round(shots_expected_a, 1),
            "shotsB": round(shots_expected_b, 1),
            "possessionA": round(possession_a, 1),
            "possessionB": round(possession_b, 1)
        }
    }


def eval_historical_leg(leg_key, hg, ag, home_slug, away_slug, team_a_slug, team_b_slug):
    """Determina si un logro se cumplió en un partido histórico (solo con marcador de goles)."""
    is_a_home = (home_slug == team_a_slug)
    
    if leg_key == "win_a":
        return hg > ag if is_a_home else ag > hg
    elif leg_key == "draw":
        return hg == ag
    elif leg_key == "win_b":
        return ag > hg if is_a_home else hg > ag
    elif leg_key == "btts_yes":
        return hg >= 1 and ag >= 1
    elif leg_key == "btts_no":
        return hg == 0 or ag == 0
    elif leg_key.startswith("over_") and leg_key.endswith("_goals"):
        try:
            val = float(leg_key.split("_")[1].replace(",", "."))
            return (hg + ag) > val
        except:
            return False
    elif leg_key.startswith("under_") and leg_key.endswith("_goals"):
        try:
            val = float(leg_key.split("_")[1].replace(",", "."))
            return (hg + ag) < val
        except:
            return False
    elif leg_key == "double_chance_1X":
        return hg >= ag if is_a_home else ag >= hg
    elif leg_key == "double_chance_12":
        return hg != ag
    elif leg_key == "double_chance_X2":
        return ag >= hg if is_a_home else hg >= ag
    elif leg_key == "handicap_minus_1_5_a":
        return (hg - ag) >= 2 if is_a_home else (ag - hg) >= 2
    elif leg_key == "handicap_plus_1_5_b":
        return (hg - ag) < 2 if is_a_home else (ag - hg) < 2
    elif leg_key == "handicap_minus_1_5_b":
        return (ag - hg) >= 2 if is_a_home else (hg - ag) >= 2
    elif leg_key == "handicap_plus_1_5_a":
        return (ag - hg) < 2 if is_a_home else (hg - ag) < 2
    return None # Córners y otros mercados no se registran en results.csv


def find_similar_matches(team_a, team_b, legs=[]):
    """Busca partidos H2H directos e históricos con perfiles de ELO y relevancia temporal similar."""
    matches, ratings = load_data()
    
    elo_a = ratings.get(team_a, 1500)
    elo_b = ratings.get(team_b, 1500)
    target_diff = elo_a - elo_b
    
    direct_h2h = []
    similar_profile = []
    
    for m in matches:
        hg, ag = m["hg"], m["ag"]
        h_slug, a_slug = m["homeSlug"], m["awaySlug"]
        
        # 1. H2H directo
        if (h_slug == team_a and a_slug == team_b) or (h_slug == team_b and a_slug == team_a):
            eval_results = {}
            total_legs = 0
            successful_legs = 0
            
            for leg in legs:
                res = eval_historical_leg(leg, hg, ag, h_slug, a_slug, team_a, team_b)
                if res is not None:
                    eval_results[leg] = res
                    total_legs += 1
                    if res:
                        successful_legs += 1
            
            direct_h2h.append({
                "date": m["date"],
                "homeName": m["homeName"],
                "awayName": m["awayName"],
                "score": f"{hg}-{ag}",
                "tournament": m["tournament"],
                "legsEvaluation": eval_results,
                "fullyMet": (successful_legs == total_legs) if total_legs > 0 else True
            })
            
        # 2. Similar profile matches (since 1990 to keep it relevant, filter out direct H2Hs)
        elif m["date"] >= "1990-01-01":
            elo_h = ratings.get(h_slug, 1500)
            elo_a_match = ratings.get(a_slug, 1500)
            match_diff = elo_h - elo_a_match
            
            # Calculate similarity metrics
            diff_similarity = math.exp(-abs(target_diff - match_diff) / 150.0)
            strength_similarity = math.exp(-(abs(elo_a - elo_h) + abs(elo_b - elo_a_match)) / 300.0)
            
            try:
                year = int(m["date"].split("-")[0])
            except:
                year = 2000
            recency_weight = max(0.1, 1.0 - (2026 - year) / 36.0)
            
            # Weighted average similarity
            similarity_score = 0.5 * diff_similarity + 0.3 * strength_similarity + 0.2 * recency_weight
            
            if similarity_score >= 0.65:
                eval_results = {}
                total_legs = 0
                successful_legs = 0
                
                for leg in legs:
                    res = eval_historical_leg(leg, hg, ag, h_slug, a_slug, team_a, team_b)
                    if res is not None:
                        eval_results[leg] = res
                        total_legs += 1
                        if res:
                            successful_legs += 1
                
                similar_profile.append({
                    "date": m["date"],
                    "homeName": m["homeName"],
                    "awayName": m["awayName"],
                    "score": f"{hg}-{ag}",
                    "tournament": m["tournament"],
                    "legsEvaluation": eval_results,
                    "fullyMet": (successful_legs == total_legs) if total_legs > 0 else True,
                    "similarity": round(similarity_score * 100, 1)
                })

    # Sort similar matches by similarity score descending, direct H2H by date descending
    similar_profile = sorted(similar_profile, key=lambda x: x["similarity"], reverse=True)[:10]
    direct_h2h = sorted(direct_h2h, key=lambda x: x["date"], reverse=True)[:10]
    
    return {
        "directH2H": direct_h2h,
        "similarProfile": similar_profile
    }

