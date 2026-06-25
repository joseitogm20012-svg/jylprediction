"""
Verificar si FBref tiene páginas de estadísticas para eliminatorias
a través de scraping HTML directo (sin soccerdata).
Buscamos las URLs de las eliminatorias más recientes para los 9 equipos.
"""
import sys, io, requests
from bs4 import BeautifulSoup

if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9"
}

# Test URLs de clasificatorias en FBref
test_urls = [
    # CONMEBOL WCQ 2026
    ("CONMEBOL WCQ 2026 shooting", "https://fbref.com/en/comps/685/2026/shooting/2026-CONMEBOL-World-Cup-Qualifying-Stats"),
    # UEFA WCQ 2026
    ("UEFA WCQ 2026 shooting", "https://fbref.com/en/comps/684/2026/shooting/2026-UEFA-World-Cup-Qualifying-Stats"),
    # CONCACAF WCQ 2026
    ("CONCACAF WCQ 2026 shooting", "https://fbref.com/en/comps/686/2026/shooting/2026-CONCACAF-World-Cup-Qualifying-Stats"),
    # CAF WCQ 2026
    ("CAF WCQ 2026 shooting", "https://fbref.com/en/comps/687/2026/shooting/2026-CAF-World-Cup-Qualifying-Stats"),
    # AFC WCQ 2026
    ("AFC WCQ 2026 shooting", "https://fbref.com/en/comps/688/2026/shooting/2026-AFC-World-Cup-Qualifying-Stats"),
]

for label, url in test_urls:
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        print(f"{label}: {r.status_code} ({len(r.text)} chars)")
        if r.status_code == 200:
            soup = BeautifulSoup(r.text, 'html.parser')
            tables = soup.find_all('table', id=lambda x: x and 'shooting' in x)
            print(f"  Tablas shooting encontradas: {[t.get('id') for t in tables]}")
    except Exception as e:
        print(f"{label}: ERROR - {e}")
    
    import time
    time.sleep(2)  # polite delay
