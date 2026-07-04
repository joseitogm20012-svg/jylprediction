"""Test accessible sources for per-match corner data."""
import requests, json, time

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
H = {"User-Agent": UA, "Accept": "application/json"}

def test(label, url, headers=None, parse=None):
    try:
        h = {**H, **(headers or {})}
        r = requests.get(url, headers=h, timeout=10)
        status = r.status_code
        print(f"{status:>4}  {label:<30} {len(r.text):>6} bytes")
        if status == 200 and parse:
            result = parse(r)
            if result:
                print(f"       → {result}")
        return r
    except Exception as e:
        print(f"  ERR  {label:<30} {e}")
        return None

time.sleep(1)
print("\n=== WHOSCORED ===")
# Whoscored team page
r = test("WhoScored home", "https://www.whoscored.com/", {"User-Agent": UA})
time.sleep(1)
# Their match page for a known match
r = test("WhoScored match", "https://www.whoscored.com/Matches/1234567/LiveStatistics", {"User-Agent": UA})
time.sleep(1)
# Their API for match center
r = test("WhoScored API match", "https://www.whoscored.com/Matches/1234567/LiveStatisticsSummary", {"User-Agent": UA, "Referer": "https://www.whoscored.com/"})

time.sleep(2)
print("\n=== 365SCORES ===")
# 365Scores API
r = test("365scores API", "https://api.365scores.com/odata/v1/Leagues?$top=1", {"User-Agent": UA})
time.sleep(1)
# Search teams
r = test("365scores search", "https://api.365scores.com/odata/v1/Teams?$filter=contains(Name,'Argentina')&$top=1", {"User-Agent": UA})
time.sleep(1)
# Try their web API for match stats
r = test("365scores web", "https://www.365scores.com/football/team/argentina/114/statistics", {"User-Agent": UA})

time.sleep(2)
print("\n=== SOCCERWAY ===")
# Soccerway  
r = test("Soccerway home", "https://int.soccerway.com/", {"User-Agent": UA})
time.sleep(1)
# Soccerway API - they have a known JSON endpoint
r = test("Soccerway scores", "https://int.soccerway.com/a/block_homepage_scores?block_id=block_homepage_scores&callback_params=&action=loadScores", {"User-Agent": UA, "X-Requested-With": "XMLHttpRequest"})

time.sleep(2)
print("\n=== FOOTSTATS ===")
r = test("Footystats", "https://api.footystats.org/leagues?key=demo", {"User-Agent": UA})

time.sleep(2)
print("\n=== API-FOOTBALL (check if any free tier exists) ===")
# Try the free tier
r = test("API-Football v3", "https://v3.football.api-sports.io/status", {"x-apisports-key": "demo"})