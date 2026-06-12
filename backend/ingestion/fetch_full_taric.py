"""
Fetch full CN/TARIC hierarchy from UK Trade Tariff API.
Run locally: python fetch_full_taric.py

Outputs: data/taric/full_taric_nodes.json
Then run: python -m ingestion.ingest_full_taric
"""
import json
import time
import requests
from pathlib import Path

BASE = "https://www.trade-tariff.service.gov.uk/api/v2"
HEADERS = {"Accept": "application/json"}
OUTPUT = Path("data/taric/full_taric_nodes.json")
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

LEVEL_MAP = {
    2: "CHAPTER",
    4: "HEADING",
    6: "SUBHEADING",
    8: "CN8",
    10: "TARIC10",
}


def fetch_json(url: str, retries: int = 3) -> dict | None:
    for attempt in range(retries):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=30)
            if resp.status_code == 200:
                return resp.json()
            if resp.status_code == 404:
                return None
            print(f"  HTTP {resp.status_code} on {url}, retry {attempt+1}")
        except Exception as e:
            print(f"  Error on {url}: {e}, retry {attempt+1}")
        time.sleep(1)
    return None


def extract_commodities(heading_data: dict) -> list[dict]:
    """Extract all commodity codes from a heading response."""
    nodes = []
    included = heading_data.get("included", [])

    for item in included:
        if item["type"] in ("commodity", "subheading"):
            attrs = item.get("attributes", {})
            code = attrs.get("goods_nomenclature_item_id", "")
            desc = attrs.get("formatted_description") or attrs.get("description", "")
            # Clean HTML from description
            import re
            desc = re.sub(r'<[^>]+>', '', desc).strip()

            if not code:
                continue

            code_len = len(code.rstrip("0")) or 2
            # Round up to even
            if code_len % 2 == 1:
                code_len += 1
            code_len = min(code_len, 10)

            nodes.append({
                "code": code,
                "description": desc,
                "level": LEVEL_MAP.get(code_len, "TARIC10"),
            })

    return nodes


def main():
    all_nodes = []

    # Step 1: Get all sections
    print("Fetching sections...")
    sections_data = fetch_json(f"{BASE}/sections")
    if not sections_data:
        print("FATAL: Could not fetch sections")
        return

    sections = sections_data.get("data", [])
    print(f"Found {len(sections)} sections")

    # Step 2: Get chapters from each section
    chapter_ids = []
    for sec in sections:
        sec_id = sec["id"]
        sec_data = fetch_json(f"{BASE}/sections/{sec_id}")
        if not sec_data:
            continue
        sec_attrs = sec_data.get("data", {}).get("attributes", {})
        sec_number = sec_attrs.get("position", sec_id)

        for item in sec_data.get("included", []):
            if item["type"] == "chapter":
                ch_attrs = item.get("attributes", {})
                ch_code = ch_attrs.get("goods_nomenclature_item_id", "")[:2]
                ch_desc = ch_attrs.get("formatted_description") or ch_attrs.get("description", "")
                import re
                ch_desc = re.sub(r'<[^>]+>', '', ch_desc).strip()

                if ch_code:
                    chapter_ids.append(ch_code)
                    all_nodes.append({
                        "code": ch_code,
                        "description": ch_desc,
                        "level": "CHAPTER",
                        "section_number": str(sec_number),
                    })

        time.sleep(0.2)

    print(f"Found {len(chapter_ids)} chapters")

    # Step 3: Get headings from each chapter
    heading_ids = []
    for i, ch_id in enumerate(chapter_ids):
        print(f"Chapter {ch_id} ({i+1}/{len(chapter_ids)})...")
        ch_data = fetch_json(f"{BASE}/chapters/{ch_id}")
        if not ch_data:
            continue

        for item in ch_data.get("included", []):
            if item["type"] == "heading":
                h_attrs = item.get("attributes", {})
                h_code = h_attrs.get("goods_nomenclature_item_id", "")[:4]
                h_desc = h_attrs.get("formatted_description") or h_attrs.get("description", "")
                import re
                h_desc = re.sub(r'<[^>]+>', '', h_desc).strip()

                if h_code and len(h_code) == 4:
                    heading_ids.append(h_code)
                    all_nodes.append({
                        "code": h_code,
                        "description": h_desc,
                        "level": "HEADING",
                        "parent_code": ch_id,
                    })

        time.sleep(0.2)

    print(f"Found {len(heading_ids)} headings")

    # Step 4: Get commodities from each heading
    for i, h_id in enumerate(heading_ids):
        if (i + 1) % 50 == 0:
            print(f"Heading {h_id} ({i+1}/{len(heading_ids)})...")

        h_data = fetch_json(f"{BASE}/headings/{h_id}")
        if not h_data:
            continue

        # Extract heading-level chapter notes
        h_attrs = h_data.get("data", {}).get("attributes", {})
        chapter_note = ""
        for item in h_data.get("included", []):
            if item["type"] == "chapter":
                ch_attrs = item.get("attributes", {})
                chapter_note = ch_attrs.get("chapter_note", "") or ""

        commodities = extract_commodities(h_data)
        for c in commodities:
            c["parent_code"] = h_id
            c["chapter_notes"] = chapter_note[:2000] if chapter_note else ""

        all_nodes.extend(commodities)
        time.sleep(0.15)

    print(f"\nTotal nodes collected: {len(all_nodes)}")

    # Deduplicate by code (keep first occurrence)
    seen = set()
    unique = []
    for n in all_nodes:
        if n["code"] not in seen:
            seen.add(n["code"])
            unique.append(n)

    print(f"After dedup: {len(unique)} unique codes")

    # Count by level
    from collections import Counter
    levels = Counter(n["level"] for n in unique)
    for lvl in ["CHAPTER", "HEADING", "SUBHEADING", "CN8", "TARIC10"]:
        print(f"  {lvl}: {levels.get(lvl, 0)}")

    OUTPUT.write_text(json.dumps(unique, indent=2))
    print(f"\nSaved to {OUTPUT}")


if __name__ == "__main__":
    main()
