"""Use Playwright to intercept FlashScore match statistics API calls."""
import asyncio, json
from playwright.async_api import async_playwright

async def check():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
        page = await context.new_page()
        
        # Capture all XHR responses  
        xhr_data = []
        async def handle_response(response):
            url = response.url
            if "api" in url.lower() or "data" in url.lower() or "request" in url.lower() or "statistics" in url.lower():
                try:
                    body = await response.text()
                    if len(body) > 10 and len(body) < 50000:
                        if "corner" in body.lower() or "statistics" in body.lower():
                            xhr_data.append((url, response.status, body[:500]))
                            print(f"\n*** CAPTURED API CALL ***")
                            print(f"URL: {url}")
                            print(f"Status: {response.status}")
                            print(f"Body: {body[:500]}")
                except:
                    pass
        page.on("response", handle_response)
        
        # Navigate to FlashScore match
        url = "https://www.flashscore.com/match/4UXzDy1d/#/match-summary/match-statistics"
        print(f"Loading: {url}")
        
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=20000)
        except Exception as e:
            print(f"Navigation: {e}")
        
        # Wait for API calls  
        print("Waiting for API data...")
        await asyncio.sleep(10)
        
        print(f"\nTotal XHR captures with corner/statistics: {len(xhr_data)}")
        if not xhr_data:
            # Just show ALL captured API URLs
            print("No corner/statistics data captured in XHR")
        
        await browser.close()

asyncio.run(check())