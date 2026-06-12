# backend/reasoning/hs6_selector.py
"""
HS6 auto-selector v2.
Changes vs v1:
- Structured outputs (schema-enforced JSON).
- HARD grounding: the returned code MUST be one of the retrieval candidates;
  otherwise we fall back to the top reranked candidate and flag low confidence.
  (v1 trusted the LLM string blindly — it could emit a code that exists nowhere.)
- Confidence is blended with the reranker score, not LLM vibes alone.
"""
from reasoning.llm import call_json
from reasoning.schemas import HS6_SCHEMA
from config import settings

SYSTEM = """You are an EU customs classification expert.
Select the SINGLE BEST HS6 (6-digit subheading) for the product.

Rules:
- GRI 1 first: terms of the headings and section/chapter notes.
- GRI 3 if needed: most specific description wins; then essential character.
- You may ONLY choose a code from the candidate list. Never invent codes.
- explanation: 2-3 sentences citing product attributes and heading terms.
- alternatives: up to 2 plausible runner-ups FROM THE LIST with the boundary reason."""


async def auto_select_hs6(description: str, key_attributes: list[str],
                          candidates: list[dict]) -> dict:
    if not candidates:
        return {"code": None, "explanation": "No candidates found.",
                "confidence": "low", "gri_applied": "", "alternatives": []}

    allowed = {c["code"] for c in candidates}
    cand_text = "\n".join(
        f"- {c['code']} — {c.get('description','')}"
        f"\n  Path: {c.get('ancestor_path','')}"
        f"\n  Rerank: {c.get('rerank_score', 0):.2f}"
        + (f"\n  Chapter notes: {c['chapter_notes'][:300]}" if c.get('chapter_notes') else "")
        for c in candidates
    )
    attrs = "; ".join(key_attributes) if key_attributes else "(none extracted)"

    result = await call_json(
        SYSTEM,
        f'Product: "{description}"\nKey attributes: {attrs}\n\n'
        f"Candidates (ranked):\n{cand_text}\n\nPick the best HS6.",
        HS6_SCHEMA,
    )

    # ── Grounding enforcement ──
    if result.get("code") not in allowed:
        top = candidates[0]
        result = {
            "code": top["code"],
            "explanation": "Model proposed an out-of-list code; "
                           "fell back to the top retrieval candidate.",
            "confidence": "low",
            "gri_applied": "",
            "alternatives": [],
        }
    result["alternatives"] = [a for a in result.get("alternatives", [])
                              if a.get("code") in allowed]

    # ── Confidence calibration: cap LLM confidence by retrieval evidence ──
    by_code = {c["code"]: c for c in candidates}
    rscore = by_code.get(result["code"], {}).get("rerank_score", 0.0)
    if rscore < settings.MIN_CONFIDENCE_SCORE and result["confidence"] == "high":
        result["confidence"] = "medium"
    result["rerank_score"] = rscore
    result["description"] = by_code.get(result["code"], {}).get("description", "")
    return result
