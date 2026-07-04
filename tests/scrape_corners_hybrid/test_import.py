import importlib, sys, pathlib

def test_new_scraper_import():
    # Ensure the project root is in sys.path for the import
    sys.path.append(str(pathlib.Path(__file__).parents[2]))  # project root
    module = importlib.import_module('scrapycoco.scrape_corners_hybrid')
    assert hasattr(module, 'main')
    assert callable(module.main)
