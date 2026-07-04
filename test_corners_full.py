import sys
sys.path.insert(0, r'C:\Users\Equipo\Desktop\predecirv2\backend')
from predictor import load_corners_data, compute_rolling_corner_avg

# Load corners data
corners_data = load_corners_data()
print('Loaded corners data: {} teams'.format(len(corners_data)))

# Test a few key teams
for team in ['argentina', 'france', 'brazil', 'germany', 'england', 'turkey', 'canada', 'qatar']:
    if team in corners_data:
        c = corners_data[team]
        print('  {}: for={}, against={}, games={}, source={}'.format(
            team, c.get("corners_for"), c.get("corners_against"), c.get("games"), c.get("_source", "old")
        ))

# Test compute_rolling_corner_avg with empty per_match_data (should use fallback)
per_match_data = {}
print('\nTesting compute_rolling_corner_avg with empty per_match_data (fallback to corners_stats.json):')
for team in ['argentina', 'germany', 'canada']:
    result = compute_rolling_corner_avg(team, per_match_data)
    print('  {}: {}'.format(team, result))