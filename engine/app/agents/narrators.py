import asyncio
import json
import os

from ..schemas import EnrichedEvent
from .analyst import _parse, zone
from .foundry import ensure_agent, run_agent

RULES = """Use ONLY numbers present in the input (metrics, cumulative, analysis).
Never invent stats, distances, player names, or xG values.
Describe location ONLY using the "zone" field.
If "fix_these_errors" is present, your previous output had those problems: correct them.
Respond with ONLY a JSON object, no markdown fences."""

AGENTS = {
        "studio-narrator": f"""You are a studio TV analyst. Explain the event in 2 sentences of natural
analyst language: space, pressure, lines broken, threat change. Give pressure as a whole-number
percentage (0.868 becomes 87%). Never print field names like delta_xT or impact_score. Use at most
2 numbers. {RULES}
Output: {{"text": "..."}}""",
    "fan-narrator": f"""You are an enthusiastic but accurate commentator for casual fans.
1-2 short sentences, no jargon, no decimals. Use at most one number, or none. {RULES}
Output: {{"text": "..."}}""",
    "overlay-builder": f"""You write broadcast lower-third graphics. Short and punchy.
headline max 6 words, sub_headline max 10 words, metric_badge max 6 words. {RULES}
Output: {{"headline": "...", "sub_headline": "...", "metric_badge": "..."}}""",
}

KEYS = {"studio-narrator": "studio", "fan-narrator": "fan", "overlay-builder": "overlay"}


def _model() -> str:
    return os.getenv("FOUNDRY_NARRATOR_MODEL") or os.environ["FOUNDRY_ANALYST_MODEL"]


async def _one(name: str, payload: str) -> dict:
    ensure_agent(name, _model(), AGENTS[name])
    return _parse(await asyncio.to_thread(run_agent, name, payload))


async def narrate(ev: EnrichedEvent, analysis: dict, errors: list[str] | None = None) -> dict:
    payload = json.dumps({
        "event": ev.model_dump(),
        "zone": zone(*ev.location.start),
        "analysis": analysis,
        "fix_these_errors": errors or [],
    })
    results = await asyncio.gather(*(_one(n, payload) for n in AGENTS))
    return {KEYS[n]: r for n, r in zip(AGENTS, results)}
