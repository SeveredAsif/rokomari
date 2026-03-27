"""
cache.py
--------
A simple Redis-based cache for search results.

Why cache?
----------
Cosine similarity computes on EVERY product in the database every time a request
comes in. If you have 10,000 products and 100 users searching per second, that's
1,000,000 comparisons per second — very slow and expensive.

Caching stores the result of an expensive computation so the second request for
the same thing is instant (just a key lookup).

Node.js analogy:
----------------
In Node.js you'd use the 'redis' or 'ioredis' package:
    const redis = require('redis')
    const client = redis.createClient({ url: process.env.REDIS_URL })
    await client.set('key', JSON.stringify(data), { EX: 300 })
    const cached = await client.get('key')

This file does exactly the same thing in Python.

NOTE for skeleton phase:
------------------------
Redis is an OPTIONAL dependency for now. If REDIS_URL is not set in .env,
the cache silently does nothing (every call is a cache miss, and data is
never stored). This means the service works fine without Redis — you can
add it later when you're ready.
"""

import os
import json
import redis
from typing import Optional, Any

# If REDIS_URL is missing from .env, _client stays None and all cache
# operations become no-ops (they return None / do nothing silently).
_client: Optional[redis.Redis] = None


def get_redis_client() -> Optional[redis.Redis]:
    """
    Returns a Redis client, creating it on first call (singleton pattern).
    Returns None if REDIS_URL is not configured.
    """
    global _client
    if _client is not None:
        return _client

    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        # Redis not configured — cache will be a no-op
        return None

    try:
        _client = redis.from_url(redis_url, decode_responses=True)
        _client.ping()  # Test the connection
        print(f"✓ Connected to Redis at {redis_url}")
        return _client
    except Exception as e:
        print(f"✗ Could not connect to Redis: {e}")
        return None


def cache_get(key: str) -> Optional[Any]:
    """
    Fetch a value from Redis cache.
    Returns None if the key doesn't exist OR if Redis is not configured.

    Usage:
        cached = cache_get(f"search:{user_id}:{q}")
        if cached is not None:
            return cached
    """
    client = get_redis_client()
    if client is None:
        return None

    try:
        value = client.get(key)
        if value is None:
            return None
        # Redis stores strings, so we parse back to Python objects
        return json.loads(value)
    except Exception as e:
        print(f"Cache read error: {e}")
        return None


def cache_set(key: str, value: Any, ttl_seconds: int = 300) -> bool:
    """
    Store a value in Redis cache with a TTL (time-to-live).
    Returns True if successful, False otherwise.

    Args:
        key: the cache key (e.g., "search:user_123:history+of+bangladesh")
        value: the data to cache (dict, list, etc.)
        ttl_seconds: how long to keep this cache entry (default 5 minutes)

    Usage:
        cache_set(f"search:{user_id}:{q}", results, ttl_seconds=300)
    """
    client = get_redis_client()
    if client is None:
        return False

    try:
        # Convert Python object to JSON string
        json_value = json.dumps(value)
        # Store in Redis with expiration time (in seconds)
        client.setex(key, ttl_seconds, json_value)
        return True
    except Exception as e:
        print(f"Cache write error: {e}")
        return False


def cache_clear(pattern: str = "*") -> int:
    """
    Delete all keys matching the pattern from Redis.
    Returns the number of keys deleted.

    Args:
        pattern: glob pattern (e.g., "search:*" deletes all search cache)

    WARNING: Using "*" alone is dangerous in production (deletes everything).
    """
    client = get_redis_client()
    if client is None:
        return 0

    try:
        keys = client.keys(pattern)
        if keys:
            return client.delete(*keys)
        return 0
    except Exception as e:
        print(f"Cache clear error: {e}")
        return 0
