"""LLM response models and validation for personality analysis."""

import json
from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, field_validator, ValidationError
from .core import (
    PersonalityProfile, 
    PersonalityTrait, 
    CommunicationStyle, 
    ResearchSource,
    PersonalityType,
    FormalityLevel,
    VerbosityLevel,
    TechnicalLevel
)
from ..utils.validation import sanitize_text


class LLMTrait(BaseModel):
    """Individual personality trait from LLM analysis."""
    trait: str = Field(..., description="Trait name")
    intensity: int = Field(..., ge=1, le=10, description="Trait intensity 1-10")
    description: str = Field(..., description="Trait explanation")
    
    @field_validator('trait', 'description')
    @classmethod
    def validate_text_fields(cls, v):
        """Validate and sanitize text fields."""
        return sanitize_text(v)


class LLMCommunicationStyle(BaseModel):
    """Communication style from LLM analysis."""
    tone: str = Field(..., description="Overall tone")
    formality: str = Field(..., description="casual, formal, or mixed")
    verbosity: str = Field(..., description="concise, moderate, or verbose")
    technical_level: str = Field(..., description="beginner, intermediate, or expert")
    
    @field_validator('tone')
    @classmethod
    def validate_tone(cls, v):
        """Validate and sanitize tone field."""
        return sanitize_text(v)
    
    @field_validator('formality')
    @classmethod
    def validate_formality(cls, v):
        """Validate formality level."""
        v = sanitize_text(v).lower()
        valid_values = ['casual', 'formal', 'mixed']
        if v not in valid_values:
            raise ValueError(f"Formality must be one of: {', '.join(valid_values)}")
        return v
    
    @field_validator('verbosity')
    @classmethod
    def validate_verbosity(cls, v):
        """Validate verbosity level."""
        v = sanitize_text(v).lower()
        valid_values = ['concise', 'moderate', 'verbose']
        if v not in valid_values:
            raise ValueError(f"Verbosity must be one of: {', '.join(valid_values)}")
        return v
    
    @field_validator('technical_level')
    @classmethod
    def validate_technical_level(cls, v):
        """Validate technical level."""
        v = sanitize_text(v).lower()
        valid_values = ['beginner', 'intermediate', 'expert']
        if v not in valid_values:
            raise ValueError(f"Technical level must be one of: {', '.join(valid_values)}")
        return v


class LLMPersonalityResponse(BaseModel):
    """Structured response from LLM personality analysis."""
    name: str = Field(..., description="Personality name or title")
    type: str = Field(..., description="celebrity, fictional, archetype, or custom")
    description: str = Field(..., description="Brief personality description")
    traits: List[LLMTrait] = Field(..., description="List of personality traits")
    communication_style: LLMCommunicationStyle = Field(..., description="Communication preferences")
    mannerisms: List[str] = Field(default_factory=list, description="Behavioral patterns")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Analysis confidence score")
    
    @field_validator('name', 'description')
    @classmethod
    def validate_text_fields(cls, v):
        """Validate and sanitize text fields."""
        return sanitize_text(v)
    
    @field_validator('type')
    @classmethod
    def validate_type(cls, v):
        """Validate personality type."""
        v = sanitize_text(v).lower()
        valid_types = ['celebrity', 'fictional', 'archetype', 'custom']
        if v not in valid_types:
            raise ValueError(f"Type must be one of: {', '.join(valid_types)}")
        return v
    
    @field_validator('mannerisms')
    @classmethod
    def validate_mannerisms(cls, v):
        """Validate and sanitize mannerisms list."""
        return [sanitize_text(mannerism) for mannerism in v if mannerism.strip()]
    
    @field_validator('traits')
    @classmethod
    def validate_traits_not_empty(cls, v):
        """Ensure at least one trait is provided."""
        if not v:
            raise ValueError("At least one trait must be provided")
        return v


class LLMValidationError(Exception):
    """Error raised when LLM response validation fails."""
    
    def __init__(self, message: str, raw_response: str, validation_errors: List[str]):
        self.message = message
        self.raw_response = raw_response
        self.validation_errors = validation_errors
        super().__init__(message)


class LLMParsingError(Exception):
    """Error raised when LLM response cannot be parsed as JSON."""
    
    def __init__(self, message: str, raw_response: str):
        self.message = message
        self.raw_response = raw_response
        super().__init__(message)


async def parse_llm_response(response_text: str) -> Dict[str, Any]:
    """Parse LLM response text as JSON.
    
    Args:
        response_text: Raw text response from LLM
        
    Returns:
        Parsed JSON data as dictionary
        
    Raises:
        LLMParsingError: If response cannot be parsed as JSON
    """
    if not response_text or not response_text.strip():
        raise LLMParsingError("Empty response from LLM", response_text)
    
    # Try to extract JSON from response if it contains extra text
    response_text = response_text.strip()
    
    # Look for JSON block markers
    if "```json" in response_text:
        start = response_text.find("```json") + 7
        end = response_text.find("```", start)
        if end != -1:
            response_text = response_text[start:end].strip()
    elif "```" in response_text:
        start = response_text.find("```") + 3
        end = response_text.find("```", start)
        if end != -1:
            response_text = response_text[start:end].strip()
    
    # Look for JSON object boundaries
    if not response_text.startswith('{'):
        start = response_text.find('{')
        if start != -1:
            response_text = response_text[start:]
    
    if not response_text.endswith('}'):
        end = response_text.rfind('}')
        if end != -1:
            response_text = response_text[:end + 1]
    
    try:
        return json.loads(response_text)
    except json.JSONDecodeError as e:
        raise LLMParsingError(f"Failed to parse JSON: {str(e)}", response_text)


