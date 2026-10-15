from typing import Literal
from pydantic import BaseModel

EventType = Literal["pass", "carry", "tackle", "interception"]
Point = tuple[float, float]


class Player(BaseModel):
    id: str
    name: str
    team: str


class RawEvent(BaseModel):
    match_id: str
    timestamp: str
    event_type: EventType
    player: Player
    start: Point
    end: Point
    success: bool = True
    opponents: list[Point]  # 10 outfield opponents


class Location(BaseModel):
    start: Point
    end: Point


class Metrics(BaseModel):
    delta_xT: float
    pressure: float
    lines_broken: int
    pass_difficulty: float
    impact_score: float


class Cumulative(BaseModel):
    match_score: float
    rank_on_pitch: int


class EnrichedEvent(BaseModel):
    match_id: str
    timestamp: str
    event_type: EventType
    player: Player
    location: Location
    metrics: Metrics
    cumulative: Cumulative
    significance: Literal["LOW", "MEDIUM", "HIGH"]