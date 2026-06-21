import json
import threading
import redis
from app.config import app_config

_client = None
_client_lock = threading.Lock()

def get_redis():
    global _client
    if _client is None:
        with _client_lock:
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

def append_turn(ticket_id: str, role: str, content: str, ttl: int = 3600):
    r = get_redis()
    key = f"ticket:{ticket_id}:turns"
    r.rpush(key, json.dumps({"role": role, "content": content}))
    r.expire(key, ttl)

def get_turns(ticket_id: str) -> list[dict]:
    raw = get_redis().lrange(f"ticket:{ticket_id}:turns", 0, -1)
    return [json.loads(item) for item in raw]
