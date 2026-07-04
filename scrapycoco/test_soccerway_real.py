"""Quick test: explore real Soccerway HTML structure."""
import requests, re
from bs4 import BeautifulSoup

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

r = requests.get("https://int.soccerway.com/matches/2026/",
                 headers={"User-Agent": UA}, timeout=15)
html = r.text
print(f"Status: {r.status_code}, Size: {len(r.text)}")

# Find match-related content
print("\n--- Pattern search ---")
for p in ["/match/", "fixture", "/matches/"]:
    count = len(re.findall(p, html, re.IGNORECASE))
    print(f"  '{p}': {count} occurrences")

# Check if there's inline JSON with match data
print("\n--- JSON data blocks ---")
json_patterns = [
    r'window\.footballmenudata\s*=\s*({.+?});',
    r'data-block__matches__list"\s*:\s*(\[.+?\])',
]
for pat in json_patterns:
    matches = re.findall(pat, html, re.DOTALL)
    if matches:
        print(f"  Pattern found: {pat[:50]}... ({len(matches)} matches)")
        for m in matches[:2]:
            print(f"    {m[:200]}")

# Search for anchor tags more manually
soup = BeautifulSoup(html, "html.parser")
print(f"\n--- All <a> tags with href ---")
match_as = []
for a in soup.find_all("a", href=True):
    href = a.get("href", "")
    if "match" in href.lower():
        match_as.append(href)
print(f"  Total <a> tags: {len(soup.find_all('a', href=True))}")
print(f"  Match-related <a> tags: {len(match_as)}")
for href in match_as[:10]:
    print(f"    {href}")

# Also check li/div with match links
print("\n--- Other elements with match URLs ---")
for tag in soup.find_all(["div", "li", "span"]):
    text = tag.get_text().lower()
    if "match" in text and "corner" in text:
        print(f"  Tag {tag.name} with 'match' and 'corner': {text[:100]}")

# The real page might load matches via JS. Check script tags.
print("\n--- Script tags with match data ---")
for script in soup.find_all("script"):
    content = script.text if script.text else ""
    if "match" in content.lower() and len(content) < 2000:
        print(f"  Script ({len(content)} chars): {content[:300]}")
        break