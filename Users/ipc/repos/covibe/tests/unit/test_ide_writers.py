"""Unit tests for IDE writer functionality."""

import pytest
from pathlib import Path
from datetime import datetime
from covibe.integrations.ide_writers import (
    write_cursor_config,
    write_claude_config,
    write_windsurf_config,
    write_to_ide,
    write_to_multiple_ides
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
    
    # Check content
    content = config_file.read_text()
    assert "Test Cowboy" in content
    assert "---" in content  # YAML frontmatter


@pytest.mark.asyncio
async def test_write_cursor_config_with_backup(tmp_path, sample_config):
    """Test writing Cursor configuration with existing file (backup)."""
    # Create existing file
    cursor_dir = tmp_path / ".cursor" / "rules"
    cursor_dir.mkdir(parents=True)
    existing_file = cursor_dir / "personality.mdc"
    existing_file.write_text("existing content")
    
    result = await write_cursor_config(sample_config, tmp_path)
    
    assert result.success is True
    assert result.backup_path is not None
    assert Path(result.backup_path).exists()


@pytest.mark.asyncio
async def test_write_claude_config(tmp_path, sample_config):
    """Test writing Claude configuration."""
    result = await write_claude_config(sample_config, tmp_path)
    
    assert result.success is True
    assert "CLAUDE.md" in result.file_path
    assert "Successfully wrote" in result.message
    
    # Check that file was created
    config_file = tmp_path / "CLAUDE.md"
    assert config_file.exists()
    
    # Check content
    content = config_file.read_text()
    assert "Test Cowboy" in content
    assert "Claude Personality Configuration" in content


@pytest.mark.asyncio
async def test_write_windsurf_config(tmp_path, sample_config):
    """Test writing Windsurf configuration."""
    result = await write_windsurf_config(sample_config, tmp_path)
    
    assert result.success is True
    assert ".windsurf" in result.file_path
    assert "Successfully wrote" in result.message
    
    # Check that file was created
    config_file = tmp_path / ".windsurf"
    assert config_file.exists()
    
    # Check content
    content = config_file.read_text()
    assert "Test Cowboy" in content
    assert "Windsurf AI Personality" in content


@pytest.mark.asyncio
async def test_write_to_ide_cursor(tmp_path, sample_config):
    """Test writing to IDE with cursor type."""
    result = await write_to_ide("cursor", sample_config, tmp_path)
    
    assert result.success is True
    assert "personality.mdc" in result.file_path


@pytest.mark.asyncio
async def test_write_to_ide_unsupported(tmp_path, sample_config):
    """Test writing to unsupported IDE type."""
    result = await write_to_ide("unsupported", sample_config, tmp_path)
    
    assert result.success is False
    assert "Unsupported IDE type" in result.message


@pytest.mark.asyncio
async def test_write_to_multiple_ides(tmp_path, sample_config):
    """Test writing to multiple IDEs."""
    ide_types = ["cursor", "claude", "windsurf"]
    results = await write_to_multiple_ides(ide_types, sample_config, tmp_path)
    
    assert len(results) == 3
    assert all(result.success for result in results)
    
    # Check that all files were created
    assert (tmp_path / ".cursor" / "rules" / "personality.mdc").exists()
    assert (tmp_path / "CLAUDE.md").exists()
    assert (tmp_path / ".windsurf").exists()


@pytest.mark.asyncio
async def test_write_to_multiple_ides_with_failure(tmp_path, sample_config):
    """Test writing to multiple IDEs with some failures."""
    ide_types = ["cursor", "unsupported", "claude"]
    results = await write_to_multiple_ides(ide_types, sample_config, tmp_path)
    
    assert len(results) == 3
    assert results[0].success is True  # cursor
    assert results[1].success is False  # unsupported
    assert results[2].success is True  # claude