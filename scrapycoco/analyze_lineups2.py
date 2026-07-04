"""Analyze lineup substitutes"""
from bs4 import BeautifulSoup

with open('C:/Users/Equipo/Desktop/mundial104/debug_lineups2.html', encoding='utf-8') as f:
    soup = BeautifulSoup(f.read(), 'html.parser')

# Check for substitutes sections
sub_sels = [
    "div[class*='substitutes']",
    "div[class*='subs']",
    "div[class*='banquillo']",
    "div[class*='sustituto']",
    "*[class*='substitutesList']",
    "*[class*='Substitutes']",
]
for sel in sub_sels:
    subs = soup.select(sel)
    if subs:
        print(f'{sel}: {len(subs)} found')
        for s in subs[:3]:
            cls = s.get('class', [])
            text = s.get_text().strip()[:100]
            print(f'  class={cls} text={text}')
    else:
        # try contains text
        pass

# Check for any div with "suplentes" or "substitutes" text
for tag in soup.find_all(['div', 'h4', 'h5', 'span']):
    text = tag.get_text().strip().lower()
    if text in ['suplentes', 'substitutes', 'subs', 'banquillo', 'suplentes:', 'substitutes:']:
        cls = tag.get('class', [])
        print(f'\nFound "{tag.get_text().strip()}": <{tag.name} class={cls}>')
        # Print siblings
        for sib in tag.find_next_siblings()[:5]:
            print(f'  Sibling: <{sib.name} class={sib.get("class", [])}> text="{sib.get_text().strip()[:60]}"')

# Scan for substitute-like groups in the lineup section
lineups_container = soup.select_one("div[class*='tabContent__lineups']")
if lineups_container:
    # Find all sections with h5 headers
    for h5 in lineups_container.find_all(['h5', 'h4', 'span']):
        txt = h5.get_text().strip().lower()
        if 'sub' in txt or 'banqu' in txt or 'supl' in txt:
            print(f'\nHeader: {h5.get_text().strip()}')
            parent = h5.parent
            print(f'Parent class: {parent.get("class", [])}')
            # Find names in parent
            names = parent.select('*[class*="lineupsParticipantName"],*[class*="participantName"]')
            for n in names:
                print(f'  Player: {n.get_text().strip()}')
