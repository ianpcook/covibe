"""Integration tests for advanced input processing API endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from src.covibe.api.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestAdvancedInputAPI:
    """Test advanced input processing API endpoints."""
    
    def test_analyze_personality_input_specific_name(self, client):
        """Test analyzing specific personality names."""
        response = client.post(
            "/api/personality/analyze",
            json={"description": "tony stark"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["input_type"] == "specific_name"
        assert data["confidence"] > 0.9
        assert data["primary_personality"] == "tony stark"
    
    def test_analyze_personality_input_combination(self, client):
        """Test analyzing combination personality requests."""
        response = client.post(
            "/api/personality/analyze",
            json={"description": "tony stark but more patient"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["input_type"] == "combination"
        assert data["confidence"] == 0.9
        assert data["primary_personality"] == "tony stark"
        assert data["modifiers"] == ["patient"]
        assert data["combination_type"] == "but_more"
    
    def test_analyze_personality_input_ambiguous(self, client):
        """Test analyzing ambiguous personality input."""
        response = client.post(
            "/api/personality/analyze",
            json={"description": "tony start"}  # typo
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["input_type"] == "ambiguous"
        assert data["confidence"] > 0.6
        assert data["suggestions"] is not None
        assert len(data["suggestions"]) > 0
    
    def test_analyze_personality_input_unclear(self, client):
        """Test analyzing unclear personality input."""
        response = client.post(
            "/api/personality/analyze",
            json={"description": "something unclear"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["input_type"] == "unclear"
        assert data["clarification_questions"] is not None
        assert len(data["clarification_questions"]) > 0
    
    def test_generate_personality_suggestions(self, client):
        """Test generating personality suggestions."""
        response = client.post(
            "/api/personality/suggestions",
            json={"description": "tony start"},
            params={"max_suggestions": 3}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert len(data) <= 3
        assert all("name" in item and "confidence" in item for item in data)
        assert any("tony stark" in item["name"].lower() for item in data)
    
    def test_generate_clarification_questions(self, client):
        """Test generating clarification questions."""
        response = client.post(
            "/api/personality/clarify",
            json={"description": "unclear input"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        assert all("question" in item and "options" in item for item in data)
    
    @patch('src.covibe.services.orchestration.orchestrate_personality_request_enhanced')
    def test_enhanced_personality_creation_success(self, mock_orchestrate, client):
        """Test successful enhanced personality creation."""
        # Mock successful orchestration
        from src.covibe.services.orchestration import OrchestrationResult
        from src.covibe.models.core import PersonalityConfig, PersonalityProfile, PersonalityType
        from datetime import datetime
        
        mock_config = PersonalityConfig(
            id="test_id",
            profile=PersonalityProfile(
                id="profile_id",
                name="Tony Stark",
                type=PersonalityType.FICTIONAL,
                traits=[],
                communication_style=None,
                mannerisms=[],
                sources=[]
            ),
            context="test context",
            ide_type="cursor",
            file_path="/test/path",
            active=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        mock_orchestrate.return_value = OrchestrationResult(
            success=True,
            config=mock_config
        )
        
        # Mock persistence service
        with patch('src.covibe.api.personality.get_persistence_service') as mock_persistence:
            mock_service = AsyncMock()
            mock_persistence.return_value = mock_service
            
            response = client.post(
                "/api/personality/enhanced",
                json={
                    "description": "tony stark but more patient",
                    "source": "api"
                }
            )
            
            assert response.status_code == 201
            data = response.json()
            assert data["id"] == "test_id"
            assert data["profile"]["name"] == "Tony Stark"
    
    @patch('src.covibe.services.orchestration.orchestrate_personality_request_enhanced')
    def test_enhanced_personality_creation_ambiguous(self, mock_orchestrate, client):
        """Test enhanced personality creation with ambiguous input."""
        from src.covibe.services.orchestration import OrchestrationResult
        from src.covibe.models.core import ErrorDetail
        
        mock_orchestrate.return_value = OrchestrationResult(
            success=False,
            error=ErrorDetail(
                code="AMBIGUOUS_INPUT",
                message="Multiple personalities match 'tony start'",
                suggestions=["tony stark", "Did you mean 'tony stark'?"]
            )
        )
        
        response = client.post(
            "/api/personality/enhanced",
            json={
                "description": "tony start",  # typo
                "source": "api"
            }
        )
        
        assert response.status_code == 422  # Unprocessable Entity
        data = response.json()
        assert data["error"]["code"] == "AMBIGUOUS_INPUT"
        assert "suggestions" in data["error"]
    
    @patch('src.covibe.services.orchestration.orchestrate_personality_request_enhanced')
    def test_enhanced_personality_creation_unclear(self, mock_orchestrate, client):
        """Test enhanced personality creation with unclear input."""
        from src.covibe.services.orchestration import OrchestrationResult
        from src.covibe.models.core import ErrorDetail
        
        mock_orchestrate.return_value = OrchestrationResult(
            success=False,
            error=ErrorDetail(
                code="UNCLEAR_INPUT",
                message="I need more information about 'unclear input'",
                suggestions=["Could you be more specific?", "Try a character name"]
            )
        )
        
        response = client.post(
            "/api/personality/enhanced",
            json={
                "description": "unclear input",
                "source": "api"
            }
        )
        
        assert response.status_code == 422  # Unprocessable Entity
        data = response.json()
        assert data["error"]["code"] == "UNCLEAR_INPUT"
        assert "suggestions" in data["error"]
    
    def test_analyze_empty_input(self, client):
        """Test analyzing empty input."""
        response = client.post(
            "/api/personality/analyze",
            json={"description": ""}
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_analyze_too_long_input(self, client):
        """Test analyzing input that's too long."""
        long_description = "a" * 1000
        response = client.post(
            "/api/personality/analyze",
            json={"description": long_description}
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_suggestions_with_max_limit(self, client):
        """Test suggestions with maximum limit."""
        response = client.post(
            "/api/personality/suggestions",
            json={"description": "genius"},
            params={"max_suggestions": 10}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 10
    
    def test_suggestions_with_invalid_max(self, client):
        """Test suggestions with invalid max parameter."""
        response = client.post(
            "/api/personality/suggestions",
            json={"description": "genius"},
            params={"max_suggestions": 15}  # Above limit
        )
        
        assert response.status_code == 422  # Validation error


class TestInputProcessingScenarios:
    """Test various input processing scenarios."""
    
    def test_celebrity_names(self, client):
        """Test processing celebrity names."""
        test_cases = [
            "einstein",
            "Albert Einstein",
            "EINSTEIN"
        ]
        
        for description in test_cases:
            response = client.post(
                "/api/personality/analyze",
                json={"description": description}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["input_type"] in ["specific_name", "ambiguous"]
    
    def test_fictional_characters(self, client):
        """Test processing fictional character names."""
        test_cases = [
            "sherlock holmes",
            "yoda",
            "batman",
            "spiderman"
        ]
        
        for description in test_cases:
            response = client.post(
                "/api/personality/analyze",
                json={"description": description}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["input_type"] in ["specific_name", "ambiguous"]
    
    def test_archetype_descriptions(self, client):
        """Test processing archetype descriptions."""
        test_cases = [
            "mentor",
            "genius",
            "robot",
            "drill sergeant",
            "wise monk"
        ]
        
        for description in test_cases:
            response = client.post(
                "/api/personality/analyze",
                json={"description": description}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["input_type"] in ["specific_name", "descriptive_phrase", "ambiguous"]
    
    def test_combination_patterns(self, client):
        """Test various combination patterns."""
        test_cases = [
            "tony stark but more patient",
            "sherlock but less arrogant",
            "yoda mixed with einstein",
            "like batman but friendlier"
        ]
        
        for description in test_cases:
            response = client.post(
                "/api/personality/analyze",
                json={"description": description}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["input_type"] == "combination"
            assert data["combination_type"] is not None
            assert data["primary_personality"] is not None
            assert data["modifiers"] is not None
    
    def test_descriptive_phrases(self, client):
        """Test processing descriptive phrases."""
        test_cases = [
            "friendly mentor",
            "patient teacher",
            "sarcastic genius",
            "calm leader"
        ]
        
        for description in test_cases:
            response = client.post(
                "/api/personality/analyze",
                json={"description": description}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["input_type"] in ["descriptive_phrase", "ambiguous", "unclear"]