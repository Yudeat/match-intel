import asyncio
import json
import os
import re

from ..schemas import EnrichedEvent
from .foundry import ensure_agent, run_agent

AGENT_NAME = "tactical-analyst"

INSTRUCTIONS = """You are a football tactical analyst inside a live match-intelligence system.
You receive ONE event as JSON: deterministic metrics already computed by a spatial engine,
plus the current top-3 cumulative leaderboard.

Rules:
- Use ONLY numbers present in the input. Never invent stats, players, or xG values.
- Explain WHY the event mattered tactically (space created, pressure beaten, lines broken,
  defensive threat removed), grounded in the metrics.
- Negative impact_score means the action cost the team threat; explain it plainly.
- Be concise and neutral. No hype.

Respond with ONLY a JSON object, no markdown fences:
{
  "finding": "one-sentence tactical summary",
  "why": "2-3 sentences explaining the tactical cause",
  "key_factors": ["short factor", "short factor"],
  "cited_metrics": {"impact_score": 0.0, "delta_xT": 0.0, "pressure": 0.0, "lines_broken": 0},
  "confidence": "LOW|MEDIUM|HIGH"
}
cited_metrics must copy values exactly from the input.Describe where the action happened ONLY using the "zone" field. Never infer location from coordinates."""


def _parse(text: str) -> dict:
    if not text or not text.strip():
        return {
            "finding": "Analysis unavailable",
            "why": "Empty response received from model.",
            "key_factors": [],
            "cited_metrics": {"impact_score": 0.0, "delta_xT": 0.0, "pressure": 0.0, "lines_broken": 0},
            "confidence": "LOW"
        }
    
    cleaned = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {
            "finding": cleaned[:100],
            "why": "Model output failed strict JSON parsing.",
            "key_factors": [],
            "cited_metrics": {"impact_score": 0.0, "delta_xT": 0.0, "pressure": 0.0, "lines_broken": 0},
            "confidence": "LOW"
        }

async def analyze(event: EnrichedEvent, leaderboard: list[dict]) -> dict:
    ensure_agent(AGENT_NAME, os.environ["FOUNDRY_ANALYST_MODEL"], INSTRUCTIONS)
    payload = json.dumps({
        "event": event.model_dump(),
        "zone": zone(*event.location.start),
        "leaderboard_top3": leaderboard,
    })
    text = await asyncio.to_thread(run_agent, AGENT_NAME, payload, system_instruction=INSTRUCTIONS)
    return _parse(text)

def zone(x: float, y: float) -> str:
    third = "own defensive third" if x < 35 else "middle third" if x < 70 else "attacking third"
    lane = "central channel" if 22 <= y <= 46 else "wide area"
    return f"{third}, {lane}"