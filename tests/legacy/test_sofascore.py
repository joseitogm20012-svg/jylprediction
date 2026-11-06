"""Test script for SofascoreScraper"""
import sys
import os
from pathlib import Path

# Add scrapycoco to path
sys.path.append(os.path.join(os.getcwd(), "scrapycoco"))

try:
    from scrapers.sofascore import SofascoreScraper
    print("Imported SofascoreScraper successfully")
    
    scraper = SofascoreScraper()
    print("Running scraper...")
    scraper.run()
    print("Scraper run finished.")
    
    # Verify files
    raw_dir = Path("data/raw")
    player_stats = raw_dir / "player_stats.json"
    xg_team = raw_dir / "xg_by_team.json"
    
    if player_stats.exists():
        print(f"player_stats.json exists: {player_stats.stat().st_size} bytes")
    else:
        print("player_stats.json MISSING")
        
    if xg_team.exists():
        print(f"xg_by_team.json exists: {xg_team.stat().st_size} bytes")
    else:
        print("xg_by_team.json MISSING")

except Exception as e:
    print(f"Error during test: {e}")
    import traceback
    traceback.print_exc()
