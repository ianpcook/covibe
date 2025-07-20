"""Unit tests for IDE detection functionality."""

import pytest
from pathlib import Path
from covibe.integrations.ide_detection import (
    detect_cursor,
    detect_claude,
    detect_windsurf,
    detect_vscode,
    detect_kiro,
    detect_ides,
    get_primary_ide,
    get_ide_summary
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
    assert ".cursor directory" in result.markers


def test_detect_cursor_with_files(tmp_path):
    """Test Cursor detection with cursor-specific files."""
    # Create .cursorignore file
    (tmp_path / ".cursorignore").touch()
    
    result = detect_cursor(tmp_path)
    
    assert result is not None
    assert result.name == "Cursor"
    assert ".cursorignore" in result.markers


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
    assert "CLAUDE.md file" in result.markers


def test_detect_claude_no_markers(tmp_path):
    """Test Claude detection with no markers."""
    result = detect_claude(tmp_path)
    assert result is None


def test_detect_windsurf_with_file(tmp_path):
    """Test Windsurf detection with .windsurf file."""
    # Create .windsurf file
    (tmp_path / ".windsurf").touch()
    
    result = detect_windsurf(tmp_path)
    
    assert result is not None
    assert result.name == "Windsurf"
    assert result.type == "windsurf"
    assert result.confidence > 0.8
    assert ".windsurf file" in result.markers


def test_detect_vscode_with_directory(tmp_path):
    """Test VS Code detection with .vscode directory."""
    # Create .vscode directory with settings.json
    vscode_dir = tmp_path / ".vscode"
    vscode_dir.mkdir()
    (vscode_dir / "settings.json").touch()
    
    result = detect_vscode(tmp_path)
    
    assert result is not None
    assert result.name == "VS Code"
    assert result.type == "vscode"
    assert result.confidence > 0.5
    assert ".vscode directory" in result.markers


def test_detect_kiro_with_directory(tmp_path):
    """Test Kiro detection with .kiro directory."""
    # Create .kiro/steering directory
    kiro_dir = tmp_path / ".kiro"
    steering_dir = kiro_dir / "steering"
    steering_dir.mkdir(parents=True)
    
    result = detect_kiro(tmp_path)
    
    assert result is not None
    assert result.name == "Kiro"
    assert result.type == "kiro"
    assert result.confidence > 0.8
    assert ".kiro directory" in result.markers


def test_detect_ides_multiple(tmp_path):
    """Test detecting multiple IDEs."""
    # Create markers for multiple IDEs
    (tmp_path / ".cursor").mkdir()
    (tmp_path / "CLAUDE.md").touch()
    (tmp_path / ".windsurf").touch()
    
    results = detect_ides(str(tmp_path))
    
    assert len(results) == 3
    ide_types = [ide.type for ide in results]
    assert "cursor" in ide_types
    assert "claude" in ide_types
    assert "windsurf" in ide_types


def test_get_primary_ide(tmp_path):
    """Test getting primary IDE from detected IDEs."""
    # Create markers with different confidence levels
    (tmp_path / ".cursor").mkdir()  # High confidence
    (tmp_path / ".cursorignore").touch()  # Lower confidence
    
    results = detect_ides(str(tmp_path))
    primary = get_primary_ide(results)
    
    assert primary is not None
    assert primary.type == "cursor"
    assert primary.confidence > 0.8


def test_get_ide_summary(tmp_path):
    """Test getting IDE summary."""
    # Create markers for multiple IDEs
    (tmp_path / ".cursor").mkdir()
    (tmp_path / "CLAUDE.md").touch()
    
    results = detect_ides(str(tmp_path))
    summary = get_ide_summary(results)
    
    assert summary["total_detected"] == 2
    assert summary["primary_ide"] is not None
    assert len(summary["all_detected"]) == 2


def test_get_primary_ide_empty():
    """Test getting primary IDE with empty list."""
    primary = get_primary_ide([])
    assert primary is None


def test_get_ide_summary_empty():
    """Test getting IDE summary with empty list."""
    summary = get_ide_summary([])
    assert summary["total_detected"] == 0
    assert summary["primary_ide"] is None
    assert summary["all_detected"] == []