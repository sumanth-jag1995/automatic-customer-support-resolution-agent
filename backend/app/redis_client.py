import redis
from app.config import app_config

_client = None

def get_redis():
    global _client
    if _client is None:
        if not app_config.upstash_redis_url:
            raise RuntimeError("UPSTASH_REDIS_URL is not configured")
        _client = redis.from_url(app_config.upstash_redis_url, decode_responses=True)
    return _client

def set_memory(ticket_id: str, key: str, value: str, ttl: int = 3600):
    r = get_redis()
    r.setex(f"ticket:{ticket_id}:{key}", ttl, value)

def get_memory(ticket_id: str, key: str) -> str | None:
    return get_redis().get(f"ticket:{ticket_id}:{key}")

def append_turn(ticket_id: str, role: str, content: str):
    r = get_redis()
    r.rpush(f"ticket:{ticket_id}:turns", f"{role}:{content}")

def get_turns(ticket_id: str) -> list[str]:
    return get_redis().lrange(f"ticket:{ticket_id}:turns", 0, -1)
