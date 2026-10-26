export type Player = { id: string; name: string; team: string };
export type Metrics = {
  delta_xT: number;
  pressure: number;
  lines_broken: number;
  pass_difficulty: number;
  impact_score: number;
};
export type ImpactEvent = {
  seq: number;
  match_id: string;
  timestamp: string;
  event_type: "pass" | "carry" | "tackle" | "interception";
  player: Player;
  location: { start: [number, number]; end: [number, number] };
  metrics: Metrics;
  cumulative: { match_score: number; rank_on_pitch: number };
  significance: "LOW" | "MEDIUM" | "HIGH";
};
export type Insight = {
  timestamp: string;
  player: Player;
  metrics: Metrics;
  analysis: { finding: string; why: string; key_factors: string[]; confidence: string };
  narratives: {
    studio: { text: string };
    fan: { text: string };
    overlay: { headline: string; sub_headline: string; metric_badge: string };
  };
  validation: string;
};
export type Board = Record<string, { name: string; score: number }>;
