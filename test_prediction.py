import sys
sys.path.insert(0, r'C:\Users\Equipo\Desktop\predecirv2\backend')
from predictor import run_prediction_sim, load_data, load_corners_data

# Load data first
ratings, matches = load_data()
corners_data = load_corners_data()

print('Loaded ratings:', len(ratings))
print('Loaded matches:', len(matches))
print('Loaded corners data:', len(corners_data))

# Test a prediction
result = run_prediction_sim(
    team_a='Argentina',
    team_b='France',
    rank_a=ratings.get('Argentina', 1800),
    rank_b=ratings.get('France', 1800),
    fifa_weight_pct=0.4,
    h2h_weight_pct=0.2,
    half_life_months=18,
    num_sims=1000,
    venue='neutral'
)

print('\nPREDICTION: Argentina vs France (neutral)')
print('  1X2: H={:.1%} D={:.1%} A={:.1%}'.format(result["home_win"], result["draw"], result["away_win"]))
print('  Expected corners home: {}'.format(result.get("expected_corners_home", "N/A")))
print('  Expected corners away: {}'.format(result.get("expected_corners_away", "N/A")))
print('  Total corners: {}'.format(result.get("total_corners", "N/A")))