"""Debug wcl-substitute structure"""
from bs4 import BeautifulSoup

with open('C:/Users/Equipo/Desktop/mundial104/debug_lineups2.html', encoding='utf-8') as f:
    soup = BeautifulSoup(f.read(), 'html.parser')

subs = soup.select("*[class*='wcl-substitute']")
print(f"wcl-substitute elements: {len(subs)}")

for s in subs[:3]:
    print(f"\nElement class: {s.get('class')}")
    print(f"  Tag: {s.name}")
    print(f"  Text: {s.get_text().strip()[:60]}")
    children = list(s.children)
    print(f"  Children: {len(children)}")
    for c in children:
        if c.name:
            print(f"    <{c.name} class={c.get('class', [])} text='{c.get_text().strip()[:40]}'")

# Also check: are lineupsParticipantName elements ancestors of wcl-substitute?
sub_name_els = soup.select("*[class*='participantName']")
print(f"\nparticipantName elements: {len(sub_name_els)}")
for ne in sub_name_els[:5]:
    print(f"  Text: '{ne.get_text().strip()[:40]}' class: {ne.get('class', [])[:2]}")
    # check if inside wcl-substitute
    parent = ne.parent
    if parent and 'wcl-substitute' in str(parent.get('class', [])):
        print(f"    -> INSIDE wcl-substitute!")
