# backend/api/classifier.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from uuid import UUID
import math

from retrieval import retrieve_hs6_candidates
from retrieval.narrowing import generate_narrowing_questions
from reasoning.hs6_selector import auto_select_hs6
from reasoning.hs10_suggester import suggest_hs10
from db.queries import (create_session, update_session, get_session,
                        get_measures_for_code, codes_exist)

router = APIRouter(prefix="/api/classify", tags=["TARIC Classifier"])


def sanitize(obj):
    if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
        return None
    if isinstance(obj, dict):
        return {k: sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [sanitize(v) for v in obj]
    return obj


class StartSessionReq(BaseModel):
    origin_country: str = Field(..., min_length=2, max_length=2)
    destination_country: str = Field(..., min_length=2, max_length=2)
    incoterms: str | None = None

class StartSessionResp(BaseModel):
    session_id: UUID

class SuggestHS6Req(BaseModel):
    session_id: UUID
    description: str = Field(..., min_length=10, max_length=2000)

class OverrideHS6Req(BaseModel):
    session_id: UUID
    hs6_code: str = Field(..., pattern=r"^\d{6}$")

class NarrowingAnswerReq(BaseModel):
    session_id: UUID
    answers: dict[str, str]

class FeedbackReq(BaseModel):
    session_id: UUID
    final_hs10: str
    feedback: str = Field(..., pattern=r"^(correct|partial|wrong)$")
    note: str | None = None


@router.post("/session", response_model=StartSessionResp)
async def start_session(req: StartSessionReq):
    sid = await create_session(req.origin_country.upper(),
                               req.destination_country.upper(), req.incoterms)
    return {"session_id": sid}


@router.post("/hs6/suggest")
async def suggest_hs6(req: SuggestHS6Req):
    """Description -> grounded HS6 selection + provenance + narrowing questions."""
    retrieval = await retrieve_hs6_candidates(req.description, top_k=8)
    candidates = sanitize(retrieval["candidates"])

    hs6_result = await auto_select_hs6(req.description,
                                       retrieval["key_attributes"], candidates)
    selected = hs6_result.get("code")
    if not selected:
        raise HTTPException(400, "Could not determine an HS6 code for this product. "
                                 "Try adding material, function, and how it is sold.")

    questions = await generate_narrowing_questions(selected, req.description)

    await update_session(req.session_id, {
        "product_desc": req.description,
        "candidate_hs6": candidates,
        "selected_hs6": selected,
        "narrowing_qs": questions,
    })
    return {
        "hs6": hs6_result,
        "candidates": candidates,
        "narrowing_questions": questions,
        "retrieval": {                       # provenance panel data
            "expanded_query": retrieval["expanded_query"],
            "key_attributes": retrieval["key_attributes"],
        },
    }


@router.post("/hs6/override")
async def override_hs6(req: OverrideHS6Req):
    """v2: user disagrees with auto-selection -> pick an alternative HS6."""
    session = await get_session(req.session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    if req.hs6_code not in await codes_exist([req.hs6_code]):
        raise HTTPException(400, f"{req.hs6_code} is not a valid HS6 in the nomenclature.")
    questions = await generate_narrowing_questions(req.hs6_code, session["product_desc"] or "")
    await update_session(req.session_id, {"selected_hs6": req.hs6_code,
                                          "narrowing_qs": questions})
    return {"selected_hs6": req.hs6_code, "narrowing_questions": questions}


@router.post("/hs10/suggest")
async def suggest_hs10_endpoint(req: NarrowingAnswerReq):
    session = await get_session(req.session_id)
    if not session:
        raise HTTPException(404, "Session not found")
    result = sanitize(await suggest_hs10(
        hs6_code=session["selected_hs6"],
        description=session["product_desc"],
        narrowing_answers=req.answers,
        origin_country=session["origin_country"],
        dest_country=session["dest_country"],
    ))
    await update_session(req.session_id, {
        "narrowing_ans": req.answers,
        "suggested_hs10": result.get("suggestions", []),
        "evidence": result.get("evidence", {}),
    })
    return result


@router.post("/feedback")
async def submit_feedback(req: FeedbackReq):
    await update_session(req.session_id, {
        "final_hs10": req.final_hs10,
        "user_feedback": req.feedback,
        "feedback_note": req.note,
    })
    return {"status": "logged"}


@router.get("/measures/{taric_code}")
async def get_measures(taric_code: str, origin: str | None = None):
    return {"taric_code": taric_code,
            "measures": await get_measures_for_code(taric_code, origin)}
