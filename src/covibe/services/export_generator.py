"""Export file generation service for IDE-specific configuration files."""

from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import hashlib
import json
from ..models.core import PersonalityConfig, ExportFormatOptions, ExportResult, PreviewResult
from ..integrations.ide_writers import (
    write_cursor_config,
    write_claude_config, 
    write_windsurf_config,
    get_llm_metadata,
    format_llm_metadata_comment,
    format_trait_details,
    format_enhanced_mannerisms
)


def get_supported_ide_types() -> List[str]:
    """Get list of supported IDE types for export."""
    return ["cursor", "claude", "windsurf", "generic"]


def get_ide_file_extension(ide_type: str) -> str:
    """Get file extension for IDE type."""
    extensions = {
        "cursor": "mdc",
        "claude": "md", 
        "windsurf": "windsurf",
        "generic": "md"
    }
    return extensions.get(ide_type.lower(), "md")


def get_ide_mime_type(ide_type: str) -> str:
    """Get MIME type for IDE configuration file."""
    mime_types = {
        "cursor": "text/markdown",
        "claude": "text/markdown",
        "windsurf": "application/json", 
        "generic": "text/markdown"
    }
    return mime_types.get(ide_type.lower(), "text/plain")


def get_syntax_language(ide_type: str) -> str:
    """Get syntax highlighting language for IDE type."""
    languages = {
        "cursor": "markdown",
        "claude": "markdown",
        "windsurf": "json",
        "generic": "markdown"
    }
    return languages.get(ide_type.lower(), "markdown")


async def generate_placement_instructions(
    ide_type: str,
    file_name: str,
    config: PersonalityConfig
) -> List[str]:
    """Generate step-by-step placement instructions for IDE integration.
    
    Args:
        ide_type: Target IDE type
        file_name: Generated file name
        config: Personality configuration
        
    Returns:
        List of placement instruction steps
    """
    ide_lower = ide_type.lower()
    
    if ide_lower == "cursor":
        return [
            f"1. Save the file as `.cursor/rules/{file_name}` in your project root",
            "2. Create the `.cursor/rules/` directory if it doesn't exist",
            "3. Cursor will automatically load the personality rules",
            "4. Restart Cursor if the changes don't take effect immediately",
            "5. The personality will apply to all AI interactions in this project"
        ]
    elif ide_lower == "claude":
        return [
            f"1. Save the file as `{file_name}` in your project root directory",
            "2. Claude will automatically detect and use this configuration",
            "3. The personality will apply to all Claude interactions in this project",
            "4. You can reference specific sections using @CLAUDE.md mentions",
            "5. Edit the file anytime to adjust personality traits"
        ]
    elif ide_lower == "windsurf":
        return [
            f"1. Save the file as `.{file_name}` in your project root directory",
            "2. Windsurf will automatically load the JSON configuration",
            "3. Restart Windsurf if the configuration doesn't load immediately", 
            "4. The personality will apply to all AI assistant interactions",
            "5. Modify the JSON structure to fine-tune personality traits"
        ]
    else:
        return [
            f"1. Save the file as `{file_name}` in your project directory",
            "2. Configure your IDE to use this personality file",
            "3. Refer to your IDE documentation for specific integration steps",
            "4. The personality configuration follows standard markdown format",
            "5. Customize the content as needed for your specific use case"
        ]


