#!/usr/bin/env python3
import os
import json
import math
import csv
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SEED = {
  "argentina":2085,"france":2065,"spain":2055,"brazil":2045,"england":2000,"portugal":1980,"netherlands":1965,"germany":1945,"belgium":1925,"italy":1915,"colombia":1890,"uruguay":1875,"croatia":1870,"morocco":1840,"switzerland":1825,"usa":1830,"mexico":1825,"japan":1810,"senegal":1795,"denmark":1790,"ecuador":1760,"australia":1735,"south-korea":1730,"iran":1720,"poland":1715,"canada":1700,"serbia":1695,"wales":1665,"ghana":1665,"tunisia":1655,"ivory-coast":1655,"nigeria":1645,"saudi-arabia":1640,"qatar":1630,"egypt":1620,"algeria":1615,"scotland":1610,"cameroon":1600,"paraguay":1595,"venezuela":1590,"chile":1580,"peru":1575,"czech-republic":1570,"bosnia-and-herzegovina":1545,"south-africa":1520,"new-zealand":1495,"panama":1480,"jamaica":1460,"honduras":1440,"jordan":1420,"haiti":1380,"el-salvador":1370,"trinidad-and-tobago":1360,"guatemala":1345
}

HOME_ADV = 75
BURN_IN = 150
DC_RHO = -0.13
VIG_MARGIN = 1.05
MIN_EDGE = 0.05
BET_SIZE = 1.0

def get_k(league):
    league = league.lower()
    if "world cup" in league and "qual" not in league:
        return 55
    if "world cup" in league or "qual" in league or "qualification" in league:
        return 40
    if any(x in league for x in ["copa america", "euro championship", "asian cup", "africa cup", "gold cup"]):
        return 50
    if "nations league" in league or "nations cup" in league:
        return 32
    if "friendl" in league:
        return 18
    return 28

def dc_tau(a, b, lambda_val, mu, rho):
    if a == 0 and b == 0:
        return 1.0 - lambda_val * mu * rho
    if a == 0 and b == 1:
        return 1.0 + lambda_val * rho
    if a == 1 and b == 0:
        return 1.0 + mu * rho
    if a == 1 and b == 1:
        return 1.0 - rho
    return 1.0

def expected_score(rating_a, rating_b, home_bonus_a=0):
    return 1.0 / (1.0 + 10.0 ** ((rating_b - (rating_a + home_bonus_a)) / 400.0))

def expected_goals(rating, opponent, home_bonus=0):
    diff = (rating + home_bonus) - opponent
    val = 1.35 + diff / 400.0
    return max(0.3, min(3.5, val))

def poisson_pmf(k, lambda_val):
    if lambda_val <= 0:
        return 1.0 if k == 0 else 0.0
    return (lambda_val ** k) * math.exp(-lambda_val) / math.factorial(k)

def match_prob(rating_a, rating_b, home_bonus_a=0):
    lambda_val = expected_goals(rating_a, rating_b, home_bonus_a)
    mu = expected_goals(rating_b, rating_a, -home_bonus_a / 2.0)
    win_a = 0.0
    draw = 0.0
    win_b = 0.0
    
    for a in range(9):
        p_a = poisson_pmf(a, lambda_val)
        for b in range(9):
            tau = dc_tau(a, b, lambda_val, mu, DC_RHO)
            p = p_a * poisson_pmf(b, mu) * tau
            if a > b:
                win_a += p
            elif a < b:
                win_b += p
            else:
                draw += p
                
    total = win_a + draw + win_b
    if total <= 0:
        return {"winA": 0.33, "draw": 0.33, "winB": 0.33}
    return {
        "winA": win_a / total,
        "draw": draw / total,
        "winB": win_b / total
    }

