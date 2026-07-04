import asyncio
import re
from playwright import async_api
from playwright.async_api import expect

async def run_test():
    pw = None
    browser = None
    context = None

    try:
        # Start a Playwright session in asynchronous mode
        pw = await async_api.async_playwright().start()

        # Launch a Chromium browser in headless mode with custom arguments
        browser = await pw.chromium.launch(
            headless=True,
            args=[
                "--window-size=1280,720",
                "--disable-dev-shm-usage",
                "--ipc=host",
                "--single-process"
            ],
        )

        # Create a new browser context (like an incognito window)
        context = await browser.new_context()
        # Wider default timeout to match the agent's DOM-stability budget;
        # auto-waiting Playwright APIs (expect, locator.wait_for) inherit this.
        context.set_default_timeout(15000)

        # Open a new page in the browser context
        page = await context.new_page()

        # Interact with the page elements to simulate user flow
        # -> navigate
        await page.goto("http://localhost:3005/")
        try:
            await page.wait_for_load_state("domcontentloaded", timeout=5000)
        except Exception:
            pass
        
        # -> Scroll to the bottom of the dashboard page to reveal all scraper cards so the full scraper grid can be verified.
        await page.mouse.wheel(0, 300)
        
        # --> Assertions to verify final state
        
        # --> Verify all scraper cards are displayed
        await page.locator("xpath=/html/body/div[1]/div[3]/main/section[1]/div[3]/div[1]/div[2]/div[2]/button[1]").nth(0).scroll_into_view_if_needed()
        # Assert: First scraper card's preview button is visible, indicating the card is displayed.
        await expect(page.locator("xpath=/html/body/div[1]/div[3]/main/section[1]/div[3]/div[1]/div[2]/div[2]/button[1]").nth(0)).to_be_visible(timeout=15000), "First scraper card's preview button is visible, indicating the card is displayed."
        await page.locator("xpath=/html/body/div[1]/div[3]/main/section[1]/div[3]/div[2]/div[2]/div[2]/button[1]").nth(0).scroll_into_view_if_needed()
        # Assert: Second scraper card's preview button is visible, indicating the card is displayed.
        await expect(page.locator("xpath=/html/body/div[1]/div[3]/main/section[1]/div[3]/div[2]/div[2]/div[2]/button[1]").nth(0)).to_be_visible(timeout=15000), "Second scraper card's preview button is visible, indicating the card is displayed."
        await page.locator("xpath=/html/body/div[1]/div[3]/main/section[1]/div[3]/div[3]/div[2]/div[2]/button[1]").nth(0).scroll_into_view_if_needed()
        # Assert: Third scraper card's preview button is visible, indicating the card is displayed.
        await expect(page.locator("xpath=/html/body/div[1]/div[3]/main/section[1]/div[3]/div[3]/div[2]/div[2]/button[1]").nth(0)).to_be_visible(timeout=15000), "Third scraper card's preview button is visible, indicating the card is displayed."
        await page.locator("xpath=/html/body/div[1]/div[3]/main/section[1]/div[3]/div[4]/div[2]/div[2]/button[1]").nth(0).scroll_into_view_if_needed()
        # Assert: Fourth scraper card's preview button is visible, indicating the card is displayed.
        await expect(page.locator("xpath=/html/body/div[1]/div[3]/main/section[1]/div[3]/div[4]/div[2]/div[2]/button[1]").nth(0)).to_be_visible(timeout=15000), "Fourth scraper card's preview button is visible, indicating the card is displayed."
        await page.locator("xpath=/html/body/div[1]/div[3]/main/section[1]/div[3]/div[5]/div[2]/div[2]/button[1]").nth(0).scroll_into_view_if_needed()
        # Assert: Fifth scraper card's preview button is visible, indicating the card is displayed.
        await expect(page.locator("xpath=/html/body/div[1]/div[3]/main/section[1]/div[3]/div[5]/div[2]/div[2]/button[1]").nth(0)).to_be_visible(timeout=15000), "Fifth scraper card's preview button is visible, indicating the card is displayed."
        await page.locator("xpath=/html/body/div[1]/div[3]/main/section[1]/div[3]/div[6]/div[2]/div[2]/button[1]").nth(0).scroll_into_view_if_needed()
        # Assert: Sixth scraper card's preview button is visible, indicating the card is displayed.
        await expect(page.locator("xpath=/html/body/div[1]/div[3]/main/section[1]/div[3]/div[6]/div[2]/div[2]/button[1]").nth(0)).to_be_visible(timeout=15000), "Sixth scraper card's preview button is visible, indicating the card is displayed."
        await page.locator("xpath=/html/body/div[1]/div[3]/main/section[1]/div[3]/div[7]/div[2]/div[2]/button[1]").nth(0).scroll_into_view_if_needed()
        # Assert: Seventh scraper card's preview button is visible, indicating the card is displayed.
        await expect(page.locator("xpath=/html/body/div[1]/div[3]/main/section[1]/div[3]/div[7]/div[2]/div[2]/button[1]").nth(0)).to_be_visible(timeout=15000), "Seventh scraper card's preview button is visible, indicating the card is displayed."
        await page.locator("xpath=/html/body/div[1]/div[3]/main/section[1]/div[3]/div[8]/div[2]/div[2]/button[1]").nth(0).scroll_into_view_if_needed()
        # Assert: Eighth scraper card's preview button is visible, indicating the card is displayed.
        await expect(page.locator("xpath=/html/body/div[1]/div[3]/main/section[1]/div[3]/div[8]/div[2]/div[2]/button[1]").nth(0)).to_be_visible(timeout=15000), "Eighth scraper card's preview button is visible, indicating the card is displayed."
        
        # --> Verify the main dashboard tabs are displayed
        await page.locator("xpath=/html/body/div[1]/nav/button[1]").nth(0).scroll_into_view_if_needed()
        # Assert: The 'Extracción' main dashboard tab is visible.
        await expect(page.locator("xpath=/html/body/div[1]/nav/button[1]").nth(0)).to_be_visible(timeout=15000), "The 'Extracción' main dashboard tab is visible."
        await page.locator("xpath=/html/body/div[1]/nav/button[2]").nth(0).scroll_into_view_if_needed()
        # Assert: The '📊 Historial' main dashboard tab is visible.
        await expect(page.locator("xpath=/html/body/div[1]/nav/button[2]").nth(0)).to_be_visible(timeout=15000), "The '\ud83d\udcca Historial' main dashboard tab is visible."
        await page.locator("xpath=/html/body/div[1]/nav/button[3]").nth(0).scroll_into_view_if_needed()
        # Assert: The '⚙️ Configuración' main dashboard tab is visible.
        await expect(page.locator("xpath=/html/body/div[1]/nav/button[3]").nth(0)).to_be_visible(timeout=15000), "The '\u2699\ufe0f Configuraci\u00f3n' main dashboard tab is visible."
        await page.locator("xpath=/html/body/div[1]/nav/button[4]").nth(0).scroll_into_view_if_needed()
        # Assert: The '⏰ Programador' main dashboard tab is visible.
        await expect(page.locator("xpath=/html/body/div[1]/nav/button[4]").nth(0)).to_be_visible(timeout=15000), "The '\u23f0 Programador' main dashboard tab is visible."
        await asyncio.sleep(5)

    finally:
        if context:
            await context.close()
        if browser:
            await browser.close()
        if pw:
            await pw.stop()

asyncio.run(run_test())
    