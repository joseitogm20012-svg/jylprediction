import requests
import json

urls = [
    "https://cup26matches.com/data/wc2026-results.json",
    "https://cup26matches.com/data/results.json",
    "https://cup26matches.com/data/results.csv",
    "https://cup26matches.com/data/probabilities.json"
]

for url in urls:
    try:
        print(f"Checking {url}...")
        r = requests.get(url, timeout=5)
        print(f"  Status: {r.status_code}")
        if r.status_code == 200:
            print(f"  Length: {len(r.text)}")
            if url.endswith(".json"):
                data = r.json()
                if "matches" in data:
                    print(f"  Found {len(data['matches'])} matches in json")
                    print("  Sample:", data["matches"][-2:])
                else:
                    print("  Keys:", list(data.keys())[:5])
    except Exception as e:
        print(f"  Error: {e}")
