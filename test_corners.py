import sys
sys.path.insert(0, 'C:\\Users\\Equipo\\Desktop\\predecirv2')
from backend.predictor import load_corners_stats

corners = load_corners_stats()
print(f'Loaded {len(corners)} teams from corners_stats.json')

for team in ['argentina', 'france', 'brazil', 'germany', 'england', 'turkey', 'canada', 'qatar']:
    if team in corners:
        c = corners[team]
        print(f'  {team}: for={c.get("corners_for")}, against={c.get("corners_against")}, source={c.get("_source", "old")}')