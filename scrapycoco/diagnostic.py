import hashlib
import json
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional
from bs4 import BeautifulSoup


@dataclass
class SelectorInfo:
    tag: str
    class_list: list[str]
    id_value: Optional[str]
    text_sample: Optional[str]
    count: int


@dataclass
class StructureSnapshot:
    url: str
    timestamp: str
    selectors: dict[str, list[SelectorInfo]]
    tab_labels: list[str]
    table_count: int
    html_hash: str
    class_hashes: dict[str, str]


@dataclass
class DiffItem:
    selector_key: str
    change_type: str  # "removed" | "added" | "changed_class" | "count_changed"
    old_value: str = ""
    new_value: str = ""
    severity: str = "warning"  # "critical" | "warning" | "info"


@dataclass
class StructureDiff:
    has_changes: bool
    items: list[DiffItem] = field(default_factory=list)
    severity: str = "none"


KEYWORDS = [
    "row", "table", "tab", "player", "lineup", "stat", "odds",
    "name", "value", "category", "participant", "score", "team",
    "home", "away", "date", "time", "form", "match", "title",
    "header", "cell", "col", "body", "content", "wrapper",
    "container", "section", "list", "item", "link", "button"
]


def _extract_selectors(soup: BeautifulSoup) -> dict[str, list[SelectorInfo]]:
    result = {}
    html = str(soup)
    for kw in KEYWORDS:
        pattern = re.compile(r'class="([^"]*' + re.escape(kw) + r'[^"]*)"', re.I)
        matches = set()
        for m in pattern.finditer(html):
            classes = m.group(1).split()
            for c in classes:
                if kw.lower() in c.lower():
                    matches.add(c)
        if matches:
            infos = []
            for cls in sorted(matches)[:10]:
                elements = soup.select(f"[class~='{cls}']")
                tag = elements[0].name if elements else "unknown"
                text = (elements[0].get_text(strip=True)[:40] if elements else "")
                infos.append(SelectorInfo(
                    tag=tag,
                    class_list=[cls],
                    id_value=elements[0].get("id") if elements else None,
                    text_sample=text,
                    count=len(elements)
                ))
            result[kw] = infos

    # Extract IDs
    ids = {}
    for el in soup.find_all(id=True):
        ids[el.get("id")] = el.name
    if ids:
        result["_ids"] = [SelectorInfo(tag=t, class_list=[], id_value=i, text_sample="", count=1) for i, t in list(ids.items())[:20]]

    return result


def _extract_tab_labels(soup: BeautifulSoup) -> list[str]:
    tabs = []
    for btn in soup.find_all(["button", "a", "div"], class_=re.compile(r'tab', re.I)):
        text = btn.get_text(strip=True)
        if text and len(text) < 30:
            tabs.append(text)
    return list(dict.fromkeys(tabs))[:10]


def _extract_class_hashes(soup: BeautifulSoup) -> dict[str, str]:
    html = str(soup)
    hashes = {}
    pattern = re.compile(r'class="([^"]*)"')
    for m in pattern.finditer(html):
        classes = m.group(1).split()
        for c in classes:
            parts = c.rsplit("_", 1)
            if len(parts) == 2 and len(parts[1]) >= 4 and parts[1].isalnum():
                base = parts[0]
                if base not in hashes:
                    hashes[base] = c
    return hashes


def take_snapshot(soup: BeautifulSoup, url: str = "") -> StructureSnapshot:
    html_str = str(soup)
    html_hash = hashlib.sha256(html_str.encode()).hexdigest()[:16]
    return StructureSnapshot(
        url=url,
        timestamp=datetime.now(timezone.utc).isoformat(),
        selectors=_extract_selectors(soup),
        tab_labels=_extract_tab_labels(soup),
        table_count=len(soup.find_all("table")),
        html_hash=html_hash,
        class_hashes=_extract_class_hashes(soup)
    )


def compare_snapshots(old: StructureSnapshot, new: StructureSnapshot) -> StructureDiff:
    diff = StructureDiff(has_changes=False)

    if old.html_hash != new.html_hash:
        diff.items.append(DiffItem(
            selector_key="html_hash",
            change_type="changed",
            old_value=old.html_hash,
            new_value=new.html_hash,
            severity="warning"
        ))

    if old.table_count != new.table_count:
        diff.items.append(DiffItem(
            selector_key="table_count",
            change_type="count_changed",
            old_value=str(old.table_count),
            new_value=str(new.table_count),
            severity="warning"
        ))

    old_tabs = set(old.tab_labels)
    new_tabs = set(new.tab_labels)
    for t in old_tabs - new_tabs:
        diff.items.append(DiffItem(selector_key="tab", change_type="removed", old_value=t, severity="critical"))
    for t in new_tabs - old_tabs:
        diff.items.append(DiffItem(selector_key="tab", change_type="added", new_value=t, severity="info"))

    old_keys = set(old.class_hashes.keys())
    new_keys = set(new.class_hashes.keys())
    for k in old_keys & new_keys:
        if old.class_hashes[k] != new.class_hashes[k]:
            diff.items.append(DiffItem(
                selector_key=f"class_hash:{k}",
                change_type="changed_class",
                old_value=old.class_hashes[k],
                new_value=new.class_hashes[k],
                severity="warning"
            ))
    for k in old_keys - new_keys:
        if not k.startswith("_"):
            diff.items.append(DiffItem(selector_key=f"class_hash:{k}", change_type="removed", old_value=k, severity="warning"))
    for k in new_keys - old_keys:
        if not k.startswith("_"):
            diff.items.append(DiffItem(selector_key=f"class_hash:{k}", change_type="added", new_value=k, severity="info"))

    old_sel_keys = set(old.selectors.keys())
    new_sel_keys = set(new.selectors.keys())
    for k in old_sel_keys - new_sel_keys:
        if not k.startswith("_"):
            diff.items.append(DiffItem(selector_key=f"selector:{k}", change_type="removed", severity="critical"))
    for k in new_sel_keys - old_sel_keys:
        if not k.startswith("_"):
            diff.items.append(DiffItem(selector_key=f"selector:{k}", change_type="added", severity="info"))

    if diff.items:
        diff.has_changes = True
        severities = [i.severity for i in diff.items]
        if "critical" in severities:
            diff.severity = "critical"
        elif "warning" in severities:
            diff.severity = "warning"
        else:
            diff.severity = "info"

    return diff


def snapshot_to_dict(snapshot: StructureSnapshot) -> dict:
    return {
        "url": snapshot.url,
        "timestamp": snapshot.timestamp,
        "table_count": snapshot.table_count,
        "tab_labels": snapshot.tab_labels,
        "html_hash": snapshot.html_hash,
        "class_hashes": snapshot.class_hashes,
        "selectors": {
            k: [asdict(s) for s in v] for k, v in snapshot.selectors.items()
        }
    }


def dict_to_snapshot(data: dict) -> StructureSnapshot:
    selectors = {}
    for k, v in data.get("selectors", {}).items():
        selectors[k] = [SelectorInfo(**s) for s in v]
    return StructureSnapshot(
        url=data.get("url", ""),
        timestamp=data.get("timestamp", ""),
        selectors=selectors,
        tab_labels=data.get("tab_labels", []),
        table_count=data.get("table_count", 0),
        html_hash=data.get("html_hash", ""),
        class_hashes=data.get("class_hashes", {})
    )
