"use client";
import { useState } from "react";
import type { Question } from "@/lib/api";

export default function StepNarrowing({ questions, loading, onBack, onSubmit }:
  { questions: Question[]; loading: boolean; onBack: () => void; onSubmit: (a: Record<string, string>) => void }) {
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const done = questions.every((q) => answers[q.discriminator_key]);
  return (
    <section>
      <div className="font-code text-[11px] tracking-[0.16em] uppercase text-[var(--stamp)] mb-2">Entry 04 · Narrowing</div>
      <h1 className="font-serif-d text-3xl font-semibold mb-2">
        {questions.length ? `${questions.length === 1 ? "One answer separates" : "A few answers separate"} the remaining codes.` : "No narrowing needed."}
      </h1>
      <p className="text-[var(--muted)] mb-7 max-w-[54ch]">Each question exists because the candidate codes genuinely differ on it — nothing you already told us is re-asked.</p>
      {questions.map((q) => (
        <div key={q.discriminator_key} className="bg-white border border-[var(--line)] rounded-xl p-5 mb-3.5">
          <label className="block text-sm font-semibold">{q.question}</label>
          {q.why_it_matters && <p className="text-xs text-[var(--muted)] mt-1 mb-3">Why it matters: {q.why_it_matters}</p>}
          <div className="flex flex-wrap gap-2">
            {q.options.map((o) => (
              <button key={o}
                onClick={() => setAnswers({ ...answers, [q.discriminator_key]: o })}
                className={`border rounded-full px-4 py-2 text-sm ${answers[q.discriminator_key] === o
                  ? "bg-[var(--ink)] text-white border-[var(--ink)]"
                  : "bg-[var(--paper)] border-[var(--line)] hover:border-[var(--ink)]"}`}>
                {o}
              </button>
            ))}
          </div>
        </div>
      ))}
      <div className="flex gap-3 mt-6">
        <button onClick={onBack} className="border border-[var(--line)] rounded-md px-5 py-3 font-semibold hover:border-[var(--ink)]">← Back</button>
        <button onClick={() => onSubmit(answers)} disabled={(!done && questions.length > 0) || loading}
          className="bg-[var(--ink)] text-white rounded-md px-5 py-3 font-semibold hover:bg-[#1d2e54] disabled:opacity-50">
          {loading ? "Classifying…" : "Get TARIC10 code →"}
        </button>
      </div>
    </section>
  );
}
