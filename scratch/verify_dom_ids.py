import re

# Read app.js to find all document.getElementById calls
with open("C:/Users/Equipo/Desktop/predecirv2/app.js", "r", encoding="utf-8") as f:
    js_content = f.read()

# Find all occurrences of document.getElementById("...") or document.getElementById('...')
js_ids = set(re.findall(r'document\.getElementById\([\'"]([a-zA-Z0-9_-]+)[\'"]\)', js_content))

# Read index.html to find all IDs defined
with open("C:/Users/Equipo/Desktop/predecirv2/index.html", "r", encoding="utf-8") as f:
    html_content = f.read()

# Find all occurrences of id="..." or id='...'
html_ids = set(re.findall(r'\bid\s*=\s*[\'"]([a-zA-Z0-9_-]+)[\'"]', html_content))

print(f"Total IDs in app.js: {len(js_ids)}")
print(f"Total IDs in index.html: {len(html_ids)}")

print("\n--- IDs in app.js but MISSING in index.html ---")
missing_in_html = js_ids - html_ids
for mid in sorted(missing_in_html):
    print(mid)

print("\n--- IDs in index.html but NOT queried in app.js ---")
not_queried = html_ids - js_ids
for nid in sorted(not_queried):
    print(nid)
