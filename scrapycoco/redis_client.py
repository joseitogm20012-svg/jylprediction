import os
import json
import logging
from typing import Optional, Any

logger = logging.getLogger(__name__)

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
_redis = None


async def connect():
    global _redis
    if _redis is not None:
        return _redis
    try:
        import redis.asyncio as aioredis
        _redis = aioredis.from_url(REDIS_URL, decode_responses=True, socket_timeout=5)
        await _redis.ping()
        logger.info(f"Redis connected: {REDIS_URL}")
    except Exception as e:
        logger.warning(f"Redis connection failed: {e}. Running without Redis.")
        _redis = None
    return _redis


async def disconnect():
    global _redis
    if _redis:
        await _redis.close()
        _redis = None
        logger.info("Redis disconnected")


def get_client():
    return _redis


async def is_connected() -> bool:
    if not _redis:
        return False
    try:
        await _redis.ping()
        return True
    except Exception:
        return False


# --- Cache helpers ---

async def cache_get(key: str) -> Optional[str]:
    if not _redis:
        return None
    try:
        return await _redis.get(key)
    except Exception as e:
        logger.warning(f"Redis get error: {e}")
        return None


async def cache_set(key: str, value: str, ttl: int = 300):
    if not _redis:
        return
    try:
        await _redis.setex(key, ttl, value)
    except Exception as e:
        logger.warning(f"Redis set error: {e}")


async def cache_delete(key: str):
    if not _redis:
        return
    try:
        await _redis.delete(key)
    except Exception as e:
        logger.warning(f"Redis delete error: {e}")


async def cache_get_json(key: str) -> Optional[Any]:
    raw = await cache_get(key)
    if raw:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return None
    return None


async def cache_set_json(key: str, data: Any, ttl: int = 300):
    try:
        await cache_set(key, json.dumps(data, ensure_ascii=False), ttl)
    except Exception as e:
        logger.warning(f"Redis set_json error: {e}")


# --- Queue helpers ---

async def enqueue(scraper_id: str, **kwargs):
    if not _redis:
        return False
    task = json.dumps({"scraper_id": scraper_id, **kwargs})
    try:
        await _redis.rpush("scrapycoco:queue", task)
        return True
    except Exception as e:
        logger.warning(f"Redis enqueue error: {e}")
        return False


async def dequeue() -> Optional[dict]:
    if not _redis:
        return None
    try:
        _, task = await _redis.blpop("scrapycoco:queue", timeout=5)
        if task:
            return json.loads(task)
    except Exception as e:
        logger.warning(f"Redis dequeue error: {e}")
    return None


async def queue_length() -> int:
    if not _redis:
        return 0
    try:
        return await _redis.llen("scrapycoco:queue")
    except Exception:
        return 0


async def get_info() -> dict:
    if not _redis:
        return {"available": False}
    try:
        info = await _redis.info()
        return {
            "available": True,
            "version": info.get("redis_version", "unknown"),
            "uptime_seconds": info.get("uptime_in_seconds", 0),
            "connected_clients": info.get("connected_clients", 0),
            "used_memory_human": info.get("used_memory_human", "unknown"),
            "total_keys": await _redis.dbsize(),
            "queue_length": await queue_length(),
        }
    except Exception as e:
        return {"available": False, "error": str(e)}
