"""IDE configuration writers for different IDE types with LLM enhancement support."""

from pathlib import Path
from typing import Union, Optional, List
from dataclasses import dataclass
from datetime import datetime
from ..models.core import PersonalityConfig, ResearchSource


@dataclass
class WriteResult:
    """Result of writing IDE configuration."""
    success: bool
    file_path: str
    message: str


def get_llm_metadata(config: PersonalityConfig) -> Optional[dict]:
    """Extract LLM metadata from personality profile sources.
    
    Args:
        config: PersonalityConfig to analyze
        
    Returns:
        Dict with LLM metadata or None if not LLM-generated
    """
    if not config.profile.sources:
        return None
    
    for source in config.profile.sources:
        if source.type.startswith("llm_"):
            provider = source.type.replace("llm_", "")
            return {
                "provider": provider,
                "confidence": source.confidence,
                "generated_at": source.last_updated,
                "is_llm_generated": True
            }
    
    return {"is_llm_generated": False}


def format_llm_metadata_comment(metadata: Optional[dict], format_type: str = "markdown") -> str:
    """Format LLM metadata as a comment block.
    
    Args:
        metadata: LLM metadata dict
        format_type: Comment format type ("markdown", "html", etc.)
        
    Returns:
        Formatted metadata comment string
    """
    if not metadata or not metadata.get("is_llm_generated"):
        return ""
    
    timestamp = metadata.get("generated_at", datetime.now())
    if isinstance(timestamp, datetime):
        timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")
    else:
        timestamp_str = str(timestamp)
    
    confidence_percent = int(metadata.get("confidence", 0.0) * 100)
    provider = metadata.get("provider", "unknown").title()
    
    if format_type == "markdown":
        return f"""
<!-- LLM-Generated Personality Configuration -->
<!-- Provider: {provider} -->
<!-- Confidence: {confidence_percent}% -->
<!-- Generated: {timestamp_str} -->
<!-- This configuration was created using AI analysis -->

"""
    elif format_type == "html":
        return f"""
<!-- 
LLM-Generated Personality Configuration
Provider: {provider}
Confidence: {confidence_percent}%
Generated: {timestamp_str}
This configuration was created using AI analysis
-->

"""
    else:
        return f"""
# LLM-Generated Personality Configuration
# Provider: {provider}
# Confidence: {confidence_percent}%
# Generated: {timestamp_str}
# This configuration was created using AI analysis

"""


def format_trait_details(config: PersonalityConfig) -> str:
    """Format detailed trait information for LLM-generated profiles.
    
    Args:
        config: PersonalityConfig to format
        
    Returns:
        Formatted trait details string
    """
    if not config.profile.traits:
        return "No specific traits identified."
    
    trait_lines = []
    for trait in config.profile.traits:
        intensity_bar = "●" * trait.intensity + "○" * (10 - trait.intensity)
        trait_lines.append(f"- **{trait.trait.title()}** ({trait.intensity}/10): {intensity_bar}")
        
        # Add examples if available
        if hasattr(trait, 'examples') and trait.examples:
            for example in trait.examples[:2]:  # Limit to first 2 examples
                trait_lines.append(f"  - {example}")
    
    return "\n".join(trait_lines)


def format_enhanced_mannerisms(config: PersonalityConfig) -> str:
    """Format enhanced mannerisms for LLM-generated profiles.
    
    Args:
        config: PersonalityConfig to format
        
    Returns:
        Formatted mannerisms string
    """
    if not config.profile.mannerisms:
        return "- No specific mannerisms identified"
    
    return "\n".join(f"- {mannerism}" for mannerism in config.profile.mannerisms)


