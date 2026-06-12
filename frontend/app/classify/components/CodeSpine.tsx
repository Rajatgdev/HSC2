"use client";
// The signature element: the 10-digit code assembles as the flow progresses.
const ROWS: [string, number][] = [
  ["Chapter (2)", 2], ["Heading (4)", 4], ["HS6 — universal (6)", 6],
  ["CN8 — EU (8)", 8], ["TARIC10 — final (10)", 10],
];

export default function CodeSpine({ code }: { code: string }) {
  const n = code.length;
  return (
    <aside className="lg:sticky lg:top-24 self-start">
      <h3 className="font-code text-[11px] tracking-[0.14em] uppercase text-[var(--muted)] mb-3">
        Commodity code
      </h3>
      <div className="flex gap-1.5 flex-wrap">
        {Array.from({ length: 5 }).map((_, p) => (
          <div key={p} className="flex gap-[3px]">
            {[0, 1].map((i) => {
              const idx = p * 2 + i;
              const filled = idx < n;
              return (
                <div key={i}
                  className={`w-[30px] h-[42px] rounded border flex items-center justify-center font-code text-[19px] font-semibold transition-all duration-300
                    ${filled ? "text-[var(--ink)] border-[var(--ink)] -translate-y-0.5 shadow-[0_2px_0_var(--ink)] bg-white"
                             : "text-[var(--line)] border-dashed border-[var(--line)] bg-white"}`}>
                  {filled ? code[idx] : "·"}
                </div>
              );
            })}
          </div>
        ))}
      </div>
      <div className="mt-4">
        {ROWS.map(([label, need]) => (
          <div key={label}
            className={`grid grid-cols-[14px_1fr] gap-2.5 py-2 border-b border-[var(--line)] text-[12.5px]
              ${n >= need ? "text-[var(--ink)]" : "text-[var(--muted)]"}`}>
            <span className={`font-code ${n >= need ? "text-[var(--good)]" : "text-[var(--line)]"}`}>
              {n >= need ? "●" : "○"}
            </span>
            <span className="font-code font-medium">{label}{n >= need && ` — ${code.slice(0, need)}`}</span>
          </div>
        ))}
      </div>
      <p className="mt-4 text-[11.5px] text-[var(--muted)] leading-relaxed">
        HS6 is recognized worldwide. Digits 7–8 are the EU Combined Nomenclature; 9–10 are
        TARIC-specific. Final liability rests with the declarant — consider a BTI for binding certainty.
      </p>
    </aside>
  );
}
