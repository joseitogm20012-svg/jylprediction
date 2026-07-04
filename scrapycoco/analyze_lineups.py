"""Analyze lineup HTML structure to fix team grouping"""
from bs4 import BeautifulSoup
from collections import Counter

with open('C:/Users/Equipo/Desktop/mundial104/debug_lineups2.html', encoding='utf-8') as f:
    soup = BeautifulSoup(f.read(), 'html.parser')

els = soup.select('*[class*="lineupsParticipantName"]')
print('Total player elements:', len(els))

for el in els[:3]:
    name = el.get_text().strip()
    print(f'\nPlayer: {name}')
    ancestors = list(el.parents)
    for i, anc in enumerate(ancestors[:8]):
        cls = anc.get('class', [])
        print(f'  Depth {i}: {anc.name} class={cls}')

# Group by different ancestor depths
for depth in range(1, 10):
    groups = {}
    for el in els:
        name = el.get_text().strip()
        ancestors = list(el.parents)
        if len(ancestors) > depth:
            aid = id(ancestors[depth])
            if aid not in groups:
                groups[aid] = []
            groups[aid].append(name)
    counts = [len(g) for g in groups.values()]
    if len(groups) >= 2:
        print(f'\nDepth {depth}: {len(groups)} groups -> {sorted(counts, reverse=True)[:4]}')
        largest = sorted(groups.values(), key=len, reverse=True)[:2]
        if len(largest) >= 2:
            print(f'  Group 0: {largest[0][:3]}...')
            print(f'  Group 1: {largest[1][:3]}...')
    else:
        print(f'\nDepth {depth}: {len(groups)} group -> {counts}')
