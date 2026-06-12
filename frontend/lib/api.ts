// frontend/lib/api.ts
const BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new Error(detail.detail ?? `Request failed (${res.status})`);
  }
  return res.json();
}

export type Evidence = { doc_code: string; doc_type: "node" | "bti"; index: string; rank: number; score: number };
export type Candidate = { code: string; description: string; ancestor_path?: string; rerank_score: number; evidence: Evidence[] };
export type HS6Result = { code: string; description: string; explanation: string; confidence: "high" | "medium" | "low"; gri_applied: string; rerank_score: number; alternatives: { code: string; reason: string }[] };
export type Question = { question: string; options: string[]; discriminator_key: string; why_it_matters: string };
export type Suggestion = { code: string; description: string; confidence: string; explanation: string; gri_applied: string; bti_reference: string | null; measures: { measure_type: string; duty_expression: string; geo_area_desc: string }[] };

export const api = {
  startSession: (origin_country: string, destination_country: string, incoterms?: string) =>
    post<{ session_id: string }>("/api/classify/session", { origin_country, destination_country, incoterms }),
  suggestHS6: (session_id: string, description: string) =>
    post<{ hs6: HS6Result; candidates: Candidate[]; narrowing_questions: Question[]; retrieval: { expanded_query: string; key_attributes: string[] } }>(
      "/api/classify/hs6/suggest", { session_id, description }),
  overrideHS6: (session_id: string, hs6_code: string) =>
    post<{ selected_hs6: string; narrowing_questions: Question[] }>("/api/classify/hs6/override", { session_id, hs6_code }),
  suggestHS10: (session_id: string, answers: Record<string, string>) =>
    post<{ suggestions: Suggestion[]; ambiguous: boolean; ambiguity_note: string | null }>("/api/classify/hs10/suggest", { session_id, answers }),
  feedback: (session_id: string, final_hs10: string, feedback: string, note?: string) =>
    post("/api/classify/feedback", { session_id, final_hs10, feedback, note }),
};
