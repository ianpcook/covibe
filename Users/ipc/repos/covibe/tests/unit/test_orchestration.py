"""Unit tests for orchestration functionality."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime
from pathlib import Path
from covibe.services.orchestration import (
    orchestrate_personality_creation,
    orchestrate_research_only,
    orchestrate_context_generation,
    orchestrate_ide_detection,
    OrchestrationOptions,
    OrchestrationCache
)
from covibe.models.core import (
    PersonalityRequest,
    SourceType,
    PersonalityProfile,
    PersonalityType,
    CommunicationStyle,
    FormalityLevel,
    VerbosityLevel,
    TechnicalLevel,
    ResearchSource,
    ResearchResult
)


@pytest.fixture
def sample_request():
    """Create a sample personality request."""
    return PersonalityRequest(
        id="test-123",
        description="cowboy personality",
        user_id="user-123",
        timestamp=datetime.now(),
        source=SourceType.API
    )


@pytest.fixture
def sample_profile():
    """Create a sample personality profile."""
    source = ResearchSource(
        type="test",
        url=None,
        confidence=0.9,
        last_updated=datetime.now()
    )
    
    comm_style = CommunicationStyle(
        tone="straightforward",
        formality=FormalityLevel.CASUAL,
        verbosity=VerbosityLevel.CONCISE,
        technical_level=TechnicalLevel.INTERMEDIATE
    )
    
    return PersonalityProfile(
        id="cowboy-profile",
        name="Cowboy",
        type=PersonalityType.ARCHETYPE,
        traits=[],
        communication_style=comm_style,
        mannerisms=["uses simple language"],
        sources=[source]
    )


@pytest.mark.asyncio
async def test_orchestrate_personality_creation_success(sample_request, sample_profile):
    """Test successful personality creation orchestration."""
    # Mock research result
    research_result = ResearchResult(
        query="cowboy personality",
        profiles=[sample_profile],
        confidence=0.9,
        suggestions=[],
        errors=[]
    )
    
    with patch('covibe.services.orchestration.research_personality', return_value=research_result), \
         patch('covibe.services.orchestration.generate_personality_context', return_value="Generated context"):
        
        options = OrchestrationOptions(skip_ide_integration=True)
        result = await orchestrate_personality_creation(sample_request, options)
        
        assert result.success is True
        assert result.config is not None
        assert result.config.profile.name == "Cowboy"
        assert result.research_confidence == 0.9
        assert result.context_generated is True
        assert len(result.errors) == 0


@pytest.mark.asyncio
async def test_orchestrate_personality_creation_no_profiles(sample_request):
    """Test orchestration when no profiles are found."""
    # Mock research result with no profiles
    research_result = ResearchResult(
        query="unknown personality",
        profiles=[],
        confidence=0.0,
        suggestions=["Try a different description"],
        errors=["No profiles found"]
    )
    
    with patch('covibe.services.orchestration.research_personality', return_value=research_result):
        
        result = await orchestrate_personality_creation(sample_request)
        
        assert result.success is False
        assert result.config is None
        assert result.research_confidence == 0.0
        assert len(result.errors) > 0
        assert len(result.suggestions) > 0


@pytest.mark.asyncio
async def test_orchestrate_personality_creation_with_ide_integration(sample_request, sample_profile, tmp_path):
    """Test orchestration with IDE integration."""
    # Mock research result
    research_result = ResearchResult(
        query="cowboy personality",
        profiles=[sample_profile],
        confidence=0.9,
        suggestions=[],
        errors=[]
    )
    
    # Mock IDE detection
    mock_ide_info = MagicMock()
    mock_ide_info.type = "cursor"
    mock_ide_info.name = "Cursor"
    
    # Mock write result
    mock_write_result = MagicMock()
    mock_write_result.success = True
    mock_write_result.file_path = str(tmp_path / ".cursor" / "rules" / "personality.mdc")
    mock_write_result.message = "Success"
    
    with patch('covibe.services.orchestration.research_personality', return_value=research_result), \
         patch('covibe.services.orchestration.generate_personality_context', return_value="Generated context"), \
         patch('covibe.services.orchestration.detect_ides', return_value=[mock_ide_info]), \
         patch('covibe.services.orchestration.get_primary_ide', return_value=mock_ide_info), \
         patch('covibe.services.orchestration.write_to_ide', return_value=mock_write_result):
        
        options = OrchestrationOptions(
            project_path=str(tmp_path),
            auto_detect_ide=True
        )
        result = await orchestrate_personality_creation(sample_request, options)
        
        assert result.success is True
        assert result.config is not None
        assert result.config.ide_type == "cursor"
        assert len(result.ide_integrations) == 1
        assert result.ide_integrations[0].success is True


@pytest.mark.asyncio
async def test_orchestrate_research_only():
    """Test research-only orchestration."""
    # Mock research result
    mock_profile = MagicMock()
    mock_profile.name = "Test Personality"
    mock_profile.type = PersonalityType.ARCHETYPE
    mock_profile.traits = []
    mock_profile.sources = [MagicMock(confidence=0.8)]
    mock_profile.communication_style = MagicMock()
    mock_profile.communication_style.tone = "friendly"
    mock_profile.communication_style.formality = FormalityLevel.CASUAL
    mock_profile.communication_style.verbosity = VerbosityLevel.MODERATE
    mock_profile.communication_style.technical_level = TechnicalLevel.INTERMEDIATE
    
    research_result = ResearchResult(
        query="test personality",
        profiles=[mock_profile],
        confidence=0.8,
        suggestions=[],
        errors=[]
    )
    
    with patch('covibe.services.orchestration.research_personality', return_value=research_result):
        
        result = await orchestrate_research_only("test personality")
        
        assert result["success"] is True
        assert result["profiles_found"] == 1
        assert result["confidence"] == 0.8
        assert len(result["profiles"]) == 1


@pytest.mark.asyncio
async def test_orchestrate_context_generation():
    """Test context generation orchestration."""
    # Mock research result
    mock_profile = MagicMock()
    mock_profile.name = "Test Personality"
    mock_profile.type = PersonalityType.ARCHETYPE
    mock_profile.sources = [MagicMock()]
    
    research_result = ResearchResult(
        query="test personality",
        profiles=[mock_profile],
        confidence=0.8,
        suggestions=[],
        errors=[]
    )
    
    with patch('covibe.services.orchestration.research_personality', return_value=research_result), \
         patch('covibe.services.orchestration.generate_context_for_ide', return_value="Generated context"):
        
        result = await orchestrate_context_generation("test personality", "cursor")
        
        assert result["success"] is True
        assert result["personality_name"] == "Test Personality"
        assert result["ide_type"] == "cursor"
        assert result["context"] == "Generated context"


@pytest.mark.asyncio
async def test_orchestrate_ide_detection(tmp_path):
    """Test IDE detection orchestration."""
    # Create test IDE markers
    cursor_dir = tmp_path / ".cursor"
    cursor_dir.mkdir()
    
    # Mock IDE detection
    mock_ide_info = MagicMock()
    mock_ide_info.name = "Cursor"
    mock_ide_info.type = "cursor"
    mock_ide_info.confidence = 0.8
    mock_ide_info.config_path = str(cursor_dir / "rules" / "personality.mdc")
    mock_ide_info.markers = [".cursor directory"]
    
    with patch('covibe.services.orchestration.detect_ides', return_value=[mock_ide_info]), \
         patch('covibe.services.orchestration.get_primary_ide', return_value=mock_ide_info):
        
        result = await orchestrate_ide_detection(str(tmp_path))
        
        assert result["success"] is True
        assert result["total_detected"] == 1
        assert result["primary_ide"]["name"] == "Cursor"
        assert result["primary_ide"]["type"] == "cursor"


def test_orchestration_cache():
    """Test orchestration cache functionality."""
    cache = OrchestrationCache(max_size=2, ttl_seconds=1)
    
    # Test set and get
    cache.set("key1", "value1")
    assert cache.get("key1") == "value1"
    
    # Test cache miss
    assert cache.get("nonexistent") is None
    
    # Test max size limit
    cache.set("key2", "value2")
    cache.set("key3", "value3")  # Should evict key1
    
    assert cache.get("key1") is None
    assert cache.get("key2") == "value2"
    assert cache.get("key3") == "value3"


@pytest.mark.asyncio
async def test_orchestration_error_handling(sample_request):
    """Test orchestration error handling."""
    # Mock research to raise an exception
    with patch('covibe.services.orchestration.research_personality', side_effect=Exception("Research failed")):
        
        result = await orchestrate_personality_creation(sample_request)
        
        assert result.success is False
        assert len(result.errors) > 0
        assert "Orchestration failed" in result.errors[0]
        assert len(result.suggestions) > 0


@pytest.mark.asyncio
async def test_orchestrate_context_generation_no_profiles():
    """Test context generation when no profiles found."""
    research_result = ResearchResult(
        query="unknown personality",
        profiles=[],
        confidence=0.0,
        suggestions=["Try different description"],
        errors=[]
    )
    
    with patch('covibe.services.orchestration.research_personality', return_value=research_result):
        
        result = await orchestrate_context_generation("unknown personality")
        
        assert result["success"] is False
        assert "No personality profiles found" in result["error"]
        assert len(result["suggestions"]) > 0