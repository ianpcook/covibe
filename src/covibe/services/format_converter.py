"""Format conversion service for IDE Export System."""

import json
import re
from typing import Optional, Dict, Any, List
from datetime import datetime
from ..models.core import (
    PersonalityConfig, 
    PersonalityProfile,
    PersonalityTrait,
    CommunicationStyle,
    PersonalityType,
    FormalityLevel,
    VerbosityLevel,
    TechnicalLevel,
    ResearchSource,
    ConversionResult,
    IDEFormatDetectionResult
)
from .export_metadata import extract_metadata_from_import


async def convert_to_ide_format(
    config: PersonalityConfig,
    target_ide: str,
    source_ide: Optional[str] = None
) -> ConversionResult:
    """Convert personality config to specific IDE format.
    
    Args:
        config: PersonalityConfig to convert
        target_ide: Target IDE format
        source_ide: Source IDE format (optional)
        
    Returns:
        ConversionResult with converted content
    """
    try:
        from .export_generator import generate_export_file
        
        # Generate export file for target IDE
        export_result = await generate_export_file(config, target_ide)
        
        if not export_result.success:
            return ConversionResult(
                success=False,
                converted_content="",
                target_format=target_ide,
                conversion_notes=[],
                error=export_result.error
            )
        
        # Generate conversion notes
        notes = []
        notes.append(f"Converted personality '{config.profile.name}' to {target_ide} format")
        
        if source_ide and source_ide != target_ide:
            notes.append(f"Source format: {source_ide}")
            
            # Add format-specific conversion notes
            if source_ide.lower() == "windsurf" and target_ide.lower() in ["cursor", "claude", "generic"]:
                notes.append("Converted from JSON structure to markdown format")
            elif source_ide.lower() in ["cursor", "claude", "generic"] and target_ide.lower() == "windsurf":
                notes.append("Converted from markdown to JSON structure")
        
        notes.append(f"Generated {export_result.file_size} bytes of content")
        
        return ConversionResult(
            success=True,
            converted_content=export_result.content,
            target_format=target_ide,
            conversion_notes=notes
        )
        
    except Exception as e:
        return ConversionResult(
            success=False,
            converted_content="",
            target_format=target_ide,
            conversion_notes=[],
            error=f"Conversion failed: {str(e)}"
        )


async def detect_ide_format(
    file_content: str,
    file_name: str
) -> IDEFormatDetectionResult:
    """Detect IDE format from file content and name.
    
    Args:
        file_content: Content of the file
        file_name: Name of the file
        
    Returns:
        IDEFormatDetectionResult with detection results
    """
    indicators = []
    confidence = 0.0
    detected_ide = "unknown"
    
    file_name_lower = file_name.lower()
    
    # Check file name patterns
    if file_name_lower.endswith('.mdc'):
        indicators.append("File extension: .mdc")
        confidence += 0.4
        detected_ide = "cursor"
    elif file_name_lower == "claude.md":
        indicators.append("File name: CLAUDE.md")
        confidence += 0.5
        detected_ide = "claude"
    elif file_name_lower == ".windsurf" or file_name_lower.endswith('.windsurf'):
        indicators.append("File name: .windsurf or .windsurf extension")
        confidence += 0.5
        detected_ide = "windsurf"
    elif file_name_lower.endswith('.md'):
        indicators.append("File extension: .md")
        confidence += 0.1
        detected_ide = "generic"
    
    # Check file content patterns
    try:
        # Try to parse as JSON (Windsurf format)
        json_data = json.loads(file_content)
        indicators.append("Valid JSON structure")
        confidence += 0.3
        
        if 'personality' in json_data:
            indicators.append("Contains 'personality' key")
            confidence += 0.2
            detected_ide = "windsurf"
            
        if 'metadata' in json_data and 'generated_at' in json_data.get('metadata', {}):
            indicators.append("Contains metadata with generated_at")
            confidence += 0.1
            detected_ide = "windsurf"
            
    except json.JSONDecodeError:
        # Not JSON, check for markdown patterns
        if '# Claude Personality Configuration' in file_content:
            indicators.append("Contains Claude-specific header")
            confidence += 0.4
            detected_ide = "claude"
        elif '# Personality Configuration:' in file_content:
            indicators.append("Contains personality configuration header")
            confidence += 0.2
            if detected_ide == "unknown":
                detected_ide = "cursor"
        elif re.search(r'<!--.*LLM-Generated.*-->', file_content, re.DOTALL):
            indicators.append("Contains LLM metadata comments")
            confidence += 0.2
        
        # Check for Cursor-specific patterns
        if '.cursor/rules/' in file_content or 'personality.mdc' in file_content:
            indicators.append("References .cursor/rules/ or personality.mdc")
            confidence += 0.3
            detected_ide = "cursor"
            
        # Check for Claude-specific patterns
        if 'Claude' in file_content and ('CLAUDE.md' in file_content or 'Claude configuration' in file_content):
            indicators.append("Contains Claude-specific references")
            confidence += 0.3
            detected_ide = "claude"
        
        # Generic markdown indicators
        if re.search(r'^#+ ', file_content, re.MULTILINE):
            indicators.append("Contains markdown headers")
            confidence += 0.1
            
        if '## Communication Style' in file_content:
            indicators.append("Contains Communication Style section")
            confidence += 0.1
            
        if '## Personality Traits' in file_content:
            indicators.append("Contains Personality Traits section")
            confidence += 0.1
    
    # Ensure confidence doesn't exceed 1.0
    confidence = min(confidence, 1.0)
    
    # Check if IDE is supported
    from .export_generator import get_supported_ide_types
    supported = detected_ide in get_supported_ide_types()
    
    return IDEFormatDetectionResult(
        detected_ide=detected_ide,
        confidence=confidence,
        format_indicators=indicators,
        supported=supported
    )


