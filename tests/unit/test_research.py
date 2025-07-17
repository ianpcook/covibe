"""Unit tests for personality research functionality."""

import pytest
from unittest.mock import AsyncMock, patch
from covibe.services.research import (
    get_archetype_data,
    extract_traits_from_text,
    calculate_wikipedia_confidence,
    research_personality
)
from covibe.models.core import PersonalityType


def test_get_archetype_data_cowboy():
    """Test getting cowboy archetype data."""
    result, confidence = get_archetype_data("cowboy personality")
    
    assert result is not None
    assert result["name"] == "Cowboy"
    assert "independent" in result["traits"]
    assert confidence > 0.8


def test_get_archetype_data_robot():
    """Test getting robot archetype data."""
    result, confidence = get_archetype_data("like a robot")
    
    assert result is not None
    assert result["name"] == "Robot/AI"
    assert "logical" in result["traits"]
    assert confidence > 0.8


def test_get_archetype_data_no_match():
    """Test getting archetype data with no match."""
    result, confidence = get_archetype_data("completely unknown archetype")
    
    assert result is None
    assert confidence == 0.0


def test_extract_traits_from_text():
    """Test extracting traits from descriptive text."""
    text = "A brilliant and creative genius who shows great leadership."
    
    traits = extract_traits_from_text(text)
    
    assert len(traits) > 0
    trait_names = [t.trait for t in traits]
    assert "intelligent" in trait_names  # Should match "brilliant"
    assert "creative" in trait_names


def test_calculate_wikipedia_confidence_full_data():
    """Test confidence calculation with complete data."""
    data = {
        "title": "Test Person",
        "description": "A description",
        "extract": "A long extract with lots of information about the person and their achievements and contributions to society which spans multiple sentences.",
        "url": "https://example.com"
    }
    
    confidence = calculate_wikipedia_confidence(data)
    assert confidence == 1.0


def test_calculate_wikipedia_confidence_empty_data():
    """Test confidence calculation with empty data."""
    data = {}
    
    confidence = calculate_wikipedia_confidence(data)
    assert confidence == 0.0


@pytest.mark.asyncio
async def test_research_personality_archetype():
    """Test personality research that finds archetype data."""
    result = await research_personality("cowboy personality")
    
    assert result.query == "cowboy personality"
    assert len(result.profiles) > 0
    assert result.profiles[0].type == PersonalityType.ARCHETYPE
    assert result.confidence > 0.8
