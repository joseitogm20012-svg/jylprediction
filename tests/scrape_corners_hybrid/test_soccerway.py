import importlib, sys, pathlib

def test_new_scraper_fetch_soccerway_fixtures(monkeypatch):
    sys.path.append(str(pathlib.Path(__file__).parents[2]))
    mod = importlib.import_module('scrapycoco.scrape_corners_hybrid')
    # Mock requests.get to return HTML with a match link
    class DummyResponse:
        def __init__(self, text):
            self.text = text
        def raise_for_status(self):
            pass
    def mock_get(url, timeout=15):
        # Return simple HTML containing a match link
        html = '<a href="/match/argentina-mexico-2026/1234567/">Match</a>'
        return DummyResponse(html)
    monkeypatch.setattr(mod.requests, "get", mock_get)
    fixtures = mod.fetch_soccerway_fixtures()
    assert isinstance(fixtures, list)
    assert len(fixtures) == 1
    f = fixtures[0]
    assert f['id'] == '1234567'
    assert f['url'] == 'https://int.soccerway.com/match/argentina-mexico-2026/1234567/'
    assert f['home'] == 'Argentina'
    assert f['away'] == 'Mexico'

def test_new_scraper_extract_corners_soccerway(monkeypatch):
    sys.path.append(str(pathlib.Path(__file__).parents[2]))
    mod = importlib.import_module('scrapycoco.scrape_corners_hybrid')
    class DummyResponse:
        def __init__(self, text):
            self.text = text
        def raise_for_status(self):
            pass
    def mock_get(url, timeout=15):
        html = '<table><tr><td>Corners</td><td>5</td><td>3</td></tr></table>'
        return DummyResponse(html)
    monkeypatch.setattr(mod.requests, "get", mock_get)
    corners = mod.extract_corners_soccerway('https://example.com/match')
    assert corners == (5, 3)
