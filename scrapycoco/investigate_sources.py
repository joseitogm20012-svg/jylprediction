"""Thorough investigation of per-match corner data sources."""
import requests, time, re, json
from bs4 import BeautifulSoup

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
H = {"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"}

def test(label, url, parse_func=None, headers=None, timeout=12, **kwargs):
    try:
        h = {**H, **(headers or {})}
        r = requests.get(url, headers=h, timeout=timeout, **kwargs)
        size = len(r.text)
        
        has_corner = False
        if r.status_code == 200 and "corner" in r.text.lower():
            has_corner = True
        
        print(f"  {r.status_code:>3}  {label:45s} {size:>7}b {'[CORNERS]' if has_corner else ''}")
        
        if parse_func and r.status_code == 200:
            result = parse_func(r)
            if result:
                print(f"       -> {result}")
        
        return r
    except Exception as e:
        print(f"  ERR  {label:45s} {str(e)[:80]}")
        return None


# ============= A. WHOSCORED =============
print("\n" + "=" * 60)
print("A. WHOSCORED")
print("=" * 60)

# Try to get a match page with proper WHOscored format
r = test("WhoScored live scores", "https://www.whoscored.com/LiveScores", timeout=15)
if r and r.status_code == 200:
    # Extract actual match URLs from the HTML
    match_links = re.findall(r'{"matchId":(\d+)', r.text)
    print(f"  JSON match IDs found: {match_links[:5]}")
    
    if match_links:
        mid = match_links[0]
        time.sleep(1)
        # Try match center API (they return JSON)
        r2 = test(f"API /Matches/{mid}", f"https://www.whoscored.com/Matches/{mid}/MatchCenter", 
                 headers={"Referer": "https://www.whoscored.com/", "X-Requested-With": "XMLHttpRequest"})
        
        if r2 and r2.status_code == 200:
            data = r2.json()
            if "corner" in str(data).lower():
                # Find corner keys in the JSON
                def find_corners(d, path=""):
                    if isinstance(d, dict):
                        for k, v in d.items():
                            if "corner" in k.lower():
                                print(f"       CORNER FIELD: {path}.{k} = {v}")
                            find_corners(v, f"{path}.{k}")
                    elif isinstance(d, list):
                        for i, v in enumerate(d):
                            find_corners(v, f"{path}[{i}]")
                find_corners(data)

time.sleep(1)

# Try their scheduled/live events
r = test("WhoScored WC matches", "https://www.whoscored.com/Regions/155/Tournaments/2/Seasons/10123/Stages/12274/Fixtures", timeout=15)

time.sleep(2)
# ============= B. SOCCERWAY =============
print("\n" + "=" * 60)
print("B. SOCCERWAY")
print("=" * 60)

# Try the WC competition page
r = test("Soccerway WC 2026", "https://int.soccerway.com/international/world/world-cup/2026-wc-qualifying-concacaf/r12345/")
time.sleep(1)

# Try their match page with statistics
r2 = test("Soccerway match stats", "https://int.soccerway.com/matches/2026/06/11/world/world-cup/mexico/south-africa/1234567/")
time.sleep(1)

# Try their JSON endpoints  
r3 = test("Soccerway JSON feeds", "https://int.soccerway.com/a/block_homepage_matches?block_id=block_homepage_matches&callback_params=&action=loadMatches")

time.sleep(2)
# ============= C. API-FOOTBALL =============
print("\n" + "=" * 60)
print("C. API-FOOTBALL (https://www.api-football.com)")
print("=" * 60)

# Their fixtures endpoint returns match stats. With a proper key, it returns corner data.
# Let's test the general API health
r = test("API-Football status", "https://v3.football.api-sports.io/status", 
         headers={"x-apisports-key": "test"})

# The response shows what data structure is available
if r and r.status_code == 200:
    resp = r.json()
    errors = resp.get("errors", {})
    if "token" in errors:
        print("       -> Requires free API key (signup at api-football.com)")
        print("       -> Free tier: 100 requests/day")
        print("       -> Includes: corners, shots, crosses, cards per fixture")

time.sleep(2)
# ============= D. GOAL.COM =============
print("\n" + "=" * 60)
print("D. GOAL.COM")
print("=" * 60)

r = test("Goal.com", "https://www.goal.com/en-us", timeout=15)

