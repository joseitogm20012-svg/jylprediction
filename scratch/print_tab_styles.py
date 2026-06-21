with open("C:/Users/Equipo/Desktop/predecirv2/index.css", "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    if ".tab-header {" in line:
        for i in range(idx, min(idx + 45, len(lines))):
            print(f"{i+1}: {lines[i]}", end="")
        break
