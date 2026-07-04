import json, openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from pathlib import Path

# Load data
data_path = Path("C:/Users/Equipo/Desktop/predecirv2/data/corners_stats.json")
with open(data_path) as f:
    data = json.load(f)

# Build rows sorted by corners_for descending
rows = []
for team, stats in sorted(data.items(), key=lambda x: x[1].get("corners_for", 0), reverse=True):
    cf = stats.get("corners_for", 0)
    ca = stats.get("corners_against", 0)
    games = stats.get("games", 0)
    rows.append({
        "team": team.replace("-", " ").title(),
        "corners_for": cf,
        "corners_against": ca,
        "total": round(cf + ca, 2),
        "games": games,
        "per_game": round((cf + ca) / max(games, 1), 2),
    })

# Create Excel workbook
wb = openpyxl.Workbook()
ws = wb.active
ws.title = "Corners Stats WC2026"

# Header styles
header_font = Font(bold=True, size=11, color="FFFFFF")
header_fill = PatternFill(start_color="2F5496", end_color="2F5496", fill_type="solid")
header_alignment = Alignment(horizontal="center", vertical="center")
thin_border = Border(
    left=Side(style="thin"), right=Side(style="thin"),
    top=Side(style="thin"), bottom=Side(style="thin"),
)
warn_fill = PatternFill(start_color="FFF2CC", end_color="FFF2CC", fill_type="solid")

# Write headers
headers = ["Equipo", "Corners A Favor", "Corners En Contra", "Total Corners", "Partidos", "Corners/Partido"]
for col, h in enumerate(headers, 1):
    cell = ws.cell(row=1, column=col, value=h)
    cell.font = header_font
    cell.fill = header_fill
    cell.alignment = header_alignment
    cell.border = thin_border

# Write data rows
for i, row in enumerate(rows, 2):
    ws.cell(row=i, column=1, value=row["team"]).border = thin_border
    ws.cell(row=i, column=2, value=row["corners_for"]).border = thin_border
    ws.cell(row=i, column=3, value=row["corners_against"]).border = thin_border
    ws.cell(row=i, column=4, value=row["total"]).border = thin_border
    ws.cell(row=i, column=5, value=row["games"]).border = thin_border
    ws.cell(row=i, column=6, value=row["per_game"]).border = thin_border

    # Highlight rows with only 1 game (unreliable data)
    if row["games"] == 1:
        for col in range(1, 7):
            ws.cell(row=i, column=col).fill = warn_fill

# Column widths
ws.column_dimensions["A"].width = 18
ws.column_dimensions["B"].width = 16
ws.column_dimensions["C"].width = 16
ws.column_dimensions["D"].width = 14
ws.column_dimensions["E"].width = 10
ws.column_dimensions["F"].width = 14

# Freeze header row + auto-filter
ws.freeze_panes = "A2"
ws.auto_filter.ref = f"A1:F{len(rows)+1}"

# Second sheet: summary
ws2 = wb.create_sheet("Resumen")
ws2["A1"] = "Resumen de Corners - Mundial 2026"
ws2["A1"].font = Font(bold=True, size=14)
ws2["A3"] = f"Total equipos: {len(rows)}"
ws2["A4"] = f"Promedio corners a favor: {round(sum(r['corners_for'] for r in rows)/len(rows), 2)}"
ws2["A5"] = f"Promedio corners en contra: {round(sum(r['corners_against'] for r in rows)/len(rows), 2)}"
ws2["A6"] = "Fuente: corners_stats.json (FBref + datos historicos)"
ws2["A8"] = f"Equipos con solo 1 partido (datos poco fiables): {sum(1 for r in rows if r['games'] == 1)}"
ws2["A9"] = "Filas amarillas en la hoja principal = equipos con 1 solo partido"
ws2["A11"] = "NOTA: El scraper hibrido (Soccerway + FlashScore) actualizara per_match_corners.json"
ws2["A12"] = "      que el predictor usara como fuente principal cuando tenga datos reales."
ws2.column_dimensions["A"].width = 70

# Save to desktop
desktop = Path.home() / "Desktop" / "corners_wc2026.xlsx"
wb.save(str(desktop))
print(f"Excel saved to {desktop}")
print(f"Total teams: {len(rows)}")
print(f"Teams with only 1 game: {sum(1 for r in rows if r['games'] == 1)}")