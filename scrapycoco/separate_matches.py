"""
Separate WC2026 matches from friendlies.
- Moves pre-tournament matches (before June 11, 2026) to /amistosos/
- Keeps WC matches (June 11 - July 19, 2026) in main folder
"""
import json, re, shutil
from pathlib import Path
from datetime import datetime, date

SRC = Path("C:/Users/Equipo/Desktop/mundial104")
DST_AMISTOSOS = SRC / "amistosos"
DST_AMISTOSOS.mkdir(exist_ok=True)

WC_START = date(2026, 6, 11)
WC_END = date(2026, 7, 19)

def parse_date_from_desc(desc):
    m = re.search(r'(\d{2})\.(\d{2})\.(\d{4})', desc)
    if m:
        try:
            return date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
        except: pass
    m2 = re.search(r'(\d{2})\.(\d{2})\.\s', desc)
    if m2:
        try:
            return date(2026, int(m2.group(2)), int(m2.group(1)))
        except: pass
    return None

n_total = 0
n_wc = 0
n_amistosos = 0
n_unknown = 0

for fp in sorted(SRC.glob("[A-Za-z0-9][A-Za-z0-9][A-Za-z0-9][A-Za-z0-9][A-Za-z0-9][A-Za-z0-9][A-Za-z0-9][A-Za-z0-9].json")):
    n_total += 1
    with open(fp, encoding="utf-8") as f:
        data = json.load(f)
    desc = data.get("description", "")
    score = (data.get("score") or "").strip()
    dt = parse_date_from_desc(desc)

    if dt:
        if dt < WC_START or dt > WC_END:
            kind = "amistoso"
            n_amistosos += 1
        else:
            kind = "mundial"
            n_wc += 1
    else:
        # If no date found, check if it has a score (played match)
        if score and score != "-":
            kind = "mundial (sin fecha)"  # probably WC
            n_wc += 1
        else:
            kind = "desconocido"
            n_unknown += 1

    if kind.startswith("amistoso") or kind == "desconocido":
        mid = fp.stem
        # Move json
        shutil.move(str(fp), str(DST_AMISTOSOS / fp.name))
        # Move csv
        csv_fp = SRC / (mid + ".csv")
        if csv_fp.exists():
            shutil.move(str(csv_fp), str(DST_AMISTOSOS / csv_fp.name))
        print("  %s -> amistosos/  (%s)" % (mid, desc.replace(",",";")[:50]))

print("\n" + "=" * 50)
print("RESUMEN")
print("=" * 50)
print("Total procesados: %d" % n_total)
print("Mundial:   %d" % n_wc)
print("Amistosos: %d" % n_amistosos)
print("Unknown:   %d" % n_unknown)
print("")
print("Archivos en amistosos/: %d" % len(list(DST_AMISTOSOS.glob("*.json"))))
print("Archivos en mundial104/: %d" % len(list(SRC.glob("[A-Za-z0-9][A-Za-z0-9][A-Za-z0-9][A-Za-z0-9][A-Za-z0-9][A-Za-z0-9][A-Za-z0-9][A-Za-z0-9].json"))))
