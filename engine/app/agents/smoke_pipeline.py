import asyncio
import json

from ..impact import MatchState, enrich
from ..simulator import generate_match
from .pipeline import run_pipeline


async def main():
    state = MatchState()
    for raw in generate_match(300):
        ev = enrich(raw, state)
        if ev.significance == "HIGH":
            print(json.dumps(await run_pipeline(ev, []), indent=2))
            return


asyncio.run(main())