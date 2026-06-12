# backend/reasoning/hs10_suggester.py
"""
HS10 suggester v2.
Changes vs v1:
- Structured outputs.
- HARD grounding: suggestions filtered to the actual children list, and
  bti_reference validated against the BTI rows actually shown to the model
  (v1 let the model cite phantom BTIs).
- Returns the evidence pack (children considered + BTIs shown) so the UI can
  render a provenance panel.
"""
from reasoning.llm import call_json
from reasoning.schemas import HS10_SCHEMA
from db.queries import get_taric10_descendants, get_bti_for_code, get_measures_for_code
from graph.taric_tree import get_sibling_context

SYSTEM = """You are an EU customs classification expert classifying to 10-digit TARIC.
Apply GRI 1-6 strictly (GRI 6: compare subheadings at the same dash level only).
You MUST:
1. Only suggest codes from the provided children list.
2. Cite specific product attributes + narrowing answers in each explanation.
3. Only cite a BTI reference that appears in the precedent list.
4. If 'Not sure / Other' answers leave genuine ambiguity, set ambiguous=true and
   recommend applying for a Binding Tariff Information ruling."""


def _user_prompt(description, hs6, origin, dest, answers, children, btis, siblings):
    children_text = "\n".join(f"  {c['code']}: {c['description']}" for c in children)
    bti_text = "\n".join(
        f"  [{b['bti_ref']}] \"{b['product_desc'][:300]}\" -> {b['taric_code']}"
        + (f"\n    Rationale: {b['classification_rationale'][:200]}"
           if b.get('classification_rationale') else "")
        for b in btis
    ) or "  None."
    answers_text = "\n".join(f"  {k}: {v}" for k, v in answers.items()) or "  None."
    siblings_text = "\n".join(
        f"  {s['code']}: {s['description']}" for s in siblings[:3]) or "  None."
    return (f"PRODUCT: {description}\n\nCORRIDOR: {origin} -> {dest}\n\n"
            f"HS6: {hs6}\n\nNARROWING ANSWERS:\n{answers_text}\n\n"
            f"VALID CODES UNDER {hs6}:\n{children_text}\n\n"
            f"SIBLING HEADINGS:\n{siblings_text}\n\nBTI PRECEDENTS:\n{bti_text}")


async def suggest_hs10(hs6_code: str, description: str,
                       narrowing_answers: dict[str, str],
                       origin_country: str, dest_country: str) -> dict:
    children = await get_taric10_descendants(hs6_code)
    btis = await get_bti_for_code(hs6_code, limit=5)
    siblings = get_sibling_context(hs6_code)

    if not children:
        return {"suggestions": [], "ambiguous": True,
                "ambiguity_note": f"No TARIC codes found under {hs6_code}.",
                "evidence": {"children": [], "bti": []}}

    result = await call_json(
        SYSTEM,
        _user_prompt(description, hs6_code, origin_country, dest_country,
                     narrowing_answers, children, btis, siblings),
        HS10_SCHEMA,
    )

    # ── Grounding enforcement ──
    valid_codes = {c["code"] for c in children}
    valid_btis = {b["bti_ref"] for b in btis}
    desc_by_code = {c["code"]: c["description"] for c in children}

    grounded = []
    for s in result.get("suggestions", []):
        if s["code"] not in valid_codes:
            continue                      # drop hallucinated codes
        if s.get("bti_reference") and s["bti_reference"] not in valid_btis:
            s["bti_reference"] = None     # drop phantom citations
        s["description"] = desc_by_code.get(s["code"], "")
        s["measures"] = await get_measures_for_code(s["code"], origin_country)
        grounded.append(s)

    if not grounded:
        result["ambiguous"] = True
        result["ambiguity_note"] = (result.get("ambiguity_note")
                                    or "No grounded suggestion survived validation; "
                                       "consider a BTI application.")
    result["suggestions"] = grounded
    result["evidence"] = {
        "children": children,
        "bti": [{"bti_ref": b["bti_ref"], "taric_code": b["taric_code"],
                 "product_desc": b["product_desc"][:300]} for b in btis],
    }
    return result
