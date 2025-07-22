"""Export metadata handling service for IDE Export System."""

from datetime import datetime
from typing import Optional, Dict, Any, List
import hashlib
import json
import re
from ..models.core import PersonalityConfig, ExportMetadata
from ..integrations.ide_writers import get_llm_metadata


async def generate_export_metadata(
    config: PersonalityConfig,
    ide_type: str,
    export_timestamp: datetime,
    exported_by: Optional[str] = None,
    additional_data: Optional[Dict[str, Any]] = None
) -> ExportMetadata:
    """Generate comprehensive metadata for exported configuration.
    
    Args:
        config: PersonalityConfig being exported
        ide_type: Target IDE type
        export_timestamp: When the export was created
        exported_by: Who/what created the export
        additional_data: Additional metadata to include
        
    Returns:
        ExportMetadata object with comprehensive export tracking data
    """
    # Get LLM metadata if available
    llm_metadata = get_llm_metadata(config)
    
    # Generate checksum based on core configuration data
    config_data = {
        "profile": config.profile.model_dump(),
        "context": config.context,
        "ide_type": ide_type
    }
    config_json = json.dumps(config_data, sort_keys=True)
    checksum = hashlib.sha256(config_json.encode('utf-8')).hexdigest()
    
    return ExportMetadata(
        export_version="1.0",
        personality_id=config.id,
        personality_name=config.profile.name,
        ide_type=ide_type,
        exported_at=export_timestamp,
        exported_by=exported_by,
        original_created_at=config.created_at,
        llm_generated=llm_metadata.get("is_llm_generated", False) if llm_metadata else False,
        llm_provider=llm_metadata.get("provider") if llm_metadata else None,
        confidence=llm_metadata.get("confidence") if llm_metadata else None,
        checksum=checksum
    )


async def format_metadata_for_ide(
    metadata: ExportMetadata,
    ide_type: str,
    include_checksum: bool = True
) -> str:
    """Format metadata as comments appropriate for IDE format.
    
    Args:
        metadata: ExportMetadata to format
        ide_type: Target IDE type for formatting
        include_checksum: Whether to include checksum in output
        
    Returns:
        Formatted metadata string as IDE-appropriate comments
    """
    ide_lower = ide_type.lower()
    
    # Prepare metadata lines
    lines = [
        f"Personality: {metadata.personality_name}",
        f"ID: {metadata.personality_id}",
        f"IDE: {metadata.ide_type}",
        f"Exported: {metadata.exported_at.strftime('%Y-%m-%d %H:%M:%S UTC')}",
        f"Created: {metadata.original_created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}"
    ]
    
    if metadata.exported_by:
        lines.append(f"Exported by: {metadata.exported_by}")
    
    if metadata.llm_generated:
        lines.append(f"LLM Generated: Yes")
        if metadata.llm_provider:
            lines.append(f"LLM Provider: {metadata.llm_provider}")
        if metadata.confidence:
            confidence_percent = int(metadata.confidence * 100)
            lines.append(f"Confidence: {confidence_percent}%")
    else:
        lines.append(f"LLM Generated: No")
    
    lines.append(f"Export Version: {metadata.export_version}")
    
    if include_checksum:
        lines.append(f"Checksum: {metadata.checksum}")
    
    # Format based on IDE type
    if ide_lower in ["cursor", "claude", "generic"]:
        # Markdown/HTML comments
        formatted_lines = ["<!--"] + [f"  {line}" for line in lines] + ["-->"]
        return "\n".join(formatted_lines)
    
    elif ide_lower == "windsurf":
        # JSON doesn't support comments, so this would be included as metadata object
        return json.dumps({
            "export_metadata": {
                "personality_name": metadata.personality_name,
                "personality_id": metadata.personality_id,
                "ide_type": metadata.ide_type,
                "exported_at": metadata.exported_at.isoformat(),
                "original_created_at": metadata.original_created_at.isoformat(),
                "exported_by": metadata.exported_by,
                "llm_generated": metadata.llm_generated,
                "llm_provider": metadata.llm_provider,
                "confidence": metadata.confidence,
                "export_version": metadata.export_version,
                "checksum": metadata.checksum if include_checksum else None
            }
        }, indent=2)
    
    else:
        # Default to hash comments
        formatted_lines = [f"# {line}" for line in lines]
        return "\n".join(formatted_lines)


