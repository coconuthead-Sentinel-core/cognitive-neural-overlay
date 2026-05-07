import { useState } from "react";
import { processStream } from "./api";

const NODES = [
  { step: 1, node: "input",   glyph: "📥", label: "Input"   },
  { step: 2, node: "router",  glyph: "🔄", label: "Router"  },
  { step: 3, node: "memory",  glyph: "🧊", label: "Memory"  },
  { step: 4, node: "persona", glyph: "🥥", label: "Persona" },
  { step: 5, node: "synth",   glyph: "📤", label: "Synth"   },
];

interface NodeState {
  status: "pending" | "active" | "done";
  elapsed_ms?: number;
  output?: Record<string, unknown>;
}

function emptyTrace(): Record<number, NodeState> {
  return Object.fromEntries(NODES.map((n) => [n.step, { status: "pending" }]));
}

export function Console() {
  const [prompt, setPrompt]     = useState("");
  const [busy, setBusy]         = useState(false);
  const [error, setError]       = useState<string | null>(null);
  const [trace, setTrace]       = useState<Record<number, NodeState>>(emptyTrace());
  const [runId, setRunId]       = useState<string | null>(null);
  const [totalMs, setTotalMs]   = useState<number | null>(null);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim()) return;
    setBusy(true);
    setError(null);
    setRunId(null);
    setTotalMs(null);
    setTrace(emptyTrace());

    // Mark step 1 as active immediately for visual feedback.
    setTrace((t) => ({ ...t, 1: { status: "active" } }));

    try {
      for await (const evt of processStream(prompt.trim())) {
        if (evt.event === "start") {
          setRunId(evt.data.run_id);
        } else if (evt.event === "node") {
          const { step, elapsed_ms, output } = evt.data;
          setTrace((t) => {
            const next = { ...t, [step]: { status: "done" as const, elapsed_ms, output } };
            if (step + 1 <= NODES.length) {
              next[step + 1] = { status: "active" };
            }
            return next;
          });
        } else if (evt.event === "complete") {
          setTotalMs(evt.data.payload.total_ms ?? null);
        }
      }
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <form className="prompt-bar" onSubmit={onSubmit}>
        <input
          type="text"
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Send a request and watch the pipeline trace fill in left-to-right…"
          disabled={busy}
        />
        <button type="submit" disabled={busy || !prompt.trim()}>
          {busy ? "Streaming…" : "Send"}
        </button>
      </form>

      {error && <div className="error">{error}</div>}

      {(runId || totalMs !== null) && (
        <div className="console-meta">
          {runId && <><span>run </span><code>{runId.slice(0, 12)}…</code></>}
          {totalMs !== null && <span> · total {totalMs} ms</span>}
        </div>
      )}

      <div className="pipeline-trace">
        {NODES.map((n) => {
          const state = trace[n.step];
          return (
            <div key={n.step} className={`trace-card ${state.status}`}>
              <div className="trace-glyph">{n.glyph}</div>
              <div className="trace-label">{n.step}. {n.label}</div>
              <div className="trace-status">
                {state.status === "pending" && <span className="muted">…</span>}
                {state.status === "active"  && <span className="muted">working…</span>}
                {state.status === "done"    && <span>{state.elapsed_ms} ms</span>}
              </div>
              {state.status === "done" && state.output && (
                <pre className="trace-output">{JSON.stringify(state.output, null, 2)}</pre>
              )}
            </div>
          );
        })}
      </div>
    </>
  );
}
