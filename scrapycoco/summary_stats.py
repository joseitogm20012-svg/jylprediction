"""Generate final summary of all scraped matches"""
import json
from pathlib import Path

OUT_DIR = Path("C:/Users/Equipo/Desktop/mundial104")

def main():
    all_data = []
    for fp in sorted(OUT_DIR.glob("[A-Za-z0-9][A-Za-z0-9][A-Za-z0-9][A-Za-z0-9][A-Za-z0-9][A-Za-z0-9][A-Za-z0-9][A-Za-z0-9].json")):
        with open(fp, encoding="utf-8") as f:
            d = json.load(f)
        if d.get("error") and d["error"] != "No es Mundial":
            continue
        all_data.append(d)

    n_total = len(all_data)
    n_with_stats = sum(1 for d in all_data if len(d.get("estadisticas", {})) > 0)
    n_with_lineups = sum(1 for d in all_data if len(d.get("alineaciones", {}).get("local", {}).get("titulares", [])) > 0)
    n_with_both = sum(1 for d in all_data if len(d.get("estadisticas", {})) > 0 and len(d.get("alineaciones", {}).get("local", {}).get("titulares", [])) > 0)
    n_no_score = sum(1 for d in all_data if not d.get("score") or d["score"].strip() == "-" or d["score"].strip() == "")

    total_stats = sum(len(d.get("estadisticas", {})) for d in all_data)
    total_starters = sum(len(d.get("alineaciones", {}).get("local", {}).get("titulares", [])) + len(d.get("alineaciones", {}).get("visitante", {}).get("titulares", [])) for d in all_data)
    total_subs = sum(len(d.get("alineaciones", {}).get("local", {}).get("suplentes", [])) + len(d.get("alineaciones", {}).get("visitante", {}).get("suplentes", [])) for d in all_data)

    print("=" * 60)
    print("RESUMEN FINAL - SCRAPEO MUNDIAL 2026")
    print("=" * 60)
    print("Total partidos:     %d" % n_total)
    print("Con estadisticas:   %d (%.0f%%)" % (n_with_stats, n_with_stats/n_total*100))
    print("Con alineaciones:   %d (%.0f%%)" % (n_with_lineups, n_with_lineups/n_total*100))
    print("Con ambos:          %d (%.0f%%)" % (n_with_both, n_with_both/n_total*100))
    print("Sin resultado:      %d" % n_no_score)
    print("")
    print("Promedio stats:     %.1f" % (total_stats / n_with_stats if n_with_stats else 0))
    print("Promedio titulares: %.1f" % (total_starters / n_with_lineups if n_with_lineups else 0))
    print("Promedio suplentes: %.1f" % (total_subs / n_with_lineups if n_with_lineups else 0))
    print("")
    print("Archivos en %s:" % OUT_DIR)
    print("  %d JSON con datos de partidos" % n_total)
    print("  %d CSV con datos tabulares" % len(list(OUT_DIR.glob("*.csv"))))
    print("=" * 60)

    # Save master summary CSV
    with open(OUT_DIR / "00_resumen_mundial2026.csv", "w", encoding="utf-8-sig") as f:
        f.write("match_id,description,score,n_stats,has_lineups\n")
        for d in sorted(all_data, key=lambda x: x.get("match_id", "")):
            mid = d.get("match_id", "")
            desc = d.get("description", "").replace(",", ";")
            score = d.get("score", "").replace(",", ";")
            n_s = len(d.get("estadisticas", {}))
            al = d.get("alineaciones", {})
            has_lu = "SI" if al.get("local", {}).get("titulares") else "NO"
            f.write("%s,%s,%s,%d,%s\n" % (mid, desc, score, n_s, has_lu))

    print("Resumen guardado en 00_resumen_mundial2026.csv")

if __name__ == "__main__":
    main()
