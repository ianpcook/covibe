"""Unit tests for validation utilities."""

import pytest
from datetime import datetime, timedelta
from covibe.utils.validation import (
    sanitize_text,
    validate_personality_description,
    validate_personality_name,
    validate_trait_intensity,
    detect_personality_type,
)


def test_sanitize_text():
    """Test text sanitization function."""
    assert sanitize_text("") == ""
    assert sanitize_text("Hello world") == "Hello world"
    assert sanitize_text("Hello <script>alert('xss')</script> world") == "Hello alert('xss') world"
    assert sanitize_text("Hello    \n\t  world") == "Hello world"
    assert sanitize_text("  Hello world  ") == "Hello world"


def test_validate_personality_description():
    """Test personality description validation."""
    # Valid description
    is_valid, errors = validate_personality_description("Like Tony Stark but more patient")
    assert is_valid is True
    assert errors == []
    
    # Empty description
    is_valid, errors = validate_personality_description("")
    assert is_valid is False
    assert "cannot be empty" in errors[0]
    
    # Too short
    is_valid, errors = validate_personality_description("Hi")
    assert is_valid is False
    assert "at least 3 characters" in errors[0]


def test_validate_personality_name():
    """Test personality name validation."""
    # Valid name
    is_valid, errors = validate_personality_name("Sherlock Holmes")
    assert is_valid is True
    assert errors == []
    
    # Empty name
    is_valid, errors = validate_personality_name("")
    assert is_valid is False
    assert "cannot be empty" in errors[0]


def test_validate_trait_intensity():
    """Test trait intensity validation."""
    # Valid intensity
    is_valid, errors = validate_trait_intensity(5)
    assert is_valid is True
    assert errors == []
    
    # Invalid intensity
    is_valid, errors = validate_trait_intensity(0)
    assert is_valid is False
    assert "between 1 and 10" in errors[0]


def test_detect_personality_type():
    """Test personality type detection."""
    assert detect_personality_type("The famous actor Robert Downey Jr.") == "celebrity"
    assert detect_personality_type("Sherlock Holmes from the books") == "fictional"
    assert detect_personality_type("A wise mentor figure") == "archetype"
    assert detect_personality_type("Someone who is very smart") is None
