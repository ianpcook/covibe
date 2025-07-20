"""Unit tests for context generation functionality."""

import pytest
from covibe.services.context_generation import (
    generate_personality_context,
    generate_communication_style_context,
    generate_trait_context,
    get_intensity_modifier,
    generate_context_for_ide
)
from covibe.models.core import (
    PersonalityProfile,
    PersonalityTrait,
    CommunicationStyle,
    PersonalityType,
    FormalityLevel,
    VerbosityLevel,
    TechnicalLevel,
    ResearchSource
)
from datetime import datetime


@pytest.fixture
def sample_profile():
    """Create a sample personality profile for testing."""
    traits = [
        PersonalityTrait(
            category="personality",
            trait="intelligent",
            intensity=8,
            examples=["Shows analytical thinking"]
        )
    ]
    
    comm_style = CommunicationStyle(
        tone="friendly",
        formality=FormalityLevel.CASUAL,
        verbosity=VerbosityLevel.MODERATE,
        technical_level=TechnicalLevel.INTERMEDIATE
    )
    
    source = ResearchSource(
        type="test",
        url=None,
        confidence=0.9,
        last_updated=datetime.now()
    )
    
    return PersonalityProfile(
        id="test_profile",
        name="Test Personality",
        type=PersonalityType.ARCHETYPE,
        traits=traits,
        communication_style=comm_style,
        mannerisms=["uses clear examples"],
        sources=[source]
    )


def test_generate_personality_context(sample_profile):
    """Test complete personality context generation."""
    context = generate_personality_context(sample_profile)
    
    assert "Test Personality" in context
    assert "Communication Style" in context
    assert "Personality Traits" in context


def test_generate_communication_style_context(sample_profile):
    """Test communication style context generation."""
    context = generate_communication_style_context(sample_profile.communication_style)
    
    assert "Communication Style" in context
    assert "friendly" in context
    assert "Casual" in context


def test_generate_trait_context(sample_profile):
    """Test trait context generation."""
    context = generate_trait_context(sample_profile.traits)
    
    assert "Personality Traits" in context
    assert "Intelligent" in context


def test_get_intensity_modifier():
    """Test trait intensity modifier generation."""
    assert get_intensity_modifier(10) == "Very Strong"
    assert get_intensity_modifier(8) == "Strong"
    assert get_intensity_modifier(6) == "Moderate"
    assert get_intensity_modifier(4) == "Mild"
    assert get_intensity_modifier(2) == "Subtle"


def test_generate_context_for_cursor(sample_profile):
    """Test Cursor IDE context formatting."""
    context = generate_context_for_ide(sample_profile, "cursor")
    
    assert "---" in context  # YAML frontmatter
    assert "Test Personality" in context


def test_generate_context_for_claude(sample_profile):
    """Test Claude IDE context formatting."""
    context = generate_context_for_ide(sample_profile, "claude")
    
    assert "# Claude Personality Configuration" in context
    assert "Test Personality" in context
