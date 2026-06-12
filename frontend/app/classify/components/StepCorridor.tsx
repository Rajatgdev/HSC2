"use client";
import { useState } from "react";

const ORIGINS = [["CN","China"],["IN","India"],["US","United States"],["GB","United Kingdom"],["VN","Vietnam"],["TR","Türkiye"]];
const DESTS = [["IE","Ireland"],["DE","Germany"],["FR","France"],["NL","Netherlands"],["ES","Spain"],["IT","Italy"]];
const INCO = ["", "EXW", "FOB", "CIF", "DDP", "DAP"];

export default function StepCorridor({ onNext }: { onNext: (o: string, d: string, i?: string) => void }) {
  const [origin, setOrigin] = useState("CN");
  const [dest, setDest] = useState("IE");
  const [inco, setInco] = useState("");
  const sel = "w-full p-3 border border-[var(--line)] rounded-md bg-white focus:outline-[var(--ink)]";
  return (
    <section>
      <div className="font-code text-[11px] tracking-[0.16em] uppercase text-[var(--stamp)] mb-2">Entry 01 · Trade corridor</div>
      <h1 className="font-serif-d text-3xl font-semibold mb-2">Where is this shipment moving?</h1>
      <p className="text-[var(--muted)] mb-7 max-w-[54ch]">Origin and destination decide which duties, preferences and restrictions apply to the final code.</p>
      <div className="grid sm:grid-cols-2 gap-4 mb-4">
        <div><label className="block text-sm font-semibold mb-1.5">Origin country</label>
          <select className={sel} value={origin} onChange={(e) => setOrigin(e.target.value)}>
            {ORIGINS.map(([c, n]) => <option key={c} value={c}>{n} ({c})</option>)}
          </select></div>
        <div><label className="block text-sm font-semibold mb-1.5">Destination country</label>
          <select className={sel} value={dest} onChange={(e) => setDest(e.target.value)}>
            {DESTS.map(([c, n]) => <option key={c} value={c}>{n} ({c})</option>)}
          </select></div>
      </div>
      <div className="mb-4"><label className="block text-sm font-semibold mb-1.5">Incoterm <span className="font-normal text-[var(--muted)]">(optional)</span></label>
        <select className={sel} value={inco} onChange={(e) => setInco(e.target.value)}>
          {INCO.map((i) => <option key={i} value={i}>{i || "Not specified"}</option>)}
        </select>
        <p className="text-xs text-[var(--muted)] mt-1.5">Used for context only — it doesn't change the classification.</p></div>
      <button onClick={() => onNext(origin, dest, inco || undefined)}
        className="bg-[var(--ink)] text-white rounded-md px-5 py-3 font-semibold hover:bg-[#1d2e54]">
        Describe the product →
      </button>
    </section>
  );
}
