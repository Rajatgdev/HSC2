"use client";
import { useState } from "react";
import { api, Candidate, HS6Result, Question, Suggestion } from "@/lib/api";
import CodeSpine from "./components/CodeSpine";
import StepCorridor from "./components/StepCorridor";
import StepDescription from "./components/StepDescription";
import StepHS6 from "./components/StepHS6";
import StepNarrowing from "./components/StepNarrowing";
import StepResult from "./components/StepResult";

type Step = 1 | 2 | 3 | 4 | 5;

export default function ClassifyPage() {
  const [step, setStep] = useState<Step>(1);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [corridor, setCorridor] = useState({ origin: "", dest: "", inco: "" });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hs6, setHS6] = useState<HS6Result | null>(null);
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [questions, setQuestions] = useState<Question[]>([]);
  const [result, setResult] = useState<{ suggestions: Suggestion[]; ambiguous: boolean; ambiguity_note: string | null } | null>(null);

  const spineCode =
    step >= 5 && result?.suggestions[0] ? result.suggestions[0].code
    : step >= 3 && hs6?.code ? hs6.code
    : "";

  const startSession = async (origin: string, dest: string, inco?: string) => {
    setError(null);
    try {
      const { session_id } = await api.startSession(origin, dest, inco);
      setSessionId(session_id);
      setCorridor({ origin, dest, inco: inco ?? "" });
      setStep(2);
    } catch (e) { setError((e as Error).message); }
  };

  const classify = async (description: string) => {
    if (!sessionId) return;
    setLoading(true); setError(null);
    try {
      const res = await api.suggestHS6(sessionId, description);
      setHS6(res.hs6); setCandidates(res.candidates); setQuestions(res.narrowing_questions);
      setStep(3);
    } catch (e) { setError((e as Error).message); }
    finally { setLoading(false); }
  };

  const override = async (code: string) => {
    if (!sessionId || !hs6) return;
    setLoading(true);
    try {
      const res = await api.overrideHS6(sessionId, code);
      setHS6({ ...hs6, code, explanation: "Manually selected.", confidence: "medium", alternatives: [] });
      setQuestions(res.narrowing_questions);
    } finally { setLoading(false); }
  };

  const narrow = async (answers: Record<string, string>) => {
    if (!sessionId) return;
    setLoading(true); setError(null);
    try {
      const res = await api.suggestHS10(sessionId, answers);
      setResult(res); setStep(5);
    } catch (e) { setError((e as Error).message); }
    finally { setLoading(false); }
  };

  return (
    <div className="min-h-screen">
      <header className="border-b border-[var(--line)] sticky top-0 bg-[var(--paper)] z-10">
        <div className="max-w-[1100px] mx-auto px-6 py-4 flex items-baseline justify-between">
          <div className="font-serif-d font-bold text-xl">
            HS Ledger <small className="font-code font-normal text-[11px] text-[var(--muted)] ml-2 tracking-widest">TARIC · CN 2026 · EBTI</small>
          </div>
          {corridor.origin && (
            <div className="font-code text-xs text-[var(--muted)]">
              <b className="text-[var(--ink)]">{corridor.origin}</b> → <b className="text-[var(--ink)]">{corridor.dest}</b>{corridor.inco && ` · ${corridor.inco}`}
            </div>
          )}
        </div>
      </header>

      <div className="max-w-[1100px] mx-auto px-6 grid lg:grid-cols-[1fr_280px] gap-12 py-10 pb-20">
        <main>
          {error && step !== 2 && <p className="mb-4 text-sm text-[var(--stamp)]">{error}</p>}
          {step === 1 && <StepCorridor onNext={startSession} />}
          {step === 2 && <StepDescription loading={loading} error={error} onBack={() => setStep(1)} onSubmit={classify} />}
          {step === 3 && hs6 && <StepHS6 hs6={hs6} candidates={candidates} onBack={() => setStep(2)} onNext={() => setStep(4)} onOverride={override} />}
          {step === 4 && <StepNarrowing questions={questions} loading={loading} onBack={() => setStep(3)} onSubmit={narrow} />}
          {step === 5 && result && (
            <StepResult suggestions={result.suggestions} ambiguous={result.ambiguous} ambiguityNote={result.ambiguity_note}
              onFeedback={(code, fb) => sessionId && api.feedback(sessionId, code, fb)}
              onRestart={() => location.reload()} />
          )}
        </main>
        <CodeSpine code={spineCode} />
      </div>

      <footer className="border-t border-[var(--line)] py-5">
        <div className="max-w-[1100px] mx-auto px-6 text-xs text-[var(--muted)]">
          HS Ledger v2 · grounded in CN 2026 + EBTI 2020–2026 · every suggestion carries its retrieval evidence
        </div>
      </footer>
    </div>
  );
}
