import random
from typing import Iterator

from .schemas import Player, RawEvent

NAMES = ["Rivera", "Okafor", "Lindqvist", "Haddad", "Moreau", "Tanaka",
         "Silva", "Novak", "Adeyemi", "Kowalski", "Brandt"]
PLAYERS = [Player(id=f"P{i+1}", name=n, team="Home") for i, n in enumerate(NAMES)]
clip = lambda v, lo, hi: max(lo, min(hi, v))


def _opponents(rng, ball):
    """Everything is from the acting team's view, attacking toward x=105."""
    d = rng.uniform(65, 85)
    m = d - rng.uniform(10, 18)
    a = m - rng.uniform(10, 18)
    opps = []
    for x, count in ((d, 4), (m, 4), (a, 2)):
        for _ in range(count):
            opps.append((clip(x + rng.gauss(0, 2), 0, 105), rng.uniform(5, 63)))
    if rng.random() < 0.5:  # a defender closing the ball down
        opps[rng.randrange(4, 8)] = (clip(ball[0] + rng.uniform(-3, 3), 0, 105),
                                     clip(ball[1] + rng.uniform(-3, 3), 0, 68))
    return opps


def generate_match(n: int = 300, seed: int = 42,
                   match_id: str = "syn-001") -> Iterator[RawEvent]:
    rng = random.Random(seed)
    for k in range(n):
        minutes = 90 * k / n
        ts = f"{int(minutes):02d}:{int((minutes % 1) * 60):02d}"
        etype = rng.choices(["pass", "carry", "tackle", "interception"],
                            weights=[70, 15, 10, 5])[0]

        if etype in ("tackle", "interception"):
            sx, sy = rng.uniform(5, 70), rng.uniform(3, 65)
            ex, ey, ok = sx, sy, rng.random() < 0.8
        else:
            sx, sy = rng.uniform(5, 100), rng.uniform(3, 65)
            dx, dy = (rng.gauss(10, 12), rng.gauss(0, 10)) if etype == "pass" \
                else (rng.gauss(6, 5), rng.gauss(0, 4))
            ex, ey = clip(sx + dx, 0, 105), clip(sy + dy, 0, 68)
            ok = rng.random() < (0.85 if etype == "pass" else 0.9)

        yield RawEvent(
            match_id=match_id, timestamp=ts, event_type=etype,
            player=rng.choice(PLAYERS), start=(sx, sy), end=(ex, ey),
            success=ok, opponents=_opponents(rng, (sx, sy)),
        )