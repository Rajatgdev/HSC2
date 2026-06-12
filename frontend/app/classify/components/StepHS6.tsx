"use client";
import type { Candidate, HS6Result } from "@/lib/api";

const CONF: Record<string, string> = {
  high: "text-[var(--good)] border-[var(--good)]",
  medium: "text-[#9A6B12] border-[#9A6B12]",
  low: "text-[var(--stamp)] border-[var(--stamp)]",
};

export default function StepHS6({ hs6, candidates, onBack, onNext, onOverride }:
  { hs6: HS6Result; candidates: Candidate[]; onBack: () => void; onNext: () => void; onOverride: (code: string) => void }) {
  const selected = candidates.find((c) => c.code === hs6.code);
  return (
    <section>
      <div className="font-code text-[11px] tracking-[0.16em] uppercase text-[var(--stamp)] mb-2">Entry 03 · Universal subheading</div>
      <h1 className="font-serif-d text-3xl font-semibold mb-2">HS6 selected — and here's the evidence.</h1>
      <p className="text-[var(--muted)] mb-7 max-w-[54ch]">This 6-digit code is recognized worldwide. Check the reasoning; pick an alternative if it's wrong.</p>

      <div className="bg-white border border-[var(--ink)] rounded-xl p-6 shadow-[0_3px_0_var(--ink)]">
        <div className="flex justify-between items-start gap-4">
          <div>
            <div className="font-code text-[26px] font-semibold tracking-wider">
              {hs6.code.replace(/(\d{2})(?=\d)/g, "$1 ")}
            </div>
            <div className="font-code text-[12.5px] text-[var(--muted)] mt-1">{selected?.ancestor_path ?? hs6.description}</div>
          </div>
          <span className={`font-code text-[11px] tracking-widest uppercase border-[1.5px] rounded px-2.5 py-1 -rotate-2 shrink-0 ${CONF[hs6.confidence]}`}>
            {hs6.confidence} confidence
          </span>
        </div>
        <p className="mt-3 text-sm">{hs6.explanation}</p>
        <p className="font-code text-xs text-[var(--muted)] mt-2.5">
          Rule applied: {hs6.gri_applied || "—"} · Reranker score {hs6.rerank_score?.toFixed(2)}
        </p>

        {selected && selected.evidence?.length > 0 && (
          <details className="mt-3.5 border-t border-[var(--line)] pt-3">
            <summary className="cursor-pointer text-[13px] font-semibold text-[var(--muted)] hover:text-[var(--ink)]">
              Why this code — retrieval evidence ({selected.evidence.length} sources)
            </summary>
            <div className="mt-2.5 flex flex-col gap-2">
              {selected.evidence.map((e, i) => (
                <div key={i} className="font-code text-[12.5px] text-[var(--muted)] flex gap-2 items-baseline">
                  <span className={`text-[10px] border rounded px-1.5 uppercase tracking-widest ${e.doc_type === "bti" ? "text-[var(--stamp)] border-[var(--stamp)]" : "border-[var(--line)]"}`}>
                    {e.doc_type === "bti" ? "BTI" : `${e.index} #${e.rank}`}
                  </span>
                  {e.doc_code}
                </div>
              ))}
            </div>
          </details>
        )}

        {hs6.alternatives?.length > 0 && (
          <div className="mt-2">
            {hs6.alternatives.map((a) => (
              <button key={a.code} onClick={() => onOverride(a.code)}
                className="block font-code text-[13px] text-[var(--muted)] underline hover:text-[var(--ink)] py-1 text-left">
                Disagree? Use {a.code} — {a.reason}
              </button>
            ))}
          </div>
        )}
      </div>

      <div className="flex gap-3 mt-6">
        <button onClick={onBack} className="border border-[var(--line)] rounded-md px-5 py-3 font-semibold hover:border-[var(--ink)]">← Edit description</button>
        <button onClick={onNext} className="bg-[var(--ink)] text-white rounded-md px-5 py-3 font-semibold hover:bg-[#1d2e54]">Narrow to 10 digits →</button>
      </div>
    </section>
  );
}
