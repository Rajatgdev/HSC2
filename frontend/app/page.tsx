import Link from "next/link";

export default function Home() {
  return (
    <main className="min-h-screen flex items-center justify-center">
      <div className="max-w-2xl px-6 py-16">
        <p className="font-code text-[11px] tracking-[0.18em] uppercase text-[var(--stamp)] mb-4">CN 2026 · EBTI 2020–2026 · GRI 1–6</p>
        <h1 className="font-serif-d text-5xl font-semibold leading-tight mb-5">
          The 10-digit code,<br />with its paper trail.
        </h1>
        <p className="text-[var(--muted)] text-lg mb-9 max-w-[48ch]">
          Describe your goods once. HS Ledger retrieves the matching CN 2026 headings and
          binding-ruling precedents, asks only the questions that actually separate the candidate
          codes, and shows the evidence behind every digit.
        </p>
        <Link href="/classify"
          className="inline-block bg-[var(--ink)] text-white px-8 py-3.5 rounded-md font-semibold hover:bg-[#1d2e54]">
          Start a classification
        </Link>
        <p className="font-code text-xs text-[var(--muted)] mt-10">
          2 digits chapter · 4 heading · 6 universal HS · 8 EU CN · 10 TARIC
        </p>
      </div>
    </main>
  );
}
