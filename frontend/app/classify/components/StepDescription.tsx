"use client";
import { useMemo, useState } from "react";

const CHECKS: [string, RegExp][] = [
  ['Material or composition (e.g. "100% polyester", "stainless steel")', /polyester|cotton|steel|wool|plastic|leather|aluminium|nylon|%/i],
  ["Function or use (what it does / who uses it)", /jacket|use|for |wear|tool|valve|machine|device|garment/i],
  ["Processing state (woven / knitted / assembled / raw…)", /woven|knitted|assembled|raw|padded|coated|stitched|moulded/i],
  ["Packaging (retail vs bulk)", /retail|bulk|packed|individually|carton/i],
];

const LOAD_LINES = [
  "Expanding description into nomenclature terms…",
  "Searching CN 2026 entries + EBTI rulings (BM25 + dense)…",
  "Reranking candidates against chapter notes…",
  "Applying General Rules of Interpretation…",
];

export default function StepDescription({ loading, error, onBack, onSubmit }:
  { loading: boolean; error: string | null; onBack: () => void; onSubmit: (d: string) => void }) {
  const [desc, setDesc] = useState("");
  const hits = useMemo(() => CHECKS.map(([, re]) => re.test(desc)), [desc]);
  return (
    <section>
      <div className="font-code text-[11px] tracking-[0.16em] uppercase text-[var(--stamp)] mb-2">Entry 02 · Product declaration</div>
      <h1 className="font-serif-d text-3xl font-semibold mb-2">Describe the goods as if to a customs officer.</h1>
      <p className="text-[var(--muted)] mb-7 max-w-[54ch]">Material, function, how it's made, and how it's sold. The checklist fills as your description gets classifiable.</p>
      <label className="block text-sm font-semibold mb-1.5">Product description</label>
      <textarea value={desc} onChange={(e) => setDesc(e.target.value)} rows={5}
        placeholder="e.g. Men's hooded jacket, outer shell 100% woven polyester, padded, water-resistant coating, packed individually for retail sale"
        className="w-full p-3 border border-[var(--line)] rounded-md bg-white focus:outline-[var(--ink)]" />
      <div className="border border-dashed border-[var(--line)] rounded-lg p-4 mt-3 bg-white">
        <h4 className="font-code text-[11px] tracking-[0.12em] uppercase text-[var(--muted)] mb-2">Classifiability check</h4>
        <ul>{CHECKS.map(([label], i) => (
          <li key={label} className={`text-[13px] py-0.5 ${hits[i] ? "text-[var(--good)]" : "text-[var(--muted)]"}`}>
            <span className="font-code">{hits[i] ? "● " : "○ "}</span>{label}
          </li>))}
        </ul>
      </div>
      {error && <p className="mt-3 text-sm text-[var(--stamp)]">{error}</p>}
      {loading && (
        <div className="py-6">{LOAD_LINES.map((l, i) => (
          <p key={l} className="font-code text-[13px] text-[var(--muted)] py-1 animate-pulse" style={{ animationDelay: `${i * 0.5}s` }}>
            <span className="text-[var(--stamp)]">→ </span>{l}</p>))}
        </div>
      )}
      <div className="flex gap-3 mt-6">
        <button onClick={onBack} className="border border-[var(--line)] rounded-md px-5 py-3 font-semibold hover:border-[var(--ink)]">← Back</button>
        <button onClick={() => onSubmit(desc)} disabled={desc.length < 10 || loading}
          className="bg-[var(--ink)] text-white rounded-md px-5 py-3 font-semibold hover:bg-[#1d2e54] disabled:opacity-50">
          Classify →
        </button>
      </div>
    </section>
  );
}