async def extract_metadata_from_import(
    file_content: str,
    ide_type: str
) -> Optional[ExportMetadata]:
    """Extract metadata from imported configuration file.
    
    Args:
        file_content: Content of imported file
        ide_type: IDE type of imported file
        
    Returns:
        ExportMetadata object if found, None otherwise
    """
    ide_lower = ide_type.lower()
    
    try:
        if ide_lower in ["cursor", "claude", "generic"]:
            # Extract from HTML/Markdown comments
            return await _extract_from_html_comments(file_content)
        
        elif ide_lower == "windsurf":
            # Extract from JSON structure
            return await _extract_from_json_metadata(file_content)
        
        else:
            # Try hash comments
            return await _extract_from_hash_comments(file_content)
    
    except Exception:
        # If extraction fails, return None
        return None


async def _extract_from_html_comments(content: str) -> Optional[ExportMetadata]:
    """Extract metadata from HTML/Markdown comments."""
    # Find comment block
    comment_match = re.search(r'<!--(.*?)-->', content, re.DOTALL)
    if not comment_match:
        return None
    
    comment_content = comment_match.group(1).strip()
    
    # Extract metadata fields
    metadata_fields = {}
    for line in comment_content.split('\n'):
        line = line.strip()
        if ':' in line:
            key, value = line.split(':', 1)
            metadata_fields[key.strip().lower().replace(' ', '_')] = value.strip()
    
    # Build ExportMetadata if we have required fields
    if 'personality' in metadata_fields and 'id' in metadata_fields:
        return ExportMetadata(
            export_version=metadata_fields.get('export_version', '1.0'),
            personality_id=metadata_fields.get('id', ''),
            personality_name=metadata_fields.get('personality', ''),
            ide_type=metadata_fields.get('ide', 'unknown'),
            exported_at=datetime.fromisoformat(metadata_fields.get('exported', datetime.now().isoformat())),
            exported_by=metadata_fields.get('exported_by'),
            original_created_at=datetime.fromisoformat(metadata_fields.get('created', datetime.now().isoformat())),
            llm_generated=metadata_fields.get('llm_generated', '').lower() == 'yes',
            llm_provider=metadata_fields.get('llm_provider'),
            confidence=float(metadata_fields.get('confidence', '0').rstrip('%')) / 100 if metadata_fields.get('confidence') else None,
            checksum=metadata_fields.get('checksum', '')
        )
    
    return None


async def _extract_from_json_metadata(content: str) -> Optional[ExportMetadata]:
    """Extract metadata from JSON structure."""
    try:
        data = json.loads(content)
        
        # Look for export_metadata key
        if 'export_metadata' in data:
            meta = data['export_metadata']
            return ExportMetadata(
                export_version=meta.get('export_version', '1.0'),
                personality_id=meta.get('personality_id', ''),
                personality_name=meta.get('personality_name', ''),
                ide_type=meta.get('ide_type', 'unknown'),
                exported_at=datetime.fromisoformat(meta.get('exported_at', datetime.now().isoformat())),
                exported_by=meta.get('exported_by'),
                original_created_at=datetime.fromisoformat(meta.get('original_created_at', datetime.now().isoformat())),
                llm_generated=meta.get('llm_generated', False),
                llm_provider=meta.get('llm_provider'),
                confidence=meta.get('confidence'),
                checksum=meta.get('checksum', '')
            )
        
        # Also check metadata key (alternative location)
        if 'metadata' in data:
            meta = data['metadata']
            return ExportMetadata(
                export_version=meta.get('version', '1.0'),
                personality_id=data.get('personality', {}).get('name', ''),
                personality_name=data.get('personality', {}).get('name', ''),
                ide_type='windsurf',
                exported_at=datetime.fromisoformat(meta.get('generated_at', datetime.now().isoformat())),
                exported_by=None,
                original_created_at=datetime.fromisoformat(meta.get('llm_generated_at', datetime.now().isoformat())),
                llm_generated=meta.get('llm_generated', False),
                llm_provider=meta.get('llm_provider'),
                confidence=meta.get('confidence'),
                checksum=''
            )
    
    except (json.JSONDecodeError, KeyError, ValueError):
        pass
    
    return None


