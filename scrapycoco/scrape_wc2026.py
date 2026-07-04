"""
SCRAPEO MUNDIAL 2026
V5: Final - lf__formation for starters, wcl-substitute for subs
"""
import json, csv, asyncio, re
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright

OUT_DIR = Path("C:/Users/Equipo/Desktop/mundial104")
OUT_DIR.mkdir(parents=True, exist_ok=True)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
]

log_lines = []

def log(msg):
    ts = datetime.now().strftime("%H:%M:%S")
    print("[%s] %s" % (ts, msg))
    log_lines.append("[%s] %s" % (ts, msg))

async def cookie_banner(page):
    try:
        btn = await page.query_selector("#onetrust-accept-btn-handler")
        if btn: await btn.click()
    except Exception: pass

async def click_secondary_tab_by_href(page, keyword):
    try:
        hrefs = await page.evaluate('''() => {
            const tabs = document.querySelectorAll('div[class*="tabsSecondary"] a[data-discover="true"]');
            const result = {};
            for (const a of tabs) {
                if (a.href) result[a.href] = a.textContent.trim();
            }
            return result;
        }''')
        for href, text in hrefs.items():
            if keyword.lower() in text.lower() or keyword.lower() in href.lower():
                log("Navegando a tab: %s" % href)
                await page.goto(href, timeout=30000, wait_until="domcontentloaded")
                await asyncio.sleep(4)
                return True
    except Exception as e:
        log("Error click_secondary_tab_by_href: %s" % e)
    return False

# ── ESTADÍSTICAS ──

async def scrape_team_stats(page) -> dict:
    stats = {}
    try:
        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")
        for row in soup.select("div[class*='wcl-row_']"):
            cat = row.select_one("div[class*='wcl-category_']")
            home = row.select_one("div[class*='wcl-homeValue_']")
            away = row.select_one("div[class*='wcl-awayValue_']")
            if cat and home and away:
                stats[cat.get_text().strip()] = {
                    "home": home.get_text().strip(),
                    "away": away.get_text().strip()
                }
        log("Estadisticas: %d categorias." % len(stats))
    except Exception as e:
        log("Error estadisticas: %s" % e)
    return stats

# ── ALINEACIONES ──

def group_by_ancestor(els, depth):
    from collections import defaultdict
    groups = defaultdict(list)
    for el in els:
        name = el.get_text().strip()
        if not name:
            continue
        ancestors = list(el.parents)
        if len(ancestors) > depth:
            groups[id(ancestors[depth])].append(name)
    return [list(dict.fromkeys(g)) for g in groups.values()]

async def scrape_lineups(page) -> dict:
    lineups = {"local": {"titulares": [], "suplentes": [], "formacion": ""},
               "visitante": {"titulares": [], "suplentes": [], "formacion": ""}}
    try:
        html = await page.content()
        soup = BeautifulSoup(html, "html.parser")

        # STARTERS: lineupsParticipantName grouped by lf__formation (depth 3)
        players = soup.select("*[class*='lineupsParticipantName']")
        if players:
            groups = group_by_ancestor(players, 3)
            groups.sort(key=len, reverse=True)
            team_groups = [g for g in groups if len(g) >= 4][:2]
            if len(team_groups) >= 2:
                lineups["local"]["titulares"] = team_groups[0]
                lineups["visitante"]["titulares"] = team_groups[1]
                log("OK Starters: %d vs %d" % (len(team_groups[0]), len(team_groups[1])))

        # FORMATIONS
        form_texts = []
        for el in soup.select("*[class*='formation']"):
            t = el.get_text().strip()
            m = re.match(r'^(\d[\d\s-]*)', t)
            if m:
                form_texts.append(m.group(1))
        if len(form_texts) >= 2:
            lineups["local"]["formacion"] = form_texts[0]
            lineups["visitante"]["formacion"] = form_texts[1]
        elif form_texts:
            lineups["local"]["formacion"] = form_texts[0]
            log("Formaciones: %s / %s" % (form_texts[0] if len(form_texts)>0 else "",
                                           form_texts[1] if len(form_texts)>1 else ""))

        # SUBS: wcl-substitute → nameWrapper
        sub_name_els = soup.select("*[class*='wcl-substitute'] button[class*='nameWrapper']")
        if sub_name_els:
            sub_groups = group_by_ancestor(sub_name_els, 4)
            sub_groups.sort(key=len, reverse=True)
            team_subs = [g for g in sub_groups if len(g) >= 2][:2]
            if len(team_subs) >= 2:
                lineups["local"]["suplentes"] = team_subs[0]
                lineups["visitante"]["suplentes"] = team_subs[1]
                log("OK Subs: %d vs %d" % (len(team_subs[0]), len(team_subs[1])))

        n_lt = len(lineups["local"]["titulares"])
        n_vt = len(lineups["visitante"]["titulares"])
        n_ls = len(lineups["local"]["suplentes"])
        n_vs = len(lineups["visitante"]["suplentes"])
        log("Alineaciones: %d vs %d titulares, %d vs %d supl." % (n_lt, n_vt, n_ls, n_vs))
    except Exception as e:
        log("Error alineaciones: %s" % e)
    return lineups

