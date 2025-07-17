"""Functional validation utilities for personality descriptions and API requests."""

import re
from typing import List, Optional, Tuple
from datetime import datetime


def sanitize_text(text: str) -> str:
    """Sanitize input text by removing harmful characters and normalizing whitespace."""
    if not text:
        return ""
    
    # Remove potential script tags and normalize whitespace
    sanitized = re.sub(r'<[^>]*>', '', text)
    sanitized = re.sub(r'\s+', ' ', sanitized)
    return sanitized.strip()


def validate_personality_description(description: str) -> Tuple[bool, List[str]]:
    """
    Validate personality description input.
    
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    if not description or not description.strip():
        errors.append("Personality description cannot be empty")
        return False, errors
    
    sanitized = sanitize_text(description)
    
    if len(sanitized) < 3:
        errors.append("Personality description must be at least 3 characters long")
    
    if len(sanitized) > 500:
        errors.append("Personality description must be less than 500 characters")
    
    return len(errors) == 0, errors


def validate_personality_name(name: str) -> Tuple[bool, List[str]]:
    """
    Validate personality name input.
    
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    if not name or not name.strip():
        errors.append("Personality name cannot be empty")
        return False, errors
    
    sanitized = sanitize_text(name)
    
    if len(sanitized) < 2:
        errors.append("Personality name must be at least 2 characters long")
    
    if len(sanitized) > 100:
        errors.append("Personality name must be less than 100 characters")
    
    return len(errors) == 0, errors


def validate_trait_intensity(intensity: int) -> Tuple[bool, List[str]]:
    """
    Validate trait intensity value.
    
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    if not isinstance(intensity, int):
        errors.append("Trait intensity must be an integer")
        return False, errors
    
    if intensity < 1 or intensity > 10:
        errors.append("Trait intensity must be between 1 and 10")
    
    return len(errors) == 0, errors


def detect_personality_type(description: str) -> Optional[str]:
    """
    Attempt to detect personality type from description.
    
    Returns:
        Detected type or None if unclear
    """
    description_lower = description.lower()
    
    # Celebrity indicators
    celebrity_indicators = [
        'actor', 'actress', 'singer', 'musician', 'politician', 'scientist',
        'author', 'writer', 'director', 'artist', 'athlete', 'celebrity'
    ]
    
    # Fictional character indicators
    fictional_indicators = [
        'character', 'from', 'movie', 'book', 'tv show', 'series', 'novel',
        'comic', 'anime', 'manga', 'game', 'fictional'
    ]
    
    # Archetype indicators
    archetype_indicators = [
        'cowboy', 'robot', 'drill sergeant', 'mentor', 'teacher', 'coach',
        'pirate', 'knight', 'wizard', 'detective', 'scientist', 'rebel'
    ]
    
    for indicator in celebrity_indicators:
        if indicator in description_lower:
            return "celebrity"
    
    for indicator in fictional_indicators:
        if indicator in description_lower:
            return "fictional"
    
    for indicator in archetype_indicators:
        if indicator in description_lower:
            return "archetype"
    
    return None


def validate_url(url: Optional[str]) -> Tuple[bool, List[str]]:
    """
    Validate URL format if provided.
    
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    if url is None:
        return True, errors
    
    if not isinstance(url, str):
        errors.append("URL must be a string")
        return False, errors
    
    # Basic URL validation
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    if not url_pattern.match(url):
        errors.append("Invalid URL format")
    
    return len(errors) == 0, errors
