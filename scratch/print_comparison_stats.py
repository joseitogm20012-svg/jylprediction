with open("C:/Users/Equipo/Desktop/predecirv2/predictor.py", "r", encoding="utf-8") as f:
    lines = f.readlines()

for idx, line in enumerate(lines):
    if "comparison_stats = {" in line:
        # print 30 lines starting from here
        for i in range(idx, min(idx + 50, len(lines))):
            print(f"{i+1}: {lines[i]}", end="")
        break
