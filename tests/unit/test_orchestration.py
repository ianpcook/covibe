"""
Unit tests for the orchestration service.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch

from src.covibe.services.orchestration import (
    orchestrate_personality_request,
    orchestrate_research_only,
    orchestrate_batch_requests,
    PersonalityCache,
    CacheEntry,
    OrchestrationResult,
    get_cache_stats,
    clear_cache,
    _execute_research_stage,
    _execute_context_stage,
    _execute_ide_integration_stage
)
from src.covibe.models.core import (
    PersonalityRequest, PersonalityProfile, PersonalityConfig,
    ResearchResult, ErrorDetail, SourceType, PersonalityType,
    CommunicationStyle, FormalityLevel, VerbosityLevel, TechnicalLevel
)


@pytest.fixture
def sample_request():
    """Sample personality request for testing."""
    return PersonalityRequest(
        id="test-123",
        description="Tony Stark",
        user_id="user-456",
        timestamp=datetime.now(),
        source=SourceType.API
    )


@pytest.fixture
def sample_profile():
    """Sample personality profile for testing."""
    return PersonalityProfile(
        id="profile-123",
        name="Tony Stark",
        type=PersonalityType.FICTIONAL,
        traits=[],
        communication_style=CommunicationStyle(
            tone="confident",
            formality=FormalityLevel.CASUAL,
            verbosity=VerbosityLevel.MODERATE,
            technical_level=TechnicalLevel.EXPERT
        ),
        mannerisms=["witty remarks", "technical jargon"],
        sources=[]
    )


@pytest.fixture
def sample_research_result(sample_profile):
    """Sample research result for testing."""
    return ResearchResult(
        query="Tony Stark",
        profiles=[sample_profile],
        confidence=0.9,
        suggestions=[],
        errors=[]
    )


class TestPersonalityCache:
    """Test personality cache functionality."""
    
    def test_cache_entry_expiration(self):
        """Test cache entry expiration logic."""
        # Fresh entry
        entry = CacheEntry(
            result=Mock(),
            timestamp=datetime.now(),
            ttl_hours=1
        )
        assert not entry.is_expired
        
        # Expired entry
        old_entry = CacheEntry(
            result=Mock(),
            timestamp=datetime.now() - timedelta(hours=2),
            ttl_hours=1
        )
        assert old_entry.is_expired
    
    def test_cache_get_set(self, sample_research_result):
        """Test cache get and set operations."""
        cache = PersonalityCache()
        
        # Cache miss
        assert cache.get("Tony Stark") is None
        
        # Cache set and hit
        cache.set("Tony Stark", sample_research_result)
        result = cache.get("Tony Stark")
        assert result == sample_research_result
        
        # Case insensitive
        result = cache.get("tony stark")
        assert result == sample_research_result
    
    def test_cache_expiration_cleanup(self, sample_research_result):
        """Test cache expiration and cleanup."""
        cache = PersonalityCache()
        
        # Add expired entry
        cache._cache["expired"] = CacheEntry(
            result=sample_research_result,
            timestamp=datetime.now() - timedelta(hours=25),
            ttl_hours=24
        )
        
        # Add fresh entry
        cache.set("fresh", sample_research_result)
        
        # Get expired entry should return None and clean up
        assert cache.get("expired") is None
        assert "expired" not in cache._cache
        
        # Fresh entry should still be there
        assert cache.get("fresh") == sample_research_result
    
    def test_clear_expired(self, sample_research_result):
        """Test clearing expired entries."""
        cache = PersonalityCache()
        
        # Add mix of fresh and expired entries
        cache.set("fresh1", sample_research_result)
        cache.set("fresh2", sample_research_result)
        
        cache._cache["expired1"] = CacheEntry(
            result=sample_research_result,
            timestamp=datetime.now() - timedelta(hours=25),
            ttl_hours=24
        )
        cache._cache["expired2"] = CacheEntry(
            result=sample_research_result,
            timestamp=datetime.now() - timedelta(hours=26),
            ttl_hours=24
        )
        
        # Clear expired
        cleared_count = cache.clear_expired()
        assert cleared_count == 2
        assert len(cache._cache) == 2
        assert "fresh1" in cache._cache
        assert "fresh2" in cache._cache


class TestOrchestrationStages:
    """Test individual orchestration stages."""
    
    @pytest.mark.asyncio
    async def test_research_stage_with_cache(self, sample_research_result):
        """Test research stage with caching."""
        with patch('src.covibe.services.orchestration.research_personality') as mock_research:
            mock_research.return_value = sample_research_result
            
            # First call should hit research function
            result1 = await _execute_research_stage("Tony Stark", use_cache=True)
            assert result1 == sample_research_result
            mock_research.assert_called_once_with("Tony Stark")
            
            # Second call should hit cache
            mock_research.reset_mock()
            result2 = await _execute_research_stage("Tony Stark", use_cache=True)
            assert result2 == sample_research_result
            mock_research.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_research_stage_without_cache(self, sample_research_result):
        """Test research stage without caching."""
        with patch('src.covibe.services.orchestration.research_personality') as mock_research:
            mock_research.return_value = sample_research_result
            
            # Both calls should hit research function
            result1 = await _execute_research_stage("Tony Stark", use_cache=False)
            assert result1 == sample_research_result
            
            result2 = await _execute_research_stage("Tony Stark", use_cache=False)
            assert result2 == sample_research_result
            
            assert mock_research.call_count == 2
    
    @pytest.mark.asyncio
    async def test_research_stage_error_handling(self):
        """Test research stage error handling."""
        # Clear cache first to ensure no cached results interfere
        with patch('src.covibe.services.orchestration._personality_cache') as mock_cache:
            mock_cache.get.return_value = None  # No cached result
            
            with patch('src.covibe.services.orchestration.research_personality') as mock_research:
                mock_research.side_effect = Exception("API Error")
                
                result = await _execute_research_stage("Unknown Person", use_cache=True)
                
                assert result.query == "Unknown Person"
                assert result.profiles == []
                assert result.confidence == 0.0
                assert "API Error" in result.errors
    
    @pytest.mark.asyncio
    async def test_context_stage_success(self, sample_profile):
        """Test context generation stage success."""
        with patch('src.covibe.services.orchestration.generate_personality_context') as mock_context:
            mock_context.return_value = "Generated context"
            
            result = await _execute_context_stage(sample_profile)
            assert result == "Generated context"
            mock_context.assert_called_once_with(sample_profile)
    
    @pytest.mark.asyncio
    async def test_context_stage_error(self, sample_profile):
        """Test context generation stage error handling."""
        with patch('src.covibe.services.orchestration.generate_personality_context') as mock_context:
            mock_context.side_effect = Exception("Context error")
            
            result = await _execute_context_stage(sample_profile)
            assert result is None
    
    @pytest.mark.asyncio
    async def test_ide_integration_stage_success(self, sample_profile):
        """Test IDE integration stage success."""
        project_path = Path("/test/project")
        
        with patch('src.covibe.services.orchestration.detect_ides') as mock_detect, \
             patch('src.covibe.services.orchestration.get_primary_ide') as mock_primary:
            
            mock_ide_info = Mock()
            mock_ide_info.type = "cursor"
            mock_ide_info.config_path = "/test/.cursor/rules/personality.mdc"
            mock_ide_info.name = "Cursor"
            mock_ide_info.confidence = 0.9
            
            mock_detect.return_value = [mock_ide_info]
            mock_primary.return_value = mock_ide_info
            
            result = await _execute_ide_integration_stage(
                sample_profile, "test context", project_path, "test-123"
            )
            
            assert result is not None
            assert result.ide_type == "cursor"
            assert result.active is True
            assert "/test/.cursor/rules/personality.mdc" in result.file_path
    
    @pytest.mark.asyncio
    async def test_ide_integration_stage_no_ide_detected(self, sample_profile):
        """Test IDE integration stage with no IDE detected."""
        project_path = Path("/test/project")
        
        with patch('src.covibe.services.orchestration.detect_ides') as mock_detect, \
             patch('src.covibe.services.orchestration.get_primary_ide') as mock_primary:
            
            mock_detect.return_value = []
            mock_primary.return_value = None
            
            result = await _execute_ide_integration_stage(
                sample_profile, "test context", project_path, "test-123"
            )
            
            assert result is not None
            assert result.ide_type == "unknown"
            assert result.active is False
            assert result.file_path == ""


class TestFullOrchestration:
    """Test full orchestration workflows."""
    
    @pytest.mark.asyncio
    async def test_orchestrate_personality_request_success(self, sample_request, sample_research_result):
        """Test successful personality request orchestration."""
        with patch('src.covibe.services.orchestration._execute_research_stage') as mock_research, \
             patch('src.covibe.services.orchestration._execute_context_stage') as mock_context, \
             patch('src.covibe.services.orchestration._execute_ide_integration_stage') as mock_ide:
            
            mock_research.return_value = sample_research_result
            mock_context.return_value = "Generated context"
            mock_ide.return_value = PersonalityConfig(
                id=sample_request.id,
                profile=sample_research_result.profiles[0],
                context="Generated context",
                ide_type="cursor",
                file_path="/test/config.mdc",
                active=True,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            
            result = await orchestrate_personality_request(
                sample_request, 
                project_path=Path("/test/project")
            )
            
            assert result.success is True
            assert result.config is not None
            assert result.config.ide_type == "cursor"
            assert result.error is None
    
    @pytest.mark.asyncio
    async def test_orchestrate_personality_request_no_profiles(self, sample_request):
        """Test orchestration with no research results."""
        empty_result = ResearchResult(
            query="Unknown Person",
            profiles=[],
            confidence=0.0,
            suggestions=[],
            errors=[]
        )
        
        with patch('src.covibe.services.orchestration._execute_research_stage') as mock_research:
            mock_research.return_value = empty_result
            
            result = await orchestrate_personality_request(sample_request)
            
            assert result.success is False
            assert result.error.code == "RESEARCH_FAILED"
            assert result.partial_results["research"] == empty_result
    
    @pytest.mark.asyncio
    async def test_orchestrate_personality_request_context_failure(self, sample_request, sample_research_result):
        """Test orchestration with context generation failure."""
        with patch('src.covibe.services.orchestration._execute_research_stage') as mock_research, \
             patch('src.covibe.services.orchestration._execute_context_stage') as mock_context:
            
            mock_research.return_value = sample_research_result
            mock_context.return_value = None
            
            result = await orchestrate_personality_request(sample_request)
            
            assert result.success is False
            assert result.error.code == "CONTEXT_GENERATION_FAILED"
            assert result.partial_results["research"] == sample_research_result
    
    @pytest.mark.asyncio
    async def test_orchestrate_personality_request_without_project_path(self, sample_request, sample_research_result):
        """Test orchestration without project path (no IDE integration)."""
        with patch('src.covibe.services.orchestration._execute_research_stage') as mock_research, \
             patch('src.covibe.services.orchestration._execute_context_stage') as mock_context:
            
            mock_research.return_value = sample_research_result
            mock_context.return_value = "Generated context"
            
            result = await orchestrate_personality_request(sample_request)
            
            assert result.success is True
            assert result.config is not None
            assert result.config.ide_type == "unknown"
            assert result.config.active is False
    
    @pytest.mark.asyncio
    async def test_orchestrate_research_only(self, sample_research_result):
        """Test research-only orchestration."""
        with patch('src.covibe.services.orchestration._execute_research_stage') as mock_research:
            mock_research.return_value = sample_research_result
            
            result = await orchestrate_research_only("Tony Stark")
            
            assert result == sample_research_result
            mock_research.assert_called_once_with("Tony Stark", True)
    
    @pytest.mark.asyncio
    async def test_orchestrate_batch_requests(self, sample_research_result):
        """Test batch request orchestration."""
        requests = [
            PersonalityRequest(
                id=f"test-{i}",
                description=f"Person {i}",
                timestamp=datetime.now(),
                source=SourceType.API
            )
            for i in range(3)
        ]
        
        with patch('src.covibe.services.orchestration.orchestrate_personality_request') as mock_orchestrate:
            mock_orchestrate.return_value = OrchestrationResult(success=True)
            
            results = await orchestrate_batch_requests(requests, max_concurrent=2)
            
            assert len(results) == 3
            assert all(result.success for result in results)
            assert mock_orchestrate.call_count == 3
    
    @pytest.mark.asyncio
    async def test_orchestrate_batch_requests_with_errors(self):
        """Test batch orchestration with some failures."""
        requests = [
            PersonalityRequest(
                id="test-1",
                description="Person 1",
                timestamp=datetime.now(),
                source=SourceType.API
            ),
            PersonalityRequest(
                id="test-2",
                description="Person 2",
                timestamp=datetime.now(),
                source=SourceType.API
            )
        ]
        
        with patch('src.covibe.services.orchestration.orchestrate_personality_request') as mock_orchestrate:
            mock_orchestrate.side_effect = [
                OrchestrationResult(success=True),
                Exception("Test error")
            ]
            
            results = await orchestrate_batch_requests(requests)
            
            assert len(results) == 2
            assert results[0].success is True
            assert results[1].success is False
            assert results[1].error.code == "BATCH_REQUEST_ERROR"


class TestCacheManagement:
    """Test cache management functions."""
    
    @pytest.mark.asyncio
    async def test_get_cache_stats(self, sample_research_result):
        """Test cache statistics."""
        # Clear cache first
        await clear_cache(clear_all=True)
        
        # Add some entries
        cache = PersonalityCache()
        cache.set("fresh", sample_research_result)
        cache._cache["expired"] = CacheEntry(
            result=sample_research_result,
            timestamp=datetime.now() - timedelta(hours=25),
            ttl_hours=24
        )
        
        # Patch the global cache
        with patch('src.covibe.services.orchestration._personality_cache', cache):
            stats = get_cache_stats()
            
            assert stats["total_entries"] == 2
            assert stats["expired_entries"] == 1
            assert stats["active_entries"] == 1
    
    @pytest.mark.asyncio
    async def test_clear_cache_all(self, sample_research_result):
        """Test clearing all cache entries."""
        # Add some entries to global cache
        with patch('src.covibe.services.orchestration._personality_cache') as mock_cache:
            # Create a mock dict with clear method
            mock_dict = Mock()
            mock_dict.__len__ = Mock(return_value=2)
            mock_cache._cache = mock_dict
            
            cleared_count = await clear_cache(clear_all=True)
            
            assert cleared_count == 2
            mock_dict.clear.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_clear_cache_expired_only(self):
        """Test clearing only expired cache entries."""
        with patch('src.covibe.services.orchestration._personality_cache') as mock_cache:
            mock_cache.clear_expired.return_value = 3
            
            cleared_count = await clear_cache(clear_all=False)
            
            assert cleared_count == 3
            mock_cache.clear_expired.assert_called_once()