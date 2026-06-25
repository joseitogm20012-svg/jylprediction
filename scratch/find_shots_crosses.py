with open("C:/Users/Equipo/Desktop/predecirv2/predictor.py", "r", encoding="utf-8") as f:
    content = f.read()

keywords = ["shots", "crosses", "tiros", "centros"]
for kw in keywords:
    matches = [line for line in content.split("\n") if kw in line]
    print(f"Matches for '{kw}': {len(matches)}")
    for m in matches[:5]:
        print(f"  {m}")