async def validate_llm_response(response_text: str) -> LLMPersonalityResponse:
    """Validate and parse LLM response into structured format.
    
    Args:
        response_text: Raw text response from LLM
        
    Returns:
        Validated LLMPersonalityResponse object
        
    Raises:
        LLMParsingError: If response cannot be parsed as JSON
        LLMValidationError: If response structure is invalid
    """
    try:
        # Parse JSON from response
        response_data = await parse_llm_response(response_text)
        
        # Validate structure using Pydantic model
        return LLMPersonalityResponse(**response_data)
        
    except ValidationError as e:
        error_messages = []
        for error in e.errors():
            field = " -> ".join(str(loc) for loc in error['loc'])
            error_messages.append(f"{field}: {error['msg']}")
        
        raise LLMValidationError(
            f"LLM response validation failed: {'; '.join(error_messages)}",
            response_text,
            error_messages
        )


async def convert_llm_to_profile(
    llm_response: LLMPersonalityResponse,
    profile_id: str,
    llm_provider: str = "unknown",
    llm_model: str = "unknown"
) -> PersonalityProfile:
    """Convert LLM response to internal PersonalityProfile format.
    
    Args:
        llm_response: Validated LLM response
        profile_id: Unique identifier for the profile
        llm_provider: Name of the LLM provider used
        llm_model: Name of the specific model used
        
    Returns:
        PersonalityProfile object compatible with existing system
    """
    # Convert LLM traits to PersonalityTrait format
    personality_traits = []
    for llm_trait in llm_response.traits:
        # Group traits by category (use trait name as category for now)
        trait_category = llm_trait.trait.split()[0] if llm_trait.trait else "General"
        
        personality_trait = PersonalityTrait(
            category=trait_category,
            trait=llm_trait.trait,
            intensity=llm_trait.intensity,
            examples=[llm_trait.description]  # Use description as example
        )
        personality_traits.append(personality_trait)
    
    # Convert LLM communication style to CommunicationStyle format
    communication_style = CommunicationStyle(
        tone=llm_response.communication_style.tone,
        formality=FormalityLevel(llm_response.communication_style.formality),
        verbosity=VerbosityLevel(llm_response.communication_style.verbosity),
        technical_level=TechnicalLevel(llm_response.communication_style.technical_level)
    )
    
    # Create research source for LLM analysis
    research_source = ResearchSource(
        type="llm_analysis",
        url=None,
        confidence=llm_response.confidence,
        last_updated=datetime.now()
    )
    
    # Convert personality type
    personality_type = PersonalityType(llm_response.type)
    
    return PersonalityProfile(
        id=profile_id,
        name=llm_response.name,
        type=personality_type,
        traits=personality_traits,
        communication_style=communication_style,
        mannerisms=llm_response.mannerisms,
        sources=[research_source]
    )


async def repair_llm_response(response_text: str) -> Optional[str]:
    """Attempt to repair malformed LLM response.
    
    Args:
        response_text: Raw text response from LLM that failed validation
        
    Returns:
        Repaired response text or None if repair is not possible
    """
    if not response_text or not response_text.strip():
        return None
    
    response_text = response_text.strip()
    
    # Try to fix common JSON issues
    try:
        # Remove trailing commas
        response_text = response_text.replace(',}', '}').replace(',]', ']')
        
        # Try to balance braces
        open_braces = response_text.count('{')
        close_braces = response_text.count('}')
        
        if open_braces > close_braces:
            response_text += '}' * (open_braces - close_braces)
        elif close_braces > open_braces:
            # Remove extra closing braces from the end
            extra_braces = close_braces - open_braces
            for _ in range(extra_braces):
                last_brace = response_text.rfind('}')
                if last_brace != -1:
                    response_text = response_text[:last_brace] + response_text[last_brace + 1:]
        
        # Try to parse the repaired response
        json.loads(response_text)
        return response_text
        
    except json.JSONDecodeError:
        return None


async def validate_and_repair_llm_response(response_text: str) -> LLMPersonalityResponse:
    """Validate LLM response with automatic repair attempts.
    
    Args:
        response_text: Raw text response from LLM
        
    Returns:
        Validated LLMPersonalityResponse object
        
    Raises:
        LLMParsingError: If response cannot be parsed as JSON
        LLMValidationError: If response structure is invalid after repair attempts
    """
    try:
        # First attempt: validate as-is
        return await validate_llm_response(response_text)
    except (LLMParsingError, LLMValidationError):
        # Second attempt: try to repair and validate
        repaired_response = await repair_llm_response(response_text)
        if repaired_response:
            try:
                return await validate_llm_response(repaired_response)
            except (LLMParsingError, LLMValidationError):
                pass
        
        # If repair failed, raise the original error
        raise