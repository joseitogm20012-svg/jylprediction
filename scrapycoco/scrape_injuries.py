"""
SCRAPEO DE LESIONES — TRANSFERMARKT
Scrapea lesiones, valor de plantilla, edad promedio y DT
para las 48 selecciones del Mundial 2026.
"""
import json, asyncio, re, sys, time
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

OUT_DIR = Path("C:/Users/Equipo/Desktop/predecirv2/data")
OUT_DIR.mkdir(parents=True, exist_ok=True)

INJURIES_PATH = OUT_DIR / "injuries.json"
TRANSFERMARKT_PATH = OUT_DIR / "transfermarkt_stats.json"

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
]

WC_TEAMS = [
    "argentina", "brazil", "australia", "cameroon",
    "spain", "nigeria", "usa", "saudi-arabia",
    "poland", "south-korea", "egypt",
    "france", "denmark", "tunisia", "canada",
    "england", "serbia", "iran", "jamaica",
    "portugal", "morocco", "paraguay", "new-zealand",
    "belgium", "croatia", "ecuador", "costa-rica",
    "netherlands", "senegal", "qatar", "panama",
    "italy", "colombia", "japan", "algeria",
    "mexico", "switzerland", "greece", "bolivia",
    "uruguay", "south-africa", "chile", "honduras",
    "czech-republic", "turkey", "guatemala", "indonesia",
    "germany",
]

SLUG_TO_DISPLAY = {
    "usa": "USA",
    "south-korea": "South Korea",
    "new-zealand": "New Zealand",
    "costa-rica": "Costa Rica",
    "saudi-arabia": "Saudi Arabia",
    "south-africa": "South Africa",
    "czech-republic": "Czech Republic",
}

def display_name(slug):
    if slug in SLUG_TO_DISPLAY:
        return SLUG_TO_DISPLAY[slug]
    return slug.replace("-", " ").title()

log_lines = []

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    print("[%s] %s" % (ts, msg))
    log_lines.append("[%s] %s" % (ts, msg))

async def search_transfermarkt_url(page, team_display):
    query = f"site:transfermarkt.com {team_display} national team squad startseite"
    url = f"https://www.google.com/search?q={query}"
    try:
        await page.goto(url, timeout=20000, wait_until="domcontentloaded")
        await asyncio.sleep(2)
        el = await page.query_selector("a[href*='transfermarkt.com/']")
        if el:
            href = await el.get_attribute("href")
            if href:
                return href.split("&")[0]
    except:
        pass
    return None

async def scrape_team(browser, slug):
    team_display = display_name(slug)
    log(">>> %s (%s)" % (slug, team_display))

    context = await browser.new_context(
        user_agent=USER_AGENTS[hash(slug) % len(USER_AGENTS)],
        viewport={"width": 1366, "height": 768}
    )
    page = await context.new_page()

    result = {
        "team": team_display,
        "slug": slug,
        "market_value": "",
        "average_age": "",
        "manager": "",
        "injuries": [],
        "error": None
    }

    try:
        profile_url = await search_transfermarkt_url(page, team_display)
        if not profile_url:
            # Try without "squad"
            profile_url = await search_transfermarkt_url(page, team_display.replace(" national team", ""))
        if not profile_url:
            log("  %s: No se encontro URL" % slug)
            result["error"] = "No URL found"
            return result

        log("  URL: %s" % profile_url)
        await page.goto(profile_url, timeout=25000, wait_until="domcontentloaded")
        await asyncio.sleep(3)

        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")
        header = soup.find(class_="data-header")

        if header:
            for span in header.find_all("span", class_="data-header__label"):
                text = span.get_text()
                val_el = span.find("span", class_="data-header__content")
                if not val_el:
                    val_el = span.find("a")
                val = val_el.get_text().strip() if val_el else ""

                if "Edad media" in text or "Average age" in text:
                    result["average_age"] = val
                if "Entrenador" in text or "Coach" in text or "Manager" in text:
                    result["manager"] = val

            value_div = header.find(class_="data-header__market-value")
            if value_div:
                result["market_value"] = value_div.get_text().strip()

        log("  Edad: %s | DT: %s | Valor: %s" % (
            result["average_age"] or "?",
            result["manager"] or "?",
            result["market_value"] or "?"
        ))

        # ── INJURIES ──
        injury_url = profile_url.replace("/startseite/", "/verletzungen/")
        if "/startseite" not in profile_url.lower() and "/startseite" not in injury_url:
            injury_url = re.sub(r'/verein/\d+', '/verletzungen/verein/', profile_url)

        log("  Lesiones: %s" % injury_url)
        try:
            await page.goto(injury_url, timeout=20000, wait_until="domcontentloaded")
            await asyncio.sleep(2.5)
            ih = await page.content()
            isoup = BeautifulSoup(ih, "html.parser")
            itable = isoup.find("table", class_="items")
            if itable:
                for tr in itable.find_all("tr"):
                    tds = tr.find_all("td")
                    if len(tds) >= 3:
                        player = tds[0].get_text(strip=True)
                        injury = tds[1].get_text(strip=True)
                        status = tds[2].get_text(strip=True)
                        if player and injury:
                            result["injuries"].append({
                                "player": player,
                                "injury": injury,
                                "status": status
                            })
                log("  Lesiones: %d" % len(result["injuries"]))
            else:
                log("  Sin tabla de lesiones")
        except Exception as e:
            log("  Error lesiones: %s" % e)

    except Exception as e:
        log("  ERROR %s: %s" % (slug, e))
        result["error"] = str(e)
    finally:
        await context.close()

    return result

async def main():
    log("=" * 60)
    log("SCRAPEO DE LESIONES — TRANSFERMARKT")
    log("Equipos: %d selecciones" % len(WC_TEAMS))
    log("=" * 60)

    # Load existing data
    injuries_all = {}
    if INJURIES_PATH.exists():
        try:
            injuries_all = json.loads(INJURIES_PATH.read_text(encoding="utf-8"))
            log("Cargados %d equipos existentes en injuries.json" % len(injuries_all))
        except:
            pass

    transfermarkt_all = {}
    if TRANSFERMARKT_PATH.exists():
        try:
            transfermarkt_all = json.loads(TRANSFERMARKT_PATH.read_text(encoding="utf-8"))
            log("Cargados %d equipos existentes en transfermarkt_stats.json" % len(transfermarkt_all))
        except:
            pass

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        for i, slug in enumerate(WC_TEAMS, 1):
            log("[%d/%d]" % (i, len(WC_TEAMS)))
            t0 = time.time()
            data = await scrape_team(browser, slug)
            elapsed = time.time() - t0

            # Save to injuries
            injuries_all[slug] = {
                "injuries": data["injuries"]
            }

            # Save to transfermarkt_stats
            transfermarkt_all[slug] = {
                "team": data["team"],
                "slug": slug,
                "market_value": data["market_value"],
                "average_age": data["average_age"],
                "manager": data["manager"],
            }

            log("  Hecho en %.1fs" % elapsed)

            # Write after each team in case of crash
            INJURIES_PATH.write_text(
                json.dumps(injuries_all, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
            TRANSFERMARKT_PATH.write_text(
                json.dumps(transfermarkt_all, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )

            await asyncio.sleep(1.5)

        await browser.close()

    log("=" * 60)
    complete = sum(1 for v in injuries_all.values() if v.get("injuries"))
    log("COMPLETADO: %d/%d equipos con lesiones" % (complete, len(WC_TEAMS)))
    log("injuries.json: %s" % INJURIES_PATH)
    log("transfermarkt_stats.json: %s" % TRANSFERMARKT_PATH)
    log("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
