with open("C:/Users/Equipo/Desktop/predecirv2/index.css", "r", encoding="utf-8") as f:
    content = f.read()

import re
matches = [line for line in content.split("\n") if ".tab-" in line or "tab-btn" in line]
print(f"Tab-related style lines: {len(matches)}")
for m in matches[:10]:
    print(m)
