"""
Parse the official EU CN2026 PDF to extract the full Combined Nomenclature hierarchy.
Run: python -m ingestion.parse_cn2026_pdf

Input:  data/taric/CN2026.pdf  (copy your PDF here)
Output: data/taric/full_cn2026_nodes.json

Then run:
  python -m ingestion.ingest_full_taric
  python -m ingestion.generate_embeddings
  python -m ingestion.build_indexes
"""
import json
import re
from pathlib import Path

try:
    import fitz  # PyMuPDF
except ImportError:
    print("Install PyMuPDF: pip install pymupdf")
    exit(1)

PDF_PATH = Path("data/taric/CN2026.pdf")
OUTPUT = Path("data/taric/full_cn2026_nodes.json")
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

LEVEL_MAP = {
    2: "CHAPTER",
    4: "HEADING",
    6: "SUBHEADING",
    8: "CN8",
}

# Regex: CN codes on their own line: "0101", "0101 21", "0101 21 00"
CODE_RE = re.compile(r'^(\d{4}(?:\s\d{2}(?:\s\d{2})?)?)\s*$', re.MULTILINE)

# Chapter headers: "CHAPTER 1", "CHAPTER 84"
CHAPTER_RE = re.compile(r'^CHAPTER\s+(\d+)\s*$', re.MULTILINE)

# Section headers: "SECTION I", "SECTION XVI"
SECTION_RE = re.compile(r'^SECTION\s+([IVXLC]+)\s*$', re.MULTILINE)


def clean_desc(desc: str) -> str:
    """Clean up a description line."""
    desc = desc.strip()
    # Remove trailing dots/spaces used for alignment
    desc = re.sub(r'[\s.]{3,}$', '', desc)
    desc = re.sub(r'\s*\(\d+\)\s*$', '', desc)  # Remove footnote refs like (1)
    # Remove leading dashes but keep them for hierarchy indication
    return desc.strip()


def compute_parent(code: str, all_codes: set) -> str | None:
    """Walk up the hierarchy to find nearest existing parent."""
    for n in [6, 4, 2]:
        if n < len(code):
            parent = code[:n]
            if parent in all_codes:
                return parent
    return None


def parse_pdf(pdf_path: str) -> list[dict]:
    doc = fitz.open(pdf_path)
    print(f"PDF: {doc.page_count} pages")

    all_nodes = []
    current_section = ""
    current_chapter = ""
    current_chapter_notes = ""

    # Track chapter notes pages (they appear before the tariff table)
    chapter_notes_buffer = {}

    for page_idx in range(doc.page_count):
        text = doc[page_idx].get_text()
        lines = text.split('\n')

        # Detect section
        for m in SECTION_RE.finditer(text):
            current_section = m.group(1)

        # Detect chapter
        for m in CHAPTER_RE.finditer(text):
            ch_num = m.group(1).zfill(2)
            current_chapter = ch_num

            # Extract chapter notes (text between "Note" and the first CN code)
            note_start = text.find('Note')
            if note_start == -1:
                note_start = text.find('note')
            if note_start > -1:
                # Grab up to 3000 chars of notes
                chapter_notes_buffer[ch_num] = text[note_start:note_start + 3000].strip()

        # Extract CN codes
        for m in CODE_RE.finditer(text):
            raw_code = m.group(1).replace(' ', '')
            code_len = len(raw_code)

            if code_len not in (4, 6, 8):
                continue

            level = LEVEL_MAP.get(code_len, "CN8")

            # Get description: lines after the code until next code or duty rate
            pos = m.end()
            desc_lines = []
            remaining = text[pos:pos + 500].strip().split('\n')

            for line in remaining:
                line = line.strip()
                # Stop at duty rate (number with comma like "2,2" or "Free")
                if re.match(r'^(\d+[,.]?\d*|Free|—)\s*$', line):
                    break
                # Stop at next CN code
                if re.match(r'^\d{4}(\s\d{2}(\s\d{2})?)?\s*$', line):
                    break
                if line and line not in ('1', '2', '3', '4'):
                    desc_lines.append(line)

            desc = clean_desc(' '.join(desc_lines))

            # Skip empty or header-like entries
            if not desc and code_len == 4:
                # Heading might have description on same concept line
                pass

            chapter_code = raw_code[:2]

            node = {
                "code": raw_code,
                "level": level,
                "description": desc,
                "section_number": current_section,
                "chapter_notes": chapter_notes_buffer.get(chapter_code, ""),
                "subheading_notes": "",
            }
            all_nodes.append(node)

    doc.close()

    # Add chapter nodes
    chapters_seen = set()
    for n in all_nodes:
        ch = n["code"][:2]
        if ch not in chapters_seen:
            chapters_seen.add(ch)

    # Build the set of all codes for parent resolution
    all_codes = {n["code"] for n in all_nodes}

    # Also add chapter-level nodes if not already there
    for ch in chapters_seen:
        if ch not in all_codes:
            all_nodes.append({
                "code": ch,
                "level": "CHAPTER",
                "description": f"Chapter {ch}",
                "section_number": "",
                "chapter_notes": chapter_notes_buffer.get(ch, ""),
                "subheading_notes": "",
            })
            all_codes.add(ch)

    # Assign parent_code
    for n in all_nodes:
        n["parent_code"] = compute_parent(n["code"], all_codes)

    # Synthesize TARIC10 codes (CN8 + "00") for each CN8 entry
    taric10_nodes = []
    for n in all_nodes:
        if n["level"] == "CN8":
            taric10_code = n["code"] + "00"
            if taric10_code not in all_codes:
                taric10_nodes.append({
                    "code": taric10_code,
                    "level": "TARIC10",
                    "description": n["description"],
                    "parent_code": n["code"],
                    "section_number": n["section_number"],
                    "chapter_notes": n["chapter_notes"],
                    "subheading_notes": n.get("subheading_notes", ""),
                })
                all_codes.add(taric10_code)

    all_nodes.extend(taric10_nodes)

    # Deduplicate
    seen = set()
    unique = []
    for n in all_nodes:
        if n["code"] not in seen:
            seen.add(n["code"])
            unique.append(n)

    return unique


def main():
    if not PDF_PATH.exists():
        print(f"ERROR: {PDF_PATH} not found.")
        print(f"Copy your CN2026.pdf to {PDF_PATH}")
        return

    print("Parsing CN2026 PDF...")
    nodes = parse_pdf(str(PDF_PATH))

    print(f"\nTotal nodes: {len(nodes)}")

    # Count by level
    from collections import Counter
    levels = Counter(n["level"] for n in nodes)
    for lvl in ["CHAPTER", "HEADING", "SUBHEADING", "CN8", "TARIC10"]:
        print(f"  {lvl:15s} {levels.get(lvl, 0)}")

    # Show sample for heading 8481
    print("\nSample — heading 8481 (valves):")
    for n in nodes:
        if n["code"].startswith("8481") and len(n["code"]) <= 8:
            print(f"  {n['code']:10s} {n['level']:12s} {n['description'][:60]}")

    OUTPUT.write_text(json.dumps(nodes, indent=2, ensure_ascii=False))
    print(f"\nSaved to {OUTPUT}")
    print("\nNext steps:")
    print("  python -m ingestion.ingest_full_taric")
    print("  python -m ingestion.generate_embeddings")
    print("  python -m ingestion.build_indexes")


if __name__ == "__main__":
    main()
