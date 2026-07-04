"""Test individual match pages on Soccerway and FlashScore."""
import requests, time

UA = "Mozilla/5.0"
H = {"User-Agent": UA}

r = requests.get("https://int.soccerway.com/", headers=H, timeout=10)
html = r.text

# Find match URLs manually  
imports = html.split('href="')
match_urls = set()
for part in imports:
    if '"/' in part:
        url = part.split('"')[0]
        if '/matches/2026/' in url:
            match_urls.add("https://int.soccerway.com" + url)

print(f"2026 match URLs: {len(match_urls)}")
for url in sorted(match_urls)[:5]:
    print(f"  {url}")

# If found, test one
if match_urls:
    url = sorted(match_urls)[0]
    time.sleep(1)
    r2 = requests.get(url, headers=H, timeout=10)
    print(f"\nMatch page: {r2.status_code} {len(r2.text)} bytes")
    
    # Check for corner data
    txt = r2.text.lower()
    corner_count = txt.count("corner")
    print(f"  'corner' count: {corner_count}")
    
    if corner_count > 0:
        # Find context
        idx = txt.find("corner")
        print(f"  First occurrence context: {r2.text[idx:idx+300]}")
    
    # Also check for statistics table  
    stat_count = txt.count("statistics")
    print(f"  'statistics' count: {stat_count}")

# Also try FlashScore with Chrome mobile headers
print("\n=== FlashScore mobile ===")
time.sleep(2)
flash_h = {
    "User-Agent": "Mozilla/5.0 (Linux; Android 13; Pixel 6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.6478.122 Mobile Safari/537.36",
    "Accept": "text/html,application/xhtml+xml",
    "Accept-Language": "en-US,en;q=0.9",
}

# FlashScore match page with a known WC2026 match  
r3 = requests.get("https://www.flashscore.com/match/4UXzDy1d/", headers=flash_h, timeout=15, allow_redirects=True)
print(f"FlashScore match: {r3.status_code} {len(r3.text)} bytes")

txt3 = r3.text.lower()
print(f"  'corner' count: {txt3.count('corner')}")
print(f"  'statistics' count: {txt3.count('statistics')}")
print(f"  'window.jsData' in page: {'window.jsdata' in txt3 or 'window.__data' in txt3}")
print(f"  'window.__NEXT_DATA__' in page: {'__NEXT_DATA__' in txt3}")

# Check if corner data is inline
if "corner" in txt3:
    idx = txt3.find("corner")
    print(f"  Corner context: {r3.text[idx:idx+400]}")

# Check if there are any score patterns
if "score" in txt3:
    print(f"  Score in page: YES")

# Try to find any embedded JSON with match data
scores = []
for pattern in [r'"homeScore":(\d+)', r'"awayScore":(\d+)']:
    import re
    matches = re.findall(pattern, r3.text)
    if matches:
        scores.extend(matches)
print(f"  Score data in JSON: {scores}")