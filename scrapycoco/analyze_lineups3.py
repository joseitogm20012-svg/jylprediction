"""Analyze substitutes structure in detail"""
from bs4 import BeautifulSoup

with open('C:/Users/Equipo/Desktop/mundial104/debug_lineups2.html', encoding='utf-8') as f:
    soup = BeautifulSoup(f.read(), 'html.parser')

lineups_container = soup.select_one("div[class*='tabContent__lineups']")

# Find substitutes sections
for div in lineups_container.find_all('div', class_=lambda c: c and 'lf__sidesBox' in c):
    print('lf__sidesBox section:')
    names = div.select('*[class*="lineupsParticipantName"],*[class*="participantName"],*[class*="wcl-name"]')
    for n in names:
        print(f'  Player: {n.get_text().strip()}')
    print(f'  Full text: {div.get_text().strip()[:200]}')

# Find wcl-substitute elements
subs = lineups_container.select('*[class*="wcl-substitute"]')
print(f'\nwcl-substitute elements: {len(subs)}')
for s in subs[:5]:
    name = s.select_one('*[class*="participantName"],*[class*="lineupsParticipantName"]')
    if name:
        print(f'  Player: {name.get_text().strip()} (from name)')
    else:
        print(f'  Full: {s.get_text().strip()[:60]}')
    print(f'  class: {s.get("class", [])}')

# Check each side box separately
print('\n--- Finding substitute sections by class ---')
for cls_part in ['substitutesList', 'substitutes', 'subsList', 'subs-box', 'sideBox']:
    els = lineups_container.select(f'[class*="{cls_part}"]')
    if els:
        print(f'[class*="{cls_part}"]: {len(els)}')
        for el in els[:2]:
            txt = el.get_text().strip()[:100]
            print(f'  {txt}')