async def write_cursor_config(config: PersonalityConfig, base_path: Path) -> WriteResult:
    """Write personality configuration for Cursor IDE with LLM enhancement support.
    
    Args:
        config: PersonalityConfig to write
        base_path: Base directory path for the configuration
        
    Returns:
        WriteResult with success status and details
    """
    try:
        # Create .cursor/rules directory
        cursor_dir = base_path / ".cursor" / "rules"
        cursor_dir.mkdir(parents=True, exist_ok=True)
        
        # Create personality.mdc file
        config_file = cursor_dir / "personality.mdc"
        
        # Get LLM metadata for enhanced formatting
        llm_metadata = get_llm_metadata(config)
        metadata_comment = format_llm_metadata_comment(llm_metadata, "markdown")
        
        # Generate enhanced configuration content
        trait_details = format_trait_details(config)
        mannerisms = format_enhanced_mannerisms(config)
        
        # Add confidence indicator for LLM-generated content
        confidence_note = ""
        if llm_metadata and llm_metadata.get("is_llm_generated"):
            confidence = int(llm_metadata.get("confidence", 0.0) * 100)
            provider = llm_metadata.get("provider", "unknown").title()
            confidence_note = f"\n> **AI Analysis** ({provider}): {confidence}% confidence\n"
        
        content = f"""{metadata_comment}# Personality Configuration: {config.profile.name}
{confidence_note}
## Communication Style
- **Tone**: {config.profile.communication_style.tone}
- **Formality**: {config.profile.communication_style.formality.value}
- **Verbosity**: {config.profile.communication_style.verbosity.value}
- **Technical Level**: {config.profile.communication_style.technical_level.value}

## Personality Type
{config.profile.type.value.title()}

## Personality Traits
{trait_details}

## Behavioral Patterns
{mannerisms}

## Context Guidelines
{config.context}

---
*Configuration generated on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
"""
        
        # Write the file
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return WriteResult(
            success=True,
            file_path=str(config_file),
            message=f"Successfully wrote Cursor configuration to {config_file}"
        )
        
    except Exception as e:
        return WriteResult(
            success=False,
            file_path="",
            message=f"Failed to write Cursor configuration: {str(e)}"
        )


