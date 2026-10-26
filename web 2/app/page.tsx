"use client";
import { MotionConfig } from "framer-motion";
import { useState } from "react";
import Leaderboard from "../components/Leaderboard";
import LowerThird from "../components/LowerThird";
import PitchMap from "../components/PitchMap";
import { API, useMatchStream } from "../lib/useMatchStream";
import { BODY, DISPLAY, FLARE, GAIN, INK, MUTED, PAPER } from "../lib/ui";

const BADGE: Record<string, string> = {
  PASSED: "Fact-checked",
  RETRIED: "Fact-checked after a retry",
  FALLBACK: "Template text",
  MOCK: "Mock text",
};

export default function Home() {
  const { events, insights, board, status, restart } = useMatchStream(0.3);
  const [mode, setMode] = useState<"studio" | "fan">("studio");
  const last = events[events.length - 1];
  const focus = "focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#E8833A]";

  return (
    <MotionConfig reducedMotion="user">
      <div className="min-h-screen p-5 md:p-8" style={{ ...BODY, background: PAPER, color: INK }}>
        <header className="mb-5 flex items-end justify-between">
          <div>
            <h1 className="text-4xl leading-none" style={{ ...DISPLAY, fontWeight: 700 }}>Match Intelligence</h1>
            <p className="mt-1 text-sm" style={{ color: MUTED }}>
              Player impact measured by how much each action changes the threat on the pitch.
            </p>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-5xl leading-none tabular-nums" style={DISPLAY}>{last ? `${last.timestamp}` : "00:00"}</span>
            <span className="rounded-sm px-2 py-1 text-xs font-semibold"
              style={{ background: status === "live" ? GAIN : "#cfd5dd", color: status === "live" ? "white" : INK }}>
              {status === "live" ? "Live" : status === "ended" ? "Finished" : "Connecting"}
            </span>
            <button onClick={restart} className={`rounded-sm border px-3 py-1 text-sm ${focus}`} style={{ borderColor: INK }}>
              Replay match
            </button>
          </div>
        </header>

        <div className="grid gap-6 lg:grid-cols-3">
          <section className="lg:col-span-2">
            <div className="relative">
              <PitchMap events={events} />
              <LowerThird insight={insights[insights.length - 1]} />
            </div>
            <p className="mt-2 text-sm" style={{ color: MUTED }}>
              {events.length === 0 && status === "ended"
                ? `Can't reach the engine at ${API}. Start the backend with uvicorn, then choose Replay match.`
                : events.length === 0
                ? "Waiting for the first events."
                : "Last 14 actions, attacking left to right. Teal marks a threat gain, red a loss. Orange shading shows where the pitch is most dangerous."}
            </p>
          </section>

          <aside className="space-y-8">
            <div>
              <h2 className="mb-2 text-2xl" style={{ ...DISPLAY, fontWeight: 600 }}>Impact table</h2>
              <Leaderboard board={board} />
            </div>

            <div>
              <div className="mb-2 flex items-center justify-between">
                <h2 className="text-2xl" style={{ ...DISPLAY, fontWeight: 600 }}>Commentary</h2>
                <div className="flex gap-1 text-sm" role="group" aria-label="Commentary style">
                  {(["studio", "fan"] as const).map((m) => (
                    <button key={m} onClick={() => setMode(m)} aria-pressed={mode === m}
                      className={`rounded-sm px-2 py-0.5 ${focus}`}
                      style={{ background: mode === m ? INK : "transparent", color: mode === m ? "white" : INK }}>
                      {m === "studio" ? "Analyst" : "Fan"}
                    </button>
                  ))}
                </div>
              </div>
              {insights.length === 0 ? (
                <p className="text-sm" style={{ color: MUTED }}>Commentary appears for the highest-impact actions.</p>
              ) : (
                <ul className="space-y-2">
                  {insights.slice(-6).reverse().map((ins) => (
                    <li key={ins.timestamp + ins.player.id} className="rounded-sm border-l-4 bg-white p-3 text-sm"
                      style={{ borderColor: FLARE }}>
                      <div className="mb-1 flex justify-between text-xs" style={{ color: MUTED }}>
                        <span>{ins.timestamp} {ins.player.name}</span>
                        <span>{BADGE[ins.validation] ?? ins.validation}</span>
                      </div>
                      <p>{ins.narratives[mode].text}</p>
                      {mode === "studio" && ins.analysis.why && (
                        <p className="mt-1" style={{ color: MUTED }}>{ins.analysis.why}</p>
                      )}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </aside>
        </div>
      </div>
    </MotionConfig>
  );
}
