# backend/db/queries.py
"""DB queries v2 — adds context-rich node fetch, code validation,
group-aware measures lookup."""
import uuid
import json
from typing import Any
from sqlalchemy import text
from db.session import async_session

JSONB_FIELDS = {"candidate_hs6", "narrowing_qs", "narrowing_ans",
                "suggested_hs10", "measures", "evidence"}
# Whitelist prevents arbitrary column injection through update_session keys.
ALLOWED_SESSION_FIELDS = JSONB_FIELDS | {
    "product_desc", "selected_hs6", "final_hs10", "user_feedback", "feedback_note",
}


async def create_session(origin: str, dest: str, incoterms: str | None = None) -> str:
    sid = str(uuid.uuid4())
    async with async_session() as db:
        await db.execute(text("""
            INSERT INTO classifier_sessions (id, origin_country, dest_country, incoterms)
            VALUES (:id, :o, :d, :i)
        """), {"id": sid, "o": origin, "d": dest, "i": incoterms})
        await db.commit()
    return sid


async def get_session(session_id) -> dict | None:
    async with async_session() as db:
        row = (await db.execute(text(
            "SELECT * FROM classifier_sessions WHERE id = :sid"
        ), {"sid": str(session_id)})).fetchone()
    return dict(row._mapping) if row else None


async def update_session(session_id, updates: dict) -> None:
    updates = {k: v for k, v in updates.items() if k in ALLOWED_SESSION_FIELDS}
    if not updates:
        return
    set_clauses, params = [], {"sid": str(session_id)}
    for key, value in updates.items():
        p = f"p_{key}"
        if key in JSONB_FIELDS:
            set_clauses.append(f"{key} = CAST(:{p} AS jsonb)")
            params[p] = json.dumps(value) if not isinstance(value, str) else value
        else:
            set_clauses.append(f"{key} = :{p}")
            params[p] = value
    async with async_session() as db:
        await db.execute(text(
            f"UPDATE classifier_sessions SET {', '.join(set_clauses)} WHERE id = :sid"
        ), params)
        await db.commit()


# == TARIC nodes ==

async def get_all_taric_nodes() -> list[dict]:
    async with async_session() as db:
        rows = (await db.execute(text("""
            SELECT code, level, description, parent_code, chapter_notes, subheading_notes
            FROM taric_nodes
            WHERE (valid_to IS NULL OR valid_to > CURRENT_DATE)
            ORDER BY code
        """))).fetchall()
    return [dict(r._mapping) for r in rows]


async def codes_exist(codes: list[str]) -> set[str]:
    if not codes:
        return set()
    async with async_session() as db:
        rows = (await db.execute(text(
            "SELECT code FROM taric_nodes WHERE code = ANY(:codes)"
        ), {"codes": codes})).fetchall()
    return {r.code for r in rows}


async def get_nodes_with_context(codes: list[str]) -> dict[str, dict]:
    """Rich reranker text: chapter > heading > subheading path + notes.
    v2 fix for reranking against bare 'Other' descriptions."""
    if not codes:
        return {}
    async with async_session() as db:
        rows = (await db.execute(text("""
            SELECT n.code, n.description, n.chapter_notes, n.subheading_notes,
                   h.description AS heading_desc, ch.description AS chapter_desc
            FROM taric_nodes n
            LEFT JOIN taric_nodes h  ON h.code  = LEFT(n.code, 4)
            LEFT JOIN taric_nodes ch ON ch.code = LEFT(n.code, 2)
            WHERE n.code = ANY(:codes)
        """), {"codes": codes})).fetchall()
    out = {}
    for r in rows:
        path = " > ".join(p for p in [r.chapter_desc, r.heading_desc, r.description] if p)
        rich = path
        if r.subheading_notes:
            rich += f". Notes: {r.subheading_notes[:300]}"
        elif r.chapter_notes:
            rich += f". Notes: {r.chapter_notes[:300]}"
        out[r.code] = {"description": r.description or "",
                       "ancestor_path": path, "rich_text": rich}
    return out


async def get_taric10_descendants(hs6_code: str) -> list[dict]:
    async with async_session() as db:
        for level in ("TARIC10", "CN8"):
            rows = (await db.execute(text("""
                SELECT code, level, description, chapter_notes, subheading_notes
                FROM taric_nodes
                WHERE code LIKE :prefix AND level = :lvl
                  AND (valid_to IS NULL OR valid_to > CURRENT_DATE)
                ORDER BY code
            """), {"prefix": f"{hs6_code}%", "lvl": level})).fetchall()
            if rows:
                return [dict(r._mapping) for r in rows]
    return []


async def enrich_candidates_with_metadata(candidates: list[dict]) -> list[dict]:
    codes = [c["code"] for c in candidates]
    if not codes:
        return candidates
    async with async_session() as db:
        rows = (await db.execute(text("""
            SELECT code, level, description, parent_code, chapter_notes, subheading_notes
            FROM taric_nodes WHERE code = ANY(:codes)
        """), {"codes": codes})).fetchall()
    meta = {r.code: dict(r._mapping) for r in rows}
    return [{**c,
             "description": c.get("description") or meta.get(c["code"], {}).get("description", ""),
             "level": meta.get(c["code"], {}).get("level", ""),
             "chapter_notes": meta.get(c["code"], {}).get("chapter_notes", ""),
             "subheading_notes": meta.get(c["code"], {}).get("subheading_notes", "")}
            for c in candidates]


# == BTI ==

async def get_bti_for_code(taric_code: str, limit: int = 3) -> list[dict]:
    async with async_session() as db:
        rows = (await db.execute(text("""
            SELECT bti_ref, taric_code, product_desc,
                   classification_rationale, legal_basis, issuing_country
            FROM bti_rulings
            WHERE taric_code LIKE :prefix
            ORDER BY start_date DESC NULLS LAST
            LIMIT :lim
        """), {"prefix": f"{taric_code}%", "lim": limit})).fetchall()
    return [dict(r._mapping) for r in rows]


# == Measures ==

async def get_measures_for_code(taric_code: str, origin_country: str | None = None) -> list[dict]:
    """
    v2 fix: filtering with `geo_area_code = :origin` silently dropped
    erga-omnes measures expressed as TARIC geo *groups* (e.g. '1011').
    Keep NULLs, the exact origin, and numeric group codes.
    """
    params: dict[str, Any] = {"code": taric_code}
    sql = """
        SELECT measure_type, duty_expression, geo_area_code,
               geo_area_desc, legal_base, order_number, condition_code
        FROM taric_measures
        WHERE taric_code = :code
          AND (valid_to IS NULL OR valid_to > CURRENT_DATE)
    """
    if origin_country:
        sql += """ AND (geo_area_code IS NULL
                        OR geo_area_code = :origin
                        OR geo_area_code ~ '^[0-9]+$')"""
        params["origin"] = origin_country
    sql += " ORDER BY measure_type"
    async with async_session() as db:
        rows = (await db.execute(text(sql), params)).fetchall()
    return [dict(r._mapping) for r in rows]


async def get_random_bti_rulings(n: int = 100) -> list[dict]:
    async with async_session() as db:
        rows = (await db.execute(text("""
            SELECT bti_ref, taric_code, product_desc, classification_rationale
            FROM bti_rulings ORDER BY random() LIMIT :n
        """), {"n": n})).fetchall()
    return [dict(r._mapping) for r in rows]
