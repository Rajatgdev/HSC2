# backend/retrieval/expansion.py
"""
Query expansion: rewrite layperson product descriptions into customs
nomenclature vocabulary before retrieval. Cheap (mini model), big recall win —
users say "winter jacket", the CN says "anoraks, wind-cheaters, wind-jackets".
"""
import json
from openai import AsyncOpenAI
from config import settings

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

SYSTEM = """You rewrite product descriptions into EU Combined Nomenclature
vocabulary for search. Return JSON: {"expanded": "<one paragraph>", "key_attributes": ["..."]}.
- Use customs terms (e.g. 'knitted', 'of man-made fibres', 'put up for retail sale').
- Keep ALL facts from the original. Add NO facts not stated or strictly implied.
- key_attributes: 3-6 short attribute strings that matter for classification."""


async def expand_query(description: str) -> dict:
    try:
        resp = await client.chat.completions.create(
            model=settings.LLM_MODEL_FAST,
            temperature=0.0,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": description},
            ],
        )
        data = json.loads(resp.choices[0].message.content or "{}")
        if not data.get("expanded"):
            raise ValueError("empty expansion")
        return data
    except Exception:
        return {"expanded": description, "key_attributes": []}
