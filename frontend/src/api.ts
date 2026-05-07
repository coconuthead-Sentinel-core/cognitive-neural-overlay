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

export interface PipelinePayload {
  run_id: string;
  request: string;
  classification:    Record<string, unknown>;
  routing:           Record<string, unknown>;
  memory_anchor?:    Record<string, unknown>;
  persona_selection: Record<string, unknown>;
  synthesis:         Record<string, unknown>;
  module_tags?:      string[];
  timestamp?:        string;
  glyph_pipeline?:   string;
  total_ms?:         number;
}

export interface SessionEnvelope {
  session_id:       string;
  envelope_version: string;   // "1.0"
  spec_ref:         string;   // "CSTM_Lattice v1.0 §6"
  run_id:           string;
  ts:               string;
  glyph_pipeline:   string;
  prior_run_ids:    string[];
  payload:          PipelinePayload;
  spec_gaps:        string[];
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

export interface AuditStats {
  window: number;
  window_size_actual: number;
  total_runs: number;
  latency_series: { ts: string; ms: number }[];
  clarity_series: { ts: string; score: number }[];
  sublayer_distribution: { sublayer: string; count: number }[];
  persona_modality_matrix: { modality: string; persona_style: string; count: number }[];
}

export async function getStats(window = 50): Promise<AuditStats> {
  const res = await fetch(`/cno/audit/stats?window=${window}`);
  if (!res.ok) throw new Error(`getStats failed: ${res.status}`);
  return res.json();
}

export async function process(request: string, sessionId?: string): Promise<SessionEnvelope> {
  const h = sessionId ? { ...headers, "X-CNO-Session-Id": sessionId } : headers;
  const res = await fetch(`/cno/process`, {
    method: "POST",
    headers: h,
    body: JSON.stringify({ request }),
  });
  if (!res.ok) throw new Error(`process failed: ${res.status}`);
  return res.json();
}

// --- SSE streaming ---

export type StreamEvent =
  | { event: "start";    data: { run_id: string; session_id: string; request: string } }
  | { event: "node";     data: { step: number; node: string; glyph: string; elapsed_ms: number; output: Record<string, unknown> } }
  | { event: "complete"; data: SessionEnvelope };

export async function* processStream(request: string, sessionId?: string): AsyncGenerator<StreamEvent> {
  const h = sessionId ? { ...headers, "X-CNO-Session-Id": sessionId } : headers;
  const res = await fetch(`/cno/process/stream`, {
    method: "POST",
    headers: h,
    body: JSON.stringify({ request }),
  });
  if (!res.ok || !res.body) throw new Error(`stream failed: ${res.status}`);

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const chunks = buffer.split("\n\n");
    buffer = chunks.pop() ?? "";
    for (const chunk of chunks) {
      const parsed = parseSseChunk(chunk);
      if (parsed) yield parsed;
    }
  }
  if (buffer.trim()) {
    const parsed = parseSseChunk(buffer);
    if (parsed) yield parsed;
  }
}

function parseSseChunk(chunk: string): StreamEvent | null {
  let event = "";
  const dataLines: string[] = [];
  for (const line of chunk.split("\n")) {
    if (line.startsWith("event:")) event = line.slice(6).trim();
    else if (line.startsWith("data:")) dataLines.push(line.slice(5).trim());
  }
  if (!event || dataLines.length === 0) return null;
  return { event, data: JSON.parse(dataLines.join("\n")) } as StreamEvent;
}
