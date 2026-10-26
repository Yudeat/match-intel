"use client";
import { motion } from "framer-motion";
import type { Board } from "../lib/types";
import { DISPLAY, GAIN, LOSS, MUTED } from "../lib/ui";

export default function Leaderboard({ board }: { board: Board }) {
  const rows = Object.entries(board)
    .map(([id, v]) => ({ id, ...v }))
    .sort((a, b) => b.score - a.score);
  const max = Math.max(0.01, ...rows.map((r) => Math.abs(r.score)));

  if (rows.length === 0) {
    return <p className="text-sm" style={{ color: MUTED }}>Scores appear after the first action.</p>;
  }

  return (
    <ul className="space-y-1.5">
      {rows.map((r, i) => (
        <motion.li key={r.id} layout transition={{ type: "spring", stiffness: 300, damping: 30 }}
          className="flex items-center gap-2 text-sm">
          <span className="w-5 text-right text-lg leading-none" style={{ ...DISPLAY, color: MUTED }}>{i + 1}</span>
          <span className="w-24 truncate">{r.name}</span>
          <div className="h-2 flex-1 overflow-hidden rounded-sm bg-black/10">
            <motion.div className="h-full" style={{ background: r.score >= 0 ? GAIN : LOSS }}
              animate={{ width: `${(Math.abs(r.score) / max) * 100}%` }} />
          </div>
          <span className="w-14 text-right text-lg leading-none tabular-nums" style={DISPLAY}>
            {r.score.toFixed(2)}
          </span>
        </motion.li>
      ))}
    </ul>
  );
}
