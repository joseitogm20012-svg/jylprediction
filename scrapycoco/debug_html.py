from playwright.async_api import async_playwright
import asyncio

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        print("Navegando...")
        await page.goto('https://www.flashscore.es/equipo/brasil/resultados/')
        html = await page.content()
        with open('debug_results.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print("HTML guardado en debug_results.html")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
