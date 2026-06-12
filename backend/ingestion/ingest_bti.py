# backend/ingestion/ingest_bti.py
"""
Source: EBTI Full database
Place files at: backend/data/taric/DDS2-EBTI_Full/EBTI_YYYY.csv

Run: python -m ingestion.ingest_bti
"""
import asyncio
import glob
from datetime import datetime, date
import pandas as pd
from openai import AsyncOpenAI
from db.session import async_session
from sqlalchemy import text
from config import settings

oai = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)


def parse_date(val) -> date | None:
    if not pd.notna(val):
        return None
    val = str(val).strip()
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(val, fmt).date()
        except ValueError:
            continue
    return None


async def embed_batch(texts: list[str], batch_size: int = 100) -> list[list[float]]:
    all_embs = []
    for i in range(0, len(texts), batch_size):
        chunk = texts[i:i+batch_size]
        resp = await oai.embeddings.create(
            model=settings.EMBED_MODEL,
            input=chunk,
            dimensions=settings.EMBED_DIMS,
        )
        all_embs.extend([r.embedding for r in resp.data])
    return all_embs


async def main():
    # Load recent years only for MVP — change range for full ingest
    files = sorted(glob.glob("data/taric/DDS2-EBTI_Full/EBTI_202*.csv"))
    print(f"Loading {len(files)} files: {[f.split('/')[-1] for f in files]}")

    dfs = []
    for f in files:
        df = pd.read_csv(f, dtype=str, on_bad_lines="skip")
        df.columns = df.columns.str.strip().str.replace('"', '')
        dfs.append(df)

    df = pd.concat(dfs, ignore_index=True)
    print(f"Total rows loaded: {len(df)}")

    # Only keep English rulings and valid status
    if "LANGUAGE" in df.columns:
        df = df[df["LANGUAGE"].str.upper().str.strip() == "EN"]
    if "STATUS" in df.columns:
        df = df[df["STATUS"].str.upper().str.strip().isin(["VALID", "EXPIRED", ""])]

    df = df.dropna(subset=["BTI_REFERENCE", "NOMENCLATURE_CODE", "DESCRIPTION_OF_GOODS"])
    df = df.drop_duplicates(subset=["BTI_REFERENCE"])

    # Clean TARIC code — remove trailing asterisks
    df["NOMENCLATURE_CODE"] = df["NOMENCLATURE_CODE"].str.replace("*", "", regex=False).str.strip()

    print(f"Rows after filtering (EN, valid, non-null): {len(df)}")

    embed_texts = (
        df["DESCRIPTION_OF_GOODS"].fillna("")
        + " | Classified: " + df["NOMENCLATURE_CODE"].fillna("")
        + " | " + df["CLASSIFICATION_JUSTIFICATION"].fillna("")
    ).tolist()

    print(f"Embedding {len(df)} BTI rulings...")
    embeddings = await embed_batch(embed_texts)

    async with async_session() as db:
        for i, (_, row) in enumerate(df.iterrows()):
            await db.execute(text("""
                INSERT INTO bti_rulings
                    (bti_ref, taric_code, product_desc, legal_basis,
                     classification_rationale, issuing_country,
                     start_date, end_date, embedding)
                VALUES
                    (:ref, :code, :desc, :legal, :rationale,
                     :country, :start, :end, CAST(:emb AS vector))
                ON CONFLICT (bti_ref) DO NOTHING
            """), {
                "ref": row["BTI_REFERENCE"],
                "code": row["NOMENCLATURE_CODE"],
                "desc": row["DESCRIPTION_OF_GOODS"] if pd.notna(row.get("DESCRIPTION_OF_GOODS")) else None,
                "legal": row.get("KEYWORDS") if pd.notna(row.get("KEYWORDS")) else None,
                "rationale": row.get("CLASSIFICATION_JUSTIFICATION") if pd.notna(row.get("CLASSIFICATION_JUSTIFICATION")) else None,
                "country": row.get("ISSUING_COUNTRY") if pd.notna(row.get("ISSUING_COUNTRY")) else None,
                "start": parse_date(row.get("START_DATE_OF_VALIDITY")),
                "end": parse_date(row.get("END_DATE_OF_VALIDITY")),
                "emb": str(embeddings[i]),
            })
            if (i + 1) % 500 == 0:
                await db.commit()
                print(f"  {i+1}/{len(df)} inserted")
        await db.commit()

    print(f"Done. {len(df)} BTI rulings ingested.")


if __name__ == "__main__":
    asyncio.run(main())