async def parse_imported_config(
    file_content: str,
    source_ide: str
) -> PersonalityConfig:
    """Parse imported IDE configuration file back to PersonalityConfig.
    
    Args:
        file_content: Content of the imported file
        source_ide: Source IDE type
        
    Returns:
        PersonalityConfig parsed from the file
        
    Raises:
        Exception: If parsing fails
    """
    source_ide_lower = source_ide.lower()
    
    if source_ide_lower == "windsurf":
        return await _parse_windsurf_config(file_content)
    elif source_ide_lower in ["cursor", "claude", "generic"]:
        return await _parse_markdown_config(file_content, source_ide_lower)
    else:
        raise Exception(f"Unsupported source IDE format: {source_ide}")


async def _parse_windsurf_config(file_content: str) -> PersonalityConfig:
    """Parse Windsurf JSON configuration."""
    try:
        data = json.loads(file_content)
        
        if 'personality' not in data:
            raise Exception("Invalid Windsurf config: missing 'personality' key")
        
        personality_data = data['personality']
        
        # Parse communication style
        comm_style_data = personality_data.get('communication_style', {})
        communication_style = CommunicationStyle(
            tone=comm_style_data.get('tone', 'neutral'),
            formality=FormalityLevel(comm_style_data.get('formality', 'mixed')),
            verbosity=VerbosityLevel(comm_style_data.get('verbosity', 'moderate')),
            technical_level=TechnicalLevel(comm_style_data.get('technical_level', 'intermediate'))
        )
        
        # Parse traits
        traits = []
        for trait_data in personality_data.get('traits', []):
            trait = PersonalityTrait(
                category="general",  # Default category
                trait=trait_data.get('name', ''),
                intensity=trait_data.get('intensity', 5),
                examples=trait_data.get('examples', [])
            )
            traits.append(trait)
        
        # Create research sources
        sources = []
        metadata = data.get('metadata', {})
        if metadata.get('llm_generated'):
            source = ResearchSource(
                type=f"llm_{metadata.get('llm_provider', 'unknown')}",
                confidence=metadata.get('confidence', 0.8),
                last_updated=datetime.fromisoformat(metadata.get('llm_generated_at', datetime.now().isoformat()))
            )
            sources.append(source)
        
        # Create personality profile
        profile = PersonalityProfile(
            id=personality_data.get('name', '').replace(' ', '_').lower(),
            name=personality_data.get('name', 'Unknown'),
            type=PersonalityType(personality_data.get('type', 'custom')),
            traits=traits,
            communication_style=communication_style,
            mannerisms=personality_data.get('mannerisms', []),
            sources=sources
        )
        
        # Create personality config
        config = PersonalityConfig(
            id=profile.id,
            profile=profile,
            context=personality_data.get('context', ''),
            ide_type='windsurf',
            file_path='.windsurf',
            active=True,
            created_at=datetime.fromisoformat(metadata.get('generated_at', datetime.now().isoformat())),
            updated_at=datetime.now()
        )
        
        return config
        
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        raise Exception(f"Failed to parse Windsurf config: {str(e)}")


