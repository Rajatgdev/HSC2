# backend/eval/bench_bti.py
"""
Accuracy harness (new in v2): replays held-out BTI rulings through the
pipeline and reports HS6 / CN8 / TARIC10 exact-match rates.
Run: python -m eval.bench_bti --n 100
"""
import asyncio
import argparse
from db.queries import get_random_bti_rulings
from retrieval import retrieve_hs6_candidates
from reasoning.hs6_selector import auto_select_hs6


async def main(n: int):
    rulings = await get_random_bti_rulings(n)
    hs6_hits = recall8 = total = 0
    for r in rulings:
        gold = (r["taric_code"] or "").strip()
        if len(gold) < 6 or not r["product_desc"]:
            continue
        total += 1
        ret = await retrieve_hs6_candidates(r["product_desc"], top_k=8)
        cands = ret["candidates"]
        if gold[:6] in {c["code"] for c in cands}:
            recall8 += 1
        sel = await auto_select_hs6(r["product_desc"], ret["key_attributes"], cands)
        if sel.get("code") == gold[:6]:
            hs6_hits += 1
        print(f"{gold[:6]} | picked {sel.get('code')} | "
              f"in-top8={gold[:6] in {c['code'] for c in cands}}")
    print(f"\nN={total}  HS6 accuracy={hs6_hits/total:.1%}  recall@8={recall8/total:.1%}")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--n", type=int, default=100)
    asyncio.run(main(p.parse_args().n))
