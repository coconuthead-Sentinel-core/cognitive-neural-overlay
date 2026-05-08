import { describe, it, expect, vi, beforeEach } from "vitest";
import { listRuns, getRun, getStats, process, processStream } from "../api";

beforeEach(() => {
  vi.restoreAllMocks();
});

function mockFetchOnce(body: unknown, ok = true, status = 200) {
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => ({
      ok,
      status,
      json: async () => body,
    })),
  );
}

describe("api: typed REST helpers", () => {
  it("listRuns calls /cno/audit?limit=N and returns parsed body", async () => {
    mockFetchOnce({ count: 1, runs: [{ run_id: "r1" }] });
    const out = await listRuns(25);
    expect((globalThis.fetch as any).mock.calls[0][0]).toBe("/cno/audit?limit=25");
    expect(out.count).toBe(1);
  });

  it("getRun calls /cno/audit/:id and returns detail", async () => {
    mockFetchOnce({ header: { run_id: "abc" }, crossings: [] });
    const out = await getRun("abc");
    expect((globalThis.fetch as any).mock.calls[0][0]).toBe("/cno/audit/abc");
    expect(out.header.run_id).toBe("abc");
  });

  it("getStats calls /cno/audit/stats?window=N", async () => {
    mockFetchOnce({ window: 10, total_runs: 0, latency_series: [], clarity_series: [], sublayer_distribution: [], persona_modality_matrix: [], window_size_actual: 0 });
    await getStats(10);
    expect((globalThis.fetch as any).mock.calls[0][0]).toBe("/cno/audit/stats?window=10");
  });

  it("process POSTs JSON and returns the envelope", async () => {
    mockFetchOnce({ session_id: "s1", run_id: "r1", payload: { run_id: "r1" } });
    const env = await process("hello");
    const args = (globalThis.fetch as any).mock.calls[0];
    expect(args[0]).toBe("/cno/process");
    expect(args[1].method).toBe("POST");
    expect(JSON.parse(args[1].body).request).toBe("hello");
    expect(env.session_id).toBe("s1");
  });

  it("process attaches X-CNO-Session-Id header when session is provided", async () => {
    mockFetchOnce({ session_id: "abc", run_id: "r2", payload: { run_id: "r2" } });
    await process("hi", "abc");
    const headers = (globalThis.fetch as any).mock.calls[0][1].headers;
    expect(headers["X-CNO-Session-Id"]).toBe("abc");
  });

  it("process throws on non-2xx", async () => {
    mockFetchOnce({}, false, 401);
    await expect(process("x")).rejects.toThrow(/401/);
  });
});

describe("api: SSE processStream parser", () => {
  function ssePayload(events: { event: string; data: unknown }[]): string {
    return events
      .map((e) => `event: ${e.event}\ndata: ${JSON.stringify(e.data)}\n\n`)
      .join("");
  }

  function streamFrom(body: string): ReadableStream<Uint8Array> {
    const enc = new TextEncoder();
    const chunks = [enc.encode(body)];
    return new ReadableStream({
      start(c) {
        for (const chunk of chunks) c.enqueue(chunk);
        c.close();
      },
    });
  }

  it("yields start, node*5, complete events in order", async () => {
    const body = ssePayload([
      { event: "start",    data: { run_id: "r1", session_id: "s1", request: "hi" } },
      { event: "node",     data: { step: 1, node: "input",   glyph: "📥", elapsed_ms: 1, output: {} } },
      { event: "node",     data: { step: 2, node: "router",  glyph: "🔄", elapsed_ms: 2, output: {} } },
      { event: "node",     data: { step: 3, node: "memory",  glyph: "🧊", elapsed_ms: 3, output: {} } },
      { event: "node",     data: { step: 4, node: "persona", glyph: "🥥", elapsed_ms: 4, output: {} } },
      { event: "node",     data: { step: 5, node: "synth",   glyph: "📤", elapsed_ms: 5, output: {} } },
      { event: "complete", data: { session_id: "s1", envelope_version: "1.0", spec_ref: "x", run_id: "r1", ts: "t", glyph_pipeline: "", prior_run_ids: [], payload: { run_id: "r1", request: "hi", classification: {}, routing: {}, persona_selection: {}, synthesis: {} }, spec_gaps: [] } },
    ]);
    vi.stubGlobal("fetch", vi.fn(async () => ({ ok: true, body: streamFrom(body) })));

    const seen: string[] = [];
    for await (const evt of processStream("hi")) {
      seen.push(evt.event);
    }
    expect(seen).toEqual(["start", "node", "node", "node", "node", "node", "complete"]);
  });

  it("handles event chunks split across reads", async () => {
    // Manually simulate a stream that splits one event mid-chunk.
    const enc = new TextEncoder();
    const stream = new ReadableStream({
      start(c) {
        c.enqueue(enc.encode('event: start\nda'));
        c.enqueue(enc.encode('ta: {"run_id":"x","session_id":"s","request":"q"}\n\n'));
        c.close();
      },
    });
    vi.stubGlobal("fetch", vi.fn(async () => ({ ok: true, body: stream })));

    const evts: any[] = [];
    for await (const e of processStream("q")) evts.push(e);
    expect(evts).toHaveLength(1);
    expect(evts[0].event).toBe("start");
    expect((evts[0].data as any).run_id).toBe("x");
  });
});
