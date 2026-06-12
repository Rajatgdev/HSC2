# backend/retrieval/hybrid.py
"""
Hybrid retrieval v2.

Changes vs v1:
- CN8 / TARIC10 / BTI hits are ALWAYS rolled up to their parent HS6 with
  score aggregation (v1 threw away ~84% of retrieved docs when filtering
  to 6-digit codes, and only widened as a fallback).
- Provenance is kept per HS6: which underlying documents (node or BTI)
  contributed, from which index (bm25 / dense), at which rank. This is what
  lets the UI prove the answer is grounded.
- RRF runs over *documents*, then aggregates to HS6 (sum of doc RRF scores),
  so a heading supported by many child codes + BTI rulings outranks a
  heading supported by one lexical fluke.
"""
from retrieval.embedder import embed_query
from retrieval.bm25_index import search_bm25
from retrieval.turbovec_index import search_turbovec

RRF_K = 60


def _hs6_of(code: str) -> str | None:
    if not code.isdigit():
        return None
    if len(code) < 6:
        return None
    return code[:6]


async def hybrid_search_hs6(query: str, top_k: int = 40) -> list[dict]:
    """
    Returns ranked HS6 buckets:
    [{ "code": "848180", "fused_score": float,
       "evidence": [{"doc_code","doc_type","index","rank","score"}, ...] }]
    """
    embedding = await embed_query(query)
    sparse = search_bm25(query, top_k=top_k)
    dense = search_turbovec(embedding, top_k=top_k)

    buckets: dict[str, dict] = {}

    for index_name, results in (("bm25", sparse), ("dense", dense)):
        for rank, item in enumerate(results):
            doc_code = item["code"]
            doc_type = item.get("doc_type", "node")
            hs6 = _hs6_of(doc_code)
            if hs6 is None:
                continue
            rrf = 1.0 / (RRF_K + rank + 1)
            b = buckets.setdefault(hs6, {"code": hs6, "fused_score": 0.0, "evidence": []})
            b["fused_score"] += rrf
            b["evidence"].append({
                "doc_code": doc_code,
                "doc_type": doc_type,       # "node" | "bti"
                "index": index_name,        # "bm25" | "dense"
                "rank": rank + 1,
                "score": round(float(item.get("score", 0.0)), 4),
            })

    ranked = sorted(buckets.values(), key=lambda b: b["fused_score"], reverse=True)
    for b in ranked:
        b["fused_score"] = round(b["fused_score"], 5)
    return ranked[:top_k]
