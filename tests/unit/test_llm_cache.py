"""Unit tests for LLM response caching."""

import asyncio
import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
import pytest
from unittest.mock import Mock, patch

from src.covibe.services.llm_cache import (
    CachedLLMResponse,
    InMemoryCache,
    FileCache,
    RedisCache,
    generate_cache_key,
    calculate_similarity,
    find_similar_cached_response,
    create_cache_client
)
from src.covibe.models.llm import (
    LLMPersonalityResponse,
    LLMTrait,
    LLMCommunicationStyle
)


class TestCachedLLMResponse:
    """Test CachedLLMResponse dataclass."""
    
    @pytest.fixture
    def sample_llm_response(self):
        """Create sample LLM response for testing."""
        return LLMPersonalityResponse(
            name="Tony Stark",
            type="fictional",
            description="Genius inventor with wit",
            traits=[
                LLMTrait(trait="genius", intensity=10, description="Exceptionally intelligent"),
                LLMTrait(trait="witty", intensity=8, description="Sharp sense of humor")
            ],
            communication_style=LLMCommunicationStyle(
                tone="confident",
                formality="casual",
                verbosity="moderate",
                technical_level="expert"
            ),
            mannerisms=["Makes pop culture references", "Uses technical jargon"],
            confidence=0.95
        )
    
    def test_cached_response_creation(self, sample_llm_response):
        """Test creating cached response."""
        now = datetime.now()
        expires = now + timedelta(hours=1)
        
        cached = CachedLLMResponse(
            query_hash="test_hash",
            response=sample_llm_response,
            created_at=now,
            expires_at=expires,
            hit_count=1,
            llm_provider="openai",
            llm_model="gpt-4"
        )
        
        assert cached.query_hash == "test_hash"
        assert cached.response == sample_llm_response
        assert cached.created_at == now
        assert cached.expires_at == expires
        assert cached.hit_count == 1
        assert cached.llm_provider == "openai"
        assert cached.llm_model == "gpt-4"
    
    def test_is_expired(self, sample_llm_response):
        """Test checking if cache entry is expired."""
        now = datetime.now()
        
        # Not expired
        cached = CachedLLMResponse(
            query_hash="test_hash",
            response=sample_llm_response,
            created_at=now,
            expires_at=now + timedelta(hours=1)
        )
        assert not cached.is_expired()
        
        # Expired
        cached_expired = CachedLLMResponse(
            query_hash="test_hash",
            response=sample_llm_response,
            created_at=now - timedelta(hours=2),
            expires_at=now - timedelta(hours=1)
        )
        assert cached_expired.is_expired()
    
    def test_increment_hit_count(self, sample_llm_response):
        """Test incrementing hit count."""
        cached = CachedLLMResponse(
            query_hash="test_hash",
            response=sample_llm_response,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=1)
        )
        
        assert cached.hit_count == 1
        cached.increment_hit_count()
        assert cached.hit_count == 2
        cached.increment_hit_count()
        assert cached.hit_count == 3
    
    def test_to_dict_from_dict(self, sample_llm_response):
        """Test serialization and deserialization."""
        now = datetime.now()
        expires = now + timedelta(hours=1)
        
        cached = CachedLLMResponse(
            query_hash="test_hash",
            response=sample_llm_response,
            created_at=now,
            expires_at=expires,
            hit_count=5,
            llm_provider="anthropic",
            llm_model="claude-3"
        )
        
        # Convert to dict
        data = cached.to_dict()
        assert isinstance(data, dict)
        assert data["query_hash"] == "test_hash"
        assert data["hit_count"] == 5
        assert data["llm_provider"] == "anthropic"
        
        # Convert back from dict
        restored = CachedLLMResponse.from_dict(data)
        assert restored.query_hash == cached.query_hash
        assert restored.response.name == cached.response.name
        assert restored.hit_count == cached.hit_count
        assert restored.llm_provider == cached.llm_provider


