import importlib, sys, pathlib

def test_new_scraper_slugify():
    sys.path.append(str(pathlib.Path(__file__).parents[2]))
    mod = importlib.import_module('scrapycoco.scrape_corners_hybrid')
    assert mod.slugify('United States') == 'united-states'
    assert mod.slugify("Côte d'Ivoire") == "côte-divoire"

def test_new_scraper_load_save(tmp_path):
    sys.path.append(str(pathlib.Path(__file__).parents[2]))
    mod = importlib.import_module('scrapycoco.scrape_corners_hybrid')
    # Patch OUTPUT_PATH to temporary file
    temp_file = tmp_path / 'per_match_corners.json'
    mod.OUTPUT_PATH = temp_file
    # Ensure empty load returns default structure
    data = mod.load_existing()
    assert isinstance(data, dict)
    assert data.get('matches') == []
    # Write some data and save
    data['matches'].append({
        'id': 'test',
        'date': '2026-01-01',
        'home_team': 'argentina',
        'away_team': 'mexico',
        'home_corners': 5,
        'away_corners': 3,
        'competition': 'test',
        'type': 'international'
    })
    mod.save_data(data)
    # Reload and verify
    loaded = mod.load_existing()
    assert loaded['matches'][0]['id'] == 'test'
    assert loaded['matches'][0]['home_corners'] == 5
    assert loaded['matches'][0]['away_corners'] == 3
