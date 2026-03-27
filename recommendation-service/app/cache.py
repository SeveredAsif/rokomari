"""
cache.py
--------
A simple Redis-based cache for recommendations.

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
        return None

    try:
        _client = redis.from_url(redis_url, decode_responses=True)
        _client.ping()   # test the connection immediately
        print("✅ Redis connected")
    except Exception as e:
        print(f"⚠️  Redis not available: {e} — running without cache")
        _client = None

    return _client


def cache_get(key: str) -> Optional[Any]:
    """
    Fetch a cached value by key.
    Returns the deserialized Python object, or None if not found / Redis is down.

    Example:
        data = cache_get("recommendations:user:42")
        if data is not None:
            return data   # ← fast path: skip the DB + similarity computation
    """
    client = get_redis_client()
    if client is None:
        return None
    try:
        raw = client.get(key)
        return json.loads(raw) if raw else None
    except Exception:
        return None


def cache_set(key: str, value: Any, ttl_seconds: int = 300) -> None:
    """
    Store a value in the cache with a TTL (time-to-live).
    After ttl_seconds, Redis automatically deletes the key.

    Default TTL is 300 seconds (5 minutes) — recommendations don't need
    to be perfectly fresh, and 5 minutes is a good balance.

    Example:
        cache_set("recommendations:user:42", results, ttl_seconds=300)
    """
    client = get_redis_client()
    if client is None:
        return
    try:
        client.setex(key, ttl_seconds, json.dumps(value))
    except Exception:
        pass   # Cache failures should never crash the main request


def cache_delete(key: str) -> None:
    """Invalidate (delete) a specific cache key."""
    client = get_redis_client()
    if client is None:
        return
    try:
        client.delete(key)
    except Exception:
        pass
