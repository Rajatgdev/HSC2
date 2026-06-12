"""
Generate OpenAI embeddings for taric_nodes that lack them.
Run: python -m ingestion.generate_embeddings

Targets SUBHEADING + CN8 + TARIC10 levels (skip CHAPTER/HEADING — too broad).
"""
import asyncio
from openai import AsyncOpenAI
from sqlalchemy import text
from db.session import async_session
from config import settings

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
BATCH_SIZE = 100
EMBED_MODEL = settings.EMBED_MODEL  # e.g. "text-embedding-3-small"


async def embed_batch(texts: list[str]) -> list[list[float]]:
    resp = await client.embeddings.create(model=EMBED_MODEL, input=texts)
    return [d.embedding for d in resp.data]


async def main():
    async with async_session() as db:
        # Get nodes needing embeddings
        rows = (await db.execute(text("""
            SELECT code, description
            FROM taric_nodes
            WHERE level IN ('SUBHEADING', 'CN8', 'TARIC10')
              AND embedding IS NULL
              AND description IS NOT NULL
              AND description != ''
            ORDER BY code
        """))).fetchall()

    nodes = [dict(r._mapping) for r in rows]
    print(f"Nodes needing embeddings: {len(nodes)}")

    if not nodes:
        print("All nodes already have embeddings.")
        return

    for i in range(0, len(nodes), BATCH_SIZE):
        batch = nodes[i:i + BATCH_SIZE]
        texts = [n["description"][:2000] for n in batch]
        codes = [n["code"] for n in batch]

        try:
            embeddings = await embed_batch(texts)
        except Exception as e:
            print(f"  Error at batch {i}: {e}")
            continue

        async with async_session() as db:
            for code, emb in zip(codes, embeddings):
                await db.execute(text("""
                    UPDATE taric_nodes
                    SET embedding = CAST(:emb AS vector)
                    WHERE code = :code
                """), {"emb": str(emb), "code": code})
            await db.commit()

        done = min(i + BATCH_SIZE, len(nodes))
        if done % 500 == 0 or done == len(nodes):
            print(f"  Embedded {done}/{len(nodes)}")

    print("Done! Now run: python -m ingestion.build_indexes")


if __name__ == "__main__":
    asyncio.run(main())
