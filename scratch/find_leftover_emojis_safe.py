import sys

def find_emojis(filename, out):
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    out.write(f"\n--- Emojis in {filename} ---\n")
    lines = content.split('\n')
    found_any = False
    for idx, line in enumerate(lines):
        for char in line:
            codepoint = ord(char)
            # Unicode ranges for emojis, flags, symbols
            if 0x1F000 <= codepoint <= 0x1FFFF or 0x2600 <= codepoint <= 0x27FF or codepoint > 0x1F600:
                out.write(f"Line {idx+1}: {char} (U+{codepoint:X}) -> {line.strip()}\n")
                found_any = True
                break
    if not found_any:
        out.write("None found.\n")

with open("C:/Users/Equipo/Desktop/predecirv2/scratch/emoji_results.txt", "w", encoding="utf-8") as out:
    find_emojis("C:/Users/Equipo/Desktop/predecirv2/app.js", out)
    find_emojis("C:/Users/Equipo/Desktop/predecirv2/index.html", out)

print("Saved results to scratch/emoji_results.txt")
