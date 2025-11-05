import json
import os
import redis.asyncio as redis  # modern async Redis client

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

redis_client = None

async def get_redis():
    global redis_client
    if redis_client is None:
        redis_client = redis.from_url(REDIS_URL, decode_responses=True)
    return redis_client

async def set_cache(key: str, data, expire_seconds: int = 300):
    """Cache data in Redis (auto-serialize to JSON)."""
    r = await get_redis()
    await r.set(key, json.dumps(data), ex=expire_seconds)

async def get_cache(key: str):
    """Retrieve cached data from Redis (auto-deserialize JSON)."""
    r = await get_redis()
    data = await r.get(key)
    return json.loads(data) if data else None

async def invalidate_cache(key: str):
    r = await get_redis()
    await r.delete(key)
