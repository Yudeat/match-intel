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
cited_metrics must copy values exactly from the input."""


def _parse(text: str) -> dict:
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    return json.loads(text)


async def analyze(event: EnrichedEvent, leaderboard: list[dict]) -> dict:
    ensure_agent(AGENT_NAME, os.environ["FOUNDRY_ANALYST_MODEL"], INSTRUCTIONS)
    payload = json.dumps({"event": event.model_dump(), "leaderboard_top3": leaderboard})
    text = await asyncio.to_thread(run_agent, AGENT_NAME, payload)
    return _parse(text)