async def write_claude_config(config: PersonalityConfig, base_path: Path) -> WriteResult:
    """Write personality configuration for Claude with LLM enhancement support.
    
    Args:
        config: PersonalityConfig to write
        base_path: Base directory path for the configuration
        
    Returns:
        WriteResult with success status and details
    """
    try:
        # Create CLAUDE.md file in base directory
        config_file = base_path / "CLAUDE.md"
        
        # Get LLM metadata for enhanced formatting
        llm_metadata = get_llm_metadata(config)
        metadata_comment = format_llm_metadata_comment(llm_metadata, "markdown")
        
        # Generate enhanced configuration content
        trait_details = format_trait_details(config)
        mannerisms = format_enhanced_mannerisms(config)
        
        # Add confidence and analysis details for LLM-generated content
        analysis_section = ""
        if llm_metadata and llm_metadata.get("is_llm_generated"):
            confidence = int(llm_metadata.get("confidence", 0.0) * 100)
            provider = llm_metadata.get("provider", "unknown").title()
            analysis_section = f"""
## AI Analysis Details
- **Provider**: {provider}
- **Confidence**: {confidence}%
- **Generated**: {llm_metadata.get("generated_at", datetime.now()).strftime("%Y-%m-%d %H:%M:%S")}

> This personality configuration was created using advanced AI analysis of the provided description. 
> The AI identified key traits, communication patterns, and behavioral characteristics to create 
> a comprehensive personality profile.

"""

        content = f"""{metadata_comment}# Claude Personality Configuration

## Profile: {config.profile.name}
**Type**: {config.profile.type.value.title()}
{analysis_section}
## Communication Guidelines
- **Tone**: Adopt a {config.profile.communication_style.tone} tone in all interactions
- **Formality**: Use {config.profile.communication_style.formality.value} language and communication style
- **Verbosity**: Be {config.profile.communication_style.verbosity.value} in your responses
- **Technical Level**: Target {config.profile.communication_style.technical_level.value} technical complexity

## Personality Traits
{trait_details}

## Behavioral Patterns & Mannerisms
{mannerisms}

## Context & Guidelines
{config.context}

## Implementation Notes
- Embody these characteristics consistently throughout conversations
- Adapt the personality to the context while maintaining core traits
- Balance personality expression with helpfulness and accuracy

---
*Generated personality configuration for Claude on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
"""
        
        # Write the file
        with open(config_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return WriteResult(
            success=True,
            file_path=str(config_file),
            message=f"Successfully wrote Claude configuration to {config_file}"
        )
        
    except Exception as e:
        return WriteResult(
            success=False,
            file_path="",
            message=f"Failed to write Claude configuration: {str(e)}"
        )


async def write_windsurf_config(config: PersonalityConfig, base_path: Path) -> WriteResult:
    """Write personality configuration for Windsurf IDE with LLM enhancement support.
    
    Args:
        config: PersonalityConfig to write
        base_path: Base directory path for the configuration
        
    Returns:
        WriteResult with success status and details
    """
    try:
        # Create .windsurf file in base directory
        config_file = base_path / ".windsurf"
        
        # Get LLM metadata for enhanced formatting
        llm_metadata = get_llm_metadata(config)
        
        # Generate enhanced configuration content for Windsurf
        trait_details = format_trait_details(config)
        mannerisms = format_enhanced_mannerisms(config)
        
        # Create JSON-like configuration for Windsurf
        import json
        
        windsurf_config = {
            "personality": {
                "name": config.profile.name,
                "type": config.profile.type.value,
                "communication_style": {
                    "tone": config.profile.communication_style.tone,
                    "formality": config.profile.communication_style.formality.value,
                    "verbosity": config.profile.communication_style.verbosity.value,
                    "technical_level": config.profile.communication_style.technical_level.value
                },
                "traits": [
                    {
                        "name": trait.trait,
                        "intensity": trait.intensity,
                        "examples": getattr(trait, 'examples', [])
                    }
                    for trait in config.profile.traits
                ],
                "mannerisms": config.profile.mannerisms,
                "context": config.context
            },
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "version": "1.0"
            }
        }
        
        # Add LLM metadata if available
        if llm_metadata and llm_metadata.get("is_llm_generated"):
            windsurf_config["metadata"]["llm_generated"] = True
            windsurf_config["metadata"]["llm_provider"] = llm_metadata.get("provider")
            windsurf_config["metadata"]["confidence"] = llm_metadata.get("confidence")
            windsurf_config["metadata"]["llm_generated_at"] = llm_metadata.get("generated_at").isoformat() if isinstance(llm_metadata.get("generated_at"), datetime) else str(llm_metadata.get("generated_at"))
        
        # Write JSON configuration
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(windsurf_config, f, indent=2)
        
        return WriteResult(
            success=True,
            file_path=str(config_file),
            message=f"Successfully wrote Windsurf configuration to {config_file}"
        )
        
    except Exception as e:
        return WriteResult(
            success=False,
            file_path="",
            message=f"Failed to write Windsurf configuration: {str(e)}"
        )


async def write_to_ide(ide_type: str, config: PersonalityConfig, base_path: Path) -> WriteResult:
    """Write personality configuration for specified IDE type with LLM enhancement support.
    
    Args:
        ide_type: Type of IDE ('cursor', 'claude', 'windsurf', etc.)
        config: PersonalityConfig to write
        base_path: Base directory path for the configuration
        
    Returns:
        WriteResult with success status and details
    """
    ide_type_lower = ide_type.lower()
    
    if ide_type_lower == "cursor":
        return await write_cursor_config(config, base_path)
    elif ide_type_lower == "claude":
        return await write_claude_config(config, base_path)
    elif ide_type_lower == "windsurf":
        return await write_windsurf_config(config, base_path)
    else:
        return WriteResult(
            success=False,
            file_path="",
            message=f"Unsupported IDE type: {ide_type}. Supported types: cursor, claude, windsurf"
        )