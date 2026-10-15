import asyncio
import json

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse

from .agents.foundry import foundry_configured
from .agents.gate import should_analyze
from .impact import MatchState, enrich
from .simulator import generate_match

app = FastAPI(title="Match Intelligence Engine")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000"],
                   allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
def health():
    return {"status": "ok", "agents": foundry_configured()}


def top3(state: MatchState) -> list[dict]:
    best = sorted(state.scores.items(), key=lambda kv: kv[1], reverse=True)[:3]
    return [{"player_id": p, "match_score": round(s, 3)} for p, s in best]


@app.get("/stream")
async def stream(n: int = 300, delay: float = 0.3, agents: bool = True):
    use_agents = agents and foundry_configured()
    if use_agents:
        from .agents.analyst import analyze

    async def gen():
        state = MatchState()
        queue: asyncio.Queue = asyncio.Queue()
        sem = asyncio.Semaphore(3)  # limit concurrent model calls
        tasks: list[asyncio.Task] = []

        async def analyze_task(ev, board):
            async with sem:
                try:
                    result = await analyze(ev, board)
                except Exception as exc:  # never let an agent failure kill the stream
                    print(f"analyst failed: {exc}")
                    return
            await queue.put({"event": "insight", "data": json.dumps({
                "timestamp": ev.timestamp,
                "player": ev.player.model_dump(),
                "metrics": ev.metrics.model_dump(),
                "analysis": result,
            })})

        async def producer():
            for raw in generate_match(n):
                ev = enrich(raw, state)
                await queue.put({"event": "impact", "data": ev.model_dump_json()})
                if use_agents and should_analyze(ev):
                    tasks.append(asyncio.create_task(analyze_task(ev, top3(state))))
                await asyncio.sleep(delay)
            await asyncio.gather(*tasks)
            await queue.put(None)

        producer_task = asyncio.create_task(producer())
        while (item := await queue.get()) is not None:
            yield item
        await producer_task

    return EventSourceResponse(gen())