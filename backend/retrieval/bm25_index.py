# backend/retrieval/bm25_index.py
import json, os
import bm25s
from config import settings

_retriever = None
_corpus_meta: list[dict] = []   # [{"code":..., "doc_type": "node"|"bti"}]


def load_bm25():
    global _retriever, _corpus_meta
    _retriever = bm25s.BM25.load(settings.BM25_INDEX_PATH, load_corpus=False)
    meta_path = os.path.join(settings.BM25_INDEX_PATH, "corpus_meta.json")
    ids_path = os.path.join(settings.BM25_INDEX_PATH, "corpus_ids.json")
    if os.path.exists(meta_path):
        with open(meta_path) as f:
            _corpus_meta = json.load(f)
    else:  # backward compatible with v1 artifacts
        with open(ids_path) as f:
            _corpus_meta = [{"code": c, "doc_type": "node"} for c in json.load(f)]
    return _retriever


def search_bm25(query: str, top_k: int = 40) -> list[dict]:
    if _retriever is None:
        load_bm25()
    tokenized = bm25s.tokenize([query], stopwords="en", show_progress=False)
    results, scores = _retriever.retrieve(tokenized, k=min(top_k, len(_corpus_meta)), show_progress=False)
    out = []
    for idx, score in zip(results[0], scores[0]):
        i = int(idx)
        if 0 <= i < len(_corpus_meta):
            m = _corpus_meta[i]
            out.append({"code": m["code"], "doc_type": m["doc_type"],
                        "score": float(score), "source": "bm25"})
    return out
