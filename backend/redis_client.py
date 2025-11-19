"""
Redis client module for caching and real-time features.
Railway-safe version. Works gracefully if Redis is not available.
"""

import os
import logging
import json
from typing import Optional, Any
import redis
from redis.exceptions import ConnectionError, TimeoutError

logger = logging.getLogger(__name__)

# Global Redis client
_redis_client: Optional[redis.Redis] = None


# ---------------------------------------------------------
# CONNECT TO REDIS (SILENT IF NOT AVAILABLE)
# ---------------------------------------------------------
def get_redis_client() -> Optional[redis.Redis]:
    """Return Redis client if REDIS_URL is set, else disable silently."""
    global _redis_client

    if _redis_client is not None:
        return _redis_client

    redis_url = os.environ.get("REDIS_URL")

    if not redis_url:
        logger.info("REDIS_URL not set, Redis disabled.")
        return None

    try:
        _redis_client = redis.from_url(
            redis_url,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5,
        )
        _redis_client.ping()
        logger.info("Connected to Redis.")
        return _redis_client

    except Exception:
        logger.error("Redis connection failed.")
        _redis_client = None
        return None


# ---------------------------------------------------------
# CACHE GET
# ---------------------------------------------------------
def cache_get(key: str) -> Optional[Any]:
    """Retrieve a value from Redis cache."""
    client = get_redis_client()
    if client is None:
        return None

    try:
        value = client.get(key)
        return json.loads(value) if value else None
    except Exception:
        return None


# ---------------------------------------------------------
# CACHE SET
# ---------------------------------------------------------
def cache_set(key: str, value: Any, ttl: int = 3600):
    """Store JSON-encoded value in Redis with TTL."""
    client = get_redis_client()
    if client is None:
        return False

    try:
        client.setex(key, ttl, json.dumps(value))
        return True
    except Exception:
        return False


# ---------------------------------------------------------
# HEALTH CHECK
# ---------------------------------------------------------
def is_redis_available() -> bool:
    return get_redis_client() is not None


# ---------------------------------------------------------
# CLOSE CONNECTION
# ---------------------------------------------------------
def close_redis_connection():
    global _redis_client
    if _redis_client:
        try:
            _redis_client.close()
        except Exception:
            pass
        _redis_client = None
        logger.info("Redis connection closed.")