class TestInMemoryCache:
    """Test in-memory cache implementation."""
    
    @pytest.fixture
    def sample_cached_response(self):
        """Create sample cached response."""
        response = LLMPersonalityResponse(
            name="Test Character",
            type="fictional",
            description="Test description",
            traits=[LLMTrait(trait="test", intensity=5, description="Test trait")],
            communication_style=LLMCommunicationStyle(
                tone="neutral",
                formality="formal",
                verbosity="concise",
                technical_level="intermediate"
            ),
            confidence=0.8
        )
        
        return CachedLLMResponse(
            query_hash="test_key",
            response=response,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=1)
        )
    
    @pytest.mark.asyncio
    async def test_cache_set_get(self, sample_cached_response):
        """Test setting and getting cache entries."""
        cache = InMemoryCache(max_size=10)
        
        # Set entry
        await cache.set("test_key", sample_cached_response)
        
        # Get entry
        result = await cache.get("test_key")
        assert result is not None
        assert result.query_hash == "test_key"
        assert result.hit_count == 2  # Incremented on get
        
        # Get non-existent entry
        result = await cache.get("non_existent")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_cache_expiration(self, sample_cached_response):
        """Test cache entry expiration."""
        cache = InMemoryCache(max_size=10)
        
        # Create expired entry
        expired_response = CachedLLMResponse(
            query_hash="expired_key",
            response=sample_cached_response.response,
            created_at=datetime.now() - timedelta(hours=2),
            expires_at=datetime.now() - timedelta(hours=1)
        )
        
        await cache.set("expired_key", expired_response)
        
        # Try to get expired entry
        result = await cache.get("expired_key")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_cache_eviction(self):
        """Test LRU eviction when cache is full."""
        cache = InMemoryCache(max_size=3)
        
        # Create sample response
        response = LLMPersonalityResponse(
            name="Test",
            type="fictional",
            description="Test",
            traits=[LLMTrait(trait="test", intensity=5, description="Test")],
            communication_style=LLMCommunicationStyle(
                tone="neutral",
                formality="formal",
                verbosity="concise",
                technical_level="intermediate"
            ),
            confidence=0.8
        )
        
        # Fill cache
        for i in range(4):
            cached = CachedLLMResponse(
                query_hash=f"key_{i}",
                response=response,
                created_at=datetime.now() + timedelta(seconds=i),
                expires_at=datetime.now() + timedelta(hours=1)
            )
            await cache.set(f"key_{i}", cached)
        
        # First entry should be evicted
        result = await cache.get("key_0")
        assert result is None
        
        # Others should still exist
        for i in range(1, 4):
            result = await cache.get(f"key_{i}")
            assert result is not None
    
    @pytest.mark.asyncio
    async def test_cache_delete(self, sample_cached_response):
        """Test deleting cache entries."""
        cache = InMemoryCache()
        
        await cache.set("test_key", sample_cached_response)
        result = await cache.get("test_key")
        assert result is not None
        
        await cache.delete("test_key")
        result = await cache.get("test_key")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_cache_clear(self, sample_cached_response):
        """Test clearing all cache entries."""
        cache = InMemoryCache()
        
        # Add multiple entries
        for i in range(5):
            await cache.set(f"key_{i}", sample_cached_response)
        
        # Clear cache
        await cache.clear()
        
        # All entries should be gone
        for i in range(5):
            result = await cache.get(f"key_{i}")
            assert result is None
    
    @pytest.mark.asyncio
    async def test_cache_stats(self, sample_cached_response):
        """Test cache statistics."""
        cache = InMemoryCache()
        
        # Initial stats
        stats = await cache.get_stats()
        assert stats["hits"] == 0
        assert stats["misses"] == 0
        assert stats["size"] == 0
        
        # Add entry and get it
        await cache.set("test_key", sample_cached_response)
        await cache.get("test_key")
        await cache.get("non_existent")
        
        stats = await cache.get_stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["size"] == 1
        assert stats["hit_rate"] == 0.5
    
    @pytest.mark.asyncio
    async def test_cache_context_manager(self):
        """Test cache as async context manager."""
        async with InMemoryCache() as cache:
            assert cache._cleanup_task is not None
        
        # Cleanup task should be cancelled after exit
        assert cache._cleanup_task is None


