import { useEffect, useState, useCallback } from "react";
import {
  listRuns, getRun, getStats, process,
  type RunHeader, type RunDetail, type AuditStats,
} from "./api";
import { Sparkline, Donut, HeatMap } from "./widgets";

const SUBLAYER_COLORS: Record<string, string> = {
  "Analytical Layer": "#5b9cf2",
  "Reflective Layer": "#b89af6",
  "Output Layer":     "#f2a25b",
};

export function Dashboard() {
  const [runs, setRuns]         = useState<RunHeader[]>([]);
  const [stats, setStats]       = useState<AuditStats | null>(null);
  const [selected, setSelected] = useState<RunDetail | null>(null);
  const [error, setError]       = useState<string | null>(null);
  const [busy, setBusy]         = useState(false);
  const [prompt, setPrompt]     = useState("");

  const refresh = useCallback(async () => {
    try {
      const [{ runs }, s] = await Promise.all([listRuns(50), getStats(50)]);
      setRuns(runs);
      setStats(s);
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
    <>
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

      {stats && stats.total_runs > 0 && <StatsStrip stats={stats} />}

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
    </>
  );
}

function StatsStrip({ stats }: { stats: AuditStats }) {
  const latencies = stats.latency_series.map((p) => p.ms);
  const clarities = stats.clarity_series.map((p) => p.score);
  const avgMs = latencies.length
    ? Math.round(latencies.reduce((a, b) => a + b, 0) / latencies.length)
    : 0;
  const avgClarity = clarities.length
    ? Math.round(clarities.reduce((a, b) => a + b, 0) / clarities.length)
    : 0;

  return (
    <section className="stats-strip">
      <div className="stat-card">
        <div className="stat-label">Latency (last {latencies.length})</div>
        <Sparkline values={latencies} stroke="#5b9cf2" fill="rgba(91, 156, 242, 0.18)" />
        <div className="stat-foot">avg <strong>{avgMs} ms</strong></div>
      </div>
      <div className="stat-card">
        <div className="stat-label">Clarity score</div>
        <Sparkline values={clarities} stroke="#3ec97f" fill="rgba(62, 201, 127, 0.18)" />
        <div className="stat-foot">avg <strong>{avgClarity}</strong></div>
      </div>
      <div className="stat-card">
        <div className="stat-label">Routing distribution</div>
        <Donut data={stats.sublayer_distribution} />
      </div>
      <div className="stat-card">
        <div className="stat-label">Modality × persona</div>
        <HeatMap matrix={stats.persona_modality_matrix} />
      </div>
    </section>
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
