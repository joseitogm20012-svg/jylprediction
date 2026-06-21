with open("C:/Users/Equipo/Desktop/predecirv2/index.css", "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    if ".team-flag-placeholder {" in line:
        for i in range(idx, min(idx + 20, len(lines))):
            print(f"{i+1}: {lines[i]}", end="")
        break
