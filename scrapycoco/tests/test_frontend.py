"""Playwright frontend verification for ScrapyCoco."""
from playwright.sync_api import sync_playwright
import sys

BASE_URL = "http://localhost:3006"

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(viewport={"width": 1440, "height": 900})
        page = ctx.new_page()

        print("1. Navigate to dashboard...")
        page.goto(BASE_URL, wait_until="domcontentloaded", timeout=15000)
        page.wait_for_selector(".app-layout", timeout=5000)
        assert "ScrapyCoco" in page.title(), "Title check"
        print("   OK - Title matches")

        print("2. Check sidebar navigation...")
        nav_items = page.locator(".nav-item[data-tab]")
        count = nav_items.count()
        assert count >= 5, f"Expected >=5 nav items, got {count}"
        print(f"   OK - {count} nav items found")

        print("3. Check dashboard KPIs...")
        kpis = page.locator(".kpi-value")
        assert kpis.count() >= 4, f"Expected >=4 KPIs, got {kpis.count()}"
        print(f"   OK - {kpis.count()} KPI cards rendered")

        print("4. Check Charts canvas...")
        canvases = page.locator("canvas")
        assert canvases.count() >= 2, f"Expected >=2 charts, got {canvases.count()}"
        print(f"   OK - {canvases.count()} Chart.js canvases found")

        print("5. Switch to Extractions tab...")
        page.locator('.nav-item[data-tab="extraction"]').click()
        page.wait_for_timeout(500)
        extraction_section = page.locator("#tab-extraction")
        assert extraction_section.is_visible(), "Extraction section visible"
        scrapers = page.locator(".scraper-card")
        assert scrapers.count() > 0, "Expected scraper cards"
        print(f"   OK - {scrapers.count()} scraper cards rendered")

        print("6. Switch to History tab...")
        page.locator('.nav-item[data-tab="history"]').click()
        page.wait_for_timeout(500)
        assert page.locator("#tab-history").is_visible()
        assert page.locator("#history-tbody").is_visible()
        print("   OK - History table rendered")

        print("7. Switch to Scheduler tab...")
        page.locator('.nav-item[data-tab="scheduler"]').click()
        page.wait_for_timeout(500)
        assert page.locator("#tab-scheduler").is_visible()
        print("   OK - Scheduler section rendered")

        print("8. Switch to Config tab...")
        page.locator('.nav-item[data-tab="config"]').click()
        page.wait_for_timeout(500)
        assert page.locator("#tab-config").is_visible()
        print("   OK - Config section rendered")

        print("9. Toggle sidebar...")
        page.locator("#sidebar-toggle").click()
        page.wait_for_timeout(300)
        print("   OK - Sidebar toggled")

        print("10. Toggle theme...")
        page.locator("#theme-toggle").click()
        page.wait_for_timeout(300)
        theme = page.evaluate("document.documentElement.getAttribute('data-theme')")
        assert theme == "dark", f"Expected dark theme, got {theme}"
        print(f"   OK - Theme switched to {theme}")

        print("11. Check console drawer...")
        page.locator("#console-drawer-header").click()
        page.wait_for_timeout(300)
        drawer = page.locator("#console-drawer")
        assert not drawer.evaluate("el => el.classList.contains('collapsed')")
        print("   OK - Console drawer expanded")

        print("12. Check toast system...")
        page.evaluate("showToast('Test toast', 'success')")
        page.wait_for_timeout(500)
        toast = page.locator(".toast")
        assert toast.is_visible(), "Toast visible"
        print("   OK - Toast rendered")

        # Take screenshot
        page.screenshot(path="C:\\Users\\Equipo\\Desktop\\predecirv2\\scrapycoco\\tests\\frontend_verified.png", full_page=True)
        print("\n13. Screenshot saved: frontend_verified.png")

        browser.close()
        print("\nAll 12 frontend tests passed!")

if __name__ == "__main__":
    try:
        run()
    except Exception as e:
        print(f"\nFAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
