# backend/retrieval/narrowing.py
"""
Narrowing question generator v2.
Changes vs v1:
- Structured outputs.
- Skips questions whose answer is already in the user's description
  (the model is told what's known; v1 routinely re-asked stated facts).
- Each question carries why_it_matters so the UI can show the user the stakes.
- Options are mapped back to which candidate codes they discriminate, when possible.
"""
from reasoning.llm import call_json
from reasoning.schemas import QUESTIONS_SCHEMA
from db.queries import get_taric10_descendants, get_bti_for_code

SYSTEM = """You generate discriminating questions for EU TARIC 10-digit classification.
Rules:
- 2-3 questions max, each 3-5 dropdown options, plain language.
- ONLY ask about attributes that (a) actually differ between the candidate codes
  AND (b) are NOT already answered by the product description.
- Always include "Not sure / Other" as the last option.
- why_it_matters: one short sentence on what the answer changes (e.g. duty rate band)."""


async def generate_narrowing_questions(hs6_code: str, user_description: str) -> list[dict]:
    children = await get_taric10_descendants(hs6_code)
    if len(children) <= 1:
        return []

    children_text = "\n".join(f"- {c['code']}: {c['description']}" for c in children[:40])
    btis = await get_bti_for_code(hs6_code, limit=3)
    bti_text = "\n".join(
        f"- [{b['bti_ref']}] {b['product_desc'][:200]} -> {b['taric_code']}" for b in btis
    ) or "None."

    result = await call_json(
        SYSTEM,
        f'Product (facts already known — do NOT re-ask these): "{user_description}"\n'
        f"HS6: {hs6_code}\n\nCandidate codes under it:\n{children_text}\n\n"
        f"BTI precedents:\n{bti_text}",
        QUESTIONS_SCHEMA,
    )
    return result.get("questions", [])
