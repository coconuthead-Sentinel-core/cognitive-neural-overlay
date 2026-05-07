// Lightweight inline-SVG chart primitives. No chart library — keeps the bundle small.

import type { AuditStats } from "./api";

const SUBLAYER_COLORS: Record<string, string> = {
  "Analytical Layer": "#5b9cf2",
  "Reflective Layer": "#b89af6",
  "Output Layer":     "#f2a25b",
};

// ---------- Sparkline ----------

interface SparklineProps {
  values: number[];
  width?: number;
  height?: number;
  stroke?: string;
  fill?: string;
}

export function Sparkline({
  values,
  width = 220,
  height = 48,
  stroke = "#5b9cf2",
  fill   = "rgba(91, 156, 242, 0.18)",
}: SparklineProps) {
  if (values.length < 2) {
    return <div className="sparkline-empty">need ≥ 2 data points</div>;
  }
  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = max - min || 1;
  const stepX = width / (values.length - 1);

  const points = values
    .map((v, i) => `${i * stepX},${height - ((v - min) / span) * (height - 4) - 2}`)
    .join(" ");
  const areaPath = `M0,${height} L ${points} L${width},${height} Z`;

  return (
    <svg className="sparkline" viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none">
      <path d={areaPath} fill={fill} />
      <polyline points={points} fill="none" stroke={stroke} strokeWidth="1.5" />
    </svg>
  );
}

// ---------- Donut ----------

interface DonutProps {
  data: { sublayer: string; count: number }[];
  size?: number;
}

export function Donut({ data, size = 140 }: DonutProps) {
  const total = data.reduce((s, d) => s + d.count, 0);
  const cx = size / 2;
  const cy = size / 2;
  const r = size / 2 - 8;
  const innerR = r * 0.55;

  if (total === 0) {
    return <div className="donut-empty muted">no data yet</div>;
  }

  let cursor = -Math.PI / 2; // start at 12 o'clock
  const arcs = data.map((d) => {
    const angle = (d.count / total) * Math.PI * 2;
    const start = cursor;
    const end = cursor + angle;
    cursor = end;
    return { ...d, start, end };
  });

  return (
    <div className="donut-wrap">
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        {arcs.map((a) => (
          <path
            key={a.sublayer}
            d={arcPath(cx, cy, r, innerR, a.start, a.end)}
            fill={SUBLAYER_COLORS[a.sublayer] || "#666"}
          />
        ))}
        <text x={cx} y={cy + 4} textAnchor="middle" className="donut-total">
          {total}
        </text>
      </svg>
      <ul className="donut-legend">
        {arcs.map((a) => (
          <li key={a.sublayer}>
            <span className="legend-dot" style={{ background: SUBLAYER_COLORS[a.sublayer] || "#666" }} />
            {a.sublayer} <span className="muted">· {a.count}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function arcPath(cx: number, cy: number, r: number, ir: number, start: number, end: number): string {
  // Handle full-circle case (one slice == 100%)
  const isFullCircle = Math.abs(end - start - Math.PI * 2) < 1e-6;
  if (isFullCircle) {
    return [
      `M ${cx + r} ${cy}`,
      `A ${r} ${r} 0 1 1 ${cx - r} ${cy}`,
      `A ${r} ${r} 0 1 1 ${cx + r} ${cy}`,
      `M ${cx + ir} ${cy}`,
      `A ${ir} ${ir} 0 1 0 ${cx - ir} ${cy}`,
      `A ${ir} ${ir} 0 1 0 ${cx + ir} ${cy}`,
      `Z`,
    ].join(" ");
  }
  const x1 = cx + r * Math.cos(start);
  const y1 = cy + r * Math.sin(start);
  const x2 = cx + r * Math.cos(end);
  const y2 = cy + r * Math.sin(end);
  const ix1 = cx + ir * Math.cos(end);
  const iy1 = cy + ir * Math.sin(end);
  const ix2 = cx + ir * Math.cos(start);
  const iy2 = cy + ir * Math.sin(start);
  const largeArc = end - start > Math.PI ? 1 : 0;
  return [
    `M ${x1} ${y1}`,
    `A ${r} ${r} 0 ${largeArc} 1 ${x2} ${y2}`,
    `L ${ix1} ${iy1}`,
    `A ${ir} ${ir} 0 ${largeArc} 0 ${ix2} ${iy2}`,
    `Z`,
  ].join(" ");
}

// ---------- Heat-map (modality × persona) ----------

interface HeatMapProps {
  matrix: AuditStats["persona_modality_matrix"];
}

export function HeatMap({ matrix }: HeatMapProps) {
  if (matrix.length === 0) {
    return <div className="muted">no runs yet</div>;
  }
  const modalities = Array.from(new Set(matrix.map((c) => c.modality))).sort();
  const personas   = Array.from(new Set(matrix.map((c) => c.persona_style))).sort();
  const maxCount   = Math.max(...matrix.map((c) => c.count));
  const lookup = new Map(matrix.map((c) => [`${c.modality}|${c.persona_style}`, c.count]));

  return (
    <table className="heatmap">
      <thead>
        <tr>
          <th />
          {personas.map((p) => <th key={p}>{p}</th>)}
        </tr>
      </thead>
      <tbody>
        {modalities.map((m) => (
          <tr key={m}>
            <th>{m}</th>
            {personas.map((p) => {
              const c = lookup.get(`${m}|${p}`) ?? 0;
              const intensity = c === 0 ? 0 : 0.15 + 0.65 * (c / maxCount);
              return (
                <td
                  key={p}
                  className="heatcell"
                  style={{ background: `rgba(91, 156, 242, ${intensity})` }}
                  title={`${m} × ${p}: ${c}`}
                >
                  {c || ""}
                </td>
              );
            })}
          </tr>
        ))}
      </tbody>
    </table>
  );
}
