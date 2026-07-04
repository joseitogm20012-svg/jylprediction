"""Test a real Soccerway match page for corner statistics."""
import requests, time
from bs4 import BeautifulSoup

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

# Test match page
url = "https://int.soccerway.com/match/argentina-f9OppQjp/cape-verde-MocyWdm7/"
print(f"Fetching: {url}")
r = requests.get(url, headers={"User-Agent": UA}, timeout=15)
print(f"Status: {r.status_code}, Size: {len(r.text)}")

soup = BeautifulSoup(r.text, "html.parser")

# 1. Search for corner in any table row
print("\n--- Searching for corner row ---")
found = False
for table in soup.find_all("table"):
    for row in table.find_all("tr"):
        cells = [c.get_text(strip=True) for c in row.find_all(["th", "td"])]
        if cells and "corner" in cells[0].lower():
            print(f"  FOUND in table: {cells}")
            found = True
            break
    if found:
        break
if not found:
    print("  No corner row found in any table")

# 2. Check broader: any element with "corner" text
print("\n--- Broader 'corner' search ---")
count = 0
for tag in soup.find_all(["div", "tr", "td", "th", "span", "p"]):
    text = tag.get_text().lower()
    if "corner" in text:
        count += 1
        if count <= 5:
            print(f"  Tag={tag.name} class={tag.get('class')} text={text[:100]}")
print(f"  Total elements with 'corner': {count}")

# 3. Check for statistics-related content
print("\n--- Statistics-related elements ---")
for tag in soup.find_all(["div", "section"]):
    text = tag.get_text().lower()
    if "statistic" in text:
        print(f"  Tag={tag.name} class={tag.get('class')} text={text[:150]}")
        break

# 4. Check for "shots", "possession" which are common stat table headers
print("\n--- Common stat table headers ---")
for kw in ["possession", "shots", "fouls", "yellow", "red"]:
    found_any = False
    for row in soup.find_all("tr"):
        cells = [c.get_text(strip=True).lower() for c in row.find_all(["th", "td"])]
        if cells and kw in cells[0]:
            print(f"  Found '{kw}' row: {cells[:4]}")
            found_any = True
            break
    if not found_any:
        print(f"  '{kw}': NOT FOUND")

print("\n=== DONE ===")