def generate_file_name(
    config: PersonalityConfig,
    ide_type: str,
    format_options: Optional[ExportFormatOptions] = None
) -> str:
    """Generate appropriate file name for export.
    
    Args:
        config: Personality configuration
        ide_type: Target IDE type
        format_options: Export format options
        
    Returns:
        Generated file name
    """
    if format_options and format_options.file_name:
        return format_options.file_name
    
    ide_lower = ide_type.lower()
    extension = get_ide_file_extension(ide_type)
    
    if ide_lower == "cursor":
        return f"personality.{extension}"
    elif ide_lower == "claude":
        return f"CLAUDE.{extension}"
    elif ide_lower == "windsurf":
        return f"windsurf"  # No extension for .windsurf file
    else:
        # For generic, use sanitized personality name
        safe_name = "".join(c for c in config.profile.name if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_name = safe_name.replace(' ', '_').lower()
        return f"{safe_name}_personality.{extension}"


def calculate_content_checksum(content: str) -> str:
    """Calculate SHA-256 checksum of content."""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


async def generate_export_metadata(
    config: PersonalityConfig,
    ide_type: str,
    file_name: str,
    content: str,
    format_options: Optional[ExportFormatOptions] = None
) -> Dict[str, Any]:
    """Generate export metadata.
    
    Args:
        config: Personality configuration
        ide_type: Target IDE type
        file_name: Generated file name
        content: Generated content
        format_options: Export format options
        
    Returns:
        Export metadata dictionary
    """
    llm_metadata = get_llm_metadata(config)
    
    return {
        "export_version": "1.0",
        "personality_id": config.id,
        "personality_name": config.profile.name,
        "ide_type": ide_type,
        "file_name": file_name,
        "exported_at": datetime.now().isoformat(),
        "original_created_at": config.created_at.isoformat(),
        "file_size": len(content.encode('utf-8')),
        "checksum": calculate_content_checksum(content),
        "llm_generated": llm_metadata.get("is_llm_generated", False) if llm_metadata else False,
        "llm_provider": llm_metadata.get("provider") if llm_metadata else None,
        "confidence": llm_metadata.get("confidence") if llm_metadata else None,
        "format_options": format_options.model_dump() if format_options else None
    }


async def generate_generic_config(
    config: PersonalityConfig,
    format_options: Optional[ExportFormatOptions] = None
) -> str:
    """Generate generic IDE configuration content.
    
    Args:
        config: Personality configuration
        format_options: Export format options
        
    Returns:
        Generated configuration content
    """
    llm_metadata = get_llm_metadata(config)
    
    # Add metadata comment if requested
    metadata_comment = ""
    if format_options is None or format_options.include_metadata:
        metadata_comment = format_llm_metadata_comment(llm_metadata, "markdown")
    
    # Add custom header if provided
    custom_header = ""
    if format_options and format_options.custom_header:
        custom_header = f"{format_options.custom_header}\n\n"
    
    # Generate trait details
    trait_details = format_trait_details(config)
    mannerisms = format_enhanced_mannerisms(config)
    
    # Add confidence indicator for LLM-generated content
    confidence_note = ""
    if llm_metadata and llm_metadata.get("is_llm_generated"):
        confidence = int(llm_metadata.get("confidence", 0.0) * 100)
        provider = llm_metadata.get("provider", "unknown").title()
        confidence_note = f"\n> **AI Analysis** ({provider}): {confidence}% confidence\n"
    
    content = f"""{metadata_comment}{custom_header}# Personality Configuration: {config.profile.name}
{confidence_note}
## Profile Information
- **Type**: {config.profile.type.value.title()}
- **Generated**: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## Communication Style
- **Tone**: {config.profile.communication_style.tone}
- **Formality**: {config.profile.communication_style.formality.value}
- **Verbosity**: {config.profile.communication_style.verbosity.value}
- **Technical Level**: {config.profile.communication_style.technical_level.value}

## Personality Traits
{trait_details}

## Behavioral Patterns
{mannerisms}

## Context Guidelines
{config.context}
"""

    if format_options is None or format_options.include_instructions:
        content += """
## Usage Instructions
1. Copy this configuration to your IDE's personality/context file
2. Adjust the settings according to your IDE's requirements
3. The AI assistant will adopt these personality traits in conversations
4. Modify any section to fine-tune the personality as needed

---
*Generic personality configuration - adapt as needed for your specific IDE*
"""
    
    return content.strip()


async def generate_export_file(
    config: PersonalityConfig,
    ide_type: str,
    format_options: Optional[ExportFormatOptions] = None
) -> ExportResult:
    """Generate IDE-specific configuration file content.
    
    Args:
        config: PersonalityConfig to export
        ide_type: Target IDE type
        format_options: Export format options
        
    Returns:
        ExportResult with generated content and metadata
    """
    try:
        ide_lower = ide_type.lower()
        
        if ide_lower not in get_supported_ide_types():
            return ExportResult(
                success=False,
                content="",
                file_name="",
                file_size=0,
                mime_type="",
                placement_instructions=[],
                metadata={},
                error=f"Unsupported IDE type: {ide_type}. Supported types: {', '.join(get_supported_ide_types())}"
            )
        
        # Generate file name
        file_name = generate_file_name(config, ide_type, format_options)
        
        # Generate content based on IDE type
        if ide_lower == "generic":
            content = await generate_generic_config(config, format_options)
        else:
            # Use existing IDE writers but extract content instead of writing to file
            temp_path = Path("/tmp")  # Temporary path for content generation
            
            if ide_lower == "cursor":
                result = await write_cursor_config(config, temp_path)
            elif ide_lower == "claude":
                result = await write_claude_config(config, temp_path)
            elif ide_lower == "windsurf":
                result = await write_windsurf_config(config, temp_path)
            else:
                return ExportResult(
                    success=False,
                    content="",
                    file_name="",
                    file_size=0,
                    mime_type="",
                    placement_instructions=[],
                    metadata={},
                    error=f"IDE writer not implemented for: {ide_type}"
                )
            
            if not result.success:
                return ExportResult(
                    success=False,
                    content="",
                    file_name="",
                    file_size=0,
                    mime_type="",
                    placement_instructions=[],
                    metadata={},
                    error=result.message
                )
            
            # Read generated content and clean up
            try:
                with open(result.file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                Path(result.file_path).unlink()  # Delete temporary file
            except Exception as e:
                return ExportResult(
                    success=False,
                    content="",
                    file_name="",
                    file_size=0,
                    mime_type="",
                    placement_instructions=[],
                    metadata={},
                    error=f"Failed to read generated content: {str(e)}"
                )
        
        # Generate placement instructions
        instructions = await generate_placement_instructions(ide_type, file_name, config)
        
        # Generate metadata
        metadata = await generate_export_metadata(config, ide_type, file_name, content, format_options)
        
        return ExportResult(
            success=True,
            content=content,
            file_name=file_name,
            file_size=len(content.encode('utf-8')),
            mime_type=get_ide_mime_type(ide_type),
            placement_instructions=instructions,
            metadata=metadata
        )
        
    except Exception as e:
        return ExportResult(
            success=False,
            content="",
            file_name="",
            file_size=0,
            mime_type="",
            placement_instructions=[],
            metadata={},
            error=f"Failed to generate export file: {str(e)}"
        )


async def generate_preview_content(
    config: PersonalityConfig,
    ide_type: str,
    format_options: Optional[ExportFormatOptions] = None
) -> PreviewResult:
    """Generate preview of export content without file creation.
    
    Args:
        config: PersonalityConfig to preview
        ide_type: Target IDE type
        format_options: Export format options
        
    Returns:
        PreviewResult with content preview and metadata
    """
    try:
        # Generate export content
        export_result = await generate_export_file(config, ide_type, format_options)
        
        if not export_result.success:
            raise Exception(export_result.error)
        
        # Generate placement instructions
        instructions = await generate_placement_instructions(ide_type, export_result.file_name, config)
        
        return PreviewResult(
            content=export_result.content,
            file_name=export_result.file_name,
            file_size=export_result.file_size,
            syntax_language=get_syntax_language(ide_type),
            placement_instructions=instructions,
            metadata=export_result.metadata
        )
        
    except Exception as e:
        raise Exception(f"Failed to generate preview content: {str(e)}")


async def generate_bulk_export(
    configs: List[PersonalityConfig],
    ide_types: List[str],
    format_options: Optional[ExportFormatOptions] = None
) -> Dict[str, Any]:
    """Generate bulk export package with multiple configurations.
    
    Args:
        configs: List of PersonalityConfigs to export
        ide_types: List of target IDE types
        format_options: Export format options
        
    Returns:
        Dictionary containing export results for each configuration/IDE combination
    """
    results = {}
    
    for config in configs:
        config_results = {}
        for ide_type in ide_types:
            try:
                export_result = await generate_export_file(config, ide_type, format_options)
                config_results[ide_type] = export_result.model_dump()
            except Exception as e:
                config_results[ide_type] = {
                    "success": False,
                    "error": f"Failed to export for {ide_type}: {str(e)}"
                }
        results[config.id] = config_results
    
    return results