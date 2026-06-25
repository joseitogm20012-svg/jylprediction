import json

# 48 equipos clasificados para el Mundial 2026
wc2026_teams = [
    # CONMEBOL (6)
    'argentina', 'brazil', 'uruguay', 'colombia', 'ecuador', 'venezuela',
    # UEFA (16)
    'germany', 'spain', 'france', 'england', 'portugal', 'netherlands',
    'croatia', 'switzerland', 'belgium', 'austria', 'hungary', 'denmark',
    'serbia', 'scotland', 'slovakia', 'turkey',
    # CONCACAF (6)
    'usa', 'mexico', 'canada', 'panama', 'honduras', 'costa-rica',
    # CAF (9)
    'morocco', 'senegal', 'egypt', 'nigeria', 'south-africa', 'ivory-coast',
    'mali', 'dr-congo', 'algeria',
    # AFC (8)
    'japan', 'south-korea', 'australia', 'iran', 'saudi-arabia', 'jordan',
    'uzbekistan', 'indonesia',
    # OFC (1)
    'new-zealand',
    # Intercontinental
    'paraguay', 'ukraine',
]

with open(r'data/xg_by_team.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
teams = data.get('teams', {})

print(f'Total equipos en JSON: {len(teams)}')
print()
print('Estado de datos para los 48 clasificados al Mundial 2026:')
print('-' * 90)

has_fbref = 0
has_corners = 0
no_data = []

for t in wc2026_teams:
    entry = teams.get(t, {})
    source = entry.get('source', 'MISSING')
    c_for = entry.get('corners_for_per_90')
    c_against = entry.get('corners_against_per_90')
    sh = entry.get('shots_per_90')
    matches = entry.get('matches_played', 0)

    if source == 'fbref_world_cup':
        status = 'FBref'
        has_fbref += 1
    elif source:
        status = 'Historico'
    else:
        status = 'SIN DATOS'

    corners_ok = 'OK' if (c_for is not None and c_against is not None) else 'NULL'

    if c_for is not None:
        has_corners += 1
    if not entry:
        no_data.append(t)

    sh_str = str(round(sh, 1)) if sh else 'N/A'
    c_for_str = str(round(c_for, 2)) if c_for else 'null'
    print(f"{t:<25} [{status:<10}] corners:{corners_ok:<5}  sh/90:{sh_str:<6}  c_for/90:{c_for_str:<6}  partidos:{matches}")

print()
print(f'Resumen: {has_fbref}/48 con datos FBref  |  {has_corners}/48 con corners reales')
if no_data:
    print(f'Sin datos: {no_data}')
