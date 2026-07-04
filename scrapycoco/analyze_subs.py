"""Analyze substitute grouping structure"""
from bs4 import BeautifulSoup
from collections import defaultdict

with open('C:/Users/Equipo/Desktop/mundial104/debug_lineups2.html', encoding='utf-8') as f:
    soup = BeautifulSoup(f.read(), 'html.parser')

# Find wcl-substitute elements
sub_els = soup.select('*[class*="wcl-substitute"]')
print(f'wcl-substitute elements: {len(sub_els)}')

# Group by ancestors at different depths
for depth in range(1, 10):
    groups = defaultdict(list)
    for el in sub_els:
        name_el = el.select_one('*[class*="participantName"],*[class*="lineupsParticipantName"]')
        name = name_el.get_text().strip() if name_el else el.get_text().strip()[:30]
        ancestors = list(el.parents)
        if len(ancestors) > depth:
            groups[id(ancestors[depth])].append(name)
    counts = [len(g) for g in groups.values()]
    if len(groups) >= 2:
        print(f'\nDepth {depth}: {len(groups)} groups -> {sorted(counts, reverse=True)[:4]}')
        largest = sorted(groups.values(), key=len, reverse=True)[:2]
        if len(largest) >= 2 and len(largest[0]) > 2 and len(largest[1]) > 2:
            print(f'  Group 0: {largest[0][:3]}...')
            print(f'  Group 1: {largest[1][:3]}...')

# Also check lf__sidesBox for subs with shirt numbers
print('\n=== Checking side boxes depth structure ===')
side_boxes = soup.select('div[class*="lf__sidesBox"]')
for i, sb in enumerate(side_boxes):
    players = sb.select('*[class*="lineupsParticipantName"]')
    names_full = [p.get_text().strip() for p in players if p.get_text().strip()]
    unique = list(dict.fromkeys(names_full))
    # Check if names have shirt numbers
    has_numbers = any(re.match(r'^\d+', n) for n in unique[:5])
    print(f'Side box {i+1}: {len(unique)} unique names, has_numbers={has_numbers}')
    if unique:
        print(f'  First 3: {unique[:3]}')
    # Check ancestors
    anc = list(sb.parents)
    for j, a in enumerate(anc[:5]):
        print(f'  Ancestor {j}: <{a.name} class={a.get("class", [])[:2]}>')
