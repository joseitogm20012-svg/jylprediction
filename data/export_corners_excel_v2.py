import json
import os
import pandas as pd
from pathlib import Path
from datetime import datetime

# Paths
PROJECT_DIR = Path(__file__).resolve().parent.parent
CORNERS_JSON_PATH = PROJECT_DIR / "data" / "corners_stats.json"
OUTPUT_PATH = Path(os.environ.get("USERPROFILE", "C:/Users/Equipo")) / "Desktop" / "corners_stats_2026.xlsx"

def main():
    if not CORNERS_JSON_PATH.exists():
        print(f"Error: {CORNERS_JSON_PATH} not found")
        return

    with open(CORNERS_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    rows = []
    for slug, stats in data.items():
        if slug == "_meta":
            continue
        
        overall_for = stats.get("corners_for", "N/A")
        overall_against = stats.get("corners_against", "N/A")
        
        sh = stats.get("second_half", {})
        sh_overall = sh.get("overall", {})
        sh_home = sh.get("home", {})
        sh_away = sh.get("away", {})
        
        rows.append({
            "Equipo": slug.replace("-", " ").title(),
            "AVG Corners (Full)": overall_for,
            "AVG Conceded (Full)": overall_against,
            "SH Avg Taken (Overall)": sh_overall.get("taken", "N/A"),
            "SH Avg Conceded (Overall)": sh_overall.get("conceded", "N/A"),
            "SH Avg Taken (Home)": sh_home.get("taken", "N/A"),
            "SH Avg Conceded (Home)": sh_home.get("conceded", "N/A"),
            "SH Avg Taken (Away)": sh_away.get("taken", "N/A"),
            "SH Avg Conceded (Away)": sh_away.get("conceded", "N/A"),
            "SH Over 3.5 (%)": sh_overall.get("over35", "N/A"),
            "SH Over 4.5 (%)": sh_overall.get("over45", "N/A"),
            "SH Over 5.5 (%)": sh_overall.get("over55", "N/A"),
            "Games": stats.get("games", "N/A"),
            "Source": stats.get("_source", "mixed")
        })

    df = pd.DataFrame(rows)
    
    if "AVG Corners (Full)" in df.columns:
        df["AVG Corners (Full)"] = pd.to_numeric(df["AVG Corners (Full)"], errors='coerce')
        df = df.sort_values(by="AVG Corners (Full)", ascending=False, na_position='last')

    try:
        df.to_excel(OUTPUT_PATH, index=False, sheet_name="Corner Stats 2026")
        print(f"Successfully exported to: {OUTPUT_PATH}")
    except Exception as e:
        print(f"Error exporting to Excel: {e}")

if __name__ == "__main__":
    main()
