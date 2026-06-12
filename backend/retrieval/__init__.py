# backend/retrieval/__init__.py
from retrieval.expansion import expand_query
from retrieval.hybrid import hybrid_search_hs6
from retrieval.reranker import rerank_hs6
from db.queries import enrich_candidates_with_metadata, codes_exist


async def retrieve_hs6_candidates(description: str, top_k: int = 8) -> dict:
    """
    v2 pipeline: expand → hybrid (doc-level RRF, HS6 rollup) → rerank with
    rich context → enrich → validate against DB.
    Returns {"candidates": [...], "expanded_query": str, "key_attributes": [...]}.
    """
    expansion = await expand_query(description)
    query = f"{description}\n{expansion['expanded']}"

    buckets = await hybrid_search_hs6(query, top_k=40)
    reranked = await rerank_hs6(query, buckets, top_k=top_k)
    enriched = await enrich_candidates_with_metadata(reranked)

    # Grounding guarantee: drop any candidate not present in taric_nodes
    valid = await codes_exist([c["code"] for c in enriched])
    enriched = [c for c in enriched if c["code"] in valid]

    return {
        "candidates": enriched,
        "expanded_query": expansion["expanded"],
        "key_attributes": expansion.get("key_attributes", []),
    }
