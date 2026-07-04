"""Find Sofascore Team IDs"""
from playwright.sync_api import sync_playwright

teams = [
    "Argentina", "Brazil", "France", "Spain", "England", "Portugal", 
    "Netherlands", "Germany", "Belgium", "Italy", "Colombia", "Croatia", 
    "Morocco", "United States", "Mexico", "Canada"
]
results = {}

def find_ids():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        for team in teams:
            try:
                print(f"Searching for {team}...")
                page.goto(f"https://www.sofascore.com/search?q={team}")
                # Wait for the search results to load
                page.wait_for_selector('a[href*="/team/"]', timeout=5000)
                link = page.query_selector('a[href*="/team/"]')
                if link:
                    href = link.get_attribute('href')
                    team_id = href.split("/team/")[1].split("/")[0]
                    results[team] = team_id
                    print(f"  Found: {team} -> {team_id}")
                else:
                    print(f"  Not found: {team}")
            except Exception as e:
                print(f"  Error searching {team}: {e}")
        browser.close()

if __name__ == "__main__":
    find_ids()
    print("\nMapping found:")
    print(results)
