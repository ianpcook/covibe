"""Unit tests for IDE writer functionality."""

import pytest
from pathlib import Path
from datetime import datetime
from covibe.integrations.ide_writers import (
    write_cursor_config,
    write_claude_config,
    write_to_ide
)
from covibe.models.core import (
    PersonalityConfig,
    PersonalityProfile,
    PersonalityType,
    CommunicationStyle,
    FormalityLevel,
    VerbosityLevel,
    TechnicalLevel,
    ResearchSource
)


@pytest.fixture
def sample_config():
    """Create a sample personality configuration for testing."""
    source = ResearchSource(
        type="test",
        url=None,
        confidence=0.9,
        last_updated=datetime.now()
    )
    
    comm_style = CommunicationStyle(
        tone="friendly",
        formality=FormalityLevel.CASUAL,
        verbosity=VerbosityLevel.MODERATE,
        technical_level=TechnicalLevel.INTERMEDIATE
    )
    
    profile = PersonalityProfile(
        id="test_profile",
        name="Test Cowboy",
        type=PersonalityType.ARCHETYPE,
        traits=[],
        communication_style=comm_style,
        mannerisms=["uses simple language"],
        sources=[source]
    )
    
    return PersonalityConfig(
        id="test_config",
        profile=profile,
        context="Test context",
        ide_type="test",
        file_path="",
        active=True,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )


@pytest.mark.asyncio
async def test_write_cursor_config(tmp_path, sample_config):
    """Test writing Cursor configuration."""
    result = await write_cursor_config(sample_config, tmp_path)
    
    assert result.success is True
    assert "personality.mdc" in result.file_path
    assert "Successfully wrote" in result.message
    
    # Check that file was created
    config_file = tmp_path / ".cursor" / "rules" / "personality.mdc"
    assert config_file.exists()


@pytest.mark.asyncio
async def test_write_claude_config(tmp_path, sample_config):
    """Test writing Claude configuration."""
    result = await write_claude_config(sample_config, tmp_path)
    
    assert result.success is True
    assert "CLAUDE.md" in result.file_path
    
    # Check that file was created
    config_file = tmp_path / "CLAUDE.md"
    assert config_file.exists()


@pytest.mark.asyncio
async def test_write_to_ide_unsupported(tmp_path, sample_config):
    """Test writing to unsupported IDE type."""
    result = await write_to_ide("unsupported", sample_config, tmp_path)
    
    assert result.success is False
    assert "Unsupported IDE type" in result.message
