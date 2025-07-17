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
    assert len(result["profiles"]) > 0
    
    profile = result["profiles"][0]
    assert profile["name"] == "Cowboy"
    assert profile["type"] == "archetype"
    assert "independent" in profile["traits"]


def test_research_endpoint_unknown(client):
    """Test research endpoint with unknown personality."""
    data = {
        "description": "completely unknown personality type",
        "source": "api"
    }
    
    response = client.post("/api/personality/research", json=data)
    assert response.status_code == 200
    
    result = response.json()
    assert result["query"] == "completely unknown personality type"
    assert result["profiles_found"] == 0
    assert result["confidence"] == 0.0
    assert len(result["suggestions"]) > 0


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
    assert result["profile"]["type"] == "archetype"
    assert result["active"] is True