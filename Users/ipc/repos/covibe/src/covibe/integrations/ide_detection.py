"""IDE detection functionality using functional programming principles."""

import os
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class IDEInfo:
    """Information about a detected IDE."""
    name: str
    type: str
    config_path: str
    confidence: float
    markers: List[str]


def detect_ides(project_path: str) -> List[IDEInfo]:
    """
    Detect IDEs in the given project path.
    
    Args:
        project_path: Path to the project directory
        
    Returns:
        List of detected IDE information
    """
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
    
    vscode_info = detect_vscode(project_path)
    if vscode_info:
        detected_ides.append(vscode_info)
    
    kiro_info = detect_kiro(project_path)
    if kiro_info:
        detected_ides.append(kiro_info)
    
    return detected_ides


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
        # Check for cursor-specific files in project root
        cursor_files = [".cursorignore", ".cursor.json"]
        for file_name in cursor_files:
            if (project_path / file_name).exists():
                markers.append(file_name)
                confidence += 0.3
        
        if confidence > 0:
            # Create rules directory path even if it doesn't exist yet
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
    
    # Check for Claude project indicators in existing files
    if check_file_contains_claude_markers(project_path):
        markers.append("Claude references in project files")
        confidence += 0.2
    
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
    
    # Check for Windsurf directory
    windsurf_dir = project_path / ".windsurf"
    if windsurf_dir.exists() and windsurf_dir.is_dir():
        markers.append(".windsurf directory")
        confidence += 0.8
    
    # Check for Windsurf-specific files
    windsurf_files = ["windsurf.json", ".windsurf.json", "windsurf.config.json"]
    for file_name in windsurf_files:
        if (project_path / file_name).exists():
            markers.append(file_name)
            confidence += 0.4
    
    if confidence > 0.1:
        config_path = str(windsurf_file) if windsurf_file.exists() else str(project_path / ".windsurf")
        return IDEInfo(
            name="Windsurf",
            type="windsurf",
            config_path=config_path,
            confidence=min(confidence, 1.0),
            markers=markers
        )
    
    return None


def detect_vscode(project_path: Path) -> Optional[IDEInfo]:
    """Detect VS Code IDE configuration."""
    markers = []
    confidence = 0.0
    
    # Check for .vscode directory
    vscode_dir = project_path / ".vscode"
    if vscode_dir.exists() and vscode_dir.is_dir():
        markers.append(".vscode directory")
        confidence += 0.7
        
        # Check for specific VS Code files
        vscode_files = ["settings.json", "launch.json", "tasks.json", "extensions.json"]
        for file_name in vscode_files:
            if (vscode_dir / file_name).exists():
                markers.append(f".vscode/{file_name}")
                confidence += 0.1
        
        config_path = str(vscode_dir / "settings.json")
    else:
        return None
    
    if confidence > 0.5:
        return IDEInfo(
            name="VS Code",
            type="vscode",
            config_path=config_path,
            confidence=min(confidence, 1.0),
            markers=markers
        )
    
    return None


def detect_kiro(project_path: Path) -> Optional[IDEInfo]:
    """Detect Kiro IDE configuration."""
    markers = []
    confidence = 0.0
    
    # Check for .kiro directory
    kiro_dir = project_path / ".kiro"
    if kiro_dir.exists() and kiro_dir.is_dir():
        markers.append(".kiro directory")
        confidence += 0.8
        
        # Check for steering directory (Kiro-specific)
        steering_dir = kiro_dir / "steering"
        if steering_dir.exists() and steering_dir.is_dir():
            markers.append(".kiro/steering directory")
            confidence += 0.1
        
        config_path = str(steering_dir / "personality.md") if steering_dir.exists() else str(kiro_dir / "personality.md")
    else:
        # Check for kiro-specific files
        kiro_files = ["kiro.json", ".kiro.json"]
        for file_name in kiro_files:
            if (project_path / file_name).exists():
                markers.append(file_name)
                confidence += 0.4
        
        if confidence > 0:
            config_path = str(project_path / ".kiro" / "personality.md")
        else:
            return None
    
    if confidence > 0.2:
        return IDEInfo(
            name="Kiro",
            type="kiro",
            config_path=config_path,
            confidence=min(confidence, 1.0),
            markers=markers
        )
    
    return None


def check_file_contains_claude_markers(project_path: Path) -> bool:
    """Check if project files contain Claude-specific markers."""
    try:
        # Check common files for Claude references
        files_to_check = ["README.md", "package.json", "pyproject.toml", ".gitignore"]
        
        for file_name in files_to_check:
            file_path = project_path / file_name
            if file_path.exists() and file_path.is_file():
                try:
                    content = file_path.read_text(encoding='utf-8', errors='ignore')
                    if any(marker in content.lower() for marker in ["claude", "anthropic"]):
                        return True
                except (UnicodeDecodeError, PermissionError):
                    continue
    except Exception:
        pass
    
    return False


def get_primary_ide(detected_ides: List[IDEInfo]) -> Optional[IDEInfo]:
    """
    Get the primary IDE from detected IDEs based on confidence scores.
    
    Args:
        detected_ides: List of detected IDE information
        
    Returns:
        Primary IDE info or None if no IDEs detected
    """
    if not detected_ides:
        return None
    
    # Sort by confidence score (highest first)
    sorted_ides = sorted(detected_ides, key=lambda x: x.confidence, reverse=True)
    return sorted_ides[0]


def get_ide_summary(detected_ides: List[IDEInfo]) -> Dict[str, any]:
    """
    Get a summary of detected IDEs.
    
    Args:
        detected_ides: List of detected IDE information
        
    Returns:
        Summary dictionary with IDE detection results
    """
    primary_ide = get_primary_ide(detected_ides)
    
    return {
        "total_detected": len(detected_ides),
        "primary_ide": {
            "name": primary_ide.name,
            "type": primary_ide.type,
            "confidence": primary_ide.confidence,
            "config_path": primary_ide.config_path
        } if primary_ide else None,
        "all_detected": [
            {
                "name": ide.name,
                "type": ide.type,
                "confidence": ide.confidence,
                "markers": ide.markers
            }
            for ide in detected_ides
        ]
    }


def detect_ide_from_environment() -> Optional[str]:
    """
    Detect IDE from environment variables.
    
    Returns:
        IDE type string or None if not detected
    """
    # Check common IDE environment variables
    ide_env_vars = {
        "CURSOR": "cursor",
        "CURSOR_USER_DATA_DIR": "cursor",
        "VSCODE_PID": "vscode",
        "VSCODE_CWD": "vscode",
        "TERM_PROGRAM": {
            "cursor": "cursor",
            "vscode": "vscode"
        }
    }
    
    for env_var, ide_type in ide_env_vars.items():
        env_value = os.environ.get(env_var)
        if env_value:
            if isinstance(ide_type, dict):
                return ide_type.get(env_value.lower())
            else:
                return ide_type
    
    return None