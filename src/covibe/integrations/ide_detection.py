"""IDE detection functionality using functional programming principles."""

from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass


@dataclass
class IDEInfo:
    """Information about a detected IDE."""
    name: str
    type: str
    config_path: str
    confidence: float
    markers: List[str]


def detect_cursor(project_path: Path) -> Optional[IDEInfo]:
    """Detect Cursor IDE configuration."""
    markers = []
    confidence = 0.0
    
    # Check for .cursor directory
    cursor_dir = project_path / ".cursor"
    if cursor_dir.exists() and cursor_dir.is_dir():
        markers.append(".cursor directory")
        confidence += 0.8
        
        # Check for rules directory
        rules_dir = cursor_dir / "rules"
        if rules_dir.exists() and rules_dir.is_dir():
            markers.append(".cursor/rules directory")
            confidence += 0.1
        
        config_path = str(rules_dir / "personality.mdc")
    else:
        # Check for cursor-specific files
        cursor_files = [".cursorignore", ".cursor.json"]
        for file_name in cursor_files:
            if (project_path / file_name).exists():
                markers.append(file_name)
                confidence += 0.3
        
        if confidence > 0:
            config_path = str(project_path / ".cursor" / "rules" / "personality.mdc")
        else:
            return None
    
    if confidence > 0.2:
        return IDEInfo(
            name="Cursor",
            type="cursor",
            config_path=config_path,
            confidence=min(confidence, 1.0),
            markers=markers
        )
    
    return None


def detect_claude(project_path: Path) -> Optional[IDEInfo]:
    """Detect Claude IDE configuration."""
    markers = []
    confidence = 0.0
    
    # Check for existing CLAUDE.md file
    claude_file = project_path / "CLAUDE.md"
    if claude_file.exists():
        markers.append("CLAUDE.md file")
        confidence += 0.9
    
    # Check for Claude-specific markers
    claude_markers = [".claude", "claude.json", ".claude.json"]
    for marker in claude_markers:
        if (project_path / marker).exists():
            markers.append(marker)
            confidence += 0.3
    
    if confidence > 0.1:
        return IDEInfo(
            name="Claude",
            type="claude",
            config_path=str(claude_file),
            confidence=min(confidence, 1.0),
            markers=markers
        )
    
    return None


def detect_windsurf(project_path: Path) -> Optional[IDEInfo]:
    """Detect Windsurf IDE configuration."""
    markers = []
    confidence = 0.0
    
    # Check for .windsurf file
    windsurf_file = project_path / ".windsurf"
    if windsurf_file.exists():
        markers.append(".windsurf file")
        confidence += 0.9
    
    if confidence > 0.1:
        return IDEInfo(
            name="Windsurf",
            type="windsurf",
            config_path=str(windsurf_file),
            confidence=min(confidence, 1.0),
            markers=markers
        )
    
    return None


def detect_ides(project_path: str) -> List[IDEInfo]:
    """Detect IDEs in the given project path."""
    project_path = Path(project_path).resolve()
    detected_ides = []
    
    # Check for each IDE type
    cursor_info = detect_cursor(project_path)
    if cursor_info:
        detected_ides.append(cursor_info)
    
    claude_info = detect_claude(project_path)
    if claude_info:
        detected_ides.append(claude_info)
    
    windsurf_info = detect_windsurf(project_path)
    if windsurf_info:
        detected_ides.append(windsurf_info)
    
    return detected_ides


def get_primary_ide(detected_ides: List[IDEInfo]) -> Optional[IDEInfo]:
    """Get the primary IDE from detected IDEs based on confidence scores."""
    if not detected_ides:
        return None
    
    # Sort by confidence score (highest first)
    sorted_ides = sorted(detected_ides, key=lambda x: x.confidence, reverse=True)
    return sorted_ides[0]
