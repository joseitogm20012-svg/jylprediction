import json
import math
import os
import csv
import sys
import numpy as np
from datetime import datetime, date as datetime_date
from functools import lru_cache

# Ensure backend/ is on sys.path for db import
_backend_dir = os.path.dirname(os.path.abspath(__file__))
if _backend_dir not in sys.path:
    sys.path.insert(0, _backend_dir)

import db

# Load base path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)
# Rutas actualizadas a data/raw/
RESULTS_CSV_PATH = os.path.join(PROJECT_DIR, "data", "raw", "results.csv")
ELO_PATH = os.path.join(PROJECT_DIR, "data", "raw", "elo-calibrated.json")
XG_PATH = os.path.join(PROJECT_DIR, "data", "raw", "xg_by_team.json")
PLAYER_STATS_PATH = os.path.join(PROJECT_DIR, "data", "raw", "player_stats.json")
GOALSCORERS_PATH = os.path.join(PROJECT_DIR, "data", "raw", "goalscorers.csv")
PER_MATCH_CORNERS_PATH = os.path.join(PROJECT_DIR, "data", "per_match_corners.json")

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
    """Carga datos de xG por equipo desde Supabase."""
    global _cached_xg_data
    if _cached_xg_data is not None:
        return _cached_xg_data
    
    try:
        conn = db.get_db_connection()
        cursor = db.get_cursor(conn)
        cursor.execute("SELECT * FROM public.team_metrics")
        rows = cursor.fetchall()
        conn.close()
        
        # Convertimos las filas en un diccionario keyed por team_slug
        _cached_xg_data = {row["team_slug"]: row for row in rows}
    except Exception as e:
        print(f"Error loading xG data from DB: {e}")
        _cached_xg_data = {}
        
    return _cached_xg_data

_cached_player_stats = None
def load_player_stats():
    global _cached_player_stats
    if _cached_player_stats is not None:
        return _cached_player_stats
    if os.path.exists(PLAYER_STATS_PATH):
        try:
            with open(PLAYER_STATS_PATH, "r", encoding="utf-8") as f:
                _cached_player_stats = json.load(f)
        except Exception:
            _cached_player_stats = {}
    else:
        _cached_player_stats = {}
    return _cached_player_stats

_cached_goalscorers = None
_cached_corners = None

def load_corners_data():
    """Carga datos de corners por equipo. Primero intenta Supabase DB, fallback a archivo."""
    global _cached_corners
    if _cached_corners is not None:
        return _cached_corners
    
    try:
        conn = db.get_db_connection()
        cursor = db.get_cursor(conn)
        cursor.execute("SELECT * FROM public.corners_stats")
        rows = cursor.fetchall()
        conn.close()
        
        _cached_corners = {}
        for row in rows:
            slug = row["team_slug"]
            entry = {}
            if row.get("corners_for") is not None:
                entry["corners_for"] = row["corners_for"]
            if row.get("corners_against") is not None:
                entry["corners_against"] = row["corners_against"]
            if row.get("games") is not None:
                entry["games"] = row["games"]
            if row.get("source"):
                entry["_source"] = row["source"]
            sh_taken = row.get("second_half_taken")
            sh_conceded = row.get("second_half_conceded")
            sh_matches = row.get("second_half_matches")
            if sh_taken is not None or sh_conceded is not None:
                sh = {}
                if sh_taken is not None: sh["taken"] = sh_taken
                if sh_conceded is not None: sh["conceded"] = sh_conceded
                if sh_matches is not None: sh["matches"] = sh_matches
                entry["second_half"] = {"overall": sh}
            _cached_corners[slug] = entry
        
        # Merge home/away splits from JSON (not available in DB schema)
        _merge_corner_home_away_splits(_cached_corners)
        
    except Exception as e:
        print(f"Error loading corners stats from DB: {e}")
        # Fallback a archivo
        path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "corners_stats.json")
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    _cached_corners = json.load(f)
                if isinstance(_cached_corners, dict) and "_meta" in _cached_corners:
                    del _cached_corners["_meta"]
            except Exception:
                _cached_corners = {}
        else:
            _cached_corners = {}
    
    if _cached_corners is None:
        _cached_corners = {}
    return _cached_corners

def _merge_corner_home_away_splits(cache):
    """Merge second_half.home and second_half.away from JSON into DB cache."""
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "corners_stats.json")
    if not os.path.exists(path):
        return
    try:
        with open(path, "r", encoding="utf-8") as f:
            json_data = json.load(f)
        if isinstance(json_data, dict) and "_meta" in json_data:
            del json_data["_meta"]
        for slug, entry in json_data.items():
            sh = entry.get("second_half")
            if not sh:
                continue
            if slug not in cache:
                cache[slug] = {"corners_for": entry.get("corners_for"), "corners_against": entry.get("corners_against"), "games": entry.get("games")}
            if "second_half" not in cache[slug]:
                cache[slug]["second_half"] = {}
            cache[slug]["second_half"]["home"] = sh.get("home")
            cache[slug]["second_half"]["away"] = sh.get("away")
            if "overall" not in cache[slug]["second_half"] and isinstance(sh.get("overall"), dict):
                cache[slug]["second_half"]["overall"] = sh["overall"]
    except Exception:
        pass

_cached_per_match_corners = None

def load_per_match_corners():
    """Carga datos de corners por partido. Primero intenta Supabase DB, fallback a archivo."""
    global _cached_per_match_corners
    if _cached_per_match_corners is not None:
        return _cached_per_match_corners
    
    try:
        conn = db.get_db_connection()
        cursor = db.get_cursor(conn)
        cursor.execute("SELECT * FROM public.match_corners ORDER BY date DESC NULLS LAST")
        rows = cursor.fetchall()
        conn.close()
        
        matches = []
        for row in rows:
            matches.append({
                "id": row["id"],
                "date": row.get("date") or "",
                "home_team": row.get("home_team") or "",
                "away_team": row.get("away_team") or "",
                "home_corners": row.get("home_corners") or 0,
                "away_corners": row.get("away_corners") or 0,
                "competition": row.get("competition") or "",
            })
        
        if matches:
            _cached_per_match_corners = {
                "matches": matches,
                "last_updated": datetime.now().isoformat(),
                "total_matches": len(matches),
                "note": "Cargado desde Supabase DB"
            }
        else:
            _cached_per_match_corners = None
    except Exception as e:
        print(f"Error loading match corners from DB: {e}")
        # Fallback a archivo
        if os.path.exists(PER_MATCH_CORNERS_PATH):
            try:
                with open(PER_MATCH_CORNERS_PATH, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if data.get("matches") and len(data["matches"]) > 0:
                    _cached_per_match_corners = data
                else:
                    _cached_per_match_corners = None
            except Exception:
                _cached_per_match_corners = None
        else:
            _cached_per_match_corners = None
    
    return _cached_per_match_corners

HOME_CORNER_FACTOR = 1.10
AWAY_CORNER_FACTOR = 0.90

def compute_rolling_corner_avg(team_slug, per_match_data, max_matches=10):
    if per_match_data is None:
        return None
    matches = per_match_data.get("matches", [])
    if not matches:
        return None
    team_matches = []
    for m in matches:
        if m.get("home_team") == team_slug:
            hc = m.get("home_corners")
            ac = m.get("away_corners")
            if hc is not None and ac is not None:
                team_matches.append((m.get("date", ""), float(hc), float(ac), True))
        elif m.get("away_team") == team_slug:
            hc = m.get("home_corners")
            ac = m.get("away_corners")
            if hc is not None and ac is not None:
                team_matches.append((m.get("date", ""), float(ac), float(hc), False))
    if not team_matches:
        return None
    team_matches.sort(key=lambda x: x[0] or "", reverse=True)
    recent = team_matches[:max_matches]
    weights = [0.5 ** (i / 5.0) for i in range(len(recent))]
    total_weight = sum(weights)
    if total_weight <= 0:
        return None
    avg_for = sum(m[1] * w for m, w in zip(recent, weights)) / total_weight
    avg_against = sum(m[2] * w for m, w in zip(recent, weights)) / total_weight
    return avg_for, avg_against, len(recent)

def load_goalscorers():
    global _cached_goalscorers
    if _cached_goalscorers is not None:
        return _cached_goalscorers
    
    all_scorers = []
    try:
        _gs_conn = db.get_db_connection()
        _gs_cur = db.get_cursor(_gs_conn)
        _gs_cur.execute("SELECT date, team, scorer, minute, own_goal, penalty FROM public.goalscorers")
        for _r in _gs_cur.fetchall():
            _date_raw = _r["date"] if isinstance(_r, dict) else _r[0]
            if isinstance(_date_raw, (datetime_date, datetime)):
                _date = _date_raw.strftime('%Y-%m-%d')
            else:
                _date = str(_date_raw).strip()
            _tn = (_r["team"] if isinstance(_r, dict) else _r[1]).strip().lower()
            _scorer = (_r["scorer"] if isinstance(_r, dict) else _r[2]).strip()
            _mraw = _r["minute"] if isinstance(_r, dict) else _r[3]
            _og = _r["own_goal"] if isinstance(_r, dict) else _r[4]
            _pk = _r["penalty"] if isinstance(_r, dict) else _r[5]
            all_scorers.append({"date":_date,"team":_tn,"scorer":_scorer,"minute":_mraw,"own_goal":_og,"penalty":_pk})
        _gs_cur.close()
        _gs_conn.close()
    except Exception as e:
        print(f"Error loading goalscorers from DB, falling back to CSV: {e}")
        _gs_csv = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "raw", "goalscorers.csv")
        if os.path.exists(_gs_csv):
            with open(_gs_csv, "r", encoding="utf-8") as _f:
                for _row in csv.DictReader(_f):
                    _date = _row.get("date","").strip()
                    _tn = _row.get("team","").strip().lower()
                    _scorer = _row.get("scorer","").strip()
                    try:
                        _mraw = int(float(_row.get("minute","0").strip())) if _row.get("minute","").strip() else 0
                    except:
                        _mraw = 0
                    _og = _row.get("own_goal","").strip().upper() == "TRUE"
                    _pk = _row.get("penalty","").strip().upper() == "TRUE"
                    all_scorers.append({"date":_date,"team":_tn,"scorer":_scorer,"minute":_mraw,"own_goal":_og,"penalty":_pk})
    
    _cached_goalscorers = all_scorers
    return _cached_goalscorers


