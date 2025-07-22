"""Core data models for the personality system."""

from datetime import datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field, field_validator
from ..utils.validation import (
    sanitize_text,
    validate_personality_description,
    validate_personality_name,
    validate_url,
)


class SourceType(str, Enum):
    """Source of personality request."""
    WEB = "web"
    API = "api"
    CHAT = "chat"


class PersonalityType(str, Enum):
    """Type of personality being configured."""
    CELEBRITY = "celebrity"
    FICTIONAL = "fictional"
    ARCHETYPE = "archetype"
    CUSTOM = "custom"


class FormalityLevel(str, Enum):
    """Communication formality level."""
    CASUAL = "casual"
    FORMAL = "formal"
    MIXED = "mixed"


class VerbosityLevel(str, Enum):
    """Communication verbosity level."""
    CONCISE = "concise"
    MODERATE = "moderate"
    VERBOSE = "verbose"


class TechnicalLevel(str, Enum):
    """Technical communication level."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    EXPERT = "expert"


class PersonalityRequest(BaseModel):
    """Request for personality configuration."""
    id: str
    description: str
    user_id: Optional[str] = None
    timestamp: datetime
    source: SourceType
    
    @field_validator('description')
    @classmethod
    def validate_description(cls, v):
        """Validate and sanitize personality description."""
        sanitized = sanitize_text(v)
        is_valid, errors = validate_personality_description(sanitized)
        if not is_valid:
            raise ValueError(f"Invalid description: {'; '.join(errors)}")
        return sanitized
    
    @field_validator('user_id')
    @classmethod
    def validate_user_id(cls, v):
        """Validate and sanitize user ID if provided."""
        if v is not None:
            return sanitize_text(v)
        return v


class PersonalityTrait(BaseModel):
    """Individual personality trait with intensity."""
    category: str
    trait: str
    intensity: int = Field(ge=1, le=10, description="Trait intensity from 1-10")
    examples: List[str]
    
    @field_validator('category', 'trait')
    @classmethod
    def validate_text_fields(cls, v):
        """Validate and sanitize text fields."""
        return sanitize_text(v)
    
    @field_validator('examples')
    @classmethod
    def validate_examples(cls, v):
        """Validate and sanitize example list."""
        return [sanitize_text(example) for example in v if example.strip()]


class CommunicationStyle(BaseModel):
    """Communication style preferences."""
    tone: str
    formality: FormalityLevel
    verbosity: VerbosityLevel
    technical_level: TechnicalLevel
    
    @field_validator('tone')
    @classmethod
    def validate_tone(cls, v):
        """Validate and sanitize tone field."""
        return sanitize_text(v)


class ResearchSource(BaseModel):
    """Source of personality research data."""
    type: str
    url: Optional[str] = None
    confidence: float = Field(ge=0.0, le=1.0, description="Confidence in source")
    last_updated: datetime
    
    @field_validator('url')
    @classmethod
    def validate_url_field(cls, v):
        """Validate URL format if provided."""
        if v is not None:
            is_valid, errors = validate_url(v)
            if not is_valid:
                raise ValueError(f"Invalid URL: {'; '.join(errors)}")
        return v
    
    @field_validator('type')
    @classmethod
    def validate_type(cls, v):
        """Validate and sanitize type field."""
        return sanitize_text(v)


class PersonalityProfile(BaseModel):
    """Complete personality profile with traits and style."""
    id: str
    name: str
    type: PersonalityType
    traits: List[PersonalityTrait]
    communication_style: CommunicationStyle
    mannerisms: List[str]
    sources: List[ResearchSource]
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Validate and sanitize personality name."""
        sanitized = sanitize_text(v)
        is_valid, errors = validate_personality_name(sanitized)
        if not is_valid:
            raise ValueError(f"Invalid name: {'; '.join(errors)}")
        return sanitized
    
    @field_validator('mannerisms')
    @classmethod
    def validate_mannerisms(cls, v):
        """Validate and sanitize mannerisms list."""
        return [sanitize_text(mannerism) for mannerism in v if mannerism.strip()]


class PersonalityConfig(BaseModel):
    """Complete personality configuration for IDE integration."""
    id: str
    profile: PersonalityProfile
    context: str
    ide_type: str
    file_path: str
    active: bool
    created_at: datetime
    updated_at: datetime
    
    @field_validator('context', 'ide_type', 'file_path')
    @classmethod
    def validate_text_fields(cls, v):
        """Validate and sanitize text fields."""
        return sanitize_text(v)


class ResearchResult(BaseModel):
    """Result of personality research operation."""
    query: str
    profiles: List[PersonalityProfile]
    confidence: float = Field(ge=0.0, le=1.0)
    suggestions: List[str]
    errors: List[str]


class ErrorDetail(BaseModel):
    """Error detail information."""
    code: str
    message: str
    details: Optional[dict] = None
    suggestions: List[str] = []


