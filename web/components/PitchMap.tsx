"use client";
import { motion } from "framer-motion";
import type { ImpactEvent } from "../lib/types";
import { FLARE, GAIN, INK, LOSS, TURF } from "../lib/ui";

const COLS = 16, ROWS = 12, L = 105, W = 68;

// Same formula as the engine's xT grid (impact.py), drawn as a faint surface under the pitch.
function threatCells() {
  const cells: { x: number; y: number; o: number }[] = [];
  for (let j = 0; j < ROWS; j++) {
    const centrality = 1 - Math.abs((j + 0.5) / ROWS - 0.5) * 2;
    for (let i = 0; i < COLS; i++) {
      const fx = (i + 0.5) / COLS;
      const v = 0.01 + 0.3 * fx ** 3 * (0.4 + 0.6 * centrality);
      cells.push({ x: (i * L) / COLS, y: (j * W) / ROWS, o: (v / 0.31) * 0.55 });
    }
  }
  return cells;
}

const CELLS = threatCells();

export default function PitchMap({ events }: { events: ImpactEvent[] }) {
  const recent = events.slice(-14);
  const line = { stroke: INK, strokeOpacity: 0.4, strokeWidth: 0.25, fill: "none" } as const;

  return (
    <svg viewBox="0 0 105 68" role="img" className="w-full rounded-md"
      aria-label="Pitch map showing the last 14 actions over a threat surface that rises toward goal"
      style={{ background: TURF }}>
      {CELLS.map((c, i) => (
        <rect key={i} x={c.x} y={c.y} width={L / COLS} height={W / ROWS} fill={FLARE} opacity={c.o} />
      ))}
      <rect x="0.5" y="0.5" width="104" height="67" {...line} />
      <line x1="52.5" y1="0.5" x2="52.5" y2="67.5" {...line} />
      <circle cx="52.5" cy="34" r="9.15" {...line} />
      <rect x="0.5" y="13.85" width="16.5" height="40.3" {...line} />
      <rect x="88" y="13.85" width="16.5" height="40.3" {...line} />

      {recent.map((e, i) => {
        const [x1, y1] = e.location.start;
        const [x2, y2] = e.location.end;
        const color = e.metrics.impact_score >= 0 ? GAIN : LOSS;
        const w = e.significance === "HIGH" ? 0.9 : e.significance === "MEDIUM" ? 0.6 : 0.35;
        const defensive = e.event_type === "tackle" || e.event_type === "interception";
        return (
          <motion.g key={e.seq} initial={{ opacity: 0 }}
            animate={{ opacity: 0.2 + 0.8 * ((i + 1) / recent.length) }}>
            {defensive ? (
              <circle cx={x1} cy={y1} r={1.7} fill="none" stroke={color} strokeWidth={w} />
            ) : (
              <>
                <line x1={x1} y1={y1} x2={x2} y2={y2} stroke={color} strokeWidth={w} strokeLinecap="round" />
                <circle cx={x2} cy={y2} r={0.9} fill={color} />
              </>
            )}
          </motion.g>
        );
      })}
    </svg>
  );
}