_cached_processed_scorers = None

def get_scorers_for_team(team_slug, decay_months=None):
    global _cached_processed_scorers
    
    # Load team_scorers_processed.json
    if _cached_processed_scorers is None:
        json_path = os.path.join(PROJECT_DIR, "data", "team_scorers_processed.json")
        if os.path.exists(json_path):
            try:
                with open(json_path, "r", encoding="utf-8") as f:
                    _cached_processed_scorers = json.load(f)
            except Exception as e:
                print(f"Error reading team_scorers_processed.json: {e}")
                _cached_processed_scorers = {}
        else:
            _cached_processed_scorers = {}
            
    # Get historical list
    historical = _cached_processed_scorers.get(team_slug.lower(), [])
    
    # Map scorer name to active status
    active_map = {s["name"].lower(): s["active"] for s in historical}
    
    # Calculate recent scorers
    recent = []
    if decay_months is not None and decay_months > 0:
        from datetime import timedelta
        # Load all goalscorers (with date)
        all_scorers = load_goalscorers()
        
        # Determine team names to filter
        canon_name = SLUG_TO_NAME.get(team_slug, team_slug.replace("-", " ").title())
        low_name = canon_name.lower()
        slug_clean = team_slug.replace("-", " ")
        team_names = {team_slug, slug_clean, low_name}
        
        # Find maximum date in all_scorers
        max_date = None
        for r in all_scorers:
            date_str = r.get("date")
            if date_str:
                try:
                    d = datetime.strptime(date_str, "%Y-%m-%d")
                    if max_date is None or d > max_date:
                        max_date = d
                except ValueError:
                    pass
                    
        if max_date is None:
            max_date = datetime.now()
            
        cutoff_date = max_date - timedelta(days=decay_months * 30.44)
        
        # Filter and aggregate goals
        counts = {}
        for r in all_scorers:
            tn = r["team"]
            if tn not in team_names:
                continue
                
            date_str = r.get("date")
            if not date_str:
                continue
                
            try:
                d = datetime.strptime(date_str, "%Y-%m-%d")
                if d >= cutoff_date:
                    scorer_name = r["scorer"]
                    counts[scorer_name] = counts.get(scorer_name, 0) + 1
            except ValueError:
                pass
                
        # Build list of dicts
        for name, goals in counts.items():
            active = active_map.get(name.lower(), True)
            recent.append({"name": name, "goals": goals, "active": active})
            
        # Sort by goals descending, then name ascending
        recent.sort(key=lambda x: (-x["goals"], x["name"]))
    else:
        recent = historical
        
    return {
        "historical": historical,
        "recent": recent
    }



