import json
from redis_client import redis_client

def save_match_event(match_id: str, event_data: dict) -> None:
    key = f"match:{match_id}:events"
    redis_client.rpush(key, json.dumps(event_data))

def get_match_events(match_id: str) -> list:
    key = f"match:{match_id}:events"
    raw_events = redis_client.lrange(key, 0, -1)
    return [json.loads(e) for e in raw_events]

def update_player_impact(match_id: str, player_id: str, impact_delta: float) -> None:
    key = f"match:{match_id}:leaderboard"
    redis_client.zincrby(key, impact_delta, player_id)

def get_leaderboard(match_id: str) -> list:
    key = f"match:{match_id}:leaderboard"
    top_players = redis_client.zrevrange(key, 0, 9, withscores=True)
    return [{"player_id": pid, "score": score} for pid, score in top_players]