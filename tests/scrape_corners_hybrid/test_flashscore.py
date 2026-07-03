import importlib, sys, pathlib

def test_new_scraper_extract_corners_flashscore(monkeypatch):
    sys.path.append(str(pathlib.Path(__file__).parents[2]))
    mod = importlib.import_module('scrapycoco.scrape_corners_hybrid')
    
    # Mock Playwright page
    class DummyPage:
        async def goto(self, url, **kwargs):
            pass
        async def content(self):
            return '<table><tr><td>Corners</td><td>4</td><td>2</td></tr></table>'
        async def query_selector(self, selector):
            return None
        async def click(self, selector):
            pass
        async def wait_for_timeout(self, ms):
            pass
        async def wait_for_load_state(self, state):
            pass
    
    class DummyBrowser:
        async def new_page(self):
            return DummyPage()
        async def close(self):
            pass
    
    class DummyChromium:
        async def launch(self, **kw):
            return DummyBrowser()
    
    class DummyPW:
        def __init__(self):
            self.chromium = DummyChromium()
        async def __aenter__(self):
            return self
        async def __aexit__(self, *exc):
            pass
    
    def mock_pw_factory():
        return DummyPW()
    monkeypatch.setattr(mod, 'async_playwright', mock_pw_factory)
    
    # extract_corners_flashscore is sync (uses asyncio.run internally)
    corners = mod.extract_corners_flashscore('https://www.flashscore.com/match/abc/')
    assert corners == (4, 2)