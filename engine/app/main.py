import asyncio
import json

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse

from .agents.foundry import foundry_configured
from .agents.gate import should_analyze
from .impact import enrich
from .simulator import generate_match
from .redis_client import redis_client

app = FastAPI(title="Match Intelligence Engine")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000"],
                   allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
def health():
    return {"status": "ok", "agents": foundry_configured()}


def top3(match_id: str) -> list[dict]:
    board_key = f"match:{match_id}:leaderboard"
    # Fetch top 3 players from Redis Sorted Set
    top_players = redis_client.zrevrange(board_key, 0, 2, withscores=True)
    return [{"player_id": pid, "match_score": round(score, 3)} for pid, score in top_players]


@app.get("/stream")
async def stream(n: int = 300, delay: float = 0.3, agents: bool = True):
    use_agents = agents and foundry_configured()
    if use_agents:
        from .agents.pipeline import run_pipeline

    async def gen():
        queue: asyncio.Queue = asyncio.Queue()
        sem = asyncio.Semaphore(3)  # limit concurrent model calls
        tasks: list[asyncio.Task] = []

        async def analyze_task(ev, board):
            async with sem:
                try:
                    result = await run_pipeline(ev, board)
                except Exception as exc:  # never let an agent failure kill the stream
                    print(f"analyst failed: {exc}")
                    return
            await queue.put({"event": "insight", "data": json.dumps({
                "timestamp": ev.timestamp,
                "player": ev.player.model_dump(),
                "metrics": ev.metrics.model_dump(),
                **result,
            })})

        async def producer():
            match_id = "default_match"
            for raw in generate_match(n):
                match_id = raw.match_id
                # Enriched event handles Redis state persistence automatically
                ev = enrich(raw)
                await queue.put({"event": "impact", "data": ev.model_dump_json()})
                if use_agents and should_analyze(ev):
                    tasks.append(asyncio.create_task(analyze_task(ev, top3(match_id))))
                await asyncio.sleep(delay)
            await asyncio.gather(*tasks)
            await queue.put(None)

        producer_task = asyncio.create_task(producer())
        while (item := await queue.get()) is not None:
            yield item
        await producer_task

    return EventSourceResponse(gen())