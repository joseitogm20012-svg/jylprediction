"""Find Transfermarkt IDs for all 48 WC teams via HTTP"""
import requests, time, json, re
from pathlib import Path

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
}

TEAMS = [
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

# Known: arg=3437, bra=3439. Try a range for each team
found = {}

for slug in TEAMS:
    print("Searching %s..." % slug, end=" ")
    found_id = None
    for tid in range(3370, 3600):
        url = "https://www.transfermarkt.com/%s/startseite/verein/%d" % (slug, tid)
        try:
            r = requests.get(url, headers=HEADERS, timeout=8, allow_redirects=False)
            if r.status_code == 200:
                # Check if the page title contains the team name
                title_match = re.search(r'<title>(.*?)</title>', r.text, re.IGNORECASE)
                if title_match:
                    title = title_match.group(1)
                    if "error" not in title.lower() and "404" not in title:
                        found_id = tid
                        print("ID=%d [%s]" % (tid, title[:50]))
                        break
        except:
            pass
        if tid % 20 == 0:
            time.sleep(0.05)
    
    if found_id:
        found[slug] = found_id
    else:
        print("NOT FOUND")
    
    time.sleep(0.3)

print("\n\n=== RESULTS ===")
print(json.dumps(found, indent=2))
Path("tm_ids.json").write_text(json.dumps(found, indent=2), encoding="utf-8")
