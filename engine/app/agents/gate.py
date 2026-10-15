from ..schemas import EnrichedEvent


def should_analyze(ev: EnrichedEvent, include_medium: bool = False) -> bool:
    if ev.significance == "HIGH":
        return True
    return include_medium and ev.significance == "MEDIUM"