"""Extract corner data from the promising sources."""
import requests, time, re, json
from bs4 import BeautifulSoup

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
H = {"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"}

def fetch(url, **kw):
    try:
        r = requests.get(url, headers=H, timeout=15, **kw)
        if r.status_code == 200:
            return r.text
    except:
        pass
    return None

# ============ SOCCERWAY ============
print("=" * 60)
print("SOCCERWAY - extract corner data from WC page")
print("=" * 60)

# Get a WC match page with statistics
html = fetch("https://int.soccerway.com/international/world/world-cup/2026-wc-qualifying-concacaf/r12345/")
if not html:
    html = fetch("https://int.soccerway.com/")

if html:
    # Check what corner data looks like
    # Soccerway has statistics tables on match pages
    lines_with_corner = [l.strip()[:200] for l in html.lower().split('\n') if 'corner' in l.lower() and l.strip()]
    print(f"Lines with 'corner': {len(lines_with_corner)}")
    for l in lines_with_corner[:10]:
        print(f"  {l.strip()[:180]}")

    # Look for actual data in tables  
    soup = BeautifulSoup(html, "html.parser")
    
    # Find match links  
    match_links = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/matches/" in href:
            match_links.append(href)
    print(f"\nMatch links found: {len(match_links)}")
    for ml in match_links[:5]:
        print(f"  {ml}")

    # Find statistics tables  
    tables = soup.find_all("table")
    print(f"Tables total: {len(tables)}")
    # Find tables with statistics headers
    for t in tables:
        text = t.get_text().lower()
        if "corner" in text:
            rows = t.find_all("tr")
            print(f"\nCorner table: {len(rows)} rows")
            for row in rows[:5]:
                cells = [c.get_text(strip=True)[:50] for c in row.find_all(["td","th"])]
                print(f"  {cells}")

time.sleep(3)
# ============ FLASHSCORE ============
print("\n" + "=" * 60)
print("FLASHSCORE - extract corner data from football page")
print("=" * 60)

html = fetch("https://www.flashscore.com/football/")
if html:
    # Look for the inline data  
    patterns = [
        r"window\.__data\s*=\s*(\{.+?\});",
        r"window\.environment\s*=\s*(\{.+?\});",
        r"__NEXT_DATA__\s*=\s*(\{.+?\})",
    ]
    for pat in patterns:
        matches = re.findall(pat, html, re.DOTALL)
        if matches:
            try:
                data = json.loads(matches[0])
                print(f"Found inline data: {list(data.keys())[:15]}")
            except:
                pass

    # Look for corner in script/data sections
    soup = BeautifulSoup(html, "html.parser")
    scripts = soup.find_all("script")
    for script in scripts:
        content = script.text if script.text else script.get_text() if hasattr(script, 'get_text') else ""
        if content and "corner" in content.lower():
            print(f"Script with corner: {len(content)} chars, first 200:")
            print(f"  {content[:200]}")

    # Just look for corner references in HTML  
    corn_idx = html.lower().find("corner")
    if corn_idx > 0:
        # Print context around each corner mention
        window = 200
        for i in range(3):
            idx = html.lower().find("corner", corn_idx if i == 0 else (corn_idx + 6))
            if idx >= 0:
                ctx = html[idx:idx + window]
                print(f"\nCorner context #{i} at idx {idx}:")
                print(f"  {ctx.replace(chr(10), ' ')[:180]}")

time.sleep(3)
# ============ GOAL.COM ============
print("\n" + "=" * 60)
print("GOAL.COM")
print("=" * 60)

html = fetch("https://www.goal.com/en-us")
if html:
    lines_with_corner = [l.strip()[:200] for l in html.lower().split('\n') if 'corner' in l.lower() and l.strip()]
    print(f"Lines with 'corner': {len(lines_with_corner)}")
    for l in lines_with_corner[:8]:
        print(f"  {l.strip()[:180]}")