from playwright.async_api import async_playwright
import asyncio

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        url = "https://www.flashscore.es/partido/4UWnzoz1/"
        print(f"Navegando a {url}...")
        await page.goto(url, timeout=20000)
        await asyncio.sleep(3)
        html = await page.content()
        with open('debug_match.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print("HTML guardado en debug_match.html")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(run())