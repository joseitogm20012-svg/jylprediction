import os
import json
import logging
from datetime import datetime, timezone
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

MONGO_URL = os.environ.get("MONGO_URL", "mongodb://localhost:27017/scrapycoco")
MONGO_TIMEOUT_MS = int(os.environ.get("MONGO_TIMEOUT_MS", "3000"))
MONGO_DB_NAME = os.environ.get("MONGO_DB_NAME", "scrapycoco")

_client: Optional[AsyncIOMotorClient] = None
_db: Optional[AsyncIOMotorDatabase] = None


async def connect():
    global _client, _db
    if _client is not None:
        return _db
    try:
        _client = AsyncIOMotorClient(MONGO_URL, serverSelectionTimeoutMS=MONGO_TIMEOUT_MS)
        _db = _client[MONGO_DB_NAME]
        await _client.admin.command("ping")
        logger.info(f"MongoDB connected: {MONGO_URL}")
    except Exception as e:
        logger.warning(f"MongoDB connection failed: {e}. Running without MongoDB.")
        _client = None
        _db = None
    return _db


async def disconnect():
    global _client, _db
    if _client:
        _client.close()
        _client = None
        _db = None
        logger.info("MongoDB disconnected")


def get_db() -> Optional[AsyncIOMotorDatabase]:
    return _db


async def is_connected() -> bool:
    if not _client:
        return False
    try:
        await _client.admin.command("ping")
        return True
    except Exception:
        return False


# --- Collections ---

async def get_collection(name: str):
    db = get_db()
    if db is None:
        return None
    return db[name]


async def save_raw_page(scraper_id: str, url: str, html: str, metadata: dict = None):
    col = await get_collection("raw_pages")
    if col is None:
        return None
    doc = {
        "scraper_id": scraper_id,
        "url": url,
        "html": html,
        "metadata": metadata or {},
        "crawled_at": datetime.now(timezone.utc).isoformat(),
        "html_hash": hash(html) % (2**32),
    }
    result = await col.insert_one(doc)
    return str(result.inserted_id)


async def save_cached_response(key: str, data: dict, ttl_seconds: int = 3600):
    col = await get_collection("cache")
    if col is None:
        return None
    doc = {
        "cache_key": key,
        "data": data,
        "expires_at": datetime.now(timezone.utc).timestamp() + ttl_seconds,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    result = await col.replace_one({"cache_key": key}, doc, upsert=True)
    return result.upserted_id


async def get_cached_response(key: str) -> Optional[dict]:
    col = await get_collection("cache")
    if col is None:
        return None
    doc = await col.find_one({"cache_key": key, "expires_at": {"$gt": datetime.now(timezone.utc).timestamp()}})
    return doc.get("data") if doc else None


async def save_session(scraper_id: str, session_data: dict):
    col = await get_collection("sessions")
    if col is None:
        return None
    doc = {
        "scraper_id": scraper_id,
        "session_data": session_data,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }
    result = await col.replace_one({"scraper_id": scraper_id}, doc, upsert=True)
    return result.upserted_id


async def get_session(scraper_id: str) -> Optional[dict]:
    col = await get_collection("sessions")
    if col is None:
        return None
    doc = await col.find_one({"scraper_id": scraper_id})
    return doc.get("session_data") if doc else None


async def get_collection_stats() -> dict:
    db = get_db()
    if db is None:
        return {"available": False}
    stats = {}
    for name in await db.list_collection_names():
        count = await db[name].count_documents({})
        stats[name] = count
    return {"available": True, "collections": stats}
