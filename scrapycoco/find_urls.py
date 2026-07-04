from playwright.async_api import async_playwright
import asyncio

URLS = [
    "https://www.flashscore.es/equipo/brasil/resultados/",
    "https://www.flashscore.es/equipo/brazil/resultados/",
    "https://www.flashscore.com/team/brazil/results/",
    "https://www.flashscore.com/team/brasil/results/",
    "https://www.flashscore.es/futbol/mundial-2026/resultados/",
    "https://www.flashscoreboard.com/futbol/mundial-2026/resultados/",
]

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        for url in URLS:
            print(f"\n{'='*60}\nProbando: {url}")
            try:
                await page.goto(url, timeout=15000)
                html = await page.content()
                if "no puede ser mostrada" not in html and "404" not in html:
                    print(f"  >>> EXITO! ({len(html)} chars)")
                    with open(f"debug_{url.split('/')[-2]}.html", "w", encoding="utf-8") as f:
                        f.write(html)
                else:
                    print(f"  >>> ERROR 404/bloqueado")
            except Exception as e:
                print(f"  >>> EXCEPCION: {e}")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())