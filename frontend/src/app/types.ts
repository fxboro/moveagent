export type Match = { id: number; institution_name: string; program_name: string; tuition_fee_structure: string; matching_rationale: string; source_url: string; is_approved_by_human: boolean };
export type Scores = { direct_work: number; masters_score: number; bachelors_score: number; ausbildung_score: number; monetization_strategy: string };
export type Candidate = { id: number; name: string; raw_cv_text: string; language_level: string; current_status: string; mode: string; error: string | null; created_at: string };
export type Detail = Candidate & { triage_matrix: Scores | null; matches: Match[]; dossiers: { id: number; document_type: string; content: string }[]; events: { id: number; agent: string; message: string; created_at: string }[] };
export type Check = { id: number; source: string; source_url: string; institution_name: string; status: string; note: string; checked_at: string; verified: boolean };
export type Dashboard = { mode: string; candidates: Candidate[]; checks: Check[] };

export async function api<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`/api${path}`, { ...options, headers: { 'Content-Type': 'application/json', ...options?.headers }, cache: 'no-store' });
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(typeof body.detail === 'string' ? body.detail : `Request failed (${response.status}). Check your input or backend connection.`);
  }
  return response.json();
}
