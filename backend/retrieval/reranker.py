# backend/retrieval/reranker.py
"""
Cross-encoder reranker v2.
Change vs v1: documents now include heading description + ancestor chain +
truncated notes (v1 scored against the bare heading text only, which is often
just e.g. 'Other' — useless signal).
"""
import logging
import math
from db.queries import get_nodes_with_context

logger = logging.getLogger(__name__)
_model = None
_tokenizer = None


def _load():
    global _model, _tokenizer
    try:
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
        from config import settings
        _tokenizer = AutoTokenizer.from_pretrained(settings.RERANKER_MODEL)
        _model = AutoModelForSequenceClassification.from_pretrained(settings.RERANKER_MODEL)
        _model.eval()
    except Exception as e:
        logger.warning(f"Reranker unavailable, falling back to fusion order: {e}")


def _sigmoid(x: float) -> float:
    try:
        return 1.0 / (1.0 + math.exp(-x))
    except OverflowError:
        return 0.0 if x < 0 else 1.0


def _score(query: str, docs: list[str]) -> list[float]:
    import torch
    pairs = [[query, d] for d in docs]
    with torch.no_grad():
        inputs = _tokenizer(pairs, padding=True, truncation=True,
                            max_length=512, return_tensors="pt")
        logits = _model(**inputs, return_dict=True).logits.view(-1).float()
    return [0.0 if (math.isnan(s) or math.isinf(s)) else _sigmoid(s)
            for s in logits.tolist()]


async def rerank_hs6(query: str, buckets: list[dict], top_k: int = 8) -> list[dict]:
    if not buckets:
        return []
    if _model is None:
        _load()

    codes = [b["code"] for b in buckets]
    ctx = await get_nodes_with_context(codes)   # {code: rich text}

    if _model is None:
        for b in buckets:
            b["rerank_score"] = b["fused_score"]
            b["description"] = ctx.get(b["code"], {}).get("description", "")
        return buckets[:top_k]

    docs = [ctx.get(c, {}).get("rich_text", c) for c in codes]
    scores = _score(query, docs)
    out = []
    for b, s, c in zip(buckets, scores, codes):
        out.append({**b,
                    "rerank_score": round(s, 4),
                    "description": ctx.get(c, {}).get("description", ""),
                    "ancestor_path": ctx.get(c, {}).get("ancestor_path", "")})
    out.sort(key=lambda x: x["rerank_score"], reverse=True)
    return out[:top_k]