class ErrorResponse(BaseModel):
    """Standard error response format."""
    error: ErrorDetail
    request_id: str
    timestamp: datetime


# Export-specific models for IDE Export System

class ExportFormatOptions(BaseModel):
    """Options for customizing export format."""
    file_name: Optional[str] = None
    include_metadata: bool = True
    include_instructions: bool = True
    custom_header: Optional[str] = None
    preserve_comments: bool = True
    
    @field_validator('file_name', 'custom_header')
    @classmethod
    def validate_text_fields(cls, v):
        """Validate and sanitize text fields."""
        if v is not None:
            return sanitize_text(v)
        return v


class ExportResult(BaseModel):
    """Result of export operation."""
    success: bool
    content: str
    file_name: str
    file_size: int
    mime_type: str
    placement_instructions: List[str]
    metadata: dict = Field(default_factory=dict)
    error: Optional[str] = None
    
    @field_validator('content', 'file_name', 'mime_type')
    @classmethod
    def validate_text_fields(cls, v):
        """Validate and sanitize text fields."""
        return sanitize_text(v)
    
    @field_validator('placement_instructions')
    @classmethod
    def validate_instructions(cls, v):
        """Validate and sanitize instruction list."""
        return [sanitize_text(instruction) for instruction in v if instruction.strip()]


class PreviewResult(BaseModel):
    """Result of preview generation."""
    content: str
    file_name: str
    file_size: int
    syntax_language: str
    placement_instructions: List[str]
    metadata: dict = Field(default_factory=dict)
    
    @field_validator('content', 'file_name', 'syntax_language')
    @classmethod
    def validate_text_fields(cls, v):
        """Validate and sanitize text fields."""
        return sanitize_text(v)
    
    @field_validator('placement_instructions')
    @classmethod
    def validate_instructions(cls, v):
        """Validate and sanitize instruction list."""
        return [sanitize_text(instruction) for instruction in v if instruction.strip()]


class BulkExportRequest(BaseModel):
    """Request for bulk export operations."""
    personality_ids: List[str]
    ide_types: List[str]
    format_options: Optional[ExportFormatOptions] = None
    include_readme: bool = True
    
    @field_validator('personality_ids', 'ide_types')
    @classmethod
    def validate_lists(cls, v):
        """Validate and sanitize list items."""
        return [sanitize_text(item) for item in v if item.strip()]


class BulkExportResult(BaseModel):
    """Result of bulk export operation."""
    success: bool
    zip_content: bytes
    file_name: str
    file_size: int
    included_configs: List[str]
    readme_content: str
    error: Optional[str] = None
    
    @field_validator('file_name', 'readme_content')
    @classmethod
    def validate_text_fields(cls, v):
        """Validate and sanitize text fields."""
        return sanitize_text(v)
    
    @field_validator('included_configs')
    @classmethod
    def validate_configs(cls, v):
        """Validate and sanitize config list."""
        return [sanitize_text(config) for config in v if config.strip()]


class ExportMetadata(BaseModel):
    """Metadata for exported configurations."""
    export_version: str
    personality_id: str
    personality_name: str
    ide_type: str
    exported_at: datetime
    exported_by: Optional[str] = None
    original_created_at: datetime
    llm_generated: bool
    llm_provider: Optional[str] = None
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    checksum: str
    
    @field_validator('export_version', 'personality_id', 'personality_name', 'ide_type', 'exported_by', 'llm_provider', 'checksum')
    @classmethod
    def validate_text_fields(cls, v):
        """Validate and sanitize text fields."""
        if v is not None:
            return sanitize_text(v)
        return v


class ConversionResult(BaseModel):
    """Result of format conversion."""
    success: bool
    converted_content: str
    target_format: str
    conversion_notes: List[str]
    error: Optional[str] = None
    
    @field_validator('converted_content', 'target_format')
    @classmethod
    def validate_text_fields(cls, v):
        """Validate and sanitize text fields."""
        return sanitize_text(v)
    
    @field_validator('conversion_notes')
    @classmethod
    def validate_notes(cls, v):
        """Validate and sanitize notes list."""
        return [sanitize_text(note) for note in v if note.strip()]


class IDEFormatDetectionResult(BaseModel):
    """Result of IDE format detection."""
    detected_ide: str
    confidence: float = Field(ge=0.0, le=1.0)
    format_indicators: List[str]
    supported: bool
    
    @field_validator('detected_ide')
    @classmethod
    def validate_ide(cls, v):
        """Validate and sanitize IDE field."""
        return sanitize_text(v)
    
    @field_validator('format_indicators')
    @classmethod
    def validate_indicators(cls, v):
        """Validate and sanitize indicators list."""
        return [sanitize_text(indicator) for indicator in v if indicator.strip()]
