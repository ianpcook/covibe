"""
Integration tests for the orchestration service.
"""

import pytest
import asyncio
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, Mock

from src.covibe.services.orchestration import (
    orchestrate_personality_request,
    orchestrate_research_only,
    get_cache_stats,
    clear_cache
)
from src.covibe.models.core import (
    PersonalityRequest, PersonalityProfile, PersonalityConfig,
    ResearchResult, SourceType, PersonalityType,
    CommunicationStyle, FormalityLevel, VerbosityLevel, TechnicalLevel,
    PersonalityTrait
)


@pytest.fixture
def sample_personality_profile():
    """Create a sample personality profile for testing."""
    return PersonalityProfile(
        id="test-profile-123",
        name="Tony Stark",
        type=PersonalityType.FICTIONAL,
        traits=[
            PersonalityTrait(
                category="intelligence",
                trait="analytical",
                intensity=9,
                examples=["breaks down complex problems", "thinks systematically"]
            ),
            PersonalityTrait(
                category="confidence",
                trait="confident",
                intensity=8,
                examples=["speaks with certainty", "takes charge"]
            )
        ],
        communication_style=CommunicationStyle(
            tone="confident",
            formality=FormalityLevel.CASUAL,
            verbosity=VerbosityLevel.MODERATE,
            technical_level=TechnicalLevel.EXPERT
        ),
        mannerisms=["witty remarks", "technical jargon", "references to engineering"],
        sources=[]
    )


@pytest.fixture
def sample_research_result(sample_personality_profile):
    """Create a sample research result for testing."""
    return ResearchResult(
        query="Tony Stark",
        profiles=[sample_personality_profile],
        confidence=0.9,
        suggestions=[],
        errors=[]
    )


