import asyncio

from ..impact import MatchState, enrich
from ..simulator import generate_match
from .analyst import analyze


async def main():
    state = MatchState()
    for raw in generate_match(300):
        ev = enrich(raw, state)
        if ev.significance == "HIGH":
            print(ev.model_dump_json(indent=2))
            print(await analyze(ev, []))
            return
    print("No HIGH event found")


asyncio.run(main())