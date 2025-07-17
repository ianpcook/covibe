"""Unit tests for validation utilities."""

import pytest
from datetime import datetime, timedelta
from covibe.utils.validation import (
    sanitize_text,
    validate_personality_description,
    validate_personality_name,
    validate_trait_intensity,
    validate_confidence_score,
    validate_url,
    is_valid_timestamp,
    detect_personality_type,
)


class TestSanitizeText:
    """Tests for text sanitization function."""
    
    def test_sanitize_empty_string(self):
        assert sanitize_text("") == ""
    
    def test_sanitize_normal_text(self):
        assert sanitize_text("Hello world") == "Hello world"
    
    def test_sanitize_removes_html_tags(self):
        assert sanitize_text("Hello <script>alert('xss')</script> world") == "Hello  world"
    
    def test_sanitize_normalizes_whitespace(self):
        assert sanitize_text("Hello    \n\t  world") == "Hello world"
    
    def test_sanitize_strips_whitespace(self):
        assert sanitize_text("  Hello world  ") == "Hello world"


class TestValidatePersonalityDescription:
    """Tests for personality description validation."""
    
    def test_valid_description(self):
        is_valid, errors = validate_personality_description("Like Tony Stark but more patient")
        assert is_valid is True
        assert errors == []
    
    def test_empty_description(self):
        is_valid, errors = validate_personality_description("")
        assert is_valid is False
        assert "cannot be empty" in errors[0]
    
    def test_whitespace_only_description(self):
        is_valid, errors = validate_personality_description("   ")
        assert is_valid is False
        assert "cannot be empty" in errors[0]
    
    def test_too_short_description(self):
        is_valid, errors = validate_personality_description("Hi")
        assert is_valid is False
        assert "at least 3 characters" in errors[0]
    
    def test_too_long_description(self):
        long_text = "a" * 501
        is_valid, errors = validate_personality_description(long_text)
        assert is_valid is False
        assert "less than 500 characters" in errors[0]
    
    def test_suspicious_content(self):
        is_valid, errors = validate_personality_description("javascript:alert('xss')")
        assert is_valid is False
        assert "invalid content" in errors[0]


class TestValidatePersonalityName:
    """Tests for personality name validation."""
    
    def test_valid_name(self):
        is_valid, errors = validate_personality_name("Sherlock Holmes")
        assert is_valid is True
        assert errors == []
    
    def test_empty_name(self):
        is_valid, errors = validate_personality_name("")
        assert is_valid is False
        assert "cannot be empty" in errors[0]
    
    def test_too_short_name(self):
        is_valid, errors = validate_personality_name("A")
        assert is_valid is False
        assert "at least 2 characters" in errors[0]
    
    def test_too_long_name(self):
        long_name = "a" * 101
        is_valid, errors = validate_personality_name(long_name)
        assert is_valid is False
        assert "less than 100 characters" in errors[0]
    
    def test_invalid_characters(self):
        is_valid, errors = validate_personality_name("Name@#$%")
        assert is_valid is False
        assert "invalid characters" in errors[0]
    
    def test_valid_characters_with_punctuation(self):
        is_valid, errors = validate_personality_name("Dr. John Watson-Smith, Jr.")
        assert is_valid is True
        assert errors == []


class TestValidateTraitIntensity:
    """Tests for trait intensity validation."""
    
    def test_valid_intensity(self):
        is_valid, errors = validate_trait_intensity(5)
        assert is_valid is True
        assert errors == []
    
    def test_minimum_intensity(self):
        is_valid, errors = validate_trait_intensity(1)
        assert is_valid is True
        assert errors == []
    
    def test_maximum_intensity(self):
        is_valid, errors = validate_trait_intensity(10)
        assert is_valid is True
        assert errors == []
    
    def test_too_low_intensity(self):
        is_valid, errors = validate_trait_intensity(0)
        assert is_valid is False
        assert "between 1 and 10" in errors[0]
    
    def test_too_high_intensity(self):
        is_valid, errors = validate_trait_intensity(11)
        assert is_valid is False
        assert "between 1 and 10" in errors[0]
    
    def test_non_integer_intensity(self):
        is_valid, errors = validate_trait_intensity(5.5)
        assert is_valid is False
        assert "must be an integer" in errors[0]


class TestValidateConfidenceScore:
    """Tests for confidence score validation."""
    
    def test_valid_confidence(self):
        is_valid, errors = validate_confidence_score(0.75)
        assert is_valid is True
        assert errors == []
    
    def test_minimum_confidence(self):
        is_valid, errors = validate_confidence_score(0.0)
        assert is_valid is True
        assert errors == []
    
    def test_maximum_confidence(self):
        is_valid, errors = validate_confidence_score(1.0)
        assert is_valid is True
        assert errors == []
    
    def test_too_low_confidence(self):
        is_valid, errors = validate_confidence_score(-0.1)
        assert is_valid is False
        assert "between 0.0 and 1.0" in errors[0]
    
    def test_too_high_confidence(self):
        is_valid, errors = validate_confidence_score(1.1)
        assert is_valid is False
        assert "between 0.0 and 1.0" in errors[0]
    
    def test_integer_confidence(self):
        is_valid, errors = validate_confidence_score(1)
        assert is_valid is True
        assert errors == []


class TestValidateUrl:
    """Tests for URL validation."""
    
    def test_valid_https_url(self):
        is_valid, errors = validate_url("https://example.com")
        assert is_valid is True
        assert errors == []
    
    def test_valid_http_url(self):
        is_valid, errors = validate_url("http://example.com")
        assert is_valid is True
        assert errors == []
    
    def test_none_url(self):
        is_valid, errors = validate_url(None)
        assert is_valid is True
        assert errors == []
    
    def test_invalid_url_format(self):
        is_valid, errors = validate_url("not-a-url")
        assert is_valid is False
        assert "Invalid URL format" in errors[0]
    
    def test_non_string_url(self):
        is_valid, errors = validate_url(123)
        assert is_valid is False
        assert "must be a string" in errors[0]


class TestIsValidTimestamp:
    """Tests for timestamp validation."""
    
    def test_valid_current_timestamp(self):
        now = datetime.now()
        assert is_valid_timestamp(now) is True
    
    def test_valid_past_timestamp(self):
        past = datetime.now() - timedelta(hours=1)
        assert is_valid_timestamp(past) is True
    
    def test_invalid_future_timestamp(self):
        future = datetime.now() + timedelta(hours=1)
        assert is_valid_timestamp(future) is False
    
    def test_non_datetime_input(self):
        assert is_valid_timestamp("not-a-datetime") is False


class TestDetectPersonalityType:
    """Tests for personality type detection."""
    
    def test_detect_celebrity(self):
        result = detect_personality_type("The famous actor Robert Downey Jr.")
        assert result == "celebrity"
    
    def test_detect_fictional(self):
        result = detect_personality_type("Sherlock Holmes from the books")
        assert result == "fictional"
    
    def test_detect_archetype(self):
        result = detect_personality_type("A wise mentor figure")
        assert result == "archetype"
    
    def test_detect_unclear(self):
        result = detect_personality_type("Someone who is very smart")
        assert result is None
    
    def test_detect_case_insensitive(self):
        result = detect_personality_type("ACTOR from movies")
        assert result == "celebrity"