_cached_hattrick_rate = None
def _get_hattrick_rate():
    global _cached_hattrick_rate
    if _cached_hattrick_rate is not None:
        return _cached_hattrick_rate
    try:
        match_goals = {}
        if os.path.exists(GOALSCORERS_PATH):
            with open(GOALSCORERS_PATH, "r", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    key = (row.get("date",""), row.get("home_team",""), row.get("away_team",""))
                    scorer = row.get("scorer","").strip()
                    if not key or not scorer:
                        continue
                    if key not in match_goals:
                        match_goals[key] = {}
                    match_goals[key][scorer] = match_goals[key].get(scorer, 0) + 1
        total_matches = len(match_goals)
        hat_trick_matches = sum(1 for g in match_goals.values() if any(v >= 3 for v in g.values()))
        _cached_hattrick_rate = hat_trick_matches / max(total_matches, 1)
    except Exception:
        _cached_hattrick_rate = 0.015
    return _cached_hattrick_rate

def _top_players(team_slug, stat_type, limit=10):
    ps = load_player_stats()
    team = ps.get(team_slug, {})
    players = team.get(stat_type, [])
    if not players:
        return []
    return players[:limit]

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

SLUG_TO_NAME = {v: k for k, v in NAME_TO_SLUG.items()}

def name_to_slug(name):
    if name in NAME_TO_SLUG:
        return NAME_TO_SLUG[name]
    return name.lower().replace(" ", "-").replace("'", "").replace(".", "")

_cached_matches = None
_cached_ratings = None
_cache_timestamp = 0
CACHE_TTL = 60 # 60 seconds

def load_data():
    global _cached_matches, _cached_ratings, _cache_timestamp
    import time
    now = time.time()
    
    if (_cached_matches is not None 
            and _cached_ratings is not None 
            and (now - _cache_timestamp) < CACHE_TTL):
        return _cached_matches, _cached_ratings
        
    # Clear all other database caches to ensure reload
    global _cached_xg_data, _cached_corners, _cached_goalscorers, _cached_player_stats
    _cached_xg_data = None
    _cached_corners = None
    _cached_goalscorers = None
    _cached_player_stats = None
    
    _cache_timestamp = now

    try:
        conn = db.get_db_connection()
        cursor = db.get_cursor(conn)
        
        # 1. Cargar Ratings Elo
        cursor.execute("SELECT team_slug, rating FROM public.elo_ratings")
        ratings_rows = cursor.fetchall()
        ratings = {row["team_slug"]: row["rating"] for row in ratings_rows}
        
        # 2. Cargar Partidos (Matches)
        cursor.execute("SELECT * FROM public.matches")
        matches_rows = cursor.fetchall()
        
        matches = []
        for row in matches_rows:
            # Convertir la fecha de la DB a timestamp para el ordenamiento
            date_str = row["date"]
            try:
                # Manejo simple de formato fecha
                dt_part = date_str.split("T")[0] if "T" in date_str else date_str
                parts = dt_part.split("-")
                dt = datetime(int(parts[0]), int(parts[1]), int(parts[2]))
                ts = int(dt.timestamp())
            except:
                ts = 0
                
            matches.append({
                "id": row["id"],
                "date": date_str,
                "ts": ts,
                "homeSlug": row["home_slug"],
                "awaySlug": row["away_slug"],
                "homeName": row["home_team"],
                "awayName": row["away_team"],
                "hg": row["home_score"],
                "ag": row["away_score"],
                "tournament": row["tournament"],
                "neutral": row["neutral"],
                "city": row["city"],
                "country": row["country"]
            })
            
        conn.close()
        
        # Asegurar que los partidos estén ordenados por timestamp
        matches.sort(key=lambda x: x["ts"])
        _cached_matches = matches
        _cached_ratings = ratings
        return _cached_matches, _cached_ratings
        
    except Exception as e:
        print(f"Error loading core data from DB: {e}")
        return [], {}

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

def compute_advanced_h2h(team_a, team_b, matches, ratings):
    """Enhanced H2H with full stats for the advanced H2H center view."""
    # Filter direct matches
    direct = [
        m for m in matches
        if (m.get("homeSlug") == team_a and m.get("awaySlug") == team_b) or
           (m.get("homeSlug") == team_b and m.get("awaySlug") == team_a)
    ]
    direct.sort(key=lambda x: x.get("date", ""))

    # Basic stats
    wins_a = wins_b = draws = 0
    goals_a = goals_b = 0
    biggest_win = ""
    biggest_gd = -999
    total_goals = 0
    btts_count = 0
    over25_count = 0
    cs_a_count = 0
    cs_b_count = 0
    home_a_count = away_a_count = neutral_count = 0
    home_a_w = away_a_w = neutral_w = 0
    home_a_d = away_a_d = neutral_d = 0
    home_a_l = away_a_l = neutral_l = 0
    score_freq = {}
    comp_stats = {}
    last_winner = None
    timeline = []

    for m in direct:
        is_a_home = m["homeSlug"] == team_a
        gs_a = m["hg"] if is_a_home else m["ag"]
        gs_b = m["ag"] if is_a_home else m["hg"]

        goals_a += gs_a
        goals_b += gs_b
        total_goals += gs_a + gs_b

        btts_count += 1 if (gs_a > 0 and gs_b > 0) else 0
        over25_count += 1 if (gs_a + gs_b > 2) else 0
        cs_a_count += 1 if gs_b == 0 else 0
        cs_b_count += 1 if gs_a == 0 else 0

        if gs_a > gs_b:
            wins_a += 1
            last_winner = team_a
        elif gs_a < gs_b:
            wins_b += 1
            last_winner = team_b
        else:
            draws += 1

        gd = gs_a - gs_b
        if abs(gd) > abs(biggest_gd):
            biggest_gd = gd
            winner_name = m["homeName"] if is_a_home else m["awayName"]
            loser_name = m["awayName"] if is_a_home else m["homeName"]
            biggest_win = f"{winner_name} {gs_a}-{gs_b} {loser_name}"

        score_key = f"{gs_a}-{gs_b}"
        score_freq[score_key] = score_freq.get(score_key, 0) + 1

        tournament = m.get("tournament", m.get("competition", ""))
        if tournament:
            if tournament not in comp_stats:
                comp_stats[tournament] = {"pj": 0, "winsA": 0, "draws": 0, "winsB": 0}
            comp_stats[tournament]["pj"] += 1
            if gs_a > gs_b:
                comp_stats[tournament]["winsA"] += 1
            elif gs_a < gs_b:
                comp_stats[tournament]["winsB"] += 1
            else:
                comp_stats[tournament]["draws"] += 1

        if is_a_home:
            home_a_count += 1
            if gs_a > gs_b: home_a_w += 1
            elif gs_a == gs_b: home_a_d += 1
            else: home_a_l += 1
        else:
            if m.get("neutral", False):
                neutral_count += 1
                if gs_a > gs_b: neutral_w += 1
                elif gs_a == gs_b: neutral_d += 1
                else: neutral_l += 1
            else:
                away_a_count += 1
                if gs_a > gs_b: away_a_w += 1
                elif gs_a == gs_b: away_a_d += 1
                else: away_a_l += 1

        timeline.append({
            "date": m["date"],
            "homeName": m["homeName"],
            "awayName": m["awayName"],
            "hg": m["hg"],
            "ag": m["ag"],
            "tournament": tournament
        })

    count = len(direct)
    avg_goals = round(total_goals / count, 1) if count else 0

    # Most frequent scores
    most_frequent = sorted(score_freq.items(), key=lambda x: -x[1])[:10]
    most_freq_scores = [{"score": s, "count": c} for s, c in most_frequent]

    # byCondition
    def fmt(w, d, l):
        return f"{w}V-{d}E-{l}D"
    by_condition = {
        "homeA": fmt(home_a_w, home_a_d, home_a_l),
        "awayA": fmt(away_a_w, away_a_d, away_a_l),
        "neutral": fmt(neutral_w, neutral_d, neutral_l)
    }

    # Patterns
    patterns = {
        "btts": f"{round(btts_count / count * 100)}%" if count else "0%",
        "over25": f"{round(over25_count / count * 100)}%" if count else "0%",
        "csA": f"{round(cs_a_count / count * 100)}%" if count else "0%",
        "csB": f"{round(cs_b_count / count * 100)}%" if count else "0%",
    }

    h2h_block = {
        "count": count, "winsA": wins_a, "winsB": wins_b, "draws": draws,
        "avgGoals": avg_goals, "goalsA": goals_a, "goalsB": goals_b,
        "biggestWin": biggest_win, "lastWinner": last_winner or "-",
        "patterns": patterns, "byCondition": by_condition,
        "mostFrequentScores": most_freq_scores,
        "byCompetition": [{"competition": k, **v} for k, v in comp_stats.items()],
        "timeline": timeline
    }

    # Goalscorers — count goals per player from H2H matches
    import csv
    scorers_csv = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "raw", "goalscorers.csv")
    h2h_scorers = {}
    if os.path.exists(scorers_csv):
        try:
            h2h_by_date = {}
            for m in direct:
                d = m.get("date", "")
                if hasattr(d, "isoformat"):
                    d = d.isoformat()
                elif not isinstance(d, str):
                    d = str(d)
                d = str(d).split("T")[0]
                if d not in h2h_by_date:
                    h2h_by_date[d] = set()
                h2h_by_date[d].add(m.get("homeSlug", ""))
                h2h_by_date[d].add(m.get("awaySlug", ""))
            
            period_counts = {"0-15": 0, "16-30": 0, "31-45": 0, "46-60": 0, "61-75": 0, "76-90": 0}
            total_h2h_goals = 0
            penalties_count = 0
            own_goals_count = 0
            goal_minutes = []
            
            with open(scorers_csv, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    match_date = row.get("date", "").strip()
                    if match_date not in h2h_by_date:
                        continue
                    
                    team_name = row.get("team", "").strip().lower()
                    team_slugs = h2h_by_date[match_date]
                    matched = False
                    for slug in team_slugs:
                        slug_clean = slug.replace("-", " ")
                        if team_name == slug_clean or team_name == slug:
                            matched = True
                            break
                    if not matched:
                        continue
                    
                    total_h2h_goals += 1
                    scorer = row.get("scorer", "").strip()
                    if scorer:
                        key = f"{scorer}|{team_name}"
                        h2h_scorers[key] = h2h_scorers.get(key, 0) + 1
                    
                    try:
                        minute = int(row.get("minute", 0))
                        if minute <= 15: p = "0-15"
                        elif minute <= 30: p = "16-30"
                        elif minute <= 45: p = "31-45"
                        elif minute <= 60: p = "46-60"
                        elif minute <= 75: p = "61-75"
                        else: p = "76-90"
                        period_counts[p] += 1
                        goal_minutes.append(minute)
                    except: pass
                    
                    if row.get("own_goal", "").strip().upper() == "TRUE":
                        own_goals_count += 1
                    if row.get("penalty", "").strip().upper() == "TRUE":
                        penalties_count += 1
        except Exception as e:
            print(f"[debug] goalscorers error: {e}")

    avg_goal_min = sum(goal_minutes) / len(goal_minutes) if goal_minutes else 0
    period_distribution = {
        p: round((count / total_h2h_goals * 100), 1) if total_h2h_goals > 0 else 0 
        for p, count in period_counts.items()
    }

    sorted_scorers = []
    for key, goals in sorted(h2h_scorers.items(), key=lambda x: -x[1])[:10]:
        name, team_lower = key.rsplit("|", 1)
        sorted_scorers.append({
            "name": name,
            "team": team_lower.title(),
            "goals": goals,
            "active": True
        })
    top_scorers = sorted_scorers

    scorers_block = {
        "topScorers": top_scorers,
        "avgGoalMinute": round(avg_goal_min, 1),
        "penaltiesCount": penalties_count,
        "ownGoalsCount": own_goals_count,
        "periodDistribution": period_distribution
    }

    # Form for both teams
    def calc_form(slug, all_matches, all_ratings, limit=10):
        team_m = [m for m in all_matches if m.get("homeSlug") == slug or m.get("awaySlug") == slug]
        team_m.sort(key=lambda x: x.get("date", ""), reverse=True)
        recent = team_m[:limit]
        w = d = l = 0
        gf = gc = 0
        cs = 0
        btts = 0
        o25 = 0
        streak_wins = streak_losses = streak_scoring = streak_cs = 0
        cur_wins = cur_losses = cur_scoring = cur_cs = 0
        by_rival = {"top": {"w": 0, "d": 0, "l": 0}, "high": {"w": 0, "d": 0, "l": 0}, "mid": {"w": 0, "d": 0, "l": 0}, "low": {"w": 0, "d": 0, "l": 0}}

        for m in reversed(recent):
            is_h = m["homeSlug"] == slug
            gs = m["hg"] if is_h else m["ag"]
            gc_v = m["ag"] if is_h else m["hg"]
            opp = m["awaySlug"] if is_h else m["homeSlug"]
            opp_elo = all_ratings.get(opp, 1500)

            gf += gs
            gc += gc_v
            if gs > gc_v:
                w += 1
                cur_wins += 1
                cur_losses = 0
            elif gs < gc_v:
                l += 1
                cur_losses += 1
                cur_wins = 0
            else:
                d += 1
                cur_wins = cur_losses = 0
            cur_scoring = cur_scoring + 1 if gs > 0 else 0
            cur_cs = cur_cs + 1 if gc_v == 0 else 0
            if gs > 0 and gc_v > 0: btts += 1
            if gs + gc_v > 2: o25 += 1
            if gc_v == 0: cs += 1

            if opp_elo >= 1850:
                key = "top"
            elif opp_elo >= 1700:
                key = "high"
            elif opp_elo >= 1550:
                key = "mid"
            else:
                key = "low"
            if gs > gc_v: by_rival[key]["w"] += 1
            elif gs < gc_v: by_rival[key]["l"] += 1
            else: by_rival[key]["d"] += 1

        streak_wins = cur_wins
        streak_losses = cur_losses
        streak_scoring = cur_scoring
        streak_cs = cur_cs

        n = len(recent)
        return {
            "record": f"{w}V-{d}E-{l}D",
            "avg_gf": f"{round(gf / n, 1)}" if n else "0",
            "avg_gc": f"{round(gc / n, 1)}" if n else "0",
            "clean_sheets": f"{round(cs / n * 100)}%" if n else "0%",
            "btts": f"{round(btts / n * 100)}%" if n else "0%",
            "over25": f"{round(o25 / n * 100)}%" if n else "0%",
            "streaks": {"unbeaten": streak_wins + (1 if d > 0 else 0), "losing": streak_losses, "scoring": streak_scoring, "clean_sheet": streak_cs},
            "by_rival": {k: f"{v['w']}V-{v['d']}E-{v['l']}D" for k, v in by_rival.items()}
        }

    form_block = {
        "teamA": calc_form(team_a, matches, ratings),
        "teamB": calc_form(team_b, matches, ratings)
    }

    # Insights
    # Historical prediction based on H2H data
    hist_pred = {}
    def _team_name(slug):
        return slug.replace("-"," ").title()
    if count > 0:
        if wins_a > wins_b and wins_a > draws:
            hist_pred["outcome"] = f"Victoria {_team_name(team_a)}"
            hist_pred["probability"] = round(wins_a / count * 100, 1)
        elif wins_b > wins_a and wins_b > draws:
            hist_pred["outcome"] = f"Victoria {_team_name(team_b)}"
            hist_pred["probability"] = round(wins_b / count * 100, 1)
        else:
            hist_pred["outcome"] = "Empate"
            hist_pred["probability"] = round(draws / count * 100, 1)
        hist_pred["confidence"] = "Alta" if count >= 20 else ("Media" if count >= 10 else "Baja")
        hist_pred["exp_goals"] = str(avg_goals)
        hist_pred["freq_score"] = most_freq_scores[0]["score"] if most_freq_scores else "0-0"
        hist_pred["sample_size"] = count
    else:
        hist_pred["outcome"] = "Sin historial"
        hist_pred["probability"] = 0
        hist_pred["confidence"] = "N/A"
        hist_pred["exp_goals"] = "0"
        hist_pred["freq_score"] = "-"
        hist_pred["sample_size"] = 0

    insights_block = {
        "detectedPatterns": [],
        "comparativeMatrix": {
            "avg_goals": {"h2h": str(avg_goals), "team_a": form_block["teamA"]["avg_gf"], "team_b": form_block["teamB"]["avg_gf"]},
            "btts": {"h2h": patterns["btts"], "team_a": form_block["teamA"]["btts"], "team_b": form_block["teamB"]["btts"]},
            "over25": {"h2h": patterns["over25"], "team_a": form_block["teamA"]["over25"], "team_b": form_block["teamB"]["over25"]},
            "clean_sheets": {"h2h": patterns["csA"], "team_a": form_block["teamA"]["clean_sheets"], "team_b": form_block["teamB"]["clean_sheets"]}
        },
        "historicalPrediction": hist_pred
    }

    patterns_list = []
    if count > 0:
        if wins_a > wins_b:
            patterns_list.append(f"{team_a.title()} domina el historial con {wins_a} victorias en {count} partidos.")
        elif wins_b > wins_a:
            patterns_list.append(f"{team_b.title()} domina el historial con {wins_b} victorias en {count} partidos.")
        else:
            patterns_list.append(f"Historial muy parejo: {wins_a} victorias cada uno en {count} partidos.")
        if btts_count / count > 0.6:
            patterns_list.append("Alta probabilidad de que ambos equipos marquen (BTTS) segun historial.")
        if total_goals / count > 3:
            patterns_list.append("Partidos con muchos goles historicamente.")
        if cs_a_count / count > 0.4:
            patterns_list.append(f"{team_a.title()} suele mantener su porteria a cero contra este rival.")
    else:
        patterns_list.append("Sin partidos directos registrados entre estos equipos.")
    insights_block["detectedPatterns"] = patterns_list

    return {"h2h": h2h_block, "scorers": scorers_block, "form": form_block, "insights": insights_block}

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

def run_prediction_sim(team_a, team_b, rank_a, rank_b, fifa_weight_pct, h2h_weight_pct, half_life_months, num_sims, odds_a=None, odds_draw=None, odds_b=None, strength_override_a=1.0, strength_override_b=1.0, altitude=0, host_country=None, return_raw=False, referee_intensity=1.0, predict_half="full"):
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

    # Expected corners base from real stats (corners_stats.json) or fallback
    corners_data = load_corners_data()
    real_a = corners_data.get(team_a, {})
    real_b = corners_data.get(team_b, {})
    # Determine home/away venue for second-half splits (must be before predict_half check)
    venue_a = "neutral"
    venue_b = "neutral"
    if host_country and isinstance(host_country, str):
        if team_a == host_country.lower().replace(" ", "-"):
            venue_a = "home"
            venue_b = "away"
        elif team_b == host_country.lower().replace(" ", "-"):
            venue_a = "away"
            venue_b = "home"

    # Handle Second Half vs Full Match
    if predict_half == "second":
        # Use venue-specific second-half splits when available
        sh_data_a = real_a.get("second_half", {})
        sh_data_b = real_b.get("second_half", {})
        if venue_a == "home" and sh_data_a.get("home"):
            sh_a = sh_data_a["home"]
        elif venue_a == "away" and sh_data_a.get("away"):
            sh_a = sh_data_a["away"]
        else:
            sh_a = sh_data_a.get("overall", {})
        if venue_b == "home" and sh_data_b.get("home"):
            sh_b = sh_data_b["home"]
        elif venue_b == "away" and sh_data_b.get("away"):
            sh_b = sh_data_b["away"]
        else:
            sh_b = sh_data_b.get("overall", {})
        
        base_a = sh_a.get("taken") if sh_a.get("taken") else (real_a.get("corners_for", 5.0) * 0.5)
        base_b = sh_b.get("taken") if sh_b.get("taken") else (real_b.get("corners_for", 5.0) * 0.5)
        
        # Use second-half concession if available
        concession_real_a = sh_a.get("conceded") if sh_a.get("conceded") else (real_a.get("corners_against", 4.5) * 0.5)
        concession_real_b = sh_b.get("conceded") if sh_b.get("conceded") else (real_b.get("corners_against", 4.5) * 0.5)
    else:
        base_a = real_a.get("corners_for")
        base_b = real_b.get("corners_for")
        concession_real_a = real_a.get("corners_against", 4.5)
        concession_real_b = real_b.get("corners_against", 4.5)

    corners_for_a = entry_a.get("corners_for_per_90")
    corners_for_b = entry_b.get("corners_for_per_90")

    if base_a and base_a > 0:
        expected_corners_base_a = base_a
    elif corners_for_a is not None and corners_for_a > 0:
        expected_corners_base_a = corners_for_a
    else:
        expected_corners_base_a = 5.0 * cam_a

    if base_b and base_b > 0:
        expected_corners_base_b = base_b
    elif corners_for_b is not None and corners_for_b > 0:
        expected_corners_base_b = corners_for_b
    else:
        expected_corners_base_b = 4.0 * cam_b

    # Blend with rolling per-match averages if available
    per_match_data = load_per_match_corners()
    if per_match_data:
        rolling_a = compute_rolling_corner_avg(team_a, per_match_data)
        rolling_b = compute_rolling_corner_avg(team_b, per_match_data)
        if rolling_a:
            roll_cf_a, _, n_a = rolling_a
            w_a = min(n_a / 10.0, 0.7)
            expected_corners_base_a = (1.0 - w_a) * expected_corners_base_a + w_a * roll_cf_a
        if rolling_b:
            roll_cf_b, _, n_b = rolling_b
            w_b = min(n_b / 10.0, 0.7)
            expected_corners_base_b = (1.0 - w_b) * expected_corners_base_b + w_b * roll_cf_b

    # Home/away venue factor for corners
    venue_factor_a = HOME_CORNER_FACTOR if venue_a == "home" else (AWAY_CORNER_FACTOR if venue_a == "away" else 1.0)
    venue_factor_b = HOME_CORNER_FACTOR if venue_b == "home" else (AWAY_CORNER_FACTOR if venue_b == "away" else 1.0)
    expected_corners_base_a *= venue_factor_a
    expected_corners_base_b *= venue_factor_b

    # Capped opponent adjustment: max +/- 15%
    concession_a_capped = max(0.85, min(1.15, concession_a))
    concession_b_capped = max(0.85, min(1.15, concession_b))

    lambda_corners_a = max(1.5, min(9.5, expected_corners_base_a * concession_b_capped))
    lambda_corners_b = max(1.5, min(9.5, expected_corners_base_b * concession_a_capped))

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

    # Blend with historical Over/Under percentages if available (Footiqo)
    if predict_half == "second":
        # Reuse venue-specific splits from above (already computed as sh_a, sh_b)
        
        # Dynamic historical weight based on sample size
        matches_a = sh_a.get("matches", 0) or 0
        matches_b = sh_b.get("matches", 0) or 0
        avg_matches = (matches_a + matches_b) / 2.0
        if avg_matches >= 15:
            hist_weight = 0.40
        elif avg_matches >= 10:
            hist_weight = 0.30
        elif avg_matches >= 5:
            hist_weight = 0.20
        else:
            hist_weight = 0.10
        sim_weight = 1.0 - hist_weight
        
        # Mapping of thresholds to Footiqo keys
        thresholds = {
            7.5: "over35",
            8.5: "over45",
            9.5: "over55",
            10.5: "over55"
        }
        
        probs = [prob_corners_over_7_5, prob_corners_over_8_5, prob_corners_over_9_5, prob_corners_over_10_5]
        blended_probs = []
        
        for i, thresh in enumerate([7.5, 8.5, 9.5, 10.5]):
            key = thresholds[thresh]
            hist_a = sh_a.get(key, 50) / 100.0
            hist_b = sh_b.get(key, 50) / 100.0
            hist_avg = (hist_a + hist_b) / 2.0
            
            blended_prob = (sim_weight * probs[i]) + (hist_weight * hist_avg)
            blended_probs.append(blended_prob)
            
        prob_corners_over_7_5, prob_corners_over_8_5, prob_corners_over_9_5, prob_corners_over_10_5 = blended_probs

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

    # Generate Extended Markets (cards, shots, times, players, penalties, specials)
    # Helper: Poisson probability of scoring exactly k goals given lambda
    def _pp(k, lam):
        return poisson_pmf(k, lam)

    # ---- 1. SHOTS (from shots_per_90) ----
    total_shots_exp = sh_a + sh_b
    on_target_rate = 0.35
    shots_on_target_a = sh_a * on_target_rate
    shots_on_target_b = sh_b * on_target_rate
    total_sot_exp = shots_on_target_a + shots_on_target_b

    # Most shots: Poisson comparison
    most_shots_a = sum(_pp(i, sh_a) * sum(_pp(j, sh_b) for j in range(int(i))) for i in range(0, 30))
    most_shots_b = sum(_pp(j, sh_b) * sum(_pp(i, sh_a) for i in range(int(j))) for j in range(0, 30))
    most_shots_draw = 1.0 - most_shots_a - most_shots_b

    shots_markets = {
        "expectedA": round(sh_a, 1), "expectedB": round(sh_b, 1), "expectedTotal": round(total_shots_exp, 1),
        "overUnderTotal": [
            {"threshold": 16.5, "over": round(sum(_pp(k, total_shots_exp) for k in range(17, 60)), 4), "under": round(sum(_pp(k, total_shots_exp) for k in range(0, 17)), 4)},
            {"threshold": 18.5, "over": round(sum(_pp(k, total_shots_exp) for k in range(19, 60)), 4), "under": round(sum(_pp(k, total_shots_exp) for k in range(0, 19)), 4)},
            {"threshold": 20.5, "over": round(sum(_pp(k, total_shots_exp) for k in range(21, 60)), 4), "under": round(sum(_pp(k, total_shots_exp) for k in range(0, 21)), 4)},
            {"threshold": 22.5, "over": round(sum(_pp(k, total_shots_exp) for k in range(23, 60)), 4), "under": round(sum(_pp(k, total_shots_exp) for k in range(0, 23)), 4)}
        ],
        "overUnderOnTarget": [
            {"threshold": 4.5, "over": round(sum(_pp(k, total_sot_exp) for k in range(5, 60)), 4), "under": round(sum(_pp(k, total_sot_exp) for k in range(0, 5)), 4)},
            {"threshold": 5.5, "over": round(sum(_pp(k, total_sot_exp) for k in range(6, 60)), 4), "under": round(sum(_pp(k, total_sot_exp) for k in range(0, 6)), 4)},
            {"threshold": 6.5, "over": round(sum(_pp(k, total_sot_exp) for k in range(7, 60)), 4), "under": round(sum(_pp(k, total_sot_exp) for k in range(0, 7)), 4)},
            {"threshold": 7.5, "over": round(sum(_pp(k, total_sot_exp) for k in range(8, 60)), 4), "under": round(sum(_pp(k, total_sot_exp) for k in range(0, 8)), 4)}
        ],
        "mostShots": {
            "teamA": round(most_shots_a, 4),
            "draw": round(most_shots_draw, 4),
            "teamB": round(most_shots_b, 4)
        },
        "shootingPlayersA": _top_players(team_a, "shooting", 10),
        "shootingPlayersB": _top_players(team_b, "shooting", 10)
    }
    # ---- 2. PASSES (estimated or from data) ----
    passes_a = entry_a.get("passes_per_90") or max(5.0, min(70.0, sh_a * 4))
    passes_b = entry_b.get("passes_per_90") or max(5.0, min(70.0, sh_b * 4))
    passes_completed_a = entry_a.get("passes_completed_per_90") or passes_a * 0.75
    passes_completed_b = entry_b.get("passes_completed_per_90") or passes_b * 0.75
    accuracy_a = passes_completed_a / passes_a if passes_a else 0.0
    accuracy_b = passes_completed_b / passes_b if passes_b else 0.0
    passes_markets = {
        "expectedA": round(passes_a, 1),
        "expectedB": round(passes_b, 1),
        "expectedTotal": round(passes_a + passes_b, 1),
        "accuracyA": round(accuracy_a * 100, 1),
        "accuracyB": round(accuracy_b * 100, 1)
    }

    # ---- B. LOAD GOALSCORER STATS (for TIMES, PLAYERS, PENALTIES, SPECIALS) ----
    _gs_data = {"goals_a":{},"goals_b":{},"total_a":0,"total_b":0,
                "first_a":{},"first_b":{},"multi_a":{},"multi_b":{},
                "pen_a":0,"pen_b":0,"own_a":0,"own_b":0,
                "total_matches_a":0,"total_matches_b":0,
                "goals_1h_a":0,"goals_2h_a":0,"goals_1h_b":0,"goals_2h_b":0}
    try:
        _canon_a = SLUG_TO_NAME.get(team_a, team_a.replace("-"," ").title())
        _canon_b = SLUG_TO_NAME.get(team_b, team_b.replace("-"," ").title())
        _low_a = _canon_a.lower()
        _low_b = _canon_b.lower()

        _scorers_rows = load_goalscorers()

        if _scorers_rows:
            # 1. Parse dates and find the max date
            import datetime as dt_mod
            max_date = None
            parsed_rows = []
            
            for _r in _scorers_rows:
                _date_str = _r.get("date")
                if not _date_str:
                    continue
                try:
                    if isinstance(_date_str, (dt_mod.date, dt_mod.datetime)):
                        _d = dt_mod.datetime.combine(_date_str, dt_mod.time.min) if isinstance(_date_str, dt_mod.date) else _date_str
                    else:
                        _d = dt_mod.datetime.strptime(_date_str, "%Y-%m-%d")
                    if max_date is None or _d > max_date:
                        max_date = _d
                    parsed_rows.append((_d, _r))
                except Exception:
                    pass
            
            if max_date is None:
                max_date = dt_mod.datetime.now()
                
            # Filter rows by cutoff date
            # half_life_months represents the decay months slider
            cutoff_days = int(half_life_months * 30.44)
            cutoff_date = max_date - dt_mod.timedelta(days=cutoff_days)
            
            _slug_a_clean = team_a.replace("-"," ")
            _slug_b_clean = team_b.replace("-"," ")
            _team_a_names = {team_a, _slug_a_clean, _low_a}
            _team_b_names = {team_b, _slug_b_clean, _low_b}

            _scorers_a = {}
            _scorers_b = {}
            _total_a = 0
            _total_b = 0
            _pen_a = 0
            _pen_b = 0
            _own_a = 0
            _own_b = 0
            _1h_a = 0
            _2h_a = 0
            _1h_b = 0
            _2h_b = 0
            # Goles por intervalo de 15 min: 0-15, 15-30, 30-45, 45-60, 60-75, 75-90
            _intervals_a = [0, 0, 0, 0, 0, 0]
            _intervals_b = [0, 0, 0, 0, 0, 0]
            _first_goal_min_a = []
            _first_goal_min_b = []

            for _d, _r in parsed_rows:
                if _d < cutoff_date:
                    continue
                    
                _tn = _r["team"]
                _is_a = _tn in _team_a_names
                _is_b = _tn in _team_b_names
                if not _is_a and not _is_b:
                    continue

                _min = _r.get("minute")
                if _min is None:
                    _min = 60

                if _is_a:
                    _total_a += 1
                    _scorers_a[_r["scorer"]] = _scorers_a.get(_r["scorer"], 0) + 1
                    if _min <= 45:
                        _1h_a += 1
                    else:
                        _2h_a += 1
                    # Intervalo de 15 min
                    _idx = min(int(_min // 15), 5)
                    _intervals_a[_idx] += 1
                    if not _r.get("own_goal"):
                        _first_goal_min_a.append(_min)
                    if _r["penalty"]:
                        _pen_a += 1
                    if _r["own_goal"]:
                        _own_a += 1
                if _is_b:
                    _total_b += 1
                    _scorers_b[_r["scorer"]] = _scorers_b.get(_r["scorer"], 0) + 1
                    if _min <= 45:
                        _1h_b += 1
                    else:
                        _2h_b += 1
                    _idx = min(int(_min // 15), 5)
                    _intervals_b[_idx] += 1
                    if not _r.get("own_goal"):
                        _first_goal_min_b.append(_min)
                    if _r["penalty"]:
                        _pen_b += 1
                    if _r["own_goal"]:
                        _own_b += 1

            _match_count_a = len([m for m in matches if m.get("homeSlug") == team_a or m.get("awaySlug") == team_a])
            _match_count_b = len([m for m in matches if m.get("homeSlug") == team_b or m.get("awaySlug") == team_b])

            _gs_data = {
                "goals_a": _scorers_a, "goals_b": _scorers_b,
                "total_a": _total_a, "total_b": _total_b,
                "first_a": {}, "first_b": {},
                "multi_a": {}, "multi_b": {},
                "pen_a": _pen_a, "pen_b": _pen_b,
                "own_a": _own_a, "own_b": _own_b,
                "total_matches_a": _match_count_a, "total_matches_b": _match_count_b,
                "goals_1h_a": _1h_a, "goals_2h_a": _2h_a,
                "goals_1h_b": _1h_b, "goals_2h_b": _2h_b,
                "intervals_a": _intervals_a, "intervals_b": _intervals_b,
                "first_goal_min_a": _first_goal_min_a, "first_goal_min_b": _first_goal_min_b
            }
    except Exception:
        pass

    # ---- 2. TIMES (HT/FT from per-team 1H/2H split) ----
    _total_gs_h = _gs_data["goals_1h_a"] + _gs_data["goals_1h_b"] + _gs_data["goals_2h_a"] + _gs_data["goals_2h_b"]
    if _total_gs_h > 0:
        _gs_1h = _gs_data["goals_1h_a"] + _gs_data["goals_1h_b"]
        _gs_2h = _gs_data["goals_2h_a"] + _gs_data["goals_2h_b"]
        first_half_factor = _gs_1h / _total_gs_h
        second_half_factor = _gs_2h / _total_gs_h
    else:
        first_half_factor = 0.42
        second_half_factor = 0.58
    xg_1h_a = xg_a * first_half_factor
    xg_1h_b = xg_b * first_half_factor
    xg_2h_a = xg_a * second_half_factor
    xg_2h_b = xg_b * second_half_factor

    def _win_probs(lam_a, lam_b):
        w = sum(_pp(i, lam_a) * sum(_pp(j, lam_b) for j in range(int(i))) for i in range(0, 15))
        l = sum(_pp(j, lam_b) * sum(_pp(i, lam_a) for i in range(int(j))) for j in range(0, 15))
        d = 1.0 - w - l
        return w, d, l

    w1h, d1h, l1h = _win_probs(xg_1h_a, xg_1h_b)
    w2h, d2h, l2h = _win_probs(xg_2h_a, xg_2h_b)

    def _ou_probs(lam, threshold):
        over = sum(_pp(k, lam) for k in range(int(threshold)+1, 60))
        under = 1.0 - over
        return round(over, 4), round(under, 4)

    total_1h = xg_1h_a + xg_1h_b
    total_2h = xg_2h_a + xg_2h_b

    htft = {}
    for ht_res, ht_prob in [("1", w1h), ("X", d1h), ("2", l1h)]:
        for ft_res, ft_prob in zip(["1","X","2"], [w2h, d2h, l2h]):
            key = f"{ht_res}_{ft_res}"
            htft[key] = round(ht_prob * ft_prob, 4)

    btts_1h = (1 - _pp(0, xg_1h_a)) * (1 - _pp(0, xg_1h_b))
    btts_2h = (1 - _pp(0, xg_2h_a)) * (1 - _pp(0, xg_2h_b))

    times_markets = {
        "winner1T": {"1": round(w1h, 4), "X": round(d1h, 4), "2": round(l1h, 4)},
        "winner2T": {"1": round(w2h, 4), "X": round(d2h, 4), "2": round(l2h, 4)},
        "overUnder1T": [
            {"threshold": 0.5, "over": _ou_probs(total_1h, 0.5)[0], "under": _ou_probs(total_1h, 0.5)[1]},
            {"threshold": 1.5, "over": _ou_probs(total_1h, 1.5)[0], "under": _ou_probs(total_1h, 1.5)[1]}
        ],
        "btts1T": {"yes": round(btts_1h, 4), "no": round(1.0 - btts_1h, 4)},
        "btts2T": {"yes": round(btts_2h, 4), "no": round(1.0 - btts_2h, 4)},
        "htft": htft
    }

    # ---- HELPER: Player market builders (defined before CARDS section which uses _build_booking_probs) ----
    def _build_anytime(scorers_sorted, total_goals, xg_team, limit=10):
        if not scorers_sorted or total_goals <= 0:
            return []
        result = []
        for name, goals in scorers_sorted[:limit]:
            share = goals / total_goals
            player_xg = xg_team * share
            prob = 1.0 - math.exp(-player_xg)
            prob = min(prob, 0.85)
            result.append({"name": name, "probability": round(prob, 4)})
        return result

    def _build_first(scorers_sorted, total_goals, xg_team, limit=10):
        if not scorers_sorted or total_goals <= 0:
            return []
        result = []
        for name, goals in scorers_sorted[:limit]:
            share = goals / total_goals
            player_xg = xg_team * share
            anytime = 1.0 - math.exp(-player_xg)
            prob = anytime * 0.25
            prob = min(prob, 0.30)
            result.append({"name": name, "probability": round(prob, 4)})
        return result

    def _build_multi(scorers_sorted, total_goals, xg_team, limit=10):
        if not scorers_sorted or total_goals <= 0:
            return []
        result = []
        for name, goals in scorers_sorted[:limit]:
            share = goals / total_goals
            player_xg = xg_team * share
            prob = (1.0 - math.exp(-player_xg)) - (player_xg * math.exp(-player_xg))
            prob = min(prob, 0.30)
            result.append({"name": name, "probability": round(prob, 4)})
        return result

    def _build_booking_probs(team_slug, team_cards, limit=10):
        ps = load_player_stats()
        team = ps.get(team_slug, {})
        players = team.get("misc", [])
        if not players or team_cards <= 0:
            return []
        total_bookings = sum(p.get("cards_yellow", 0) for p in players)
        if total_bookings <= 0:
            return []
        result = []
        for p in players:
            share = p.get("cards_yellow", 0) / total_bookings
            prob = 1.0 - math.exp(-team_cards * share)
            prob = min(prob, 0.40)
            result.append({"player": p["player"], "name": p["player"], "probability": round(prob, 4)})
        result.sort(key=lambda x: -x["probability"])
        return result[:limit]

    # ---- 3. CARDS (con datos reales FBref si disponibles) ----
    cards_a = entry_a.get("yellow_cards_per_90") if "yellow_cards_per_90" in entry_a else None
    cards_b = entry_b.get("yellow_cards_per_90") if "yellow_cards_per_90" in entry_b else None
    red_a = entry_a.get("red_cards_per_90") if "red_cards_per_90" in entry_a else None
    red_b = entry_b.get("red_cards_per_90") if "red_cards_per_90" in entry_b else None
    if cards_a is None:
        elo_a = ratings.get(team_a, 1500)
        cards_a = 2.5 * (1650 / max(elo_a, 1300))
    if cards_b is None:
        elo_b = ratings.get(team_b, 1500)
        cards_b = 2.5 * (1650 / max(elo_b, 1300))
    cards_a *= referee_intensity
    cards_b *= referee_intensity
    total_cards = cards_a + cards_b
    if red_a is None:
        red_prob_a = 0.08
    else:
        red_prob_a = 1.0 - math.exp(-red_a)
    if red_b is None:
        red_prob_b = 0.08
    else:
        red_prob_b = 1.0 - math.exp(-red_b)
    red_any = 1.0 - (1.0 - red_prob_a) * (1.0 - red_prob_b)

    def _make_ou(lam, thresholds):
        return [{"threshold": t, "over": round(sum(_pp(k, lam) for k in range(int(t)+1, 60)), 4), "under": round(sum(_pp(k, lam) for k in range(0, int(t)+1)), 4)} for t in thresholds]

    cards_markets = {
        "expectedA": round(cards_a, 1), "expectedB": round(cards_b, 1), "expectedTotal": round(total_cards, 1),
        "overUnder": _make_ou(total_cards, [3.5, 4.5, 5.5, 6.5]),
        "redCard": {"yes": round(red_any, 4), "no": round(1.0 - red_any, 4)},
        "bookingPlayersA": _build_booking_probs(team_a, cards_a, 10),
        "bookingPlayersB": _build_booking_probs(team_b, cards_b, 10)
    }

    # ---- 4. PLAYERS (from goal stats loaded above) ----
    _scorers_a_sorted = sorted(_gs_data["goals_a"].items(), key=lambda x: -x[1])
    _scorers_b_sorted = sorted(_gs_data["goals_b"].items(), key=lambda x: -x[1])
    _total_a = max(_gs_data["total_a"], 1)
    _total_b = max(_gs_data["total_b"], 1)

    _anytime_a = _build_anytime(_scorers_a_sorted, _total_a, xg_a)
    _anytime_b = _build_anytime(_scorers_b_sorted, _total_b, xg_b)

    players_markets = {
        "firstScorerA": _build_first(_scorers_a_sorted, _total_a, xg_a),
        "anytimeScorerA": _anytime_a,
        "multiGoalsA": _build_multi(_scorers_a_sorted, _total_a, xg_a),
        "firstScorerB": _build_first(_scorers_b_sorted, _total_b, xg_b),
        "anytimeScorerB": _anytime_b,
        "multiGoalsB": _build_multi(_scorers_b_sorted, _total_b, xg_b),
        "assistsA": [p for p in _top_players(team_a, "passing", 10) if p.get("assists", 0) > 0],
        "assistsB": [p for p in _top_players(team_b, "passing", 10) if p.get("assists", 0) > 0]
    }

    # ---- 4b. TOP SCORER (goleador mas probable del partido completo) ----
    _top_scorer = {"name": None, "team": None, "probability": 0.0}
    if _anytime_a and _anytime_a[0]["probability"] > _top_scorer["probability"]:
        _top_scorer = {"name": _anytime_a[0]["name"], "team": team_a, "probability": _anytime_a[0]["probability"]}
    if _anytime_b and _anytime_b[0]["probability"] > _top_scorer["probability"]:
        _top_scorer = {"name": _anytime_b[0]["name"], "team": team_b, "probability": _anytime_b[0]["probability"]}
    players_markets["topScorer"] = {
        "name": _top_scorer["name"],
        "team": _top_scorer["team"],
        "probability": round(_top_scorer["probability"], 4)
    }

    # ---- 4c. GOALS TIMELINE (distribucion de goles por intervalo de 15 min) ----
    _int_labels = ["0-15", "15-30", "30-45", "45-60", "60-75", "75-90"]
    _int_a = _gs_data.get("intervals_a", [0, 0, 0, 0, 0, 0])
    _int_b = _gs_data.get("intervals_b", [0, 0, 0, 0, 0, 0])
    _sum_int_a = sum(_int_a) if sum(_int_a) > 0 else 1
    _sum_int_b = sum(_int_b) if sum(_int_b) > 0 else 1

    goals_timeline = []
    for i, label in enumerate(_int_labels):
        pct_a = _int_a[i] / _sum_int_a if _sum_int_a > 0 else 0.0
        pct_b = _int_b[i] / _sum_int_b if _sum_int_b > 0 else 0.0
        # Goles esperados en este intervalo = xG * distribucion historica
        exp_a = round(xg_a * pct_a, 3)
        exp_b = round(xg_b * pct_b, 3)
        goals_timeline.append({
            "interval": label,
            "pctA": round(pct_a, 4),
            "pctB": round(pct_b, 4),
            "expA": exp_a,
            "expB": exp_b
        })
    players_markets["goalsTimeline"] = goals_timeline

    # ---- 4d. AVERAGE FIRST EVENT TIME ----
    _fga = _gs_data.get("first_goal_min_a", [])
    _fgb = _gs_data.get("first_goal_min_b", [])
    _avg_first_goal_a = round(sum(_fga) / len(_fga)) if _fga else None
    _avg_first_goal_b = round(sum(_fgb) / len(_fgb)) if _fgb else None
    # Promedio combinado (primer gol del partido)
    _all_first = sorted(_fga + _fgb)
    _avg_first_goal_match = round(sum(_all_first) / len(_all_first)) if _all_first else None
    players_markets["avgFirstEvent"] = {
        "firstGoalA": _avg_first_goal_a,
        "firstGoalB": _avg_first_goal_b,
        "firstGoalMatch": _avg_first_goal_match
    }

    # ---- 5. PENALTIES (per-team rates from goalscorers) ----
    _pen_prob_a = _gs_data["pen_a"] / max(_gs_data["total_matches_a"], 1)
    _pen_prob_b = _gs_data["pen_b"] / max(_gs_data["total_matches_b"], 1)
    _pen_prob = min(max((_pen_prob_a + _pen_prob_b) / 2, 0.02), 0.40)

    penalties_markets = {
        "conceded": {"yes": round(_pen_prob, 4), "no": round(1.0 - _pen_prob, 4)},
        "scored": {"yes": round(_pen_prob * 0.80, 4), "no": round(1.0 - _pen_prob * 0.80, 4)},
        "missed": {"yes": round(_pen_prob * 0.20, 4), "no": round(1.0 - _pen_prob * 0.20, 4)}
    }

    # ---- 6. SPECIALS ----
    cs_a = sum(p for (a,b),p in joint_probs.items() if b == 0)
    cs_b = sum(p for (a,b),p in joint_probs.items() if a == 0)
    wtn_a = sum(p for (a,b),p in joint_probs.items() if a > b and b == 0)
    wtn_b = sum(p for (a,b),p in joint_probs.items() if b > a and a == 0)

    _own_rate_a = _gs_data["own_a"] / max(_gs_data["total_matches_a"], 1)
    _own_rate_b = _gs_data["own_b"] / max(_gs_data["total_matches_b"], 1)
    _own_prob = min(max((_own_rate_a + _own_rate_b) / 2, 0.005), 0.10)

    _hattrick_prob = _get_hattrick_rate() * (1.0 - math.exp(-(xg_a + xg_b) * 0.5))
    _header_prob = 1.0 - math.exp(-(xg_a + xg_b) * 0.10)
    _freekick_prob = 1.0 - math.exp(-(xg_a + xg_b) * 0.03)

    specials_markets = {
        "headerGoal": {"yes": round(_header_prob, 4), "no": round(1.0 - _header_prob, 4)},
        "freekickGoal": {"yes": round(_freekick_prob, 4), "no": round(1.0 - _freekick_prob, 4)},
        "ownGoal": {"yes": round(_own_prob, 4), "no": round(1.0 - _own_prob, 4)},
        "hatTrick": {"yes": round(min(_hattrick_prob, 0.15), 4), "no": round(1.0 - min(_hattrick_prob, 0.15), 4)},
        "cleanSheetA": {"yes": round(cs_a, 4), "no": round(1.0 - cs_a, 4)},
        "cleanSheetB": {"yes": round(cs_b, 4), "no": round(1.0 - cs_b, 4)},
        "winToNilA": {"yes": round(wtn_a, 4), "no": round(1.0 - wtn_a, 4)},
        "winToNilB": {"yes": round(wtn_b, 4), "no": round(1.0 - wtn_b, 4)}
    }

    extended_markets = {
        "cards": cards_markets,
        "shots": shots_markets,
        "passes": passes_markets,
        "times": times_markets,
        "players": players_markets,
        "penalties": penalties_markets,
        "specials": specials_markets
    }

    result = {
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
        "comparisonStats": comparison_stats,
        "extendedMarkets": extended_markets
    }
    if return_raw:
        result["_joint_probs"] = {(str(a),str(b)):float(p) for (a,b),p in joint_probs.items()}
        result["_sim_corners_a"] = sim_corners_a.tolist()
        result["_sim_corners_b"] = sim_corners_b.tolist()
    return result

def run_betbuilder_sim(team_a, team_b, rank_a, rank_b, fifa_weight_pct, h2h_weight_pct, half_life_months, num_sims, legs, strength_override_a=1.0, strength_override_b=1.0, altitude=0, host_country=None):
    matches, ratings = load_data()
    if not legs or len(legs) == 0:
        return {"simulation": {"combinedProb": 0.0}, "historicalMatches": {"directH2H": [], "similarProfile": []}}

    result = run_prediction_sim(team_a, team_b, rank_a, rank_b, fifa_weight_pct, h2h_weight_pct, half_life_months, num_sims, strength_override_a=strength_override_a, strength_override_b=strength_override_b, altitude=altitude, host_country=host_country, return_raw=True)
    joint_probs = result.get("_joint_probs", {})
    sim_corners_a = result.get("_sim_corners_a", [])
    sim_corners_b = result.get("_sim_corners_b", [])
    goals_markets = result.get("goalsMarkets", {})
    extended_markets = result.get("extendedMarkets", {})

    # Goal leg predicates
    def _check_goals_leg(leg, a, b):
        if leg == "win_a": return a > b
        if leg == "draw": return a == b
        if leg == "win_b": return a < b
        if leg == "btts_yes": return a >= 1 and b >= 1
        if leg == "btts_no": return a == 0 or b == 0
        if leg == "double_chance_1X": return a >= b
        if leg == "double_chance_12": return a != b
        if leg == "double_chance_X2": return b >= a
        total = a + b
        if leg == "over_0_5_goals": return total > 0.5
        if leg == "under_0_5_goals": return total <= 0.5
        if leg == "over_1_5_goals": return total > 1.5
        if leg == "under_1_5_goals": return total <= 1.5
        if leg == "over_2_5_goals": return total > 2.5
        if leg == "under_2_5_goals": return total <= 2.5
        if leg == "over_3_5_goals": return total > 3.5
        if leg == "under_3_5_goals": return total <= 3.5
        if leg == "handicap_minus_1_5_a": return a - b >= 2
        if leg == "handicap_plus_1_5_a": return b - a < 2
        if leg == "handicap_minus_1_5_b": return b - a >= 2
        if leg == "handicap_plus_1_5_b": return a - b < 2
        return None

    # Corner leg predicates
    def _check_corners_leg(leg, ca, cb):
        if leg == "corners_win_a": return ca > cb
        if leg == "corners_draw": return ca == cb
        if leg == "corners_win_b": return cb > ca
        total = ca + cb
        if leg == "corners_over_7_5": return total > 7.5
        if leg == "corners_under_7_5": return total <= 7.5
        if leg == "corners_over_8_5": return total > 8.5
        if leg == "corners_under_8_5": return total <= 8.5
        if leg == "corners_over_9_5": return total > 9.5
        if leg == "corners_under_9_5": return total <= 9.5
        if leg == "corners_over_10_5": return total > 10.5
        if leg == "corners_under_10_5": return total <= 10.5
        return None

    # DNB leg lookup (probability-based, not Monte Carlo)
    def _dnb_prob(leg):
        dnb = goals_markets.get("dnb", {})
        if leg == "dnb_1": return dnb.get("1", 0.5)
        if leg == "dnb_2": return dnb.get("2", 0.5)
        return None

    # Extended markets lookup (probability-based)
    def _extended_prob(leg):
        cards = extended_markets.get("cards", {})
        shots = extended_markets.get("shots", {})
        times = extended_markets.get("times", {})
        penalties = extended_markets.get("penalties", {})
        specials = extended_markets.get("specials", {})
        players = extended_markets.get("players", {})

        # --- CARDS ---
        if leg == "cards_over_3_5":
            for ou in cards.get("overUnder", []):
                if ou.get("threshold") == 3.5: return ou.get("over", 0.5)
        if leg == "cards_under_3_5":
            for ou in cards.get("overUnder", []):
                if ou.get("threshold") == 3.5: return ou.get("under", 0.5)
        if leg == "cards_over_4_5":
            for ou in cards.get("overUnder", []):
                if ou.get("threshold") == 4.5: return ou.get("over", 0.5)
        if leg == "cards_under_4_5":
            for ou in cards.get("overUnder", []):
                if ou.get("threshold") == 4.5: return ou.get("under", 0.5)
        if leg == "cards_over_5_5":
            for ou in cards.get("overUnder", []):
                if ou.get("threshold") == 5.5: return ou.get("over", 0.5)
        if leg == "cards_under_5_5":
            for ou in cards.get("overUnder", []):
                if ou.get("threshold") == 5.5: return ou.get("under", 0.5)
        if leg == "cards_red_yes": return cards.get("redCard", {}).get("yes", 0.05)
        if leg == "cards_red_no": return cards.get("redCard", {}).get("no", 0.95)

        # --- SHOTS ---
        if leg == "shots_over_16_5":
            for ou in shots.get("overUnderTotal", []):
                if ou.get("threshold") == 16.5: return ou.get("over", 0.5)
        if leg == "shots_under_16_5":
            for ou in shots.get("overUnderTotal", []):
                if ou.get("threshold") == 16.5: return ou.get("under", 0.5)
        if leg == "shots_over_18_5":
            for ou in shots.get("overUnderTotal", []):
                if ou.get("threshold") == 18.5: return ou.get("over", 0.5)
        if leg == "shots_under_18_5":
            for ou in shots.get("overUnderTotal", []):
                if ou.get("threshold") == 18.5: return ou.get("under", 0.5)
        if leg == "shots_over_20_5":
            for ou in shots.get("overUnderTotal", []):
                if ou.get("threshold") == 20.5: return ou.get("over", 0.5)
        if leg == "shots_under_20_5":
            for ou in shots.get("overUnderTotal", []):
                if ou.get("threshold") == 20.5: return ou.get("under", 0.5)
        if leg == "shots_most_a": return shots.get("mostShots", {}).get("teamA", 0.4)
        if leg == "shots_most_b": return shots.get("mostShots", {}).get("teamB", 0.4)
        if leg == "shots_most_draw": return shots.get("mostShots", {}).get("draw", 0.2)
        if leg == "shots_sot_over_4_5":
            for ou in shots.get("overUnderOnTarget", []):
                if ou.get("threshold") == 4.5: return ou.get("over", 0.5)
        if leg == "shots_sot_under_4_5":
            for ou in shots.get("overUnderOnTarget", []):
                if ou.get("threshold") == 4.5: return ou.get("under", 0.5)
        if leg == "shots_sot_over_5_5":
            for ou in shots.get("overUnderOnTarget", []):
                if ou.get("threshold") == 5.5: return ou.get("over", 0.5)
        if leg == "shots_sot_under_5_5":
            for ou in shots.get("overUnderOnTarget", []):
                if ou.get("threshold") == 5.5: return ou.get("under", 0.5)

        # --- TIMES ---
        w1t = times.get("winner1T", {})
        w2t = times.get("winner2T", {})
        if leg == "times_1t_a": return w1t.get("1", 0.4)
        if leg == "times_1t_draw": return w1t.get("X", 0.3)
        if leg == "times_1t_b": return w1t.get("2", 0.3)
        if leg == "times_2t_a": return w2t.get("1", 0.4)
        if leg == "times_2t_draw": return w2t.get("X", 0.3)
        if leg == "times_2t_b": return w2t.get("2", 0.3)
        for ou in times.get("overUnder1T", []):
            if leg == "times_1t_over_0_5" and ou.get("threshold") == 0.5: return ou.get("over", 0.5)
            if leg == "times_1t_under_0_5" and ou.get("threshold") == 0.5: return ou.get("under", 0.5)
            if leg == "times_1t_over_1_5" and ou.get("threshold") == 1.5: return ou.get("over", 0.5)
            if leg == "times_1t_under_1_5" and ou.get("threshold") == 1.5: return ou.get("under", 0.5)
        btts1 = times.get("btts1T", {})
        btts2 = times.get("btts2T", {})
        if leg == "times_btts_1t_yes": return btts1.get("yes", 0.3)
        if leg == "times_btts_1t_no": return btts1.get("no", 0.7)
        if leg == "times_btts_2t_yes": return btts2.get("yes", 0.4)
        if leg == "times_btts_2t_no": return btts2.get("no", 0.6)
        htft = times.get("htft", {})
        if leg == "times_htft_1_1": return htft.get("1_1", 0.15)
        if leg == "times_htft_1_X": return htft.get("1_X", 0.10)
        if leg == "times_htft_1_2": return htft.get("1_2", 0.05)
        if leg == "times_htft_X_1": return htft.get("X_1", 0.12)
        if leg == "times_htft_X_X": return htft.get("X_X", 0.15)
        if leg == "times_htft_X_2": return htft.get("X_2", 0.08)
        if leg == "times_htft_2_1": return htft.get("2_1", 0.03)
        if leg == "times_htft_2_X": return htft.get("2_X", 0.07)
        if leg == "times_htft_2_2": return htft.get("2_2", 0.10)

        # --- PENALTIES ---
        pen = penalties if penalties else {}
        if leg == "pen_conceded_yes": return pen.get("conceded", {}).get("yes", 0.15)
        if leg == "pen_conceded_no": return pen.get("conceded", {}).get("no", 0.85)
        if leg == "pen_scored_yes": return pen.get("scored", {}).get("yes", 0.12)
        if leg == "pen_scored_no": return pen.get("scored", {}).get("no", 0.88)
        if leg == "pen_missed_yes": return pen.get("missed", {}).get("yes", 0.03)
        if leg == "pen_missed_no": return pen.get("missed", {}).get("no", 0.97)

        # --- SPECIALS ---
        sp = specials if specials else {}
        if leg == "special_header_yes": return sp.get("headerGoal", {}).get("yes", 0.25)
        if leg == "special_header_no": return sp.get("headerGoal", {}).get("no", 0.75)
        if leg == "special_freekick_yes": return sp.get("freekickGoal", {}).get("yes", 0.08)
        if leg == "special_freekick_no": return sp.get("freekickGoal", {}).get("no", 0.92)
        if leg == "special_own_yes": return sp.get("ownGoal", {}).get("yes", 0.02)
        if leg == "special_own_no": return sp.get("ownGoal", {}).get("no", 0.98)
        if leg == "special_hattrick_yes": return sp.get("hatTrick", {}).get("yes", 0.05)
        if leg == "special_hattrick_no": return sp.get("hatTrick", {}).get("no", 0.95)
        if leg == "special_cleansheet_a_yes": return sp.get("cleanSheetA", {}).get("yes", 0.25)
        if leg == "special_cleansheet_a_no": return sp.get("cleanSheetA", {}).get("no", 0.75)
        if leg == "special_cleansheet_b_yes": return sp.get("cleanSheetB", {}).get("yes", 0.25)
        if leg == "special_cleansheet_b_no": return sp.get("cleanSheetB", {}).get("no", 0.75)
        if leg == "special_wintonil_a_yes": return sp.get("winToNilA", {}).get("yes", 0.15)
        if leg == "special_wintonil_a_no": return sp.get("winToNilA", {}).get("no", 0.85)
        if leg == "special_wintonil_b_yes": return sp.get("winToNilB", {}).get("yes", 0.15)
        if leg == "special_wintonil_b_no": return sp.get("winToNilB", {}).get("no", 0.85)

        # --- PLAYER MARKETS (individual player legs) ---
        # Format: player_first_{name}, player_anytime_{name}, player_multi_{name}, player_assist_{name}, player_card_{name}
        if leg.startswith("player_first_"):
            player_name = leg.replace("player_first_", "")
            for p in players.get("firstScorerA", []) + players.get("firstScorerB", []):
                if p.get("name", "").lower().replace(" ", "_") == player_name.lower().replace(" ", "_"):
                    return p.get("probability", 0.0)
        if leg.startswith("player_anytime_"):
            player_name = leg.replace("player_anytime_", "")
            for p in players.get("anytimeScorerA", []) + players.get("anytimeScorerB", []):
                if p.get("name", "").lower().replace(" ", "_") == player_name.lower().replace(" ", "_"):
                    return p.get("probability", 0.0)
        if leg.startswith("player_multi_"):
            player_name = leg.replace("player_multi_", "")
            for p in players.get("multiGoalsA", []) + players.get("multiGoalsB", []):
                if p.get("name", "").lower().replace(" ", "_") == player_name.lower().replace(" ", "_"):
                    return p.get("probability", 0.0)
        if leg.startswith("player_assist_"):
            player_name = leg.replace("player_assist_", "")
            for p in players.get("assistsA", []) + players.get("assistsB", []):
                if p.get("name", "").lower().replace(" ", "_") == player_name.lower().replace(" ", "_"):
                    return p.get("probability", 0.0) if "probability" in p else (p.get("assists", 0) / 10.0)
        if leg.startswith("player_card_"):
            player_name = leg.replace("player_card_", "")
            for p in cards.get("bookingPlayersA", []) + cards.get("bookingPlayersB", []):
                if p.get("name", "").lower().replace(" ", "_") == player_name.lower().replace(" ", "_"):
                    return p.get("probability", 0.0)

        return None

    goal_legs = [l for l in legs if _check_goals_leg(l, 0, 0) is not None]
    corner_legs = [l for l in legs if _check_corners_leg(l, 0, 0) is not None]
    dnb_legs = [l for l in legs if _dnb_prob(l) is not None]
    extended_legs = [l for l in legs if _extended_prob(l) is not None]

    # Combined probability for goals-based legs (Monte Carlo)
    goals_combined = 0.0
    if goal_legs:
        for (sa, sb), p in joint_probs.items():
            a = int(sa)
            b = int(sb)
            if all(_check_goals_leg(leg, a, b) for leg in goal_legs):
                goals_combined += p
    else:
        goals_combined = 1.0

    # Combined probability for corners-based legs (Monte Carlo)
    corners_combined = 1.0
    if corner_legs and sim_corners_a and sim_corners_b:
        n = len(sim_corners_a)
        hits = 0
        for i in range(n):
            if all(_check_corners_leg(leg, int(sim_corners_a[i]), int(sim_corners_b[i])) for leg in corner_legs):
                hits += 1
        corners_combined = hits / n if n > 0 else 0.0

    # Combined probability for DNB legs (direct probability)
    dnb_combined = 1.0
    for leg in dnb_legs:
        dnb_combined *= _dnb_prob(leg)

    # Combined probability for extended-market legs (direct probability)
    extended_combined = 1.0
    for leg in extended_legs:
        extended_combined *= _extended_prob(leg)

    combined_prob = goals_combined * corners_combined * dnb_combined * extended_combined
    if combined_prob < 0.0001:
        combined_prob = 0.0

    # Historical validation
    def _can_check_from_score(leg):
        if _check_goals_leg(leg, 0, 0) is not None:
            return "goals"
        if _check_corners_leg(leg, 0, 0) is not None:
            return "corners"
        if leg in ("dnb_1", "dnb_2"):
            return "goals"
        return None

    def _check_any_leg(leg, a, b):
        c = _check_goals_leg(leg, a, b)
        if c is not None:
            return c
        if leg == "dnb_1":
            return a > b
        if leg == "dnb_2":
            return b > a
        return None

    direct_h2h = []
    similar_profile = []
    h2h_data = get_h2h_stats(team_a, team_b, matches)
    if h2h_data and h2h_data.get("matches"):
        for m in h2h_data["matches"]:
            ha = int(m.get("hg", 0))
            hb = int(m.get("ag", 0))
            checked_any = False
            all_met = True
            for leg in legs:
                cat = _can_check_from_score(leg)
                if cat is None:
                    continue
                checked_any = True
                if cat == "goals":
                    if not _check_any_leg(leg, ha, hb):
                        all_met = False
                        break
            if not checked_any:
                all_met = False
            direct_h2h.append({
                "date": m.get("date", ""),
                "homeName": m.get("home", m.get("homeSlug", team_a)),
                "awayName": m.get("away", m.get("awaySlug", team_b)),
                "score": f"{ha}-{hb}",
                "fullyMet": all_met
            })
    # Find similar-profile matches (teams with close ELO to the matchup)
    elo_a = ratings.get(team_a, 1500)
    elo_b = ratings.get(team_b, 1500)
    elo_diff = abs(elo_a - elo_b)
    candidates = []
    for m in matches:
        if m.get("homeSlug") in (team_a, team_b) or m.get("awaySlug") in (team_a, team_b):
            continue
        h_elo = ratings.get(m.get("homeSlug", ""), 1500)
        a_elo = ratings.get(m.get("awaySlug", ""), 1500)
        if abs(h_elo - a_elo) - elo_diff <= 100:
            ha = int(m.get("hg", 0))
            hb = int(m.get("ag", 0))
            checked_any = False
            all_met = True
            for leg in legs:
                cat = _can_check_from_score(leg)
                if cat is None:
                    continue
                checked_any = True
                if cat == "goals":
                    if not _check_any_leg(leg, ha, hb):
                        all_met = False
                        break
            if not checked_any:
                all_met = False
            candidates.append({
                "date": m.get("date", ""),
                "homeName": m.get("home", m.get("homeSlug", "")),
                "awayName": m.get("away", m.get("awaySlug", "")),
                "score": f"{ha}-{hb}",
                "similarity": 100 - abs(abs(h_elo - a_elo) - elo_diff),
                "fullyMet": all_met
            })
    candidates.sort(key=lambda x: x["similarity"], reverse=True)
    similar_profile = candidates[:15]

    return {
        "simulation": {"combinedProb": round(combined_prob, 4)},
        "historicalMatches": {
            "directH2H": direct_h2h[:10],
            "similarProfile": similar_profile
        }
    }