time.sleep(2)
# ============= E. ONEFOOTBALL =============
print("\n" + "=" * 60)
print("E. ONEFOOTBALL")
print("=" * 60)

r = test("OneFootball", "https://onefootball.com/en/home", timeout=15)

time.sleep(2)
# ============= F. FLASHSCORE MATCH PAGE =============
print("\n" + "=" * 60)
print("F. FLASHSCORE match detail")
print("=" * 60)

# Their match pages embed stats
r = test("FlashScore football", "https://www.flashscore.com/football/", timeout=15)
if r and r.status_code == 200:
    # Find any inline data with corner stats
    import re
    scripts = re.findall(r'window\.__data\s*=\s*({.+?});', r.text, re.DOTALL)
    if scripts:
        try:
            data = json.loads(scripts[0])
            print(f"       Inline data: keys={list(data.keys())[:10]}")
            if "corner" in str(data).lower():
                print("       ✓ CORNERS in inline data!")
                
                # Find corner data structure
                def find_corners_in_data(d, path="", depth=0):
                    if depth > 5: return
                    if isinstance(d, dict):
                        for k, v in d.items():
                            if "corner" in k.lower():
                                print(f"       KEY: {path}.{k}")
                                if isinstance(v, (int, float)):
                                    print(f"       VAL: {v}")
                            find_corners_in_data(v, f"{path}.{k}", depth+1)
                    elif isinstance(d, list):
                        for i, v in enumerate(d):
                            find_corners_in_data(v, f"{path}[{i}]", depth+1)
                find_corners_in_data(data)
        except:
            pass

# Try match detail page with statistics tab
time.sleep(1)
r2 = test("FlashScore match stats", "https://www.flashscore.com/match/4UXzDy1d/#/match-summary/match-statistics/0", timeout=15)
if r2 and r2.status_code == 200:
    print(f"       Page size: {len(r2.text)}")
    if "corner" in r2.text.lower():
        print("       ✓ CORNERS in page HTML!")

time.sleep(2)
# ============= G. FOOTYSTATS =============
print("\n" + "=" * 60)
print("G. FOOTYSTATS")
print("=" * 60)

# Try with demo key 
r = test("Footystats fixtures", "https://api.footystats.org/fixtures?key=sample", timeout=10)
if r and r.status_code != 401:
    print(f"       Response: {r.text[:300]}")

time.sleep(1)
# ============= H. WIKIPEDIA =============
print("\n" + "=" * 60)
print("H. WIKIPEDIA WC match pages")
print("=" * 60)

# Wikipedia has match detail pages
r = test("Wikipedia WC2026 group A", "https://en.wikipedia.org/wiki/2026_FIFA_World_Cup_Group_A", timeout=15)
if r and r.status_code == 200:
    # Wikipedia uses specific tags for match stats  
    # Check for 'Corner kicks' in the HTML
    c = r.text.lower().count("corner kick")
    print(f"       'corner kick' mentions: {c}")
    if c > 0:
        print("       ✓ CORNER DATA AVAILABLE in Wikipedia!")
        # Find the match result tables
        soup = BeautifulSoup(r.text, "html.parser")
        tables = soup.find_all("table", class_="wikitable")
        for t in tables:
            if "corner" in t.get_text().lower():
                rows = t.find_all("tr")
                print(f"       Corner table: {len(rows)} rows")
                for row in rows[:3]:
                    cells = [c.get_text(strip=True)[:40] for c in row.find_all(["th","td"])]
                    print(f"       {cells}")

time.sleep(2)
# ============= I. RSSSF =============
print("\n" + "=" * 60)
print("I. RSSSF")
print("=" * 60)

r = test("RSSSF WC2026", "https://www.rsssf.org/tables/2026f.html", timeout=15)
if r and r.status_code == 200:
    c = r.text.lower().count("corner")
    print(f"       'corner' mentions: {c}")

time.sleep(1)
# ============= J. TRANSFERMARKT =============
print("\n" + "=" * 60)
print("J. TRANSFERMARKT match pages")
print("=" * 60)

# Can access with Playwright (proven for squad data)
# Their match report pages might have stats
r = test("TM WC2026 matches", "https://www.transfermarkt.com/world-cup-2026/gesamtspielplan/pokalwettbewerb/WM26", timeout=15)
if r and r.status_code == 200:
    c = r.text.lower().count("corner")
    print(f"       'corner' mentions: {c}")

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)