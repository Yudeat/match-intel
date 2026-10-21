"use client";
import { useCallback, useEffect, useRef, useState } from "react";
import type { Board, ImpactEvent, Insight } from "./types";

export const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export function useMatchStream(delay = 0.3) {
  const [events, setEvents] = useState<ImpactEvent[]>([]);
  const [insights, setInsights] = useState<Insight[]>([]);
  const [board, setBoard] = useState<Board>({});
  const [status, setStatus] = useState<"connecting" | "live" | "ended">("connecting");
  const [run, setRun] = useState(0);
  const seq = useRef(0);

  const restart = useCallback(() => {
    setEvents([]);
    setInsights([]);
    setBoard({});
    setStatus("connecting");
    seq.current = 0;
    setRun((r) => r + 1);
  }, []);

  useEffect(() => {
    const es = new EventSource(`${API}/stream?delay=${delay}`);
    es.onopen = () => setStatus("live");

    es.addEventListener("impact", (e) => {
      const ev: ImpactEvent = { ...JSON.parse((e as MessageEvent).data), seq: seq.current++ };
      setEvents((p) => [...p.slice(-149), ev]);
      setBoard((p) => ({
        ...p,
        [ev.player.id]: { name: ev.player.name, score: ev.cumulative.match_score },
      }));
    });

    es.addEventListener("insight", (e) => {
      const ins: Insight = JSON.parse((e as MessageEvent).data);
      setInsights((p) => [...p.slice(-29), ins]);
    });

    // Close on error or end of match; otherwise EventSource reconnects and restarts the match.
    es.onerror = () => {
      es.close();
      setStatus("ended");
    };
    return () => es.close();
  }, [delay, run]);

  return { events, insights, board, status, restart };
}
