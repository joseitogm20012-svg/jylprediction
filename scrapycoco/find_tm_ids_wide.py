"""Find remaining national team IDs in wider range"""
import requests, json, re, concurrent.futures

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"}

# Known from earlier scan (3262-3600)
found = {name: tid for name, tid in {
    "Germany": 3262, "England": 3299, "Portugal": 3300,
    "Spain": 3375, "Italy": 3376, "France": 3377, "Greece": 3378,
    "Netherlands": 3379, "Scotland": 3380, "Turkiye": 3381,
    "Belgium": 3382, "Austria": 3383, "Switzerland": 3384, "Bulgaria": 3394,
    "Kuwait": 3432, "Australia": 3433, "Cameroon": 3434, "Japan": 3435,
    "Denmark": 3436, "Argentina": 3437, "Serbia": 3438, "Brazil": 3439,
    "Norway": 3440, "Ghana": 3441, "Poland": 3442, "Finland": 3443,
    "Nigeria": 3444, "Czechia": 3445, "Bosnia-Herzegovina": 3446,
    "Romania": 3447, "Russia": 3448, "Uruguay": 3449, "Belarus": 3450,
    "Hungary": 3468, "Senegal": 3499, "Slovakia": 3503, "Venezuela": 3504,
    "United States": 3505, "Republic of Ireland": 3509, "Canada": 3510,
    "Latvia": 3555, "Croatia": 3556, "Sweden": 3557, "Iraq": 3560,
    "Albania": 3561, "Seychelles": 3562, "Uzbekistan": 3563,
    "Namibia": 3573, "Iceland": 3574, "Morocco": 3575, "Afghanistan": 3576,
    "Panama": 3577, "Luxembourg": 3580, "Paraguay": 3581, "Iran": 3582,
    "Zimbabwe": 3583, "Peru": 3584, "Angola": 3585, "Lebanon": 3586,
    "Malta": 3587, "Slovenia": 3588, "South Korea": 3589,
    "Honduras": 3590, "Ivory Coast": 3591,
}.items()}

# Check additional ranges
new_ranges = list(range(3601, 4400)) + list(range(5700, 6400))

def check_id(tid):
    try:
        r = requests.get("https://www.transfermarkt.com/argentina/startseite/verein/%d" % tid, headers=HEADERS, timeout=12)
        if r.status_code != 200 or "Club profile" not in r.text:
            return None
        m = re.search(r'<span class="data-header__flag">.*?<img[^>]*alt="([^"]*)"', r.text, re.DOTALL)
        if m:
            return (tid, m.group(1).strip())
    except: pass
    return None

print("Scanning %d IDs..." % len(new_ranges))
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
    futures = {ex.submit(check_id, tid): tid for tid in new_ranges}
    done = 0
    for f in concurrent.futures.as_completed(futures):
        done += 1
        r = f.result()
        if r:
            tid, name = r
            if name not in found:
                found[name] = tid
                print("ID %d: %s" % (tid, name))
        if done % 200 == 0:
            print("  ... %d/%d checked, %d teams" % (done, len(new_ranges), len(found)))

print("\n=== TOTAL: %d TEAMS ===" % len(found))
json.dump(found, open("tm_national_ids_wide.json", "w", encoding="utf-8"), ensure_ascii=False, indent=2)