class TestOrchestrationIntegration:
    """Integration tests for orchestration workflows."""
    
    @pytest.mark.asyncio
    async def test_full_orchestration_workflow(self, sample_research_result, tmp_path):
        """Test complete orchestration workflow from request to IDE integration."""
        # Create test request
        request = PersonalityRequest(
            id="integration-test-123",
            description="Tony Stark",
            user_id="test-user",
            timestamp=datetime.now(),
            source=SourceType.API
        )
        
        # Mock the research function to return our sample result
        with patch('src.covibe.services.orchestration.research_personality') as mock_research:
            mock_research.return_value = sample_research_result
            
            # Execute orchestration with project path
            result = await orchestrate_personality_request(
                request, 
                project_path=tmp_path,
                use_cache=False
            )
            
            # Verify successful orchestration
            assert result.success is True
            assert result.config is not None
            assert result.error is None
            
            # Verify configuration details
            config = result.config
            assert config.id == request.id
            assert config.profile.name == "Tony Stark"
            assert config.context is not None
            assert len(config.context) > 0
            
            # Verify context contains expected elements
            assert "Tony Stark" in config.context
            assert "confident" in config.context.lower()
            assert "analytical" in config.context.lower()
            
            # Verify research function was called
            mock_research.assert_called_once_with("Tony Stark")
    
    @pytest.mark.asyncio
    async def test_orchestration_without_project_path(self, sample_research_result):
        """Test orchestration without project path (no IDE integration)."""
        request = PersonalityRequest(
            id="no-ide-test-123",
            description="Tony Stark",
            timestamp=datetime.now(),
            source=SourceType.WEB
        )
        
        with patch('src.covibe.services.orchestration.research_personality') as mock_research:
            mock_research.return_value = sample_research_result
            
            result = await orchestrate_personality_request(request, use_cache=False)
            
            assert result.success is True
            assert result.config is not None
            assert result.config.ide_type == "unknown"
            assert result.config.active is False
    
    @pytest.mark.asyncio
    async def test_research_only_workflow(self, sample_research_result):
        """Test research-only orchestration workflow."""
        with patch('src.covibe.services.orchestration.research_personality') as mock_research:
            mock_research.return_value = sample_research_result
            
            result = await orchestrate_research_only("Tony Stark", use_cache=False)
            
            assert result.query == "Tony Stark"
            assert len(result.profiles) == 1
            assert result.profiles[0].name == "Tony Stark"
            assert result.confidence == 0.9
            
            mock_research.assert_called_once_with("Tony Stark")
    
    @pytest.mark.asyncio
    async def test_caching_behavior(self, sample_research_result):
        """Test that caching works correctly across multiple requests."""
        # Clear cache first
        await clear_cache(clear_all=True)
        
        request = PersonalityRequest(
            id="cache-test-123",
            description="Tony Stark",
            timestamp=datetime.now(),
            source=SourceType.API
        )
        
        with patch('src.covibe.services.orchestration.research_personality') as mock_research:
            mock_research.return_value = sample_research_result
            
            # First request should hit research function
            result1 = await orchestrate_personality_request(request, use_cache=True)
            assert result1.success is True
            assert mock_research.call_count == 1
            
            # Second request with same description should use cache
            request2 = PersonalityRequest(
                id="cache-test-456",
                description="Tony Stark",  # Same description
                timestamp=datetime.now(),
                source=SourceType.API
            )
            
            result2 = await orchestrate_personality_request(request2, use_cache=True)
            assert result2.success is True
            # Research function should not be called again
            assert mock_research.call_count == 1
            
            # Verify cache stats
            stats = get_cache_stats()
            assert stats["active_entries"] >= 1
    
    @pytest.mark.asyncio
    async def test_error_handling_and_recovery(self):
        """Test error handling and partial results."""
        request = PersonalityRequest(
            id="error-test-123",
            description="Unknown Person",
            timestamp=datetime.now(),
            source=SourceType.API
        )
        
        # Mock research to return empty results
        empty_result = ResearchResult(
            query="Unknown Person",
            profiles=[],
            confidence=0.0,
            suggestions=["Try a more specific description"],
            errors=["No information found"]
        )
        
        with patch('src.covibe.services.orchestration.research_personality') as mock_research:
            mock_research.return_value = empty_result
            
            result = await orchestrate_personality_request(request, use_cache=False)
            
            assert result.success is False
            assert result.error is not None
            assert result.error.code == "RESEARCH_FAILED"
            assert result.partial_results is not None
            assert "research" in result.partial_results
    
    @pytest.mark.asyncio
    async def test_context_generation_integration(self, sample_research_result):
        """Test that context generation produces valid output."""
        request = PersonalityRequest(
            id="context-test-123",
            description="Tony Stark",
            timestamp=datetime.now(),
            source=SourceType.API
        )
        
        with patch('src.covibe.services.orchestration.research_personality') as mock_research:
            mock_research.return_value = sample_research_result
            
            result = await orchestrate_personality_request(request, use_cache=False)
            
            assert result.success is True
            context = result.config.context
            
            # Verify context structure and content
            assert "# Personality Context: Tony Stark" in context
            assert "## Communication Style" in context
            assert "## Personality Traits" in context
            assert "## Response Guidelines" in context
            
            # Verify personality-specific content
            assert "confident" in context.lower()
            assert "analytical" in context.lower()
            assert "witty remarks" in context
            assert "technical jargon" in context
    
    @pytest.mark.asyncio
    async def test_ide_detection_integration(self, sample_research_result, tmp_path):
        """Test IDE detection integration."""
        # Create a mock Cursor project structure
        cursor_dir = tmp_path / ".cursor"
        cursor_dir.mkdir()
        rules_dir = cursor_dir / "rules"
        rules_dir.mkdir()
        
        request = PersonalityRequest(
            id="ide-test-123",
            description="Tony Stark",
            timestamp=datetime.now(),
            source=SourceType.API
        )
        
        with patch('src.covibe.services.orchestration.research_personality') as mock_research:
            mock_research.return_value = sample_research_result
            
            result = await orchestrate_personality_request(
                request, 
                project_path=tmp_path,
                use_cache=False
            )
            
            assert result.success is True
            assert result.config.ide_type == "cursor"
            assert result.config.active is True
            assert "personality.mdc" in result.config.file_path
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, sample_research_result):
        """Test handling of concurrent orchestration requests."""
        requests = [
            PersonalityRequest(
                id=f"concurrent-{i}",
                description=f"Person {i}",
                timestamp=datetime.now(),
                source=SourceType.API
            )
            for i in range(5)
        ]
        
        with patch('src.covibe.services.orchestration.research_personality') as mock_research:
            mock_research.return_value = sample_research_result
            
            # Execute requests concurrently
            tasks = [
                orchestrate_personality_request(req, use_cache=False) 
                for req in requests
            ]
            results = await asyncio.gather(*tasks)
            
            # Verify all requests succeeded
            assert len(results) == 5
            assert all(result.success for result in results)
            
            # Verify each request has unique ID
            config_ids = [result.config.id for result in results]
            assert len(set(config_ids)) == 5  # All unique
            
            # Research should have been called for each unique description
            assert mock_research.call_count == 5