"""LLM response caching for cost optimization."""

import hashlib
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Protocol
from dataclasses import dataclass, asdict
import asyncio
from pathlib import Path

from ..models.llm import LLMPersonalityResponse
from ..utils.monitoring import performance_monitor


@dataclass
class CachedLLMResponse:
    """Cached LLM response with metadata."""
    query_hash: str
    response: LLMPersonalityResponse
    created_at: datetime
    expires_at: datetime
    hit_count: int = 1
    llm_provider: str = "unknown"
    llm_model: str = "unknown"
    
    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        return datetime.now() > self.expires_at
    
    def increment_hit_count(self) -> None:
        """Increment the hit count for this cache entry."""
        self.hit_count += 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "query_hash": self.query_hash,
            "response": self.response.model_dump(),
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
            "hit_count": self.hit_count,
            "llm_provider": self.llm_provider,
            "llm_model": self.llm_model
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CachedLLMResponse":
        """Create from dictionary."""
        return cls(
            query_hash=data["query_hash"],
            response=LLMPersonalityResponse(**data["response"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            expires_at=datetime.fromisoformat(data["expires_at"]),
            hit_count=data.get("hit_count", 1),
            llm_provider=data.get("llm_provider", "unknown"),
            llm_model=data.get("llm_model", "unknown")
        )


class CacheClient(Protocol):
    """Protocol for cache client implementations."""
    
    async def get(self, key: str) -> Optional[CachedLLMResponse]:
        """Get cached response by key."""
        ...
    
    async def set(self, key: str, value: CachedLLMResponse) -> None:
        """Set cached response."""
        ...
    
    async def delete(self, key: str) -> None:
        """Delete cached response."""
        ...
    
    async def clear(self) -> None:
        """Clear all cached responses."""
        ...
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        ...


class InMemoryCache:
    """In-memory cache implementation."""
    
    def __init__(self, max_size: int = 1000, cleanup_interval: int = 300):
        """Initialize in-memory cache.
        
        Args:
            max_size: Maximum number of cache entries
            cleanup_interval: Interval in seconds for cleaning expired entries
        """
        self._cache: Dict[str, CachedLLMResponse] = {}
        self._max_size = max_size
        self._cleanup_interval = cleanup_interval
        self._cleanup_task: Optional[asyncio.Task] = None
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "expirations": 0
        }
        self._lock = asyncio.Lock()
    
    async def start(self) -> None:
        """Start background cleanup task."""
        if not self._cleanup_task:
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
    
    async def stop(self) -> None:
        """Stop background cleanup task."""
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None
    
    async def _cleanup_loop(self) -> None:
        """Background task to clean expired entries."""
        while True:
            await asyncio.sleep(self._cleanup_interval)
            await self._cleanup_expired()
    
    async def _cleanup_expired(self) -> None:
        """Remove expired entries from cache."""
        async with self._lock:
            expired_keys = [
                key for key, value in self._cache.items()
                if value.is_expired()
            ]
            for key in expired_keys:
                del self._cache[key]
                self._stats["expirations"] += 1
    
    async def _evict_lru(self) -> None:
        """Evict least recently used entry if cache is full."""
        if len(self._cache) >= self._max_size:
            # Find entry with oldest created_at time
            oldest_key = min(
                self._cache.keys(),
                key=lambda k: self._cache[k].created_at
            )
            del self._cache[oldest_key]
            self._stats["evictions"] += 1
    
    @performance_monitor("cache_get", "cache")
    async def get(self, key: str) -> Optional[CachedLLMResponse]:
        """Get cached response by key."""
        async with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                if not entry.is_expired():
                    entry.increment_hit_count()
                    self._stats["hits"] += 1
                    return entry
                else:
                    # Remove expired entry
                    del self._cache[key]
                    self._stats["expirations"] += 1
            
            self._stats["misses"] += 1
            return None
    
    @performance_monitor("cache_set", "cache")
    async def set(self, key: str, value: CachedLLMResponse) -> None:
        """Set cached response."""
        async with self._lock:
            # Evict LRU if needed
            await self._evict_lru()
            self._cache[key] = value
    
    async def delete(self, key: str) -> None:
        """Delete cached response."""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
    
    async def clear(self) -> None:
        """Clear all cached responses."""
        async with self._lock:
            self._cache.clear()
            self._stats = {
                "hits": 0,
                "misses": 0,
                "evictions": 0,
                "expirations": 0
            }
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        async with self._lock:
            total_requests = self._stats["hits"] + self._stats["misses"]
            hit_rate = self._stats["hits"] / total_requests if total_requests > 0 else 0.0
            
            return {
                **self._stats,
                "size": len(self._cache),
                "max_size": self._max_size,
                "hit_rate": hit_rate
            }
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.stop()


def generate_cache_key(description: str, llm_provider: str = "", llm_model: str = "") -> str:
    """Generate cache key from personality description.
    
    Args:
        description: Personality description text
        llm_provider: LLM provider name
        llm_model: LLM model name
        
    Returns:
        SHA256 hash of normalized description
    """
    # Normalize description: lowercase, strip whitespace, remove punctuation
    normalized = description.lower().strip()
    
    # Include provider and model in cache key to avoid conflicts
    cache_data = f"{normalized}:{llm_provider}:{llm_model}"
    
    # Generate SHA256 hash
    return hashlib.sha256(cache_data.encode()).hexdigest()


def calculate_similarity(desc1: str, desc2: str) -> float:
    """Calculate similarity between two descriptions.
    
    Args:
        desc1: First description
        desc2: Second description
        
    Returns:
        Similarity score between 0.0 and 1.0
    """
    # Simple word-based similarity for now
    words1 = set(desc1.lower().split())
    words2 = set(desc2.lower().split())
    
    if not words1 or not words2:
        return 0.0
    
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    return len(intersection) / len(union) if union else 0.0


async def find_similar_cached_response(
    cache: CacheClient,
    description: str,
    similarity_threshold: float = 0.8
) -> Optional[CachedLLMResponse]:
    """Find similar cached response based on description similarity.
    
    Args:
        cache: Cache client instance
        description: Personality description to match
        similarity_threshold: Minimum similarity score to consider a match
        
    Returns:
        Similar cached response if found, None otherwise
    """
    # This is a simplified implementation
    # In production, you'd want to use more sophisticated similarity matching
    # like embeddings or semantic search
    
    # For now, just try exact match
    cache_key = generate_cache_key(description)
    return await cache.get(cache_key)


# File-based cache for persistence (optional)
class FileCache:
    """File-based cache implementation for persistence."""
    
    def __init__(self, cache_dir: Path, ttl_hours: int = 24):
        """Initialize file-based cache.
        
        Args:
            cache_dir: Directory to store cache files
            ttl_hours: Time to live in hours for cache entries
        """
        self.cache_dir = cache_dir
        self.ttl = timedelta(hours=ttl_hours)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_cache_path(self, key: str) -> Path:
        """Get file path for cache key."""
        return self.cache_dir / f"{key}.json"
    
    async def get(self, key: str) -> Optional[CachedLLMResponse]:
        """Get cached response from file."""
        cache_path = self._get_cache_path(key)
        
        if not cache_path.exists():
            return None
        
        try:
            with open(cache_path, 'r') as f:
                data = json.load(f)
                entry = CachedLLMResponse.from_dict(data)
                
                if entry.is_expired():
                    cache_path.unlink()
                    return None
                
                entry.increment_hit_count()
                # Update file with new hit count
                await self.set(key, entry)
                return entry
                
        except Exception:
            # If file is corrupted, remove it
            cache_path.unlink(missing_ok=True)
            return None
    
    async def set(self, key: str, value: CachedLLMResponse) -> None:
        """Save cached response to file."""
        cache_path = self._get_cache_path(key)
        
        try:
            with open(cache_path, 'w') as f:
                json.dump(value.to_dict(), f, indent=2)
        except Exception:
            # Silently fail on write errors
            pass
    
    async def delete(self, key: str) -> None:
        """Delete cached response file."""
        cache_path = self._get_cache_path(key)
        cache_path.unlink(missing_ok=True)
    
    async def clear(self) -> None:
        """Clear all cache files."""
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink()
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        cache_files = list(self.cache_dir.glob("*.json"))
        total_size = sum(f.stat().st_size for f in cache_files)
        
        return {
            "size": len(cache_files),
            "total_size_bytes": total_size,
            "cache_dir": str(self.cache_dir)
        }


# Redis cache for persistent caching across restarts
class RedisCache:
    """Redis-based cache implementation for persistence."""
    
    def __init__(self, redis_url: str, ttl_hours: int = 24, key_prefix: str = "llm_cache:"):
        """Initialize Redis cache.
        
        Args:
            redis_url: Redis connection URL
            ttl_hours: Time to live in hours for cache entries
            key_prefix: Prefix for Redis keys
        """
        self.redis_url = redis_url
        self.ttl = timedelta(hours=ttl_hours)
        self.key_prefix = key_prefix
        self._redis = None
        self._stats = {
            "hits": 0,
            "misses": 0,
            "errors": 0
        }
    
    async def _get_redis(self):
        """Get Redis connection, creating if needed."""
        if self._redis is None:
            try:
                import redis.asyncio as redis
                self._redis = redis.from_url(self.redis_url, decode_responses=True)
                # Test connection
                await self._redis.ping()
            except Exception as e:
                raise ConnectionError(f"Failed to connect to Redis: {e}")
        return self._redis
    
    def _make_key(self, key: str) -> str:
        """Create Redis key with prefix."""
        return f"{self.key_prefix}{key}"
    
    @performance_monitor("redis_cache_get", "cache")
    async def get(self, key: str) -> Optional[CachedLLMResponse]:
        """Get cached response from Redis."""
        try:
            redis_client = await self._get_redis()
            redis_key = self._make_key(key)
            
            data = await redis_client.get(redis_key)
            if data is None:
                self._stats["misses"] += 1
                return None
            
            # Parse JSON data
            cache_data = json.loads(data)
            entry = CachedLLMResponse.from_dict(cache_data)
            
            # Check expiration
            if entry.is_expired():
                await self.delete(key)
                self._stats["misses"] += 1
                return None
            
            # Increment hit count and update in Redis
            entry.increment_hit_count()
            await self.set(key, entry)
            self._stats["hits"] += 1
            return entry
            
        except Exception:
            self._stats["errors"] += 1
            return None
    
    @performance_monitor("redis_cache_set", "cache")
    async def set(self, key: str, value: CachedLLMResponse) -> None:
        """Set cached response in Redis."""
        try:
            redis_client = await self._get_redis()
            redis_key = self._make_key(key)
            
            # Serialize to JSON
            data = json.dumps(value.to_dict())
            
            # Set with TTL
            ttl_seconds = int(self.ttl.total_seconds())
            await redis_client.setex(redis_key, ttl_seconds, data)
            
        except Exception:
            self._stats["errors"] += 1
    
    async def delete(self, key: str) -> None:
        """Delete cached response from Redis."""
        try:
            redis_client = await self._get_redis()
            redis_key = self._make_key(key)
            await redis_client.delete(redis_key)
        except Exception:
            self._stats["errors"] += 1
    
    async def clear(self) -> None:
        """Clear all cached responses."""
        try:
            redis_client = await self._get_redis()
            # Find all keys with our prefix
            pattern = f"{self.key_prefix}*"
            keys = await redis_client.keys(pattern)
            if keys:
                await redis_client.delete(*keys)
        except Exception:
            self._stats["errors"] += 1
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        try:
            redis_client = await self._get_redis()
            # Count keys with our prefix
            pattern = f"{self.key_prefix}*"
            keys = await redis_client.keys(pattern)
            size = len(keys)
            
            total_requests = self._stats["hits"] + self._stats["misses"]
            hit_rate = self._stats["hits"] / total_requests if total_requests > 0 else 0.0
            
            return {
                **self._stats,
                "size": size,
                "hit_rate": hit_rate,
                "redis_url": self.redis_url
            }
        except Exception:
            return {
                **self._stats,
                "size": 0,
                "hit_rate": 0.0,
                "redis_url": self.redis_url
            }
    
    async def close(self) -> None:
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()
            self._redis = None


# Factory function for creating cache clients
async def create_cache_client(
    cache_type: str = "memory",
    **kwargs
) -> CacheClient:
    """Create cache client based on type.
    
    Args:
        cache_type: Type of cache ("memory", "file", or "redis")
        **kwargs: Additional arguments for cache initialization
        
    Returns:
        Cache client instance
    """
    if cache_type == "memory":
        max_size = kwargs.get("max_size", 1000)
        cleanup_interval = kwargs.get("cleanup_interval", 300)
        cache = InMemoryCache(max_size, cleanup_interval)
        await cache.start()
        return cache
    
    elif cache_type == "file":
        cache_dir = kwargs.get("cache_dir", Path("./cache/llm"))
        ttl_hours = kwargs.get("ttl_hours", 24)
        return FileCache(cache_dir, ttl_hours)
    
    elif cache_type == "redis":
        redis_url = kwargs.get("redis_url", "redis://localhost:6379")
        ttl_hours = kwargs.get("ttl_hours", 24)
        key_prefix = kwargs.get("key_prefix", "llm_cache:")
        return RedisCache(redis_url, ttl_hours, key_prefix)
    
    else:
        raise ValueError(f"Unknown cache type: {cache_type}")