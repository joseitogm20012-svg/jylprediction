with open("C:/Users/Equipo/Desktop/predecirv2/index.css", "r", encoding="utf-8") as f:
    content = f.read()

selectors = [".config-bar", ".results-tabs-panel", ".probability-gauges", ".comparative-bar-row", ".comp-bar"]
for s in selectors:
    matches = [line for line in content.split("\n") if s in line]
    print(f"Selector '{s}': {len(matches)} matches")
    for m in matches[:5]:
        print(f"  {m}")
