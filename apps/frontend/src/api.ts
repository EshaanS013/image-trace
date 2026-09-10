import type {
  AnalysisRun,
  Case,
  CustodyEvent,
  Evidence,
  Finding,
  Page,
  Report,
} from "./types";

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}
async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`/api/v1${path}`, options);
  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    try {
      const body = (await response.json()) as { detail?: { message?: string } };
      message = body.detail?.message ?? message;
    } catch {
      message = `Request failed (${response.status})`;
    }
    throw new ApiError(response.status, message);
  }
  return response.json() as Promise<T>;
}
const json = (method: string, body: unknown): RequestInit => ({
  method,
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(body),
});
export const api = {
  cases: () => request<Page<Case>>("/cases"),
  case: (id: string) => request<Case>(`/cases/${id}`),
  deleteCase: (id: string) =>
    request<void>(`/cases/${id}`, { method: "DELETE" }),
  createCase: (body: object) => request<Case>("/cases", json("POST", body)),
  patchCase: (id: string, body: object) =>
    request<Case>(`/cases/${id}`, json("PATCH", body)),
  evidence: (caseId: string, search = "") =>
    request<Page<Evidence>>(
      `/cases/${caseId}/evidence?page_size=200&search=${encodeURIComponent(search)}`,
    ),
  evidenceOne: (id: string) => request<Evidence>(`/evidence/${id}`),
  upload: (caseId: string, files: File[], actor: string) => {
    const form = new FormData();
    files.forEach((file) => form.append("files", file));
    form.append("acquired_by", actor);
    return request<{
      job_id: string;
      accepted: Evidence[];
      failures: { filename: string; error: string }[];
    }>(`/cases/${caseId}/evidence`, { method: "POST", body: form });
  },
  verify: (id: string, actor: string) =>
    request<Evidence>(
      `/evidence/${id}/verify-integrity?actor=${encodeURIComponent(actor)}`,
      { method: "POST" },
    ),
  deleteEvidence: (id: string) =>
    request<void>(`/evidence/${id}`, { method: "DELETE" }),
  reviewEvidence: (id: string, status: string, actor: string) =>
    request<Evidence>(
      `/evidence/${id}/review`,
      json("PATCH", { status, actor }),
    ),
  addNote: (id: string, actor: string, body: string) =>
    request(`/evidence/${id}/notes`, json("POST", { actor, body })),
  notes: (id: string) =>
    request<{ id: string; actor: string; body: string; created_at: string }[]>(
      `/evidence/${id}/notes`,
    ),
  analyses: (id: string) =>
    request<AnalysisRun[]>(`/cases/${id}/analysis-runs`),
  runAnalysis: (id: string) =>
    request<AnalysisRun>(`/cases/${id}/analysis-runs`, json("POST", {})),
  findings: (id: string) => request<Finding[]>(`/cases/${id}/findings`),
  reviewFinding: (id: string, body: object) =>
    request<Finding>(`/findings/${id}`, json("PATCH", body)),
  timeline: (id: string) =>
    request<{ items: Evidence[] }>(`/cases/${id}/timeline`),
  map: (id: string, redacted: boolean) =>
    request<{
      points: {
        evidence_file_id: string;
        evidence_id: string;
        latitude: number;
        longitude: number;
        timestamp: string | null;
        redacted: boolean;
      }[];
    }>(`/cases/${id}/map-data?redacted=${redacted}`),
  custody: (id: string) =>
    request<CustodyEvent[]>(`/cases/${id}/custody-events`),
  reports: (id: string) => request<Report[]>(`/cases/${id}/reports`),
  generateReport: (id: string, analysis_run_id: string, generated_by: string) =>
    request<Report>(
      `/cases/${id}/reports`,
      json("POST", { analysis_run_id, generated_by, redact_coordinates: true }),
    ),
};
