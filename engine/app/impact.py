import math
import numpy as np

from . import config as C
from .schemas import (Cumulative, EnrichedEvent, Location, Metrics, RawEvent)


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


class MatchState:
    """In-memory cumulative scores. Swap for Redis later."""

    def __init__(self):
        self.scores: dict[str, float] = {}

    def add(self, player_id: str, score: float) -> tuple[float, int]:
        self.scores[player_id] = self.scores.get(player_id, 0.0) + score
        total = self.scores[player_id]
        rank = 1 + sum(1 for v in self.scores.values() if v > total)
        return total, rank


def enrich(raw: RawEvent, state: MatchState) -> EnrichedEvent:
    press = pressure(raw.start, raw.opponents)
    lines = 0
    difficulty = 0.0

    if raw.event_type in ("tackle", "interception"):
        # Defensive value: threat the opponent would have had at this spot
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
    total, rank = state.add(raw.player.id, score)

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