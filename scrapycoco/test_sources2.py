"""Deep test of accessible sources for per-match corner data."""
import requests, time, re

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
H = {"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"}

def test(label, url, **kwargs):
    try:
        h = {**H, **kwargs.pop("headers", {})}
        r = requests.get(url, headers=h, timeout=10, **kwargs)
        print(f"  {r.status_code:>3}  {label:40s} {len(r.text):>6} bytes")
        return r
    except Exception as e:
        print(f"  ERR  {label:40s} {e}")
        return None

# Test WhoScored with a real match - first get the main page to extract a match link
print("=== WHOSCORED - find real match ===")
r = test("WhoScored home (no redirect)", "https://www.whoscored.com/")
if r and r.status_code == 200:
    # Look for match links in the HTML
    matches = re.findall(r'/Matches/(\d+)/Live', r.text)
    print(f"  Match IDs found: {matches[:5]}")
    
    if matches:
        time.sleep(1)
        mid = matches[0]
        # Try different endpoints
        r2 = test(f"LiveStatistics/{mid}", f"https://www.whoscored.com/Matches/{mid}/LiveStatistics", headers={"Referer": "https://www.whoscored.com/"})
        time.sleep(1)
        r3 = test(f"LiveStatisticsSummary/{mid}", f"https://www.whoscored.com/Matches/{mid}/LiveStatisticsSummary", headers={"Referer": "https://www.whoscored.com/"})
        time.sleep(1)
        r4 = test(f"MatchCenter/{mid}", f"https://www.whoscored.com/Matches/{mid}/MatchCenter", headers={"Referer": "https://www.whoscored.com/"})
        
        # Their known API pattern
        time.sleep(1)
        r5 = test(f"API v1 matches/{mid}", f"https://www.whoscored.com/api/v1/Matches/{mid}", headers={"Referer": "https://www.whoscored.com/"})
        
        # Check if there's corner data in the response
        if r2 and r2.status_code == 200:
            if "corner" in r2.text.lower():
                print("  ✓ CORNER DATA FOUND in LiveStatistics")
        if r3 and r3.status_code == 200:
            if "corner" in r3.text.lower():
                print("  ✓ CORNER DATA FOUND in LiveStatisticsSummary")
        if r4 and r4.status_code == 200:
            if "corner" in r4.text.lower():
                print("  ✓ CORNER DATA FOUND in MatchCenter")

time.sleep(2)
print("\n=== SOCCERWAY - find real match ===")
r = test("Soccerway home (UTF-8)", "https://int.soccerway.com/")
if r and r.status_code == 200:
    # Look for match links  
    matches = re.findall(r'/matches/\d+/\d+/\d+/(\d+)/', r.text)
    print(f"  Match paths found: {matches[:5]}")
    
    # Try their XHR endpoint for statistics
    time.sleep(1)
    r2 = test("Soccerway XHR", "https://int.soccerway.com/a/block_match_engines_match_components?block_id=block_match_engines_match_components&callback_params={\"match_id\":1}&action=loadMatchComponents", 
              headers={"X-Requested-With": "XMLHttpRequest"})

time.sleep(2)
print("\n=== API-FOOTBALL ===")
# First try with a valid demo key - let me see if this is the free tier
# Actually, let's try to get a sense of pricing by checking the response
r = test("API-Football status", "https://v3.football.api-sports.io/status", headers={"x-apisports-key": "test"})
if r:
    print(f"  Response: {r.text[:300]}")
    
# Try with a more realistic call - fixtures with statistics
time.sleep(1)
r2 = test("API-Football fixtures", "https://v3.football.api-sports.io/fixtures?league=1&season=2024", headers={"x-apisports-key": "test"})
if r2:
    print(f"  Response: {r2.text[:300]}")

time.sleep(2)
print("\n=== FLASHSCORE API (mobile version) ===")
flash_headers = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 13) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
    "Accept": "application/json",
    "X-Fsign": "SW9D1eZo",
}
test("FlashScore mobile", "https://www.flashscore.com/match/", headers=flash_headers)

time.sleep(1)
test("FlashScore X", "https://d.flashscore.com/x/request/?", headers={**flash_headers, "Origin": "https://www.flashscore.com"})

# Try their known proxy endpoints
time.sleep(1)
for path in ["/x/feed/", "/x/ajax/", "/x/request/"]:
    test(f"FlashScore{path}", f"https://www.flashscore.com{path}", headers=flash_headers)
    time.sleep(1)

time.sleep(2)
print("\n=== FOOTYBOT (AI-powered, uses multiple sources) ===")
test("FootyBot", "https://www.footybot.com/", headers=H)

time.sleep(1)
print("\n=== SOCCER365 (another alternative) ===")
test("Soccer365", "https://www.soccer365.com/", headers=H)