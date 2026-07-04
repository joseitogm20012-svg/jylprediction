"""Find correct national team IDs - national teams have different IDs than clubs"""
import requests, time, json, re

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
}

# Known: Argentina ID = 3437 (from TM website squad page)
# Let me check a wider range for national teams
# National teams might be in range 3400-3600 or similar

common = ["argentina", "france", "germany", "england", "spain", "italy", "netherlands", "portugal", "belgium", "croatia"]

# Check slugs that work - does "argentina" work with ID 3437?
for slug in ["argentina"]:
    url = "https://www.transfermarkt.com/%s/startseite/verein/3437" % slug
    r = requests.get(url, headers=HEADERS, timeout=10)
    title = ""
    m = re.search(r'<title>(.*?)</title>', r.text)
    if m: title = m.group(1)
    print("%s/3437: %s" % (slug, title[:80]))

# Check Brazil
for slug in ["brasilien", "brazil"]:
    url = "https://www.transfermarkt.com/%s/startseite/verein/3439" % slug
    r = requests.get(url, headers=HEADERS, timeout=10)
    title = ""
    m = re.search(r'<title>(.*?)</title>', r.text)
    if m: title = m.group(1)
    print("%s/3439: %s" % (slug, title[:80]))

# Try finding France
print("\n--- Searching France ---")
for sid in range(3435, 3500):
    url = "https://www.transfermarkt.com/france/startseite/verein/%d" % sid
    r = requests.get(url, headers=HEADERS, timeout=5)
    title = ""
    m = re.search(r'<title>(.*?)</title>', r.text)
    if m: title = m.group(1)
    if "france" in title.lower() and "club" not in title.lower() and "error" not in title.lower():
        print("France ID: %d -> %s" % (sid, title[:80]))
        break
    if sid % 10 == 0:
        print("  checked %d..." % sid)
    time.sleep(0.1)
