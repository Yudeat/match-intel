from ..schemas import EnrichedEvent
from .analyst import analyze
from .narrators import narrate
from .validator import validate


def fallback(ev: EnrichedEvent) -> dict:
    m = ev.metrics
    direction = "gain" if m.impact_score >= 0 else "loss"
    return {
        "studio": {"text": f"{ev.player.name}'s {ev.event_type} produced a net threat {direction} "
                           f"(impact {m.impact_score:+.2f}, xT change {m.delta_xT:+.2f})."},
        "fan": {"text": f"{ev.player.name} makes an impact with that {ev.event_type}."},
        "overlay": {"headline": f"{ev.player.name.upper()} IMPACT {m.impact_score:+.2f}",
                    "sub_headline": f"{m.lines_broken} lines broken",
                    "metric_badge": f"Rank #{ev.cumulative.rank_on_pitch}"},
    }


async def run_pipeline(ev: EnrichedEvent, leaderboard: list[dict]) -> dict:
    analysis = await analyze(ev, leaderboard)
    errors: list[str] | None = None
    for attempt in range(2):
        narratives = await narrate(ev, analysis, errors)
        errors = await validate(ev, narratives)
        if not errors:
            status = "PASSED" if attempt == 0 else "RETRIED"
            break
    else:
        narratives, status = fallback(ev), "FALLBACK"
    return {"analysis": analysis, "narratives": narratives, "validation": status}