def run_backtest():
    csv_path = os.path.join(BASE_DIR, "data", "results.csv")
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found.")
        return False

    matches = []
    with open(csv_path, mode='r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader)
        for row in reader:
            if len(row) < 6:
                continue
            date, home_name, away_name, hg_str, ag_str, league_name = row[0], row[1], row[2], row[3], row[4], row[5]
            if not home_name or not away_name:
                continue
            try:
                hg = int(hg_str) if hg_str != 'NA' and hg_str != '' else None
                ag = int(ag_str) if ag_str != 'NA' and ag_str != '' else None
            except ValueError:
                hg, ag = None, None
                
            home_slug = home_name.lower().replace(" ", "-").replace("'", "").replace(".", "")
            away_slug = away_name.lower().replace(" ", "-").replace("'", "").replace(".", "")
            matches.append({
                "date": date,
                "homeName": home_name,
                "awayName": away_name,
                "hg": hg,
                "ag": ag,
                "leagueName": league_name,
                "homeSlug": home_slug,
                "awaySlug": away_slug
            })

    ratings = {}
    naive_ratings = {}

    def get_rating(d, slug, name):
        k = slug if slug else f"ghost:{name}"
        if k not in d:
            d[k] = SEED.get(slug, 1500) if slug in SEED else 1500
        return d[k]

    def set_rating(d, slug, name, val):
        k = slug if slug else f"ghost:{name}"
        d[k] = val

    n = 0
    hit = 0
    brier = 0
    logloss = 0
    fav_n = 0
    fav_hit = 0
    base_home = 0
    base_elo = 0
    i = 0
    
    e_h = 0
    e_d = 0
    e_a = 0
    
    bankroll = 0.0
    bets_placed = 0
    bets_won = 0
    
    calib = [{"sumP": 0.0, "sumY": 0.0, "n": 0} for _ in range(10)]
    
    for m in matches:
        if m["hg"] is None or m["ag"] is None:
            continue
            
        ra = get_rating(ratings, m["homeSlug"], m["homeName"])
        rb = get_rating(ratings, m["awaySlug"], m["awayName"])
        
        naive_ra = get_rating(naive_ratings, m["homeSlug"], m["homeName"])
        naive_rb = get_rating(naive_ratings, m["awaySlug"], m["awayName"])
        
        if i >= BURN_IN:
            p = match_prob(ra, rb, HOME_ADV)
            probs = [p["winA"], p["draw"], p["winB"]]
            actual = 0 if m["hg"] > m["ag"] else (2 if m["hg"] < m["ag"] else 1)
            y = [1.0 if actual == 0 else 0.0, 1.0 if actual == 1 else 0.0, 1.0 if actual == 2 else 0.0]
            pred = probs.index(max(probs))
            
            n += 1
            if pred == actual:
                hit += 1
            brier += (probs[0]-y[0])**2 + (probs[1]-y[1])**2 + (probs[2]-y[2])**2
            logloss += -math.log(max(1e-12, probs[actual]))
            
            for k in range(3):
                b = min(9, math.floor(probs[k] * 10))
                calib[b]["sumP"] += probs[k]
                calib[b]["sumY"] += y[k]
                calib[b]["n"] += 1
                
            if max(probs) >= 0.5:
                fav_n += 1
                if pred == actual:
                    fav_hit += 1
            if actual == 0:
                base_home += 1
            
            # Baselines
            elo_pred = 0 if expected_score(ra, rb, HOME_ADV) >= 0.5 else 2
            if elo_pred == actual:
                base_elo += 1
                
            if actual == 0:
                e_h += 1
            elif actual == 1:
                e_d += 1
            else:
                e_a += 1
                
            # Financial simulation
            naive_p = match_prob(naive_ra, naive_rb, HOME_ADV)
            bookie_probs = [naive_p["winA"], naive_p["draw"], naive_p["winB"]]
            
            # Simple Kelly or Flat Bet
            for k in range(3):
                p_bookie = bookie_probs[k]
                odds = 1.0 / (p_bookie * VIG_MARGIN) if p_bookie > 0 else 999.0
                edge = probs[k] - (1.0 / odds)
                if edge >= MIN_EDGE:
                    bets_placed += 1
                    if actual == k:
                        bankroll += (odds - 1.0) * BET_SIZE
                        bets_won += 1
                    else:
                        bankroll -= BET_SIZE
                        
        # ELO Updates
        # Actual outcome
        sa = 1.0 if m["hg"] > m["ag"] else (0.5 if m["hg"] == m["ag"] else 0.0)
        sb = 1.0 - sa
        
        ea = expected_score(ra, rb, HOME_ADV)
        eb = expected_score(rb, ra, -HOME_ADV)
        
        k_val = get_k(m["leagueName"])
        g_diff = m["hg"] - m["ag"]
        g_mult_val = 1.0 if abs(g_diff) <= 1 else (1.5 if abs(g_diff) == 2 else (11.0 + abs(g_diff)) / 8.0)
        
        new_ra = ra + k_val * g_mult_val * (sa - ea)
        new_rb = rb + k_val * g_mult_val * (sb - eb)
        
        set_rating(ratings, m["homeSlug"], m["homeName"], new_ra)
        set_rating(ratings, m["awaySlug"], m["awayName"], new_rb)
        
        # Naive updates
        naive_ea = expected_score(naive_ra, naive_rb, HOME_ADV)
        naive_eb = expected_score(naive_rb, naive_ra, -HOME_ADV)
        new_naive_ra = naive_ra + k_val * g_mult_val * (sa - naive_ea)
        new_naive_rb = naive_rb + k_val * g_mult_val * (sb - naive_eb)
        set_rating(naive_ratings, m["homeSlug"], m["homeName"], new_naive_ra)
        set_rating(naive_ratings, m["awaySlug"], m["awayName"], new_naive_rb)
        
        i += 1

    if n == 0:
        return False
        
    ece = sum(abs(b["sumP"] / b["n"] - b["sumY"] / b["n"]) * b["n"] if b["n"] > 0 else 0 for b in calib) / (3.0 * n)
    
    output_path = os.path.join(BASE_DIR, "data", "model-backtest.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "generatedAt": datetime.utcnow().isoformat() + "Z",
            "method": "Walk-forward out-of-sample with Simulated Financial ROI in Python.",
            "totalMatches": len(matches),
            "evaluated": n,
            "burnIn": BURN_IN,
            "outcomeSplit": {
                "home": round(e_h / n, 4),
                "draw": round(e_d / n, 4),
                "away": round(e_a / n, 4)
            },
            "model": {
                "accuracy": round(hit / n, 4),
                "favouriteAccuracy": round(fav_hit / fav_n, 4) if fav_n > 0 else 0.0,
                "brier": round(brier / n, 4),
                "logloss": round(logloss / n, 4),
                "ece": round(ece, 4)
            },
            "financials": {
                "margin": VIG_MARGIN,
                "minEdge": MIN_EDGE,
                "betsPlaced": bets_placed,
                "betsWon": bets_won,
                "profitUnits": round(bankroll, 2),
                "roiPercent": round((bankroll / bets_placed) * 100, 2) if bets_placed > 0 else 0.0
            }
        }, f, indent=2)
    return True

if __name__ == "__main__":
    success = run_backtest()
    if success:
        print("Backtest completed successfully.")
    else:
        print("Backtest failed.")
