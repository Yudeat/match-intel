import asyncio
import json
import math
import os
import re

from ..schemas import EnrichedEvent
from .analyst import _parse, zone
from .foundry import ensure_agent, run_agent

NUM = re.compile(r"\d+(?:\.\d+)?")

AGENT_NAME = "fact-validator"
INSTRUCTIONS = """You are a strict fact-checker for football commentary.
You receive "metrics" and "zone" (ground truth) and "texts" (commentary). Flag any claim that
contradicts them: wrong direction (gain vs loss), wrong location, wrong player or team,
invented events, or numbers that don't match. Rounding is fine.
Respond with ONLY JSON, no fences: {"valid": true|false, "mismatches": ["..."]}"""


def _allowed(ev: EnrichedEvent) -> list[float]:
    m, c = ev.metrics, ev.cumulative
    dist = math.dist(ev.location.start, ev.location.end)
    minute, second = (int(p) for p in ev.timestamp.split(":"))
    vals = [m.delta_xT, m.pressure, m.lines_broken, m.pass_difficulty, m.impact_score,
            c.match_score, c.rank_on_pitch, minute, second,
            m.pressure * 100, round(m.pressure * 100), dist, round(dist),
            m.pass_difficulty * 100, round(m.pass_difficulty * 100)]
    return [abs(v) for v in vals]


def _collect(obj) -> list[str]:
    if isinstance(obj, str):
        return [obj]
    if isinstance(obj, dict):
        return [s for v in obj.values() for s in _collect(v)]
    if isinstance(obj, list):
        return [s for v in obj for s in _collect(v)]
    return []


def check_numbers(ev: EnrichedEvent, narratives: dict) -> list[str]:
    allowed = _allowed(ev)
    errors = []
    for text in _collect(narratives):
        for tok in NUM.findall(text):
            n = float(tok)
            if not any(abs(n - a) < 0.006 for a in allowed):
                errors.append(f"number {tok} in '{text[:60]}' is not supported by the metrics")
    return errors


async def llm_check(ev: EnrichedEvent, narratives: dict) -> list[str]:
    ensure_agent(AGENT_NAME, os.environ["FOUNDRY_ANALYST_MODEL"], INSTRUCTIONS)
    payload = json.dumps({
        "player": ev.player.model_dump(),
        "event_type": ev.event_type,
        "zone": zone(*ev.location.start),
        "metrics": ev.metrics.model_dump(),
        "texts": narratives,
    })
    verdict = _parse(await asyncio.to_thread(run_agent, AGENT_NAME, payload))
    return [] if verdict.get("valid") else verdict.get("mismatches", ["unspecified mismatch"])


async def validate(ev: EnrichedEvent, narratives: dict) -> list[str]:
    errors = check_numbers(ev, narratives)  # free and instant
    if errors:
        return errors                        # skip the LLM call
    return await llm_check(ev, narratives)