async def _parse_markdown_config(file_content: str, source_ide: str) -> PersonalityConfig:
    """Parse markdown-based configuration (Cursor, Claude, Generic)."""
    try:
        # Extract personality name
        name_match = re.search(r'# (?:Personality Configuration: |Profile: |Claude Personality Configuration\s*)(.*)', file_content)
        name = name_match.group(1).strip() if name_match else "Unknown"
        
        # Extract personality type
        type_match = re.search(r'(?:\*\*Type\*\*: |Type: )(.*)', file_content)
        personality_type = type_match.group(1).strip().lower() if type_match else "custom"
        try:
            personality_type = PersonalityType(personality_type)
        except ValueError:
            personality_type = PersonalityType.CUSTOM
        
        # Extract communication style
        tone_match = re.search(r'(?:\*\*Tone\*\*: |Tone: )(.*)', file_content)
        tone = tone_match.group(1).strip() if tone_match else "neutral"
        
        formality_match = re.search(r'(?:\*\*Formality\*\*: |Formality: )(.*)', file_content)
        formality = formality_match.group(1).strip().lower() if formality_match else "mixed"
        try:
            formality = FormalityLevel(formality)
        except ValueError:
            formality = FormalityLevel.MIXED
        
        verbosity_match = re.search(r'(?:\*\*Verbosity\*\*: |Verbosity: )(.*)', file_content)
        verbosity = verbosity_match.group(1).strip().lower() if verbosity_match else "moderate"
        try:
            verbosity = VerbosityLevel(verbosity)
        except ValueError:
            verbosity = VerbosityLevel.MODERATE
        
        tech_level_match = re.search(r'(?:\*\*Technical Level\*\*: |Technical Level: )(.*)', file_content)
        tech_level = tech_level_match.group(1).strip().lower() if tech_level_match else "intermediate"
        try:
            tech_level = TechnicalLevel(tech_level)
        except ValueError:
            tech_level = TechnicalLevel.INTERMEDIATE
        
        communication_style = CommunicationStyle(
            tone=tone,
            formality=formality,
            verbosity=verbosity,
            technical_level=tech_level
        )
        
        # Extract traits (basic parsing)
        traits = []
        trait_section = re.search(r'## Personality Traits\s*(.*?)(?=##|$)', file_content, re.DOTALL)
        if trait_section:
            trait_lines = trait_section.group(1).strip().split('\n')
            for line in trait_lines:
                line = line.strip()
                if line.startswith('- **') and '**' in line:
                    # Parse format like "- **Trait Name** (5/10): ●●●●●○○○○○"
                    trait_match = re.match(r'- \*\*(.*?)\*\* \((\d+)/10\)', line)
                    if trait_match:
                        trait_name = trait_match.group(1)
                        intensity = int(trait_match.group(2))
                        trait = PersonalityTrait(
                            category="general",
                            trait=trait_name,
                            intensity=intensity,
                            examples=[]
                        )
                        traits.append(trait)
        
        # Extract mannerisms
        mannerisms = []
        mannerism_section = re.search(r'## (?:Behavioral Patterns|Behavioral Patterns & Mannerisms)\s*(.*?)(?=##|$)', file_content, re.DOTALL)
        if mannerism_section:
            mannerism_lines = mannerism_section.group(1).strip().split('\n')
            for line in mannerism_lines:
                line = line.strip()
                if line.startswith('- ') and line != "- No specific mannerisms identified":
                    mannerisms.append(line[2:])  # Remove "- " prefix
        
        # Extract context
        context = ""
        context_section = re.search(r'## (?:Context & Guidelines|Context Guidelines)\s*(.*?)(?=##|$)', file_content, re.DOTALL)
        if context_section:
            context = context_section.group(1).strip()
        
        # Extract metadata and create sources
        sources = []
        metadata = await extract_metadata_from_import(file_content, source_ide)
        if metadata and metadata.llm_generated:
            source = ResearchSource(
                type=f"llm_{metadata.llm_provider or 'unknown'}",
                confidence=metadata.confidence or 0.8,
                last_updated=metadata.exported_at
            )
            sources.append(source)
        
        # Create personality profile
        profile = PersonalityProfile(
            id=name.replace(' ', '_').lower(),
            name=name,
            type=personality_type,
            traits=traits,
            communication_style=communication_style,
            mannerisms=mannerisms,
            sources=sources
        )
        
        # Create personality config
        config = PersonalityConfig(
            id=profile.id,
            profile=profile,
            context=context,
            ide_type=source_ide,
            file_path=_get_default_file_path(source_ide),
            active=True,
            created_at=metadata.original_created_at if metadata else datetime.now(),
            updated_at=datetime.now()
        )
        
        return config
        
    except Exception as e:
        raise Exception(f"Failed to parse {source_ide} markdown config: {str(e)}")