class TestFileCache:
    """Test file-based cache implementation."""
    
    @pytest.fixture
    def sample_cached_response(self):
        """Create sample cached response."""
        response = LLMPersonalityResponse(
            name="Test Character",
            type="fictional",
            description="Test description",
            traits=[LLMTrait(trait="test", intensity=5, description="Test trait")],
            communication_style=LLMCommunicationStyle(
                tone="neutral",
                formality="formal",
                verbosity="concise",
                technical_level="intermediate"
            ),
            confidence=0.8
        )
        
        return CachedLLMResponse(
            query_hash="test_key",
            response=response,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=1)
        )
    
    @pytest.mark.asyncio
    async def test_file_cache_set_get(self, sample_cached_response):
        """Test setting and getting cache entries from files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_dir = Path(temp_dir)
            cache = FileCache(cache_dir, ttl_hours=24)
            
            # Set entry
            await cache.set("test_key", sample_cached_response)
            
            # Check file was created
            cache_file = cache_dir / "test_key.json"
            assert cache_file.exists()
            
            # Get entry
            result = await cache.get("test_key")
            assert result is not None
            assert result.query_hash == "test_key"
            assert result.hit_count == 2  # Incremented on get
    
    @pytest.mark.asyncio
    async def test_file_cache_expiration(self):
        """Test file cache entry expiration."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_dir = Path(temp_dir)
            cache = FileCache(cache_dir, ttl_hours=24)
            
            # Create expired entry
            response = LLMPersonalityResponse(
                name="Test",
                type="fictional",
                description="Test",
                traits=[LLMTrait(trait="test", intensity=5, description="Test")],
                communication_style=LLMCommunicationStyle(
                    tone="neutral",
                    formality="formal",
                    verbosity="concise",
                    technical_level="intermediate"
                ),
                confidence=0.8
            )
            
            expired_response = CachedLLMResponse(
                query_hash="expired_key",
                response=response,
                created_at=datetime.now() - timedelta(hours=48),
                expires_at=datetime.now() - timedelta(hours=24)
            )
            
            await cache.set("expired_key", expired_response)
            
            # Try to get expired entry
            result = await cache.get("expired_key")
            assert result is None
            
            # File should be deleted
            cache_file = cache_dir / "expired_key.json"
            assert not cache_file.exists()
    
    @pytest.mark.asyncio
    async def test_file_cache_delete(self, sample_cached_response):
        """Test deleting file cache entries."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_dir = Path(temp_dir)
            cache = FileCache(cache_dir)
            
            await cache.set("test_key", sample_cached_response)
            cache_file = cache_dir / "test_key.json"
            assert cache_file.exists()
            
            await cache.delete("test_key")
            assert not cache_file.exists()
    
    @pytest.mark.asyncio
    async def test_file_cache_clear(self, sample_cached_response):
        """Test clearing all file cache entries."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_dir = Path(temp_dir)
            cache = FileCache(cache_dir)
            
            # Add multiple entries
            for i in range(3):
                await cache.set(f"key_{i}", sample_cached_response)
            
            # Verify files exist
            assert len(list(cache_dir.glob("*.json"))) == 3
            
            # Clear cache
            await cache.clear()
            
            # All files should be gone
            assert len(list(cache_dir.glob("*.json"))) == 0
    
    @pytest.mark.asyncio
    async def test_file_cache_stats(self, sample_cached_response):
        """Test file cache statistics."""
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_dir = Path(temp_dir)
            cache = FileCache(cache_dir)
            
            # Add entries
            for i in range(3):
                await cache.set(f"key_{i}", sample_cached_response)
            
            stats = await cache.get_stats()
            assert stats["size"] == 3
            assert stats["total_size_bytes"] > 0
            assert str(cache_dir) in stats["cache_dir"]


