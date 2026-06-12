# HS Ledger v2 — TARIC HS10 Classifier

Grounded 10-digit EU commodity-code classification. CN 2026 + EBTI 2020–2026.
Rebuild of HSC v1 with verified-grounding fixes in the backend and a redesigned UX.

## What changed vs v1 (and why)

### Grounding / accuracy (backend)
| # | v1 problem (verified in the repo/artifacts) | v2 fix |
|---|---|---|
| 1 | **BTI rulings were missing from the shipped indexes.** The artifacts contain exactly 11,649 docs = SUBHEADING + CN8 nodes only (0 duplicate codes, all 6/8-digit). The build script supported BTI, but the index was built before BTI ingest. | `build_indexes.py` refuses to build if the BTI table is empty; writes `corpus_meta.json` with `doc_type` so BTI hits are visible in provenance. |
| 2 | **~84% of retrieval was thrown away.** HS6 search filtered out every CN8 hit post-hoc (9,800 of 11,649 docs), only "widening" as a fallback. | Doc-level RRF, then **always** roll up CN8/TARIC10/BTI hits to parent HS6 with score aggregation + per-HS6 evidence list. |
| 3 | **2-bit vector quantization** (`bit_width=2`) on a tiny ~70 MB corpus — large recall loss to save ~3 MB. | float32 index. |
| 4 | **LLM could return ungrounded codes.** HS6 selector trusted the model string; HS10 prompt said "only children" but nothing enforced it; phantom BTI references possible. | Hard validation: HS6 must be in candidate set (else fallback + low confidence), HS10 suggestions filtered to actual children, BTI refs validated against the rows shown to the model. |
| 5 | **Regex JSON scraping** of LLM output. | OpenAI structured outputs (strict JSON schema) + retry. |
| 6 | **Reranker scored bare heading text** — often just "Other". | Reranks against chapter > heading > subheading path + notes. |
| 7 | Layperson vocab vs CN vocab mismatch ("winter jacket" vs "anoraks, wind-cheaters"). | Query expansion step (gpt-4o-mini) into nomenclature terms before retrieval. |
| 8 | Origin filter on measures dropped erga-omnes measures expressed as TARIC geo groups. | Group-aware measures filter. |
| 9 | Off-by-one index drift (1 node missing embedding, silently skipped). | Meta files written in lockstep; loud warning on missing embeddings. |
| 10 | No accuracy measurement. | `python -m eval.bench_bti --n 100` replays held-out BTI rulings → HS6 accuracy + recall@8. |
| Other | `update_session` column whitelist; CORS via env; ISO-2 validation; `/hs6/override` endpoint; embedding LRU cache + retries. | |

### UX (frontend)
- **Code Spine** — the 10-digit code physically assembles (2→4→6→8→10) in a sticky rail as you progress; progress *is* the code, and each digit-pair is labeled (chapter / heading / HS6 / CN8 / TARIC10).
- **Provenance panel** — "Why this code" expands the retrieval evidence (BM25/dense rank, BTI precedents) behind the HS6 pick. Trust through receipts, not vibes.
- **Classifiability coach** — live checklist (material / function / processing / packaging) that fills as the description becomes classifiable, before any API call is wasted.
- **Why-it-matters on every narrowing question**, one-tap chip answers, no re-asking facts already stated.
- **Stamped result** with copyable code, corridor-filtered measures, runner-up + BTI-application nudge on ambiguity, inline feedback.
- Open `demo.html` in a browser to walk the full flow with mocked data — no backend needed.

## Run
```bash
# backend
cd backend && pip install -r requirements.txt
cp .env.example .env   # set OPENAI_API_KEY, DATABASE_URL
python -m ingestion.ingest_full_taric && python -m ingestion.ingest_bti
python -m ingestion.generate_embeddings && python -m ingestion.build_indexes
uvicorn main:app --reload

# frontend
cd frontend && npm i && NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev

# accuracy benchmark
cd backend && python -m eval.bench_bti --n 100
```

Deploy as before: frontend → Vercel (`NEXT_PUBLIC_API_URL`), backend → Railway (set `CORS_ORIGINS`), DB → Neon. The new index artifacts must be rebuilt (`build_indexes`) and committed/uploaded since the layout changed (`corpus_meta.json`, `turbovec_index_meta.json`); v2 loaders fall back to v1 artifacts if the new files are absent.
