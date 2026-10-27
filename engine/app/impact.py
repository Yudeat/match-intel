import math
import numpy as np

from . import config as C
from .schemas import (Cumulative, EnrichedEvent, Location, Metrics, RawEvent)
from .redis_client import redis_client


def _build_grid() -> np.ndarray:
    """16x12 xT grid: threat rises toward goal and toward the centre."""
    grid = np.zeros((C.GRID_ROWS, C.GRID_COLS))
    for j in range(C.GRID_ROWS):
        centrality = 1 - abs((j + 0.5) / C.GRID_ROWS - 0.5) * 2
        for i in range(C.GRID_COLS):
            fx = (i + 0.5) / C.GRID_COLS
            grid[j, i] = 0.01 + 0.30 * fx**3 * (0.4 + 0.6 * centrality)
    return grid


XT_GRID = _build_grid()


def xt_at(x: float, y: float) -> float:
    col = min(max(int(x / C.PITCH_L * C.GRID_COLS), 0), C.GRID_COLS - 1)
    row = min(max(int(y / C.PITCH_W * C.GRID_ROWS), 0), C.GRID_ROWS - 1)
    return float(XT_GRID[row, col])


def pressure(ball, opponents) -> float:
    total = sum(
        max(0.0, 1 - math.dist(ball, o) / C.PRESSURE_RADIUS) for o in opponents
    )
    return min(total, 1.0)


def opponent_lines(opponents) -> list[float]:
    """Mean x of the defence (4), midfield (4) and attack (2)."""
    xs = sorted((o[0] for o in opponents), reverse=True)
    groups = [xs[0:4], xs[4:8], xs[8:10]]
    return [sum(g) / len(g) for g in groups if g]


def lines_broken(start, end, opponents) -> int:
    return sum(1 for lx in opponent_lines(opponents) if start[0] < lx <= end[0])


def impact_score(delta_xt: float, press: float, lines: int) -> float:
    return delta_xt * (1 + C.W_PRESSURE * press) + C.W_LINE * lines


def significance(score: float) -> str:
    s = abs(score)
    if s >= C.HIGH_THRESHOLD:
        return "HIGH"
    return "MEDIUM" if s >= C.MEDIUM_THRESHOLD else "LOW"


class RedisMatchState:
    """Persistent cumulative scores using Azure Managed Redis."""

    def __init__(self, match_id: str):
        self.match_id = match_id
        self.board_key = f"match:{match_id}:leaderboard"

    def add(self, player_id: str, score: float) -> tuple[float, int]:
        # Atomically increment score in a Redis Sorted Set
        new_total = redis_client.zincrby(self.board_key, score, player_id)
        
        # Calculate rank dynamically from sorted set position (0-indexed to 1-based)
        rank = redis_client.zrevrank(self.board_key, player_id) + 1
        
        return float(new_total), int(rank)


def enrich(raw: RawEvent, state=None) -> EnrichedEvent:
    press = pressure(raw.start, raw.opponents)
    lines = 0
    difficulty = 0.0

    if raw.event_type in ("tackle", "interception"):
        delta = xt_at(C.PITCH_L - raw.start[0], C.PITCH_W - raw.start[1]) if raw.success else 0.0
    elif raw.success:
        delta = xt_at(*raw.end) - xt_at(*raw.start)
        lines = lines_broken(raw.start, raw.end, raw.opponents)
    else:
        delta = -C.FAIL_PENALTY * xt_at(*raw.start)

    if raw.event_type == "pass":
        dist = math.dist(raw.start, raw.end)
        difficulty = min(1.0, 0.5 * press + 0.5 * min(dist / 40, 1.0))

    score = impact_score(delta, press, lines)
    
    # Use Redis-backed match state per match ID
    match_state = RedisMatchState(raw.match_id)
    total, rank = match_state.add(raw.player.id, score)

    return EnrichedEvent(
        match_id=raw.match_id,
        timestamp=raw.timestamp,
        event_type=raw.event_type,
        player=raw.player,
        location=Location(start=raw.start, end=raw.end),
        metrics=Metrics(
            delta_xT=round(delta, 3),
            pressure=round(press, 3),
            lines_broken=lines,
            pass_difficulty=round(difficulty, 3),
            impact_score=round(score, 3),
        ),
        cumulative=Cumulative(match_score=round(total, 3), rank_on_pitch=rank),
        significance=significance(score),
    )