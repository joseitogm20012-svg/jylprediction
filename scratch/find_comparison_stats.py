import re

with open("C:/Users/Equipo/Desktop/predecirv2/predictor.py", "r", encoding="utf-8") as f:
    python_content = f.read()

# Let's search for comparisonStats in predictor.py
matches = [line for line in python_content.split("\n") if "comparisonStats" in line or "comparison_stats" in line]
print("Matches in predictor.py:")
for m in matches:
    print(m)

with open("C:/Users/Equipo/Desktop/predecirv2/main.py", "r", encoding="utf-8") as f:
    main_content = f.read()

matches_main = [line for line in main_content.split("\n") if "comparisonStats" in line or "comparison_stats" in line]
print("\nMatches in main.py:")
for m in matches_main:
    print(m)
