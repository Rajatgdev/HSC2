"""
Ingest full TARIC hierarchy from fetch_full_taric.py output.
Run: python -m ingestion.ingest_full_taric

1. Truncates taric_nodes
2. Inserts all nodes with proper parent_code linkage
3. Generates embeddings for SUBHEADING + CN8 levels
4. Rebuilds BM25 + TurboVec indexes
"""
import json
import asyncio
from pathlib import Path
from sqlalchemy import text
from db.session import async_session
from config import settings

INPUT = Path("data/taric/full_taric_nodes.json")

LEVEL_PRIORITY = {
    "CHAPTER": 0, "HEADING": 1, "SUBHEADING": 2, "CN8": 3, "TARIC10": 4,
}


def compute_parent(code: str, all_codes: set) -> str | None:
    """Walk up the hierarchy to find the nearest existing parent."""
    prefixes = [code[:n] for n in [8, 6, 4, 2] if n < len(code)]
    for p in prefixes:
        if p in all_codes:
            return p
    return None


async def main():
    if not INPUT.exists():
        print(f"ERROR: {INPUT} not found. Run fetch_full_taric.py first.")
        return

    nodes = json.loads(INPUT.read_text())
    print(f"Loaded {len(nodes)} nodes from {INPUT}")

    # Build code set for parent resolution
    all_codes = {n["code"] for n in nodes}

    # Fix parent_code for all nodes
    for n in nodes:
        if not n.get("parent_code") or n["parent_code"] not in all_codes:
            n["parent_code"] = compute_parent(n["code"], all_codes)

    async with async_session() as db:
        # Truncate existing
        await db.execute(text("TRUNCATE taric_nodes CASCADE"))
        print("Truncated taric_nodes")

        # Batch insert
        batch_size = 200
        for i in range(0, len(nodes), batch_size):
            batch = nodes[i:i + batch_size]
            for n in batch:
                await db.execute(text("""
                    INSERT INTO taric_nodes
                        (code, level, description, parent_code,
                         section_number, chapter_notes, subheading_notes,
                         valid_from)
                    VALUES (:code, :level, :desc, :parent,
                            :sec, :ch_notes, :sh_notes,
                            CURRENT_DATE)
                    ON CONFLICT (code) DO UPDATE SET
                        description = EXCLUDED.description,
                        level = EXCLUDED.level,
                        parent_code = EXCLUDED.parent_code,
                        chapter_notes = EXCLUDED.chapter_notes,
                        subheading_notes = EXCLUDED.subheading_notes
                """), {
                    "code": n["code"],
                    "level": n["level"],
                    "desc": n.get("description", ""),
                    "parent": n.get("parent_code"),
                    "sec": n.get("section_number"),
                    "ch_notes": n.get("chapter_notes", ""),
                    "sh_notes": n.get("subheading_notes", ""),
                })
            await db.commit()
            if (i + batch_size) % 1000 == 0:
                print(f"  Inserted {min(i + batch_size, len(nodes))}/{len(nodes)}")

        print(f"Inserted {len(nodes)} nodes")

        # Count by level
        rows = (await db.execute(text(
            "SELECT level, COUNT(*) FROM taric_nodes GROUP BY level ORDER BY level"
        ))).fetchall()
        for r in rows:
            print(f"  {r[0]:15s} {r[1]}")

    print("\nDone! Now run:")
    print("  python -m ingestion.generate_embeddings")
    print("  python -m ingestion.build_indexes")


if __name__ == "__main__":
    asyncio.run(main())
