"""Test: direct Transfermarkt squad page for Argentina"""
import asyncio, json
from pathlib import Path
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        ctx = await browser.new_context(user_agent=UA, viewport={"width": 1366, "height": 768})
        page = await ctx.new_page()

        # Try English slug first
        urls = [
            "https://www.transfermarkt.com/argentina/startseite/verein/3439",
            "https://www.transfermarkt.com/argentinien/startseite/verein/3439",
        ]

        for url in urls:
            print("Trying:", url)
            try:
                await page.goto(url, timeout=20000, wait_until="domcontentloaded")
                await asyncio.sleep(2)
                title = await page.title()
                print("  Title:", title)

                if "error" not in title.lower() and "404" not in page.url:
                    print("  OK! URL:", page.url)

                    html = await page.content()
                    soup = BeautifulSoup(html, "html.parser")

                    header = soup.find(class_="data-header")
                    if header:
                        print("  HEADER FOUND")
                        for span in header.find_all("span", class_="data-header__label"):
                            val_el = span.find("span", class_="data-header__content") or span.find("a")
                            val = val_el.get_text(strip=True) if val_el else ""
                            print("    %s -> %s" % (span.get_text(strip=True)[:40], val[:40]))

                        value_div = header.find(class_="data-header__market-value")
                        if value_div:
                            print("    Market value: %s" % value_div.get_text(strip=True)[:60])

                    # Try injuries
                    injury_url = page.url.replace("/startseite/", "/verletzungen/")
                    print("  Injuries URL:", injury_url)
                    await page.goto(injury_url, timeout=20000, wait_until="domcontentloaded")
                    await asyncio.sleep(2)
                    ih = await page.content()
                    isoup = BeautifulSoup(ih, "html.parser")
                    itable = isoup.find("table", class_="items")
                    if itable:
                        injuries = []
                        for tr in itable.find_all("tr"):
                            tds = tr.find_all("td")
                            if len(tds) >= 3:
                                player = tds[0].get_text(strip=True)
                                injury = tds[1].get_text(strip=True)
                                status = tds[2].get_text(strip=True)
                                if player and injury:
                                    injuries.append({"player": player, "injury": injury, "status": status})
                        print("  INJURIES (%d):" % len(injuries))
                        for inj in injuries[:5]:
                            print("    %s - %s [%s]" % (inj["player"], inj["injury"], inj["status"]))
                    else:
                        print("  No injury table found")
                        # Save debug
                        Path("debug_injuries.html").write_text(ih, encoding="utf-8")
                    
                    break  # Found working URL
            except Exception as e:
                print("  Error:", e)

        await ctx.close()
        await browser.close()

asyncio.run(main())
