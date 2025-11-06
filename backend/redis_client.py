"""
Redis client module for caching and real-time features.
Optional integration - works gracefully if Redis is not available.
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


def get_redis_client() -> Optional[redis.Redis]:
    """Get or create Redis client."""
    global _redis_client
    
    if _redis_client is not None:
        return _redis_client
    
    redis_url = os.environ.get("REDIS_URL")

    # If no REDIS_URL provided, attempt a local Redis on default port as a convenience.
    if not redis_url:
        default_local = "redis://localhost:6379/0"
        try:
            client = redis.from_url(default_local, decode_responses=True, socket_connect_timeout=2, socket_timeout=2)
            client.ping()
            _redis_client = client
            logger.info("Connected to local Redis at redis://localhost:6379/0 (auto-detected)")
            return _redis_client
        except Exception:
            logger.info("REDIS_URL not set and no local Redis detected, Redis disabled")
            return None
    
    try:
        _redis_client = redis.from_url(
            redis_url,
            decode_responses=True,
            socket_connect_timeout=5,
            socket_timeout=5
        )
        # Test connection
        _redis_client.ping()
        logger.info("✅ Connected to Redis")
        return _redis_client
    except (ConnectionError, TimeoutError) as e:
        logger.warning(f"⚠️ Failed to connect to Redis: {e}")
        _redis_client = None
        return None
    except Exception as e:
        logger.warning(f"⚠️ Redis connection error: {e}")
        _redis_client = None
        return None


def cache_get(key: str) -> Optional[Any]:
    """Get value from Redis cache."""
    client = get_redis_client()
    if client is None:
        return None
    
    try:
        value = client.get(key)
        if value:
            return json.loads(value)
        return None
    except Exception as e:
        logger.error(f"Error getting from Redis cache: {e}")
        return None


def cache_set(key: str, value: Any, ttl: int = 3600):
    """Set value in Redis cache with TTL (default 1 hour)."""
    client = get_redis_client()
    if client is None:
        return False
    
    try:
        client.setex(key, ttl, json.dumps(value))
        return True
    except Exception as e:
        logger.error(f"Error setting Redis cache: {e}")
        return False


def is_redis_available() -> bool:
    """Check if Redis is available."""
    return get_redis_client() is not None


def close_redis_connection():
    """Close Redis connection."""
    global _redis_client
    if _redis_client is not None:
        _redis_client.close()
        _redis_client = None
        logger.info("Redis connection closed")

