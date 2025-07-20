"""IDE-specific file writers using functional programming principles."""

from pathlib import Path
from typing import List, Optional
from dataclasses import dataclass
from datetime import datetime
from ..models.core import PersonalityConfig
from ..services.context_generation import generate_context_for_ide


@dataclass
class WriteResult:
    """Result of writing personality configuration to IDE."""
    success: bool
    file_path: str
    message: str
    backup_path: Optional[str] = None


async def write_cursor_config(config: PersonalityConfig, project_path: Path) -> WriteResult:
    """Write personality configuration for Cursor IDE."""
    try:
        # Create .cursor/rules directory if it doesn't exist
        cursor_dir = project_path / ".cursor"
        rules_dir = cursor_dir / "rules"
        rules_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate Cursor-specific context
        context = generate_context_for_ide(config.profile, "cursor")
        
        # Write to personality.mdc file
        config_file = rules_dir / "personality.mdc"
        
        # Create backup if file exists
        backup_path = None
        if config_file.exists():
            backup_path = str(config_file.with_suffix(f".mdc.backup.{int(datetime.now().timestamp())}"))
            config_file.rename(backup_path)
        
        # Write new configuration
        config_file.write_text(context, encoding='utf-8')
        
        return WriteResult(
            success=True,
            file_path=str(config_file),
            message=f"Successfully wrote {config.profile.name} personality to Cursor configuration",
            backup_path=backup_path
        )
        
    except Exception as e:
        return WriteResult(
            success=False,
            file_path=str(project_path / ".cursor" / "rules" / "personality.mdc"),
            message=f"Failed to write Cursor configuration: {str(e)}"
        )


async def write_claude_config(config: PersonalityConfig, project_path: Path) -> WriteResult:
    """Write personality configuration for Claude IDE."""
    try:
        # Generate Claude-specific context
        context = generate_context_for_ide(config.profile, "claude")
        
        # Write to CLAUDE.md file
        config_file = project_path / "CLAUDE.md"
        
        # Create backup if file exists
        backup_path = None
        if config_file.exists():
            backup_path = str(config_file.with_suffix(f".md.backup.{int(datetime.now().timestamp())}"))
            config_file.rename(backup_path)
        
        # Write new configuration
        config_file.write_text(context, encoding='utf-8')
        
        return WriteResult(
            success=True,
            file_path=str(config_file),
            message=f"Successfully wrote {config.profile.name} personality to Claude configuration",
            backup_path=backup_path
        )
        
    except Exception as e:
        return WriteResult(
            success=False,
            file_path=str(project_path / "CLAUDE.md"),
            message=f"Failed to write Claude configuration: {str(e)}"
        )


async def write_to_ide(ide_type: str, config: PersonalityConfig, project_path: Path) -> WriteResult:
    """Write personality configuration to specific IDE."""
    writers = {
        "cursor": write_cursor_config,
        "claude": write_claude_config
    }
    
    writer = writers.get(ide_type.lower())
    if not writer:
        return WriteResult(
            success=False,
            file_path="",
            message=f"Unsupported IDE type: {ide_type}"
        )
    
    return await writer(config, project_path)