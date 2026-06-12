"use client";
import { useState } from "react";
import type { Suggestion } from "@/lib/api";

export default function StepResult({ suggestions, ambiguous, ambiguityNote, onFeedback, onRestart }:
  { suggestions: Suggestion[]; ambiguous: boolean; ambiguityNote: string | null;
    onFeedback: (code: string, fb: string) => void; onRestart: () => void }) {
  const [fb, setFb] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const primary = suggestions[0];
  const rest = suggestions.slice(1);
  return (
    <section>
      <div className="font-code text-[11px] tracking-[0.16em] uppercase text-[var(--stamp)] mb-2">Entry 05 · Final classification</div>
      <h1 className="font-serif-d text-3xl font-semibold mb-2">{primary ? "Filed and stamped." : "Genuinely ambiguous."}</h1>
      <p className="text-[var(--muted)] mb-7 max-w-[54ch]">Primary suggestion with applicable measures for your corridor. The evidence trail stays in the session log.</p>

      {primary && (
        <div className="relative bg-white border-[1.5px] border-[var(--ink)] rounded-xl p-6 mb-4">
          <span className={`absolute top-4 right-4 font-code text-[11px] tracking-widest uppercase border-2 rounded px-3 py-1.5 rotate-3
            ${primary.confidence === "high" ? "text-[var(--good)] border-[var(--good)]" : "text-[#9A6B12] border-[#9A6B12]"}`}>
            Classified · {primary.confidence}
          </span>
          <div className="font-code text-[26px] font-semibold tracking-wider flex items-center gap-3">
            {primary.code.replace(/(\d{2})(?=\d)/g, "$1 ")}
            <button onClick={() => { navigator.clipboard?.writeText(primary.code); setCopied(true); }}
              className="font-code text-xs border border-[var(--line)] rounded px-2.5 py-1 text-[var(--muted)] hover:border-[var(--ink)] hover:text-[var(--ink)]">
              {copied ? "Copied" : "Copy"}
            </button>
          </div>
          <div className="font-code text-[12.5px] text-[var(--muted)] mt-1">{primary.description}</div>
          <p className="mt-3 text-sm">{primary.explanation}</p>
          <p className="font-code text-xs text-[var(--muted)] mt-2.5">
            {primary.bti_reference ? `BTI precedent: ${primary.bti_reference} · ` : ""}{primary.gri_applied}
          </p>
          {primary.measures?.length > 0 && (
            <div className="mt-4">
              <h4 className="font-code text-[11px] tracking-widest uppercase text-[var(--muted)] mb-2">Measures</h4>
              {primary.measures.map((m, i) => (
                <div key={i} className="flex justify-between font-code text-[13px] py-1.5 border-b border-dashed border-[var(--line)]">
                  <span>{m.measure_type}{m.geo_area_desc ? ` (${m.geo_area_desc})` : ""}</span>
                  <span>{m.duty_expression}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {(rest.length > 0 || ambiguous) && (
        <div className="bg-[#FBF6EC] border border-[#E8D9B8] rounded-lg p-4 text-[13.5px] mb-4">
          {rest.map((s) => (
            <p key={s.code}>Runner-up: <b className="font-code">{s.code}</b> — {s.explanation}</p>
          ))}
          {ambiguous && <p className="mt-1">{ambiguityNote ?? ""} Genuinely unsure? A Binding Tariff Information ruling is free and legally binding for 3 years.</p>}
        </div>
      )}

      {primary && (
        <div className="mb-6">
          <h4 className="font-code text-[11px] tracking-widest uppercase text-[var(--muted)] mb-2">Was this correct?</h4>
          <div className="flex gap-2">
            {[["correct", "✓ Correct"], ["partial", "Partially"], ["wrong", "Wrong"]].map(([k, label]) => (
              <button key={k} onClick={() => { setFb(k); onFeedback(primary.code, k); }}
                className={`border rounded-full px-4 py-2 text-sm ${fb === k ? "bg-[var(--ink)] text-white border-[var(--ink)]" : "bg-[var(--paper)] border-[var(--line)] hover:border-[var(--ink)]"}`}>
                {label}
              </button>
            ))}
          </div>
        </div>
      )}
      <button onClick={onRestart} className="border border-[var(--line)] rounded-md px-5 py-3 font-semibold hover:border-[var(--ink)]">Classify another product</button>
    </section>
  );
}