async def _extract_from_hash_comments(content: str) -> Optional[ExportMetadata]:
    """Extract metadata from hash comments."""
    metadata_fields = {}
    
    for line in content.split('\n'):
        line = line.strip()
        if line.startswith('#') and ':' in line:
            # Remove hash and extract key:value
            comment_part = line[1:].strip()
            if ':' in comment_part:
                key, value = comment_part.split(':', 1)
                metadata_fields[key.strip().lower().replace(' ', '_')] = value.strip()
    
    # Build ExportMetadata if we have required fields
    if 'personality' in metadata_fields and 'id' in metadata_fields:
        return ExportMetadata(
            export_version=metadata_fields.get('export_version', '1.0'),
            personality_id=metadata_fields.get('id', ''),
            personality_name=metadata_fields.get('personality', ''),
            ide_type=metadata_fields.get('ide', 'unknown'),
            exported_at=datetime.fromisoformat(metadata_fields.get('exported', datetime.now().isoformat())),
            exported_by=metadata_fields.get('exported_by'),
            original_created_at=datetime.fromisoformat(metadata_fields.get('created', datetime.now().isoformat())),
            llm_generated=metadata_fields.get('llm_generated', '').lower() == 'yes',
            llm_provider=metadata_fields.get('llm_provider'),
            confidence=float(metadata_fields.get('confidence', '0').rstrip('%')) / 100 if metadata_fields.get('confidence') else None,
            checksum=metadata_fields.get('checksum', '')
        )
    
    return None


async def validate_metadata_integrity(
    metadata: ExportMetadata,
    config: PersonalityConfig,
    ide_type: str
) -> tuple[bool, List[str]]:
    """Validate metadata integrity against configuration.
    
    Args:
        metadata: ExportMetadata to validate
        config: PersonalityConfig to validate against
        ide_type: Expected IDE type
        
    Returns:
        Tuple of (is_valid, list_of_issues)
    """
    issues = []
    
    # Check personality ID match
    if metadata.personality_id != config.id:
        issues.append(f"Personality ID mismatch: metadata={metadata.personality_id}, config={config.id}")
    
    # Check personality name match
    if metadata.personality_name != config.profile.name:
        issues.append(f"Personality name mismatch: metadata={metadata.personality_name}, config={config.profile.name}")
    
    # Check IDE type match
    if metadata.ide_type.lower() != ide_type.lower():
        issues.append(f"IDE type mismatch: metadata={metadata.ide_type}, expected={ide_type}")
    
    # Check created date consistency
    if metadata.original_created_at != config.created_at:
        issues.append(f"Created date mismatch: metadata={metadata.original_created_at}, config={config.created_at}")
    
    # Validate checksum if present
    if metadata.checksum:
        config_data = {
            "profile": config.profile.model_dump(),
            "context": config.context,
            "ide_type": ide_type
        }
        expected_checksum = hashlib.sha256(
            json.dumps(config_data, sort_keys=True).encode('utf-8')
        ).hexdigest()
        
        if metadata.checksum != expected_checksum:
            issues.append(f"Checksum mismatch: metadata={metadata.checksum}, expected={expected_checksum}")
    
    return len(issues) == 0, issues


async def update_export_metadata(
    original_metadata: ExportMetadata,
    new_export_timestamp: datetime,
    exported_by: Optional[str] = None,
    increment_version: bool = False
) -> ExportMetadata:
    """Update export metadata for re-export.
    
    Args:
        original_metadata: Original ExportMetadata
        new_export_timestamp: New export timestamp
        exported_by: Who/what is doing the re-export
        increment_version: Whether to increment version number
        
    Returns:
        Updated ExportMetadata
    """
    new_version = original_metadata.export_version
    if increment_version:
        try:
            # Try to increment version number
            version_parts = original_metadata.export_version.split('.')
            if len(version_parts) >= 2:
                major, minor = int(version_parts[0]), int(version_parts[1])
                new_version = f"{major}.{minor + 1}"
        except (ValueError, IndexError):
            # If parsing fails, just append .1
            new_version = f"{original_metadata.export_version}.1"
    
    return ExportMetadata(
        export_version=new_version,
        personality_id=original_metadata.personality_id,
        personality_name=original_metadata.personality_name,
        ide_type=original_metadata.ide_type,
        exported_at=new_export_timestamp,
        exported_by=exported_by or original_metadata.exported_by,
        original_created_at=original_metadata.original_created_at,
        llm_generated=original_metadata.llm_generated,
        llm_provider=original_metadata.llm_provider,
        confidence=original_metadata.confidence,
        checksum=original_metadata.checksum
    )