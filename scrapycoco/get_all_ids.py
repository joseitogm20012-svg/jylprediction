"""
Obtener todos los match IDs del Mundial 2026 desde flashscore
"""
import asyncio, json, re
from playwright.async_api import async_playwright

async def cookie_banner(page):
    try:
        btn = await page.query_selector("#onetrust-accept-btn-handler")
        if btn: await btn.click()
    except Exception: pass

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(viewport={"width": 1366, "height": 768})
        page = await ctx.new_page()

        # Try both possible URLs
        urls = [
            "https://www.flashscore.es/futbol/mundial-2026/resultados/",
            "https://www.flashscore.es/futbol/mundo/mundial-2026/resultados/",
        ]
        
        for url in urls:
            print(f"Probando: {url}")
            try:
                await page.goto(url, timeout=30000, wait_until="domcontentloaded")
                await asyncio.sleep(5)
                await cookie_banner(page)
                await asyncio.sleep(2)
                
                html = await page.content()
                with open("C:/Users/Equipo/Desktop/mundial104/debug_tournament.html", "w", encoding="utf-8") as f:
                    f.write(html)
                
                title = await page.title()
                print(f"  Title: {title}")
                
                # Extract match IDs from hrefs containing /partido/
                match_ids = set()
                links = await page.evaluate('''() => {
                    const links = document.querySelectorAll('a[href*="/partido/"]');
                    return Array.from(links).map(a => a.href);
                }''')
                
                for link in links:
                    m = re.search(r'/partido/([a-zA-Z0-9]{8})', link)
                    if m:
                        match_ids.add(m.group(1))
                
                print(f"  Match IDs encontrados: {len(match_ids)}")
                if match_ids:
                    ids_list = sorted(match_ids)
                    print(f"  Ejemplos: {ids_list[:5]}")
                    
                    # Save
                    with open("C:/Users/Equipo/Desktop/mundial104/all_match_ids.json", "w") as f:
                        json.dump(ids_list, f, indent=2)
                    print(f"  Guardados en all_match_ids.json")
                    break
                else:
                    print("  No se encontraron match IDs en esta URL")
            except Exception as e:
                print(f"  Error: {e}")
        
        await browser.close()

asyncio.run(main())