class TestCacheUtilities:
    """Test cache utility functions."""
    
    def test_generate_cache_key(self):
        """Test cache key generation."""
        # Same input should produce same key
        key1 = generate_cache_key("Tony Stark personality", "openai", "gpt-4")
        key2 = generate_cache_key("Tony Stark personality", "openai", "gpt-4")
        assert key1 == key2
        
        # Different input should produce different keys
        key3 = generate_cache_key("Sherlock Holmes personality", "openai", "gpt-4")
        assert key1 != key3
        
        # Different provider/model should produce different keys
        key4 = generate_cache_key("Tony Stark personality", "anthropic", "claude-3")
        assert key1 != key4
        
        # Case and whitespace normalization
        key5 = generate_cache_key("  TONY STARK PERSONALITY  ", "openai", "gpt-4")
        assert key1 == key5
    
    def test_calculate_similarity(self):
        """Test description similarity calculation."""
        # Identical descriptions
        sim = calculate_similarity("Tony Stark personality", "Tony Stark personality")
        assert sim == 1.0
        
        # Completely different
        sim = calculate_similarity("Tony Stark", "Sherlock Holmes")
        assert sim == 0.0
        
        # Partial overlap
        sim = calculate_similarity("Tony Stark genius", "Tony Stark inventor")
        assert 0.0 < sim < 1.0
        
        # Empty descriptions
        sim = calculate_similarity("", "test")
        assert sim == 0.0
        
        sim = calculate_similarity("test", "")
        assert sim == 0.0
    
    @pytest.mark.asyncio
    async def test_find_similar_cached_response(self):
        """Test finding similar cached responses."""
        cache = InMemoryCache()
        
        # Create sample response
        response = LLMPersonalityResponse(
            name="Tony Stark",
            type="fictional",
            description="Genius inventor",
            traits=[LLMTrait(trait="genius", intensity=10, description="Smart")],
            communication_style=LLMCommunicationStyle(
                tone="confident",
                formality="casual",
                verbosity="moderate",
                technical_level="expert"
            ),
            confidence=0.9
        )
        
        cached = CachedLLMResponse(
            query_hash=generate_cache_key("Tony Stark personality"),
            response=response,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=1)
        )
        
        # Add to cache with correct key
        cache_key = generate_cache_key("Tony Stark personality")
        await cache.set(cache_key, cached)
        
        # Find exact match
        result = await find_similar_cached_response(cache, "Tony Stark personality")
        assert result is not None
        assert result.response.name == "Tony Stark"
    
    @pytest.mark.asyncio
    async def test_create_cache_client(self):
        """Test cache client factory."""
        # Create memory cache
        cache = await create_cache_client("memory", max_size=100)
        assert isinstance(cache, InMemoryCache)
        
        # Create file cache
        with tempfile.TemporaryDirectory() as temp_dir:
            cache = await create_cache_client(
                "file", 
                cache_dir=Path(temp_dir),
                ttl_hours=12
            )
            assert isinstance(cache, FileCache)
        
        # Invalid cache type
        with pytest.raises(ValueError, match="Unknown cache type"):
            await create_cache_client("invalid")


class TestRedisCache:
    """Test Redis cache implementation."""
    
    @pytest.fixture
    def sample_cached_response(self):
        """Create sample cached response."""
        response = LLMPersonalityResponse(
            name="Test Character",
            type="fictional",
            description="Test description",
            traits=[LLMTrait(trait="test", intensity=5, description="Test trait")],
            communication_style=LLMCommunicationStyle(
                tone="neutral",
                formality="formal",
                verbosity="concise",
                technical_level="intermediate"
            ),
            confidence=0.8
        )
        
        return CachedLLMResponse(
            query_hash="test_key",
            response=response,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=1)
        )
    
    @pytest.mark.asyncio
    async def test_redis_cache_mock(self, sample_cached_response):
        """Test Redis cache with mocked Redis client."""
        with patch('redis.asyncio.from_url') as mock_redis_factory:
            # Mock Redis client
            mock_redis = Mock()
            mock_redis.ping = Mock(return_value=True)
            mock_redis.get = Mock(return_value=None)
            mock_redis.setex = Mock()
            mock_redis.delete = Mock()
            mock_redis.keys = Mock(return_value=[])
            mock_redis.close = Mock()
            mock_redis_factory.return_value = mock_redis
            
            cache = RedisCache("redis://localhost:6379")
            
            # Test miss
            result = await cache.get("test_key")
            assert result is None
            
            # Test set (should not raise exception)
            await cache.set("test_key", sample_cached_response)
            mock_redis.setex.assert_called_once()
            
            # Test stats
            stats = await cache.get_stats()
            assert "hits" in stats
            assert "misses" in stats
            
            # Test close
            await cache.close()
            mock_redis.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_redis_cache_connection_error(self):
        """Test Redis cache connection error handling."""
        with patch('redis.asyncio.from_url') as mock_redis_factory:
            mock_redis = Mock()
            mock_redis.ping.side_effect = Exception("Connection failed")
            mock_redis_factory.return_value = mock_redis
            
            cache = RedisCache("redis://invalid:6379")
            
            # Should handle connection errors gracefully
            result = await cache.get("test_key")
            assert result is None
    
    @pytest.mark.asyncio
    async def test_create_redis_cache_client(self):
        """Test creating Redis cache client."""
        with patch('redis.asyncio.from_url'):
            cache = await create_cache_client(
                "redis",
                redis_url="redis://localhost:6379",
                ttl_hours=12,
                key_prefix="test:"
            )
            assert isinstance(cache, RedisCache)
            assert cache.redis_url == "redis://localhost:6379"
            assert cache.key_prefix == "test:"