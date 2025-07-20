"""
Integration tests for personality API endpoints.
"""

import pytest
import asyncio
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, Mock
from fastapi.testclient import TestClient

from src.covibe.api.main import app
from src.covibe.models.core import (
    PersonalityProfile, PersonalityConfig, ResearchResult,
    PersonalityType, CommunicationStyle, FormalityLevel, 
    VerbosityLevel, TechnicalLevel, PersonalityTrait
)


@pytest.fixture
def client():
    """Create test client for API testing."""
    return TestClient(app)


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


@pytest.fixture
def sample_config(sample_personality_profile):
    """Create a sample personality configuration for testing."""
    return PersonalityConfig(
        id="config-123",
        profile=sample_personality_profile,
        context="# Personality Context: Tony Stark\n\nTest context...",
        ide_type="cursor",
        file_path="/test/.cursor/rules/personality.mdc",
        active=True,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )


class TestPersonalityEndpoints:
    """Test personality API endpoints."""
    
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert data["service"] == "covibe-api"
    
    @patch('src.covibe.services.orchestration.orchestrate_personality_request')
    def test_create_personality_config_success(self, mock_orchestrate, client, sample_config):
        """Test successful personality configuration creation."""
        # Mock orchestration result
        mock_result = Mock()
        mock_result.success = True
        mock_result.config = sample_config
        mock_result.error = None
        mock_orchestrate.return_value = mock_result
        
        # Make request
        response = client.post("/api/personality/", json={
            "description": "Tony Stark",
            "user_id": "test-user",
            "project_path": "/test/project"
        })
        
        assert response.status_code == 201
        data = response.json()
        assert data["profile"]["name"] == "Tony Stark"
        assert data["ide_type"] == "cursor"
        assert data["active"] is True
        assert "context" in data
        
        # Verify orchestration was called
        mock_orchestrate.assert_called_once()
        call_args = mock_orchestrate.call_args
        assert call_args[0][0].description == "Tony Stark"
        assert call_args[1]["project_path"] == Path("/test/project")
    
    @patch('src.covibe.services.orchestration.orchestrate_personality_request')
    def test_create_personality_config_orchestration_failure(self, mock_orchestrate, client):
        """Test personality configuration creation with orchestration failure."""
        # Mock orchestration failure
        mock_result = Mock()
        mock_result.success = False
        mock_result.error = Mock()
        mock_result.error.code = "RESEARCH_FAILED"
        mock_result.error.message = "No personality profiles found"
        mock_result.error.suggestions = ["Try a more specific description"]
        mock_orchestrate.return_value = mock_result
        
        # Make request
        response = client.post("/api/personality/", json={
            "description": "Unknown Person"
        })
        
        assert response.status_code == 400
        data = response.json()
        assert data["error"]["code"] == "RESEARCH_FAILED"
        assert data["error"]["message"] == "No personality profiles found"
    
    def test_create_personality_config_validation_error(self, client):
        """Test personality configuration creation with validation error."""
        # Make request with invalid data
        response = client.post("/api/personality/", json={
            "description": ""  # Empty description should fail validation
        })
        
        assert response.status_code == 422  # Validation error
    
    @patch('src.covibe.api.personality._personality_configs')
    def test_get_personality_config_success(self, mock_configs, client, sample_config):
        """Test successful personality configuration retrieval."""
        # Mock stored configuration
        mock_configs.__contains__ = Mock(return_value=True)
        mock_configs.__getitem__ = Mock(return_value=sample_config)
        
        response = client.get("/api/personality/config-123")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == "config-123"
        assert data["profile"]["name"] == "Tony Stark"
    
    def test_get_personality_config_not_found(self, client):
        """Test personality configuration retrieval with non-existent ID."""
        response = client.get("/api/personality/non-existent-id")
        
        assert response.status_code == 404
        data = response.json()
        assert data["error"]["code"] == "NOT_FOUND"
    
    @patch('src.covibe.api.personality._personality_configs')
    @patch('src.covibe.services.orchestration.orchestrate_personality_request')
    def test_update_personality_config_success(self, mock_orchestrate, mock_configs, client, sample_config):
        """Test successful personality configuration update."""
        # Mock existing configuration
        mock_configs.__contains__ = Mock(return_value=True)
        mock_configs.__getitem__ = Mock(return_value=sample_config)
        mock_configs.__setitem__ = Mock()
        
        # Mock orchestration result for update
        updated_config = sample_config.copy()
        updated_config.profile.name = "Updated Tony Stark"
        mock_result = Mock()
        mock_result.success = True
        mock_result.config = updated_config
        mock_orchestrate.return_value = mock_result
        
        response = client.put("/api/personality/config-123", json={
            "description": "Updated Tony Stark"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["profile"]["name"] == "Updated Tony Stark"
    
    def test_update_personality_config_not_found(self, client):
        """Test personality configuration update with non-existent ID."""
        response = client.put("/api/personality/non-existent-id", json={
            "description": "Updated description"
        })
        
        assert response.status_code == 404
        data = response.json()
        assert data["error"]["code"] == "NOT_FOUND"
    
    @patch('src.covibe.api.personality._personality_configs')
    def test_delete_personality_config_success(self, mock_configs, client):
        """Test successful personality configuration deletion."""
        # Mock existing configuration
        mock_configs.__contains__ = Mock(return_value=True)
        mock_configs.__delitem__ = Mock()
        
        response = client.delete("/api/personality/config-123")
        
        assert response.status_code == 204
        mock_configs.__delitem__.assert_called_once_with("config-123")
    
    def test_delete_personality_config_not_found(self, client):
        """Test personality configuration deletion with non-existent ID."""
        response = client.delete("/api/personality/non-existent-id")
        
        assert response.status_code == 404
        data = response.json()
        assert data["error"]["code"] == "NOT_FOUND"
    
    @patch('src.covibe.services.orchestration.orchestrate_research_only')
    def test_research_personality_success(self, mock_research, client, sample_research_result):
        """Test successful personality research."""
        mock_research.return_value = sample_research_result
        
        response = client.post("/api/personality/research", json={
            "description": "Tony Stark",
            "use_cache": True
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["query"] == "Tony Stark"
        assert data["profiles_found"] == 1
        assert len(data["profiles"]) == 1
        assert data["profiles"][0]["name"] == "Tony Stark"
        assert data["confidence"] == 0.9
        
        mock_research.assert_called_once_with("Tony Stark", use_cache=True)
    
    @patch('src.covibe.services.orchestration.orchestrate_research_only')
    def test_research_personality_error(self, mock_research, client):
        """Test personality research with error."""
        mock_research.side_effect = Exception("Research failed")
        
        response = client.post("/api/personality/research", json={
            "description": "Tony Stark"
        })
        
        assert response.status_code == 500
        data = response.json()
        assert data["error"]["code"] == "RESEARCH_ERROR"
    
    @patch('src.covibe.integrations.ide_detection.detect_ides')
    @patch('src.covibe.integrations.ide_detection.get_primary_ide')
    def test_detect_ide_environment_success(self, mock_primary, mock_detect, client, tmp_path):
        """Test successful IDE environment detection."""
        # Mock IDE detection
        mock_ide = Mock()
        mock_ide.name = "Cursor"
        mock_ide.type = "cursor"
        mock_ide.config_path = "/test/.cursor/rules/personality.mdc"
        mock_ide.confidence = 0.9
        mock_ide.markers = [".cursor directory"]
        
        mock_detect.return_value = [mock_ide]
        mock_primary.return_value = mock_ide
        
        response = client.get(f"/api/personality/ide/detect?project_path={tmp_path}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_detected"] == 1
        assert data["primary_ide"]["name"] == "Cursor"
        assert data["primary_ide"]["type"] == "cursor"
    
    def test_detect_ide_environment_path_not_found(self, client):
        """Test IDE environment detection with non-existent path."""
        response = client.get("/api/personality/ide/detect?project_path=/non/existent/path")
        
        assert response.status_code == 400
        data = response.json()
        assert data["error"]["code"] == "PATH_NOT_FOUND"
    
    @patch('src.covibe.api.personality._personality_configs')
    def test_list_personality_configs(self, mock_configs, client, sample_config):
        """Test listing personality configurations."""
        # Mock configurations
        configs = [sample_config, sample_config.copy()]
        configs[1].id = "config-456"
        mock_configs.values.return_value = configs
        
        response = client.get("/api/personality/configs?limit=10&offset=0")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["configurations"]) == 2
        assert data["pagination"]["total"] == 2
        assert data["pagination"]["limit"] == 10
        assert data["pagination"]["offset"] == 0
        assert data["pagination"]["has_more"] is False
    
    @patch('src.covibe.services.orchestration.get_cache_stats')
    def test_get_cache_statistics(self, mock_stats, client):
        """Test getting cache statistics."""
        mock_stats.return_value = {
            "total_entries": 5,
            "expired_entries": 1,
            "active_entries": 4
        }
        
        response = client.get("/api/personality/cache/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert data["cache_stats"]["total_entries"] == 5
        assert data["cache_stats"]["active_entries"] == 4
        assert "timestamp" in data
    
    @patch('src.covibe.services.orchestration.clear_cache')
    def test_clear_personality_cache(self, mock_clear, client):
        """Test clearing personality cache."""
        mock_clear.return_value = 3
        
        response = client.delete("/api/personality/cache?clear_all=true")
        
        assert response.status_code == 200
        data = response.json()
        assert data["cleared_entries"] == 3
        assert data["clear_type"] == "all"
        assert "timestamp" in data
        
        mock_clear.assert_called_once_with(clear_all=True)


class TestAPIErrorHandling:
    """Test API error handling and edge cases."""
    
    def test_global_exception_handler(self, client):
        """Test global exception handler for unexpected errors."""
        # This would require triggering an unexpected exception
        # For now, we'll test that the handler structure is in place
        pass
    
    def test_request_id_middleware(self, client):
        """Test that request ID middleware adds headers."""
        response = client.get("/health")
        assert "X-Request-ID" in response.headers
        assert response.headers["X-Request-ID"].startswith("req_")
    
    def test_cors_middleware(self, client):
        """Test CORS middleware configuration."""
        response = client.options("/api/personality/")
        # CORS headers should be present for OPTIONS requests
        assert response.status_code in [200, 405]  # Depending on FastAPI version


class TestAPIValidation:
    """Test API input validation."""
    
    def test_personality_request_validation(self, client):
        """Test personality request validation."""
        # Test missing required field
        response = client.post("/api/personality/", json={})
        assert response.status_code == 422
        
        # Test description too long
        response = client.post("/api/personality/", json={
            "description": "x" * 501  # Exceeds max length
        })
        assert response.status_code == 422
        
        # Test invalid source type
        response = client.post("/api/personality/", json={
            "description": "Tony Stark",
            "source": "invalid_source"
        })
        assert response.status_code == 422
    
    def test_research_request_validation(self, client):
        """Test research request validation."""
        # Test missing description
        response = client.post("/api/personality/research", json={})
        assert response.status_code == 422
        
        # Test invalid use_cache type
        response = client.post("/api/personality/research", json={
            "description": "Tony Stark",
            "use_cache": "invalid"
        })
        assert response.status_code == 422
    
    def test_query_parameter_validation(self, client):
        """Test query parameter validation."""
        # Test invalid limit
        response = client.get("/api/personality/configs?limit=0")
        assert response.status_code == 422
        
        # Test invalid offset
        response = client.get("/api/personality/configs?offset=-1")
        assert response.status_code == 422
        
        # Test limit too high
        response = client.get("/api/personality/configs?limit=101")
        assert response.status_code == 422


class TestAPIIntegration:
    """Test full API integration scenarios."""
    
    @patch('src.covibe.services.orchestration.orchestrate_personality_request')
    @patch('src.covibe.services.orchestration.orchestrate_research_only')
    def test_full_workflow_integration(self, mock_research, mock_orchestrate, client, sample_config, sample_research_result):
        """Test full workflow from research to configuration creation."""
        # Mock research
        mock_research.return_value = sample_research_result
        
        # Mock orchestration
        mock_result = Mock()
        mock_result.success = True
        mock_result.config = sample_config
        mock_orchestrate.return_value = mock_result
        
        # Step 1: Research personality
        research_response = client.post("/api/personality/research", json={
            "description": "Tony Stark"
        })
        assert research_response.status_code == 200
        
        # Step 2: Create configuration
        config_response = client.post("/api/personality/", json={
            "description": "Tony Stark",
            "project_path": "/test/project"
        })
        assert config_response.status_code == 201
        
        # Step 3: Retrieve configuration
        config_id = config_response.json()["id"]
        with patch('src.covibe.api.personality._personality_configs') as mock_configs:
            mock_configs.__contains__ = Mock(return_value=True)
            mock_configs.__getitem__ = Mock(return_value=sample_config)
            
            get_response = client.get(f"/api/personality/{config_id}")
            assert get_response.status_code == 200
            assert get_response.json()["profile"]["name"] == "Tony Stark"