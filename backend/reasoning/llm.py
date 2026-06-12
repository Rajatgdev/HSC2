# backend/reasoning/llm.py
"""Single LLM call helper: structured outputs + retry. No more regex JSON scraping."""
import asyncio
import json
from openai import AsyncOpenAI
from config import settings

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


async def call_json(system: str, user: str, schema: dict,
                    model: str | None = None, temperature: float = 0.0) -> dict:
    last_err = None
    for attempt in range(2):
        try:
            resp = await client.chat.completions.create(
                model=model or settings.LLM_MODEL,
                temperature=temperature,
                response_format={"type": "json_schema", "json_schema": schema},
                messages=[{"role": "system", "content": system},
                          {"role": "user", "content": user}],
            )
            return json.loads(resp.choices[0].message.content or "{}")
        except Exception as e:
            last_err = e
            await asyncio.sleep(0.5 * (attempt + 1))
    raise last_err