def _get_default_file_path(ide_type: str) -> str:
    """Get default file path for IDE type."""
    paths = {
        "cursor": ".cursor/rules/personality.mdc",
        "claude": "CLAUDE.md",
        "windsurf": ".windsurf",
        "generic": "personality.md"
    }
    return paths.get(ide_type.lower(), "personality.md")


async def validate_conversion(
    original_config: PersonalityConfig,
    converted_content: str,
    target_ide: str
) -> tuple[bool, List[str]]:
    """Validate that conversion preserves essential information.
    
    Args:
        original_config: Original PersonalityConfig
        converted_content: Converted content
        target_ide: Target IDE type
        
    Returns:
        Tuple of (is_valid, list_of_issues)
    """
    issues = []
    
    try:
        # Parse the converted content back to a config
        parsed_config = await parse_imported_config(converted_content, target_ide)
        
        # Check personality name
        if parsed_config.profile.name != original_config.profile.name:
            issues.append(f"Name mismatch: '{parsed_config.profile.name}' vs '{original_config.profile.name}'")
        
        # Check personality type
        if parsed_config.profile.type != original_config.profile.type:
            issues.append(f"Type mismatch: {parsed_config.profile.type} vs {original_config.profile.type}")
        
        # Check communication style
        orig_style = original_config.profile.communication_style
        conv_style = parsed_config.profile.communication_style
        
        if conv_style.tone != orig_style.tone:
            issues.append(f"Tone mismatch: '{conv_style.tone}' vs '{orig_style.tone}'")
        if conv_style.formality != orig_style.formality:
            issues.append(f"Formality mismatch: {conv_style.formality} vs {orig_style.formality}")
        if conv_style.verbosity != orig_style.verbosity:
            issues.append(f"Verbosity mismatch: {conv_style.verbosity} vs {orig_style.verbosity}")
        if conv_style.technical_level != orig_style.technical_level:
            issues.append(f"Technical level mismatch: {conv_style.technical_level} vs {orig_style.technical_level}")
        
        # Check trait count (allow some variation in parsing)
        orig_trait_count = len(original_config.profile.traits)
        conv_trait_count = len(parsed_config.profile.traits)
        
        if abs(orig_trait_count - conv_trait_count) > 2:  # Allow 2 trait difference
            issues.append(f"Significant trait count difference: {conv_trait_count} vs {orig_trait_count}")
        
        # Check context preservation (basic)
        if len(parsed_config.context) < len(original_config.context) * 0.5:  # At least 50% preserved
            issues.append("Context appears to be significantly truncated")
        
    except Exception as e:
        issues.append(f"Failed to validate conversion: {str(e)}")
    
    return len(issues) == 0, issues