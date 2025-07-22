"""Integration tests for LLM-enhanced API functionality."""

import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from src.covibe.api.main import app
from src.covibe.models.core import ResearchResult, PersonalityProfile, PersonalityType, CommunicationStyle, FormalityLevel, VerbosityLevel, TechnicalLevel, ResearchSource
from src.covibe.models.llm import LLMPersonalityResponse, LLMTrait, LLMCommunicationStyle
from datetime import datetime


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_llm_research_result():
    """Mock LLM research result for testing."""
    profile = PersonalityProfile(
        id="test-123",
        name="Steve Jobs",
        type=PersonalityType.CELEBRITY,
        traits=[],
        communication_style=CommunicationStyle(
            tone="innovative",
            formality=FormalityLevel.MIXED,
            verbosity=VerbosityLevel.MODERATE,
            technical_level=TechnicalLevel.EXPERT
        ),
        mannerisms=["Think different", "Focus on simplicity"],
        sources=[ResearchSource(
            type="llm_openai",
            url=None,
            confidence=0.9,
            last_updated=datetime.now()
        )]
    )
    
    return ResearchResult(
        query="innovative tech leader",
        profiles=[profile],
        confidence=0.9,
        suggestions=[],
        errors=[]
    )


@pytest.mark.asyncio
async def test_research_endpoint_with_llm_enabled(client, mock_llm_research_result):
    """Test research endpoint with LLM enabled."""
    with patch('src.covibe.services.research.research_personality', new_callable=AsyncMock) as mock_research:
        mock_research.return_value = mock_llm_research_result
        
        data = {
            "description": "innovative tech leader",
            "use_cache": True
        }
        
        response = client.post(
            "/api/personality/research?use_llm=true&llm_provider=openai", 
            json=data
        )
        
        assert response.status_code == 200
        result = response.json()
        
        # Check basic response structure
        assert result["query"] == "innovative tech leader"
        assert result["profiles_found"] == 1
        assert result["confidence"] == 0.9
        
        # Check LLM-specific fields
        assert result["llm_used"] is True
        assert result["llm_provider"] == "openai"
        assert "processing_time_ms" in result
        
        # Check profile has LLM enhancement flag
        profile = result["profiles"][0]
        assert profile["name"] == "Steve Jobs"
        assert profile["llm_enhanced"] is True
        
        # Verify research function was called with correct parameters
        mock_research.assert_called_once_with(
            "innovative tech leader",
            use_llm=True,
            llm_provider="openai",
            cache_enabled=True
        )


@pytest.mark.asyncio 
async def test_research_endpoint_with_llm_disabled(client):
    """Test research endpoint with LLM disabled falls back to traditional research."""
    data = {
        "description": "cowboy personality",
        "use_cache": True
    }
    
    response = client.post(
        "/api/personality/research?use_llm=false", 
        json=data
    )
    
    assert response.status_code == 200
    result = response.json()
    
    # Should fall back to archetype research
    assert result["query"] == "cowboy personality"
    assert result["profiles_found"] > 0
    
    # LLM should not be used
    assert result["llm_used"] is False
    assert result["llm_provider"] is None


def test_llm_status_endpoint(client):
    """Test LLM provider status endpoint."""
    response = client.get("/api/personality/llm/status")
    
    assert response.status_code == 200
    result = response.json()
    
    # Check response structure
    assert "providers" in result
    assert "preferred_provider" in result
    assert "llm_research_enabled" in result
    assert "timestamp" in result
    
    # Check provider details
    providers = result["providers"]
    assert "openai" in providers
    assert "anthropic" in providers
    assert "local" in providers
    
    # Each provider should have required fields
    for provider_name, provider_info in providers.items():
        assert "available" in provider_info
        assert "connected" in provider_info
        assert "models" in provider_info
        assert "default_model" in provider_info


