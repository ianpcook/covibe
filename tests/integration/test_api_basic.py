"""Integration tests for basic API functionality."""

import pytest
from fastapi.testclient import TestClient
from covibe.api.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "covibe-api"
    assert "timestamp" in data


def test_personality_create_valid_data(client):
    """Test personality creation with valid data."""
    valid_data = {
        "description": "Like Tony Stark but more patient",
        "source": "api"
    }
    
    response = client.post("/api/personality/", json=valid_data)
    assert response.status_code == 201
    
    data = response.json()
    assert "id" in data
    assert "profile" in data
    assert data["active"] is True
