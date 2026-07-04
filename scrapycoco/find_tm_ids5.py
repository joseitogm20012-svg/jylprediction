"""Find specific TM IDs for WC teams - targeted HTTP"""
import requests, time, json, re

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
}

# Known IDs from earlier tests
KNOWN = {
    "argentina": 3437,
    "brazil": 3439,
    "denmark": 3436,
    "serbia": 3438,
    "poland": 3442,
    "nigeria": 3444,
    "czech-republic": 3445,
    "uruguay": 3449,
}

WC_SLUGS = [
    "argentina", "brazil", "australia", "cameroon",
    "spain", "nigeria", "usa", "saudi-arabia",
    "poland", "south-korea", "egypt",
    "france", "denmark", "tunisia", "canada",
    "england", "serbia", "iran", "jamaica",
    "portugal", "morocco", "paraguay", "new-zealand",
    "belgium", "croatia", "ecuador", "costa-rica",
    "netherlands", "senegal", "qatar", "panama",
    "italy", "colombia", "japan", "algeria",
    "mexico", "switzerland", "greece", "bolivia",
    "uruguay", "south-africa", "chile", "honduras",
    "czech-republic", "turkey", "guatemala", "indonesia",
    "germany",
]

def get_team_name_from_page(html):
    """Extract the display team name from TM page"""
    m = re.search(r'<span class="data-header__flag">.*?<img[^>]*alt="([^"]*)"', html, re.DOTALL)
    if m:
        return m.group(1).strip()
    m = re.search(r'data-header__headline.*?<span[^>]*>(.*?)</span>', html, re.DOTALL)
    if m:
        return m.group(1).strip()
    return None

# Check IDs from 3436 to 3600 to find all national teams
# Skip known ones
found = dict(KNOWN)

for tid in range(3451, 3600):
    if tid == 3437 or tid == 3439:
        continue
    
    try:
        r = requests.get("https://www.transfermarkt.com/argentina/startseite/verein/%d" % tid, 
                        headers=HEADERS, timeout=10)
        if r.status_code == 200:
            name = get_team_name_from_page(r.text)
            if name and "Club profile" in r.text and "error" not in r.text:
                # It's a valid team
                name_clean = name.strip()
                found[name_clean] = tid
                print("ID %d: %s" % (tid, name_clean))
    except Exception as e:
        print("  ID %d: error %s" % (tid, str(e)[:30]))
    
    time.sleep(0.5)  # Rate limit
    
    if tid % 50 == 0:
        print("  ... at ID %d, found %d teams total" % (tid, len(found)))

print("\n\n=== ALL NATIONAL TEAMS ===")
for name in sorted(found.keys()):
    print("%s: %d" % (name, found[name]))

# Map WC slugs to TM names
slug_to_tm = {}
for slug in WC_SLUGS:
    display = slug.replace("-", " ").title()
    # Find in found map
    for tm_name, tid in found.items():
        if display.lower() in tm_name.lower() or tm_name.lower().startswith(display.lower()):
            slug_to_tm[slug] = {"tm_id": tid, "tm_name": tm_name}
            break
    if slug not in slug_to_tm:
        print("NOT FOUND: %s (%s)" % (slug, display))

print("\n\n=== WC SLUG MAPPING ===")
for slug in sorted(slug_to_tm.keys()):
    info = slug_to_tm[slug]
    print("%s: %d [%s]" % (slug, info["tm_id"], info["tm_name"]))

json.dump({"ids": found, "wc_map": slug_to_tm}, 
          open("tm_national_ids.json", "w", encoding="utf-8"), 
          ensure_ascii=False, indent=2)
