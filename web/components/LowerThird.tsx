"use client";

import { AnimatePresence, motion } from "framer-motion";
import type { Insight } from "../lib/types";
import { DISPLAY, FLARE, INK, PAPER } from "../lib/ui";

interface LowerThirdProps {
  insight?: Insight;
}

export default function LowerThird({ insight }: LowerThirdProps) {
  if (!insight) return null;

  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={insight.timestamp + insight.player.id}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: 10 }}
        transition={{ duration: 0.25 }}
        className="absolute bottom-4 left-4 right-4 z-10 rounded-sm border-l-4 p-4 shadow-lg backdrop-blur-md"
        style={{ background: PAPER, borderColor: FLARE, color: INK }}
      >
        <div className="mb-1 flex items-center justify-between text-xs font-semibold uppercase tracking-wider">
          <span>{insight.timestamp} — {insight.player.name}</span>
          <span>{insight.analysis?.finding || "Key Impact"}</span>
        </div>
        <p className="text-base font-medium leading-tight" style={DISPLAY}>
          {insight.narratives?.studio?.text || insight.analysis?.finding}
        </p>
      </motion.div>
    </AnimatePresence>
  );
}