import sys, os, subprocess, json
from pathlib import Path

BASE = Path(__file__).parent
SCRIPTS = [
    ("shooting", BASE / "data" / "fetch_fbref_shooting.py"),
    ("passing", BASE / "data" / "fetch_fbref_passing.py"),
    ("keepers", BASE / "data" / "fetch_fbref_keepers.py"),
    ("corners", BASE / "data" / "fetch_fbref_corners.py"),
]
PLAYER_STATS = BASE / "data" / "player_stats.json"
XG_DATA = BASE / "data" / "xg_by_team.json"

for name, script_path in SCRIPTS:
    print(f"\n{'='*60}")
    print(f"  Running {name}...")
    print(f"{'='*60}")
    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=180
    )
    print(result.stdout[-500:] if len(result.stdout) > 500 else result.stdout)
    if result.stderr:
        print(f"  STDERR: {result.stderr[-300:]}")
    print(f"  Exit code: {result.returncode}")

# Verify output files
print(f"\n{'='*60}")
print("  VERIFYING OUTPUTS")
print(f"{'='*60}")

if PLAYER_STATS.exists():
    data = json.loads(PLAYER_STATS.read_text(encoding="utf-8"))
    total_players = sum(len(v.get("shooting", [])) for v in data.values())
    total_passing = sum(len(v.get("passing", [])) for v in data.values())
    total_keepers = sum(len(v.get("keepers", [])) for v in data.values())
    teams = list(data.keys())
    print(f"player_stats.json: {len(teams)} teams")
    print(f"  shooting players: {total_players}")
    if teams:
        sample = data[teams[0]]
        print(f"  Sample team '{teams[0]}': keys={list(sample.keys())}")
        if "shooting" in sample and sample["shooting"]:
            print(f"    First shooter: {sample['shooting'][0]}")
        if "passing" in sample and sample["passing"]:
            print(f"    First passer: {sample['passing'][0]}")
        if "keepers" in sample and sample["keepers"]:
            print(f"    First keeper: {sample['keepers'][0]}")
else:
    print(f"  MISSING: {PLAYER_STATS}")

if XG_DATA.exists():
    xg = json.loads(XG_DATA.read_text(encoding="utf-8"))
    teams_with_corners = [s for s, d in xg.items() if "corners_per_90" in d]
    print(f"\nxg_by_team.json: {len(teams_with_corners)}/{len(xg)} teams with corners_per_90")
    if teams_with_corners:
        print(f"  Sample: {teams_with_corners[0]} -> {xg[teams_with_corners[0]].get('corners_per_90')}")

print(f"\n{'='*60}")
print("  DONE")
print(f"{'='*60}")
