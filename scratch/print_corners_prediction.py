with open("C:/Users/Equipo/Desktop/predecirv2/predictor.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    if "corners_prediction = {" in line:
        for i in range(idx - 10, min(idx + 40, len(lines))):
            print(f"{i+1}: {lines[i]}", end="")
        break
