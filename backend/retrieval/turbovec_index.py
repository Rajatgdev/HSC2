# backend/retrieval/turbovec_index.py
import json
import numpy as np
import turbovec
from config import settings

_index: "turbovec.IdMapIndex | None" = None
_id_meta: list[dict] = []


def load_turbovec():
    global _index, _id_meta
    _index = turbovec.IdMapIndex.load(settings.TURBOVEC_INDEX_PATH)
    try:
        with open(f"{settings.TURBOVEC_INDEX_PATH}_meta.json") as f:
            _id_meta = json.load(f)
    except FileNotFoundError:  # v1 artifact compatibility
        with open(f"{settings.TURBOVEC_INDEX_PATH}_ids.json") as f:
            _id_meta = [{"code": c, "doc_type": "node"} for c in json.load(f)]
    return _index


def search_turbovec(embedding: list[float], top_k: int = 40) -> list[dict]:
    if _index is None:
        load_turbovec()
    q = np.array([embedding], dtype=np.float32)
    distances, indices = _index.search(q, k=min(top_k, len(_id_meta)))
    out = []
    for dist, idx in zip(distances[0], indices[0]):
        i = int(idx)
        if 0 <= i < len(_id_meta):
            m = _id_meta[i]
            out.append({"code": m["code"], "doc_type": m["doc_type"],
                        "score": float(-dist), "source": "dense"})
    return out
