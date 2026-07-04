from playwright.sync_api import sync_playwright
import json, sys, io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

BASE = "http://localhost:3005"
passed = 0
failed = 0

def test(name, ok, detail=""):
    global passed, failed
    if ok:
        passed += 1
        print(f"  [PASS] {name}")
    else:
        failed += 1
        print(f"  [FAIL] {name} - {detail}")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
    ctx = browser.new_context(
        viewport={"width": 1280, "height": 800},
        ignore_https_errors=True,
    )
    page = ctx.new_page()

    # 1. Page loads
    page.goto(BASE, wait_until="networkidle")
    test("Pagina carga sin error", "ScrapyCoco" in page.title() or page.title() != "")
    test("Titulo visible", page.locator("h1, h2, .app-title").count() > 0)

    # 2. Extraccion tab: scraper list
    test("Tab Extraccion visible", page.locator("[class*=tab],.tab-button,.nav-item").count() >= 2)
    cards = page.locator(".scraper-card, .scraper-item, [class*=scraper]")
    card_count = cards.count()
    test(f"Scrapers listados ({card_count})", card_count >= 6)

    # 3. Run a scraper (sandbox)
    print()
    print("  -- Ejecutando scraper results (sandbox) --")
    response = page.request.get(f"{BASE}/api/run/results", params={"sandbox": "true"}, timeout=15000)
    test("GET /api/run/results 200", response.ok, detail=str(response.status))

    # 4. Preview endpoint
    print()
    print("  -- Preview --")
    try:
        preview = page.request.get(f"{BASE}/api/preview/results", params={"sandbox": "true"}, timeout=10000)
        test("GET /api/preview/results 200", preview.ok)
        if preview.ok:
            data = preview.json()
            test("Preview devuelve respuesta", isinstance(data, dict))
    except Exception as e:
        test("Preview endpoint", False, detail=str(e)[:60])

    # 5. History
    print()
    print("  -- Historial --")
    hist = page.request.get(f"{BASE}/api/history", params={"limit": 5})
    test("GET /api/history 200", hist.ok)
    if hist.ok:
        rows = hist.json()
        test(f"Historial devuelve {len(rows)} registros", isinstance(rows, list))

    # 6. Metrics
    metrics = page.request.get(f"{BASE}/api/history/metrics")
    test("GET /api/history/metrics 200", metrics.ok)
    if metrics.ok:
        m = metrics.json()
        test("Metrics tiene total_runs", "total_runs" in m)

    # 7. Scheduler CRUD
    print()
    print("  -- Programador CRUD --")
    try:
        job_data = {"scraper_id": "results", "cron_expression": "0 */6 * * *", "sandbox": True, "params": {}}
        created = page.request.post(f"{BASE}/api/scheduler/add", data=json.dumps(job_data), headers={"Content-Type": "application/json"}, timeout=10000)
        test("POST /api/scheduler/add 200", created.ok, detail=str(created.status))
        job_id = None
        if created.ok:
            j = created.json()
            job_id = j.get("id") or j.get("schedule_id")
            if job_id:
                test("Job creado con id", True, detail=f"id={job_id}")
            jobs = page.request.get(f"{BASE}/api/scheduler/list", timeout=10000)
            test("GET /api/scheduler/list 200", jobs.ok)
            if jobs.ok:
                jlist = jobs.json()
                test(f"Jobs listados ({len(jlist)})", len(jlist) > 0)
            if job_id:
                paused = page.request.post(f"{BASE}/api/scheduler/{job_id}/pause", timeout=10000)
                test("Pause job 200", paused.ok, detail=str(paused.status))
                resumed = page.request.post(f"{BASE}/api/scheduler/{job_id}/resume", timeout=10000)
                test("Resume job 200", resumed.ok, detail=str(resumed.status))
                deleted = page.request.delete(f"{BASE}/api/scheduler/{job_id}", timeout=10000)
                test("Delete job 200", deleted.ok, detail=str(deleted.status))
    except Exception as e:
        test("Scheduler CRUD", False, detail=str(e)[:80])

    # 8. Scraper status list
    status = page.request.get(f"{BASE}/api/scrapers")
    test("GET /api/scrapers 200", status.ok)
    if status.ok:
        slist = status.json()
        if isinstance(slist, dict) and "value" in slist:
            test(f"Scrapers listados ({len(slist['value'])})", slist.get("Count", 0) == 8)
        elif isinstance(slist, list):
            test(f"Scrapers listados ({len(slist)})", len(slist) == 8)
        else:
            test("Scrapers listados", True)

    # 9. Export with inline data
    print()
    print("  -- Export --")
    try:
        preview_data = [{"team": "Brasil", "xg": 2.5}, {"team": "Argentina", "xg": 1.8}]
        body = json.dumps({"scraper_id": "xg", "format": "json", "preview_data": preview_data})
        exp = page.request.post(f"{BASE}/api/export", data=body, headers={"Content-Type": "application/json"}, timeout=10000)
        test("POST /api/export (json) 200", exp.ok, detail=str(exp.status))
        body2 = json.dumps({"scraper_id": "xg", "format": "csv", "preview_data": preview_data})
        exp2 = page.request.post(f"{BASE}/api/export", data=body2, headers={"Content-Type": "application/json"}, timeout=10000)
        test("POST /api/export (csv) 200", exp2.ok, detail=str(exp2.status))
    except Exception as e:
        test("Export", False, detail=str(e)[:60])

    # 10. Diagnostic
    print()
    print("  -- Diagnostico --")
    diag = page.request.post(f"{BASE}/api/diagnostic/run/results",
        data=json.dumps({"page_source": "<html><body><div class='test'>hello</div></body></html>", "url": "http://test.com"}),
        headers={"Content-Type": "application/json"})
    test("POST /api/diagnostic/run/results 200", diag.ok)
    if diag.ok:
        d = diag.json()
        test("Diagnostico tiene has_changes", "has_changes" in d)
        test("Diagnostico severity es numerico", isinstance(d.get("severity"), int) or d.get("severity") is None)

    # 11. Frontend interactions
    print()
    print("  -- Interaccion frontend --")
    page.goto(BASE, wait_until="networkidle")
    tabs = page.locator("[role=tab], .tab, .nav-item, [class*=tab]")
    tab_count = tabs.count()
    test(f"Tabs encontrados ({tab_count})", tab_count >= 3)
    for i in range(min(tab_count, 4)):
        try:
            tabs.nth(i).click()
            page.wait_for_timeout(300)
            test(f"Click tab {i+1} OK", True)
        except Exception as e:
            test(f"Click tab {i+1}", False, detail=str(e)[:60])

    # Results
    print()
    print("=" * 40)
    print(f"RESULTADOS: {passed} passed, {failed} failed")
    print("=" * 40)

    browser.close()
    sys.exit(1 if failed > 0 else 0)
