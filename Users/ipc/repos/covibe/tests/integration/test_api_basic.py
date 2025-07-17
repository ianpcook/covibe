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


def test_cors_headers(client):
    """Test CORS headers are present."""
    response = client.get("/health")
    assert "access-control-allow-origin" in response.headers


def test_request_id_header(client):
    """Test request ID header is added."""
    response = client.get("/health")
    assert "X-Request-ID" in response.headers
    assert response.headers["X-Request-ID"].startswith("req_")


def test_personality_endpoint_exists(client):
    """Test personality endpoints are accessible."""
    # Test POST endpoint (should return validation error for empty body)
    response = client.post("/api/personality/")
    assert response.status_code in [400, 422]  # Validation error expected
    
    # Test GET endpoint (should return not found)
    response = client.get("/api/personality/test-id")
    assert response.status_code == 404


def test_personality_create_validation(client):
    """Test personality creation with invalid data."""
    # Test with empty description
    invalid_data = {
        "description": "",
        "source": "api"
    }
    
    response = client.post("/api/personality/", json=invalid_data)
    assert response.status_code == 400
    
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"


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