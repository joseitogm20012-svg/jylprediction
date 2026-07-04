"""Find ALL national team IDs via concurrent HTTP requests"""
import requests, json, re, concurrent.futures, time
from pathlib import Path

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
}

# Known IDs to confirm
KNOWN_IDS = list(range(3262, 3601))

def check_id(tid):
    try:
        r = requests.get(
            "https://www.transfermarkt.com/argentina/startseite/verein/%d" % tid,
            headers=HEADERS,
            timeout=15
        )
        if r.status_code != 200:
            return None
        # Check if it's a valid team page (contains "Club profile" or "Vereinsprofil")
        if "Club profile" not in r.text and "Vereinsprofil" not in r.text:
            return None
        # Extract team name from h1 or data-header flag
        m = re.search(r'<span class="data-header__flag">.*?<img[^>]*alt="([^"]*)"', r.text, re.DOTALL)
        if m:
            name = m.group(1).strip()
            return (tid, name)
    except:
        pass
    return None

def main():
    print("Checking IDs 3262-3600 for national teams...")
    found = {}
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        futures = {executor.submit(check_id, tid): tid for tid in KNOWN_IDS}
        done = 0
        for future in concurrent.futures.as_completed(futures):
            done += 1
            result = future.result()
            if result:
                tid, name = result
                found[name] = tid
                print("ID %d: %s" % (tid, name))
            if done % 50 == 0:
                print("  ... checked %d/%d, found %d" % (done, len(KNOWN_IDS), len(found)))
    
    print("\n=== ALL NATIONAL TEAMS FOUND (%d) ===" % len(found))
    for name in sorted(found.keys()):
        print("  %s: %d" % (name, found[name]))
    
    Path("tm_all_national_ids.json").write_text(
        json.dumps(found, ensure_ascii=False, indent=2), 
        encoding="utf-8"
    )

if __name__ == "__main__":
    main()
