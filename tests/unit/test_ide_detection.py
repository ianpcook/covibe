"""Unit tests for IDE detection functionality."""

import pytest
from pathlib import Path
from covibe.integrations.ide_detection import (
    detect_cursor,
    detect_claude,
    detect_windsurf,
    detect_ides,
    get_primary_ide
)


def test_detect_cursor_with_directory(tmp_path):
    """Test Cursor detection with .cursor directory."""
    # Create .cursor/rules directory
    cursor_dir = tmp_path / ".cursor"
    rules_dir = cursor_dir / "rules"
    rules_dir.mkdir(parents=True)
    
    result = detect_cursor(tmp_path)
    
    assert result is not None
    assert result.name == "Cursor"
    assert result.type == "cursor"
    assert result.confidence > 0.8


def test_detect_cursor_no_markers(tmp_path):
    """Test Cursor detection with no markers."""
    result = detect_cursor(tmp_path)
    assert result is None


def test_detect_claude_with_file(tmp_path):
    """Test Claude detection with CLAUDE.md file."""
    # Create CLAUDE.md file
    (tmp_path / "CLAUDE.md").touch()
    
    result = detect_claude(tmp_path)
    
    assert result is not None
    assert result.name == "Claude"
    assert result.type == "claude"
    assert result.confidence > 0.8


def test_detect_windsurf_with_file(tmp_path):
    """Test Windsurf detection with .windsurf file."""
    # Create .windsurf file
    (tmp_path / ".windsurf").touch()
    
    result = detect_windsurf(tmp_path)
    
    assert result is not None
    assert result.name == "Windsurf"
    assert result.type == "windsurf"
    assert result.confidence > 0.8


def test_detect_ides_multiple(tmp_path):
    """Test detecting multiple IDEs."""
    # Create markers for multiple IDEs
    (tmp_path / ".cursor").mkdir()
    (tmp_path / "CLAUDE.md").touch()
    
    results = detect_ides(str(tmp_path))
    
    assert len(results) >= 2
    ide_types = [ide.type for ide in results]
    assert "cursor" in ide_types
    assert "claude" in ide_types


def test_get_primary_ide_empty():
    """Test getting primary IDE with empty list."""
    primary = get_primary_ide([])
    assert primary is None