@pytest.mark.asyncio
async def test_create_personality_with_llm_logging(client):
    """Test personality creation logs LLM usage."""
    with patch('src.covibe.services.orchestration.orchestrate_personality_request', new_callable=AsyncMock) as mock_orchestrate:
        from src.covibe.services.orchestration import OrchestrationResult
        from src.covibe.models.core import PersonalityConfig
        
        # Mock successful orchestration
        mock_config = PersonalityConfig(
            id="test-config-123",
            profile=PersonalityProfile(
                id="test-profile-123",
                name="Test Personality",
                type=PersonalityType.ARCHETYPE,
                traits=[],
                communication_style=CommunicationStyle(
                    tone="neutral",
                    formality=FormalityLevel.MIXED,
                    verbosity=VerbosityLevel.MODERATE,
                    technical_level=TechnicalLevel.INTERMEDIATE
                ),
                mannerisms=[],
                sources=[]
            ),
            context="Test context",
            ide_type="vscode",
            file_path="/test/path",
            active=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        mock_orchestrate.return_value = OrchestrationResult(
            success=True,
            config=mock_config
        )
        
        with patch('src.covibe.services.persistence.ConfigurationPersistenceService.create_configuration', new_callable=AsyncMock):
            data = {
                "description": "test personality",
                "source": "api"
            }
            
            with patch('logging.Logger.info') as mock_log:
                response = client.post(
                    "/api/personality/?use_llm=true&llm_provider=anthropic",
                    json=data
                )
                
                assert response.status_code == 201
                
                # Check that LLM usage was logged
                mock_log.assert_called()
                log_calls = [call.args[0] for call in mock_log.call_args_list]
                llm_log_found = any("LLM personality creation request" in log for log in log_calls)
                assert llm_log_found


def test_backward_compatibility_research_endpoint(client):
    """Test that research endpoint maintains backward compatibility."""
    # Test without LLM parameters - should work with existing API contract
    data = {
        "description": "robot personality",
        "use_cache": True
    }
    
    response = client.post("/api/personality/research", json=data)
    
    assert response.status_code == 200
    result = response.json()
    
    # All original fields should be present
    required_fields = ["query", "profiles_found", "profiles", "confidence", "suggestions", "errors"]
    for field in required_fields:
        assert field in result
    
    # New optional fields should have default values
    assert "llm_used" in result
    assert "llm_provider" in result
    assert "processing_time_ms" in result


def test_backward_compatibility_create_endpoint(client):
    """Test that create endpoint maintains backward compatibility."""
    # Test without LLM parameters - should work with existing API contract
    with patch('src.covibe.services.orchestration.orchestrate_personality_request', new_callable=AsyncMock) as mock_orchestrate:
        from src.covibe.services.orchestration import OrchestrationResult
        from src.covibe.models.core import PersonalityConfig
        
        mock_config = PersonalityConfig(
            id="test-config-123",
            profile=PersonalityProfile(
                id="test-profile-123",
                name="Robot/AI",
                type=PersonalityType.ARCHETYPE,
                traits=[],
                communication_style=CommunicationStyle(
                    tone="neutral",
                    formality=FormalityLevel.FORMAL,
                    verbosity=VerbosityLevel.CONCISE,
                    technical_level=TechnicalLevel.EXPERT
                ),
                mannerisms=[],
                sources=[]
            ),
            context="Test context",
            ide_type="vscode",
            file_path="/test/path",
            active=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        mock_orchestrate.return_value = OrchestrationResult(
            success=True,
            config=mock_config
        )
        
        with patch('src.covibe.services.persistence.ConfigurationPersistenceService.create_configuration', new_callable=AsyncMock):
            data = {
                "description": "robot personality",
                "source": "api"
            }
            
            response = client.post("/api/personality/", json=data)
            
            assert response.status_code == 201
            result = response.json()
            
            # All original response fields should be present
            required_fields = ["id", "profile", "context", "ide_type", "file_path", "active", "created_at", "updated_at"]
            for field in required_fields:
                assert field in result


@pytest.mark.asyncio
async def test_research_error_handling_with_llm(client):
    """Test error handling when LLM research fails."""
    with patch('src.covibe.services.research.research_personality', new_callable=AsyncMock) as mock_research:
        # Mock LLM failure with fallback result
        fallback_result = ResearchResult(
            query="unknown personality",
            profiles=[],
            confidence=0.0,
            suggestions=["Try using specific character names", "Try archetype descriptions"],
            errors=["LLM research failed: Connection timeout"]
        )
        mock_research.return_value = fallback_result
        
        data = {
            "description": "unknown personality",
            "use_cache": True
        }
        
        response = client.post(
            "/api/personality/research?use_llm=true&llm_provider=openai",
            json=data
        )
        
        assert response.status_code == 200
        result = response.json()
        
        # Should return fallback result with error information
        assert result["profiles_found"] == 0
        assert result["confidence"] == 0.0
        assert len(result["errors"]) > 0
        assert len(result["suggestions"]) > 0
        assert result["llm_used"] is False  # LLM failed, so not actually used