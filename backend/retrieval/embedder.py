# backend/retrieval/embedder.py
"""Embedding with LRU cache + retry. v1 hit OpenAI on every keystroke-level call."""
import asyncio
import hashlib
from collections import OrderedDict
from openai import AsyncOpenAI
from config import settings

_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
_cache: OrderedDict[str, list[float]] = OrderedDict()


async def embed_query(text: str) -> list[float]:
    key = hashlib.sha1(text.strip().lower().encode()).hexdigest()
    if key in _cache:
        _cache.move_to_end(key)
        return _cache[key]

    last_err = None
    for attempt in range(3):
        try:
            resp = await _client.embeddings.create(
                model=settings.EMBED_MODEL, input=[text], dimensions=settings.EMBED_DIMS,
            )
            emb = resp.data[0].embedding
            _cache[key] = emb
            if len(_cache) > settings.EMBED_CACHE_SIZE:
                _cache.popitem(last=False)
            return emb
        except Exception as e:
            last_err = e
            await asyncio.sleep(0.5 * (2 ** attempt))
    raise last_err
