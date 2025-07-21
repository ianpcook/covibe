"""Global test configuration and fixtures."""

import asyncio
import os
import tempfile
import shutil
from pathlib import Path
from typing import Generator

import pytest
from fastapi.testclient import TestClient

from src.covibe.api.main import app


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def client():
    """Create a test client for the FastAPI application."""
    return TestClient(app)


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for testing."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def sample_personality_data():
    """Sample personality data for testing."""
    return {
        "description": "Tony Stark - genius inventor and billionaire",
        "user_id": "test_user_123",
        "source": "api"
    }


@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up test environment variables."""
    # Set test-specific environment variables
    os.environ["TESTING"] = "true"
    os.environ["DATABASE_URL"] = "sqlite:///test.db"
    
    yield
    
    # Cleanup
    if "TESTING" in os.environ:
        del os.environ["TESTING"]
    if "DATABASE_URL" in os.environ:
        del os.environ["DATABASE_URL"]


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "benchmark: mark test as a benchmark test"
    )
    config.addinivalue_line(
        "markers", "e2e: mark test as an end-to-end test"
    )
    config.addinivalue_line(
        "markers", "security: mark test as a security test"
    )
    config.addinivalue_line(
        "markers", "performance: mark test as a performance test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on file location."""
    for item in items:
        # Add markers based on test file location
        if "e2e" in str(item.fspath):
            item.add_marker(pytest.mark.e2e)
        elif "performance" in str(item.fspath):
            item.add_marker(pytest.mark.performance)
        elif "security" in str(item.fspath):
            item.add_marker(pytest.mark.security)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)