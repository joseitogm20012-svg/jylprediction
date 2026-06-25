with open("C:/Users/Equipo/Desktop/predecirv2/index.html", "r", encoding="utf-8") as f:
    content = f.read()

import re
m_open = len(re.findall(r'<main\b', content, re.I))
m_close = len(re.findall(r'</main\b', content, re.I))
print(f"<main> count: {m_open}")
print(f"</main> count: {m_close}")
