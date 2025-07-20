"""Integration tests for context generation API functionality."""

import pytest
from fastapi.testclient import TestClient
from covibe.api.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


def test_context_generation_endpoint_cowboy(client):
    """Test context generation endpoint with cowboy archetype."""
    data = {
        "description": "cowboy personality",
        "source": "api"
    }
    
    response = client.post("/api/personality/context", json=data)
    assert response.status_code == 200
    
    result = response.json()
    assert result["personality_name"] == "Cowboy"
    assert result["personality_type"] == "archetype"
    assert result["ide_type"] == "generic"
    assert "context" in result
    assert "Personality Context: Cowboy" in result["context"]
    assert result["confidence"] > 0.8


def test_context_generation_cursor_format(client):
    """Test context generation with Cursor IDE formatting."""
    data = {
        "description": "robot personality",
        "source": "api"
    }
    
    response = client.post("/api/personality/context?ide_type=cursor", json=data)
    assert response.status_code == 200
    
    result = response.json()
    assert result["personality_name"] == "Robot/AI"
    assert result["ide_type"] == "cursor"
    assert "---" in result["context"]  # YAML frontmatter
    assert "title:" in result["context"]


def test_context_generation_claude_format(client):
    """Test context generation with Claude IDE formatting."""
    data = {
        "description": "mentor personality",
        "source": "api"
    }
    
    response = client.post("/api/personality/context?ide_type=claude", json=data)
    assert response.status_code == 200
    
    result = response.json()
    assert result["personality_name"] == "Wise Mentor"
    assert result["ide_type"] == "claude"
    assert "# Claude Personality Configuration" in result["context"]


def test_personality_create_with_context(client):
    """Test personality creation now includes generated context."""
    data = {
        "description": "drill sergeant personality",
        "source": "api"
    }
    
    response = client.post("/api/personality/", json=data)
    assert response.status_code == 201
    
    result = response.json()
    assert "context" in result
    assert "Drill Sergeant" in result["context"]
    assert "Communication Style" in result["context"]
    assert "Personality Traits" in result["context"]
    assert len(result["context"]) > 100  # Should be substantial context


def test_context_generation_unknown_personality(client):
    """Test context generation with unknown personality."""
    data = {
        "description": "completely unknown personality type",
        "source": "api"
    }
    
    response = client.post("/api/personality/context", json=data)
    assert response.status_code == 200
    
    result = response.json()
    assert "error" in result
    assert "suggestions" in result
