// Tiny typed client for the CNO audit endpoints.

export interface RunHeader {
  run_id: string;
  ts: string;
  request: string;
  modality: string;
  request_type: string;
  tone: string;
  sublayer: string;
  persona_style: string;
  clarity_score: number;
  synthesis_body: string;
}

export interface AuditEntry {
  run_id: string;
  step: number;
  node: string;
  glyph: string;
  ts: string;
  payload_in: Record<string, unknown>;
  payload_out: Record<string, unknown>;
}

export interface RunDetail {
  header: RunHeader;
  crossings: AuditEntry[];
}

export interface ProcessResult {
  run_id: string;
  request: string;
  classification: Record<string, unknown>;
  routing: Record<string, unknown>;
  memory_anchor: Record<string, unknown>;
  persona_selection: Record<string, unknown>;
  synthesis: Record<string, unknown>;
  module_tags: string[];
  timestamp: string;
  glyph_pipeline: string;
}

const headers = { "Content-Type": "application/json" };

export async function listRuns(limit = 50): Promise<{ count: number; runs: RunHeader[] }> {
  const res = await fetch(`/cno/audit?limit=${limit}`);
  if (!res.ok) throw new Error(`listRuns failed: ${res.status}`);
  return res.json();
}

export async function getRun(runId: string): Promise<RunDetail> {
  const res = await fetch(`/cno/audit/${runId}`);
  if (!res.ok) throw new Error(`getRun failed: ${res.status}`);
  return res.json();
}

export async function process(request: string): Promise<ProcessResult> {
  const res = await fetch(`/cno/process`, {
    method: "POST",
    headers,
    body: JSON.stringify({ request }),
  });
  if (!res.ok) throw new Error(`process failed: ${res.status}`);
  return res.json();
}
