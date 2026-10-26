"use client";
import { AnimatePresence, motion } from "framer-motion";
import { useEffect, useState } from "react";
import type { Insight } from "../lib/types";
import { DISPLAY, FLARE, INK } from "../lib/ui";

export default function LowerThird({ insight }: { insight?: Insight }) {
  const [dismissed, setDismissed] = useState<Insight | undefined>();

  useEffect(() => {
    if (!insight) return;
    const t = setTimeout(() => setDismissed(insight), 7000);
    return () => clearTimeout(t);
  }, [insight]);

  const shown = insight && insight !== dismissed ? insight : undefined;

  return (
    <AnimatePresence>
      {shown && (
        <motion.div key={shown.timestamp + shown.player.id}
          initial={{ x: -48, opacity: 0 }} animate={{ x: 0, opacity: 1 }} exit={{ x: -48, opacity: 0 }}
          transition={{ type: "spring", stiffness: 260, damping: 28 }}
          className="absolute bottom-3 left-3 flex max-w-[85%] overflow-hidden rounded-sm shadow-lg"
          style={{ background: INK, color: "white" }}>
          <div className="w-2 shrink-0" style={{ background: FLARE }} />
          <div className="px-4 py-2">
            <div className="text-2xl leading-tight" style={{ ...DISPLAY, fontWeight: 700 }}>
              {shown.narratives.overlay.headline}
            </div>
            <div className="text-sm opacity-90">{shown.narratives.overlay.sub_headline}</div>
            <div className="mt-0.5 text-xs font-semibold" style={{ color: FLARE }}>
              {shown.narratives.overlay.metric_badge}
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
