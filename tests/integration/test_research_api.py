"""Integration tests for research API functionality."""

import pytest
from fastapi.testclient import TestClient
from covibe.api.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


def test_research_endpoint_cowboy(client):
    """Test research endpoint with cowboy archetype."""
    data = {
        "description": "cowboy personality",
        "source": "api"
    }
    
    response = client.post("/api/personality/research", json=data)
    assert response.status_code == 200
    
    result = response.json()
    assert result["query"] == "cowboy personality"
    assert result["profiles_found"] > 0
    assert result["confidence"] > 0.8


def test_create_personality_with_research(client):
    """Test creating personality configuration with research."""
    data = {
        "description": "robot personality",
        "source": "api"
    }
    
    response = client.post("/api/personality/", json=data)
    assert response.status_code == 201
    
    result = response.json()
    assert "id" in result
    assert "profile" in result
    assert result["profile"]["name"] == "Robot/AI"
    assert result["active"] is True
