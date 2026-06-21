with open("C:/Users/Equipo/Desktop/predecirv2/predictor.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

for i in range(760, min(801, len(lines))):
    print(f"{i+1}: {lines[i]}", end="")
