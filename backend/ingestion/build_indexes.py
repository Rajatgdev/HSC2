# backend/ingestion/build_indexes.py
"""
Build BM25S + TurboVec indexes v2.

Fixes vs v1 (verified against the shipped v1 artifacts):
1. BTI rulings were MISSING from the shipped index (11,649 docs = nodes only)
   even though the script queried them — the build was run before BTI ingest.
   v2 fails loudly if the BTI table is empty so this can't happen silently.
2. Writes corpus_meta.json with doc_type ("node" | "bti") so retrieval can
   show provenance and fuse correctly.
3. bit_width=2 (2-bit quantization) destroyed dense recall to save ~3 MB on a
   tiny 70 MB corpus. v2 stores float32 (or bit_width=8 if memory matters).

Run: python -m ingestion.build_indexes
"""
import asyncio
import json
import os
import numpy as np
import bm25s
import turbovec
from db.session import async_session
from sqlalchemy import text
from config import settings


async def load_corpus():
    async with async_session() as db:
        nodes = (await db.execute(text("""
            SELECT n.code, n.level, n.description,
                   n.chapter_notes, n.subheading_notes, n.embedding::text,
                   h.description  AS heading_desc,
                   ch.description AS chapter_desc
            FROM taric_nodes n
            LEFT JOIN taric_nodes h  ON h.code = LEFT(n.code, 4) AND h.level = 'HEADING'
            LEFT JOIN taric_nodes ch ON ch.code = LEFT(n.code, 2) AND ch.level = 'CHAPTER'
            WHERE n.level IN ('SUBHEADING', 'CN8', 'TARIC10')
              AND (n.valid_to IS NULL OR n.valid_to > CURRENT_DATE)
            ORDER BY n.code
        """))).fetchall()
        btis = (await db.execute(text("""
            SELECT taric_code AS code, product_desc AS description,
                   classification_rationale AS rationale, embedding::text
            FROM bti_rulings WHERE embedding IS NOT NULL
            ORDER BY bti_ref
        """))).fetchall()
    return nodes, btis


def parse_embedding(s):
    if s is None:
        return None
    try:
        return [float(x) for x in s.strip("[]").split(",")]
    except Exception:
        return None


async def main():
    nodes, btis = await load_corpus()
    if not btis:
        raise SystemExit("BTI table is empty — run ingest_bti first. "
                         "Refusing to build an index that silently drops BTI grounding.")
    print(f"Corpus: {len(nodes)} TARIC nodes + {len(btis)} BTI rulings")

    texts, meta, embeddings = [], [], []
    for r in nodes:
        ancestor = f"{r.chapter_desc or ''} {r.heading_desc or ''} ".strip()
        texts.append(f"{ancestor} {r.description} {r.chapter_notes or ''} {r.subheading_notes or ''}")
        meta.append({"code": r.code, "doc_type": "node"})
        embeddings.append(parse_embedding(r.embedding))
    for r in btis:
        texts.append(f"{r.description} {r.rationale or ''}")
        meta.append({"code": r.code, "doc_type": "bti"})
        embeddings.append(parse_embedding(r.embedding))

    # -- BM25S --
    os.makedirs(settings.BM25_INDEX_PATH, exist_ok=True)
    tokenized = bm25s.tokenize(texts, stopwords="en")
    retriever = bm25s.BM25()
    retriever.index(tokenized)
    retriever.save(settings.BM25_INDEX_PATH)
    with open(os.path.join(settings.BM25_INDEX_PATH, "corpus_meta.json"), "w") as f:
        json.dump(meta, f)
    print(f"BM25S saved: {len(texts)} docs")

    # -- TurboVec: keep only rows with embeddings, in lockstep with meta --
    keep = [(m, e) for m, e in zip(meta, embeddings) if e is not None]
    missing = len(meta) - len(keep)
    if missing:
        print(f"WARNING: {missing} docs missing embeddings — run generate_embeddings.")
    vec_meta = [m for m, _ in keep]
    vectors = np.array([e for _, e in keep], dtype=np.float32)

    index = turbovec.IdMapIndex(dim=settings.EMBED_DIMS)  # float32; was bit_width=2
    index.add_with_ids(vectors, np.arange(len(vectors), dtype=np.uint64))
    index.write(settings.TURBOVEC_INDEX_PATH)
    with open(f"{settings.TURBOVEC_INDEX_PATH}_meta.json", "w") as f:
        json.dump(vec_meta, f)
    print(f"TurboVec saved: {len(vectors)} vectors ({vectors.nbytes/1e6:.1f} MB float32)")


if __name__ == "__main__":
    asyncio.run(main())
