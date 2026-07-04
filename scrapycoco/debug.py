"""Debug: save Alineaciones page HTML and analyze"""
import asyncio
from playwright.async_api import async_playwright

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(viewport={"width": 1366, "height": 768})
        page = await ctx.new_page()
        
        # Go to Alineaciones directly
        await page.goto(
            "https://www.flashscore.com.ve/partido/futbol/brasil-I9l9aqLq/panama-OWKqbCfi/resumen/alineaciones/?mid=4UXzDy1d",
            timeout=30000, wait_until="domcontentloaded"
        )
        await asyncio.sleep(5)
        
        # Save HTML
        html = await page.content()
        with open("C:/Users/Equipo/Desktop/mundial104/debug_lineups2.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("Saved debug_lineups2.html")
        
        # Find elements containing player info
        player_selectors = [
            "*[class*='playerName']",
            "*[class*='participantName']",
            "*[class*='lineupsParticipantName']",
            "*[class*='name']",
            "*[class*='Player']",
            "*[class*='Jersey']",
            "*[class*='Number']",
            "*[class*='jersey']",
            "*[class*='number']",
            "*[class*='shirt']",
            "*[class*='Shirt']",
        ]
        
        for sel in player_selectors:
            els = await page.query_selector_all(sel)
            count = len(els)
            texts = []
            for el in els[:5]:
                try:
                    t = (await el.text_content()).strip()[:50]
                    texts.append(t)
                except:
                    texts.append("?")
            print(f"{sel}: {count} elements -> {texts}")
        
        # General content analysis
        lineup_containers = await page.query_selector_all("div[class*='lineup'],div[class*='lineUp'],div[class*='LineUp']")
        print(f"\nLineup containers: {len(lineup_containers)}")
        
        # Check if there's a class with "lf__" or "wcl-" that might contain player info
        for cls_key in ["lf__", "wcl-", "smv__", "lineup", "lineUp", "player", "Player", "participant"]:
            els = await page.query_selector_all(f"[class*='{cls_key}']")
            print(f"\n[class*='{cls_key}']: {len(els)} elements")
            texts = []
            for el in els[:8]:
                try:
                    t = (await el.text_content()).strip()[:60]
                    texts.append(t)
                except:
                    texts.append("?")
            for t in texts:
                print(f"  -> {t}")
        
        await browser.close()

asyncio.run(main())
