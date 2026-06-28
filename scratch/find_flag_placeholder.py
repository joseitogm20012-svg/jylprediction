with open("C:/Users/Equipo/Desktop/predecirv2/index.css", "r", encoding="utf-8") as f:
    content = f.read()

import re
matches = [line for line in content.split("\n") if "team-flag-placeholder" in line]
print(f"Matches: {len(matches)}")
for m in matches:
    print(m)
