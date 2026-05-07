import { useEffect, useState, useCallback } from "react";
import {
  listRuns, getRun, process,
  type RunHeader, type RunDetail,
} from "./api";

const SUBLAYER_COLORS: Record<string, string> = {
  "Analytical Layer": "#5b9cf2",
  "Reflective Layer": "#b89af6",
  "Output Layer":     "#f2a25b",
};

export function App() {
  const [runs, setRuns]           = useState<RunHeader[]>([]);
  const [selected, setSelected]   = useState<RunDetail | null>(null);
  const [error, setError]         = useState<string | null>(null);
  const [busy, setBusy]           = useState(false);
  const [prompt, setPrompt]       = useState("");

  const refresh = useCallback(async () => {
    try {
      const { runs } = await listRuns(50);
      setRuns(runs);
    } catch (e) {
      setError(String(e));
    }
  }, []);

  useEffect(() => { refresh(); }, [refresh]);

  const onRowClick = async (run_id: string) => {
    try {
      setSelected(await getRun(run_id));
    } catch (e) {
      setError(String(e));
    }
  };

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim()) return;
    setBusy(true);
    setError(null);
    try {
      await process(prompt.trim());
      setPrompt("");
      await refresh();
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="layout">
      <header>
        <h1>CNO Audit Dashboard</h1>
        <span className="glyph-pipeline">📥 → 🔄 → 🧊 → 🥥 → 📤</span>
      </header>

      <form className="prompt-bar" onSubmit={onSubmit}>
        <input
          type="text"
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Send a request through the pipeline (e.g. 'What is canon #18?')"
          disabled={busy}
        />
        <button type="submit" disabled={busy || !prompt.trim()}>
          {busy ? "Processing…" : "Process"}
        </button>
        <button type="button" className="secondary" onClick={refresh} disabled={busy}>
          Refresh
        </button>
      </form>

      {error && <div className="error">{error}</div>}

      <div className="split">
        <section className="run-list">
          <h2>Recent Runs ({runs.length})</h2>
          {runs.length === 0 ? (
            <p className="muted">No runs yet — submit a prompt above.</p>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>Time</th>
                  <th>Request</th>
                  <th>Sublayer</th>
                  <th>Persona</th>
                  <th>Clarity</th>
                </tr>
              </thead>
              <tbody>
                {runs.map((r) => (
                  <tr
                    key={r.run_id}
                    onClick={() => onRowClick(r.run_id)}
                    className={selected?.header.run_id === r.run_id ? "selected" : ""}
                  >
                    <td>{new Date(r.ts).toLocaleTimeString()}</td>
                    <td className="truncate" title={r.request}>{r.request}</td>
                    <td>
                      <span
                        className="chip"
                        style={{ background: SUBLAYER_COLORS[r.sublayer] || "#666" }}
                      >
                        {r.sublayer}
                      </span>
                    </td>
                    <td>{r.persona_style}</td>
                    <td>{r.clarity_score}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </section>

        <section className="drill-down">
          <h2>Drill-down</h2>
          {!selected ? (
            <p className="muted">Click a row to inspect the per-node trace.</p>
          ) : (
            <RunInspector detail={selected} />
          )}
        </section>
      </div>
    </div>
  );
}

function RunInspector({ detail }: { detail: RunDetail }) {
  return (
    <div>
      <div className="run-meta">
        <code>{detail.header.run_id.slice(0, 12)}…</code>
        <span>· {new Date(detail.header.ts).toLocaleString()}</span>
      </div>
      <p className="quoted">{detail.header.request}</p>
      <div className="crossings">
        {detail.crossings.map((c) => (
          <div key={c.step} className="crossing">
            <div className="crossing-head">
              <span className="big-glyph">{c.glyph}</span>
              <strong>{c.step}. {c.node}</strong>
              <span className="muted">{new Date(c.ts).toLocaleTimeString()}</span>
            </div>
            <div className="payload-pair">
              <div>
                <h4>in</h4>
                <pre>{JSON.stringify(c.payload_in, null, 2)}</pre>
              </div>
              <div>
                <h4>out</h4>
                <pre>{JSON.stringify(c.payload_out, null, 2)}</pre>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
