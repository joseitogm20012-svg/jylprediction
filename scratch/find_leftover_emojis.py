import sys

def find_emojis(filename):
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(f"\n--- Emojis in {filename} ---")
    lines = content.split('\n')
    found_any = False
    for idx, line in enumerate(lines):
        # Scan characters
        for char in line:
            # Emoji ranges
            codepoint = ord(char)
            # High-value unicode characters (emojis, flags, etc.)
            if 0x1F000 <= codepoint <= 0x1FFFF or 0x2600 <= codepoint <= 0x27FF or codepoint > 0x1F600:
                print(f"Line {idx+1}: {char} -> {line.strip()}")
                found_any = True
                break
    if not found_any:
        print("None found.")

find_emojis("C:/Users/Equipo/Desktop/predecirv2/app.js")
find_emojis("C:/Users/Equipo/Desktop/predecirv2/index.html")