async def scrape_one_match(mid: str, context) -> dict:
    base_url = "https://www.flashscore.es/partido/%s/" % mid
    page = await context.new_page()
    result = {"match_id": mid, "estadisticas": {}, "alineaciones": {}, "error": None}
    try:
        await page.goto(base_url, timeout=30000, wait_until="domcontentloaded")
        await asyncio.sleep(2)
        await cookie_banner(page)

        html_content = (await page.content()).lower()
        if not any(x in html_content for x in ["mundial", "world cup", "worldcup"]):
            log("  %s: Saltando (no es Mundial)" % mid)
            return None
        try:
            desc = await page.query_selector("div[class*='duelParticipant'],div[class*='participant']")
            result["description"] = (await desc.text_content()).strip() if desc else (await page.title())
        except Exception: result["description"] = ""
        try:
            sw = await page.query_selector("div[class*='detailScore__wrapper']")
            result["score"] = (await sw.text_content()).strip() if sw else ""
        except Exception: result["score"] = ""

        if await click_secondary_tab_by_href(page, "estadisticas"):
            result["estadisticas"] = await scrape_team_stats(page)

        if await click_secondary_tab_by_href(page, "alineaciones"):
            result["alineaciones"] = await scrape_lineups(page)

        n_stats = len(result["estadisticas"])
        al = result.get("alineaciones", {})
        n_lt = len(al.get("local", {}).get("titulares", []))
        n_vt = len(al.get("visitante", {}).get("titulares", []))
        log("  %s: %s | %d stats | %d vs %d titulares" % (mid, result.get("score", "?"), n_stats, n_lt, n_vt))
    except Exception as e:
        result["error"] = str(e)
        log("  %s: ERROR %s" % (mid, e))
    finally:
        await page.close()
    return result

def save_match(result: dict):
    mid = result["match_id"]
    with open(OUT_DIR / ("%s.json" % mid), "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    with open(OUT_DIR / ("%s.csv" % mid), "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["# PARTIDO", result.get("description", "")])
        w.writerow(["# ID", mid])
        w.writerow(["# Tipo", "finalizado"])
        w.writerow(["# Ultima actualizacion", datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]])
        w.writerow(["# RESULTADO", result.get("score", "")])
        w.writerow([])
        stats = result.get("estadisticas", {})
        if stats:
            w.writerow(["# === ESTADISTICAS ==="])
            w.writerow(["Categoria", "Local", "Visitante"])
            for cat, vals in sorted(stats.items(), key=lambda x: x[0]):
                w.writerow([cat, vals.get("home", ""), vals.get("away", "")])
            w.writerow([])
        al = result.get("alineaciones", {})
        if al:
            w.writerow(["# === ALINEACIONES (CONFIRMADA) ==="])
            for side in ["local", "visitante"]:
                sd = al.get(side, {})
                w.writerow(["# %s (formacion: %s)" % (side.upper(), sd.get("formacion", ""))])
                if sd.get("titulares"):
                    w.writerow(["# TITULARES"])
                    for p in sd["titulares"]:
                        w.writerow([p])
                if sd.get("suplentes"):
                    w.writerow(["# SUPLENTES"])
                    for p in sd["suplentes"]:
                        w.writerow([p])
                w.writerow([])

async def main():
    log("=" * 60)
    log("SCRAPEO MUNDIAL 2026")
    log("=" * 60)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        match_id = "4UXzDy1d"
        log("Procesando: %s" % match_id)
        ctx = await browser.new_context(user_agent=USER_AGENTS[0], viewport={"width": 1366, "height": 768})
        result = await scrape_one_match(match_id, ctx)
        await ctx.close()
        if result and not result.get("error"):
            save_match(result)
            log("Guardado: %s" % match_id)
            log("Stats: %d | Titulares: %d vs %d | Suplentes: %d vs %d" % (
                len(result.get("estadisticas", {})),
                len(result.get("alineaciones", {}).get("local", {}).get("titulares", [])),
                len(result.get("alineaciones", {}).get("visitante", {}).get("titulares", [])),
                len(result.get("alineaciones", {}).get("local", {}).get("suplentes", [])),
                len(result.get("alineaciones", {}).get("visitante", {}).get("suplentes", []))
            ))
        else:
            log("Error en %s" % match_id)
        await browser.close()
    log("=" * 60)
    log("PRUEBA COMPLETADA")

if __name__ == "__main__":
    asyncio.run(main())
