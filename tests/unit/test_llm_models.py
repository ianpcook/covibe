"""Unit tests for LLM response validation models and functions."""

import json
import pytest
from datetime import datetime
from pydantic import ValidationError

from src.covibe.models.llm import (
    LLMTrait,
    LLMCommunicationStyle,
    LLMPersonalityResponse,
    LLMValidationError,
    LLMParsingError,
    parse_llm_response,
    validate_llm_response,
    convert_llm_to_profile,
    repair_llm_response,
    validate_and_repair_llm_response
)
from src.covibe.models.core import PersonalityType, FormalityLevel, VerbosityLevel, TechnicalLevel


class TestLLMTrait:
    """Test LLMTrait model validation."""
    
    def test_valid_trait(self):
        """Test creating a valid LLMTrait."""
        trait = LLMTrait(
            trait="Analytical",
            intensity=8,
            description="Enjoys breaking down complex problems"
        )
        assert trait.trait == "Analytical"
        assert trait.intensity == 8
        assert trait.description == "Enjoys breaking down complex problems"
    
    def test_trait_intensity_validation(self):
        """Test trait intensity must be between 1-10."""
        # Test valid intensities
        for intensity in [1, 5, 10]:
            trait = LLMTrait(
                trait="Test",
                intensity=intensity,
                description="Test description"
            )
            assert trait.intensity == intensity
        
        # Test invalid intensities
        for intensity in [0, 11, -1]:
            with pytest.raises(ValidationError):
                LLMTrait(
                    trait="Test",
                    intensity=intensity,
                    description="Test description"
                )
    
    def test_trait_text_sanitization(self):
        """Test that text fields are sanitized."""
        trait = LLMTrait(
            trait="  Analytical  ",
            intensity=5,
            description="  Test description  "
        )
        assert trait.trait == "Analytical"
        assert trait.description == "Test description"


class TestLLMCommunicationStyle:
    """Test LLMCommunicationStyle model validation."""
    
    def test_valid_communication_style(self):
        """Test creating a valid LLMCommunicationStyle."""
        style = LLMCommunicationStyle(
            tone="Professional",
            formality="formal",
            verbosity="moderate",
            technical_level="expert"
        )
        assert style.tone == "Professional"
        assert style.formality == "formal"
        assert style.verbosity == "moderate"
        assert style.technical_level == "expert"
    
    def test_formality_validation(self):
        """Test formality level validation."""
        valid_values = ['casual', 'formal', 'mixed']
        
        for value in valid_values:
            style = LLMCommunicationStyle(
                tone="Test",
                formality=value,
                verbosity="moderate",
                technical_level="intermediate"
            )
            assert style.formality == value
        
        # Test case insensitive
        style = LLMCommunicationStyle(
            tone="Test",
            formality="FORMAL",
            verbosity="moderate",
            technical_level="intermediate"
        )
        assert style.formality == "formal"
        
        # Test invalid value
        with pytest.raises(ValidationError):
            LLMCommunicationStyle(
                tone="Test",
                formality="invalid",
                verbosity="moderate",
                technical_level="intermediate"
            )
    
    def test_verbosity_validation(self):
        """Test verbosity level validation."""
        valid_values = ['concise', 'moderate', 'verbose']
        
        for value in valid_values:
            style = LLMCommunicationStyle(
                tone="Test",
                formality="casual",
                verbosity=value,
                technical_level="intermediate"
            )
            assert style.verbosity == value
        
        # Test invalid value
        with pytest.raises(ValidationError):
            LLMCommunicationStyle(
                tone="Test",
                formality="casual",
                verbosity="invalid",
                technical_level="intermediate"
            )
    
    def test_technical_level_validation(self):
        """Test technical level validation."""
        valid_values = ['beginner', 'intermediate', 'expert']
        
        for value in valid_values:
            style = LLMCommunicationStyle(
                tone="Test",
                formality="casual",
                verbosity="moderate",
                technical_level=value
            )
            assert style.technical_level == value
        
        # Test invalid value
        with pytest.raises(ValidationError):
            LLMCommunicationStyle(
                tone="Test",
                formality="casual",
                verbosity="moderate",
                technical_level="invalid"
            )


class TestLLMPersonalityResponse:
    """Test LLMPersonalityResponse model validation."""
    
    def test_valid_personality_response(self):
        """Test creating a valid LLMPersonalityResponse."""
        response = LLMPersonalityResponse(
            name="Sherlock Holmes",
            type="fictional",
            description="Brilliant detective with analytical mind",
            traits=[
                LLMTrait(trait="Analytical", intensity=9, description="Logical thinker"),
                LLMTrait(trait="Observant", intensity=10, description="Notices details")
            ],
            communication_style=LLMCommunicationStyle(
                tone="Direct",
                formality="formal",
                verbosity="concise",
                technical_level="expert"
            ),
            mannerisms=["Uses deductive reasoning", "Speaks precisely"],
            confidence=0.95
        )
        
        assert response.name == "Sherlock Holmes"
        assert response.type == "fictional"
        assert len(response.traits) == 2
        assert response.confidence == 0.95
    
    def test_personality_type_validation(self):
        """Test personality type validation."""
        valid_types = ['celebrity', 'fictional', 'archetype', 'custom']
        
        for ptype in valid_types:
            response = LLMPersonalityResponse(
                name="Test",
                type=ptype,
                description="Test description",
                traits=[LLMTrait(trait="Test", intensity=5, description="Test")],
                communication_style=LLMCommunicationStyle(
                    tone="Test", formality="casual", verbosity="moderate", technical_level="intermediate"
                ),
                confidence=0.8
            )
            assert response.type == ptype
        
        # Test case insensitive
        response = LLMPersonalityResponse(
            name="Test",
            type="FICTIONAL",
            description="Test description",
            traits=[LLMTrait(trait="Test", intensity=5, description="Test")],
            communication_style=LLMCommunicationStyle(
                tone="Test", formality="casual", verbosity="moderate", technical_level="intermediate"
            ),
            confidence=0.8
        )
        assert response.type == "fictional"
        
        # Test invalid type
        with pytest.raises(ValidationError):
            LLMPersonalityResponse(
                name="Test",
                type="invalid",
                description="Test description",
                traits=[LLMTrait(trait="Test", intensity=5, description="Test")],
                communication_style=LLMCommunicationStyle(
                    tone="Test", formality="casual", verbosity="moderate", technical_level="intermediate"
                ),
                confidence=0.8
            )
    
    def test_confidence_validation(self):
        """Test confidence score validation."""
        # Test valid confidence values
        for confidence in [0.0, 0.5, 1.0]:
            response = LLMPersonalityResponse(
                name="Test",
                type="custom",
                description="Test description",
                traits=[LLMTrait(trait="Test", intensity=5, description="Test")],
                communication_style=LLMCommunicationStyle(
                    tone="Test", formality="casual", verbosity="moderate", technical_level="intermediate"
                ),
                confidence=confidence
            )
            assert response.confidence == confidence
        
        # Test invalid confidence values
        for confidence in [-0.1, 1.1, 2.0]:
            with pytest.raises(ValidationError):
                LLMPersonalityResponse(
                    name="Test",
                    type="custom",
                    description="Test description",
                    traits=[LLMTrait(trait="Test", intensity=5, description="Test")],
                    communication_style=LLMCommunicationStyle(
                        tone="Test", formality="casual", verbosity="moderate", technical_level="intermediate"
                    ),
                    confidence=confidence
                )
    
    def test_traits_not_empty_validation(self):
        """Test that at least one trait is required."""
        with pytest.raises(ValidationError):
            LLMPersonalityResponse(
                name="Test",
                type="custom",
                description="Test description",
                traits=[],  # Empty traits list
                communication_style=LLMCommunicationStyle(
                    tone="Test", formality="casual", verbosity="moderate", technical_level="intermediate"
                ),
                confidence=0.8
            )
    
    def test_mannerisms_sanitization(self):
        """Test that mannerisms are sanitized and empty ones removed."""
        response = LLMPersonalityResponse(
            name="Test",
            type="custom",
            description="Test description",
            traits=[LLMTrait(trait="Test", intensity=5, description="Test")],
            communication_style=LLMCommunicationStyle(
                tone="Test", formality="casual", verbosity="moderate", technical_level="intermediate"
            ),
            mannerisms=["  Valid mannerism  ", "", "   ", "Another valid one"],
            confidence=0.8
        )
        
        assert response.mannerisms == ["Valid mannerism", "Another valid one"]


class TestLLMResponseParsing:
    """Test LLM response parsing functions."""
    
    @pytest.mark.asyncio
    async def test_parse_valid_json(self):
        """Test parsing valid JSON response."""
        json_data = {"name": "Test", "type": "custom"}
        response_text = json.dumps(json_data)
        
        result = await parse_llm_response(response_text)
        assert result == json_data
    
    @pytest.mark.asyncio
    async def test_parse_json_with_markdown(self):
        """Test parsing JSON wrapped in markdown code blocks."""
        json_data = {"name": "Test", "type": "custom"}
        response_text = f"Here's the analysis:\n```json\n{json.dumps(json_data)}\n```\nThat's it!"
        
        result = await parse_llm_response(response_text)
        assert result == json_data
    
    @pytest.mark.asyncio
    async def test_parse_json_with_generic_code_blocks(self):
        """Test parsing JSON wrapped in generic code blocks."""
        json_data = {"name": "Test", "type": "custom"}
        response_text = f"Analysis:\n```\n{json.dumps(json_data)}\n```"
        
        result = await parse_llm_response(response_text)
        assert result == json_data
    
    @pytest.mark.asyncio
    async def test_parse_json_with_extra_text(self):
        """Test parsing JSON with extra text around it."""
        json_data = {"name": "Test", "type": "custom"}
        response_text = f"Here's my analysis: {json.dumps(json_data)} Hope this helps!"
        
        result = await parse_llm_response(response_text)
        assert result == json_data
    
    @pytest.mark.asyncio
    async def test_parse_empty_response(self):
        """Test parsing empty response raises error."""
        with pytest.raises(LLMParsingError):
            await parse_llm_response("")
        
        with pytest.raises(LLMParsingError):
            await parse_llm_response("   ")
    
    @pytest.mark.asyncio
    async def test_parse_invalid_json(self):
        """Test parsing invalid JSON raises error."""
        with pytest.raises(LLMParsingError):
            await parse_llm_response("This is not JSON")
        
        with pytest.raises(LLMParsingError):
            await parse_llm_response('{"invalid": json}')


class TestLLMResponseValidation:
    """Test LLM response validation functions."""
    
    def create_valid_response_data(self):
        """Create valid response data for testing."""
        return {
            "name": "Sherlock Holmes",
            "type": "fictional",
            "description": "Brilliant detective",
            "traits": [
                {"trait": "Analytical", "intensity": 9, "description": "Logical thinker"}
            ],
            "communication_style": {
                "tone": "Direct",
                "formality": "formal",
                "verbosity": "concise",
                "technical_level": "expert"
            },
            "mannerisms": ["Uses deductive reasoning"],
            "confidence": 0.95
        }
    
    @pytest.mark.asyncio
    async def test_validate_valid_response(self):
        """Test validating a valid LLM response."""
        response_data = self.create_valid_response_data()
        response_text = json.dumps(response_data)
        
        result = await validate_llm_response(response_text)
        
        assert isinstance(result, LLMPersonalityResponse)
        assert result.name == "Sherlock Holmes"
        assert result.type == "fictional"
        assert len(result.traits) == 1
        assert result.confidence == 0.95
    
    @pytest.mark.asyncio
    async def test_validate_invalid_json(self):
        """Test validating invalid JSON raises parsing error."""
        with pytest.raises(LLMParsingError):
            await validate_llm_response("invalid json")
    
    @pytest.mark.asyncio
    async def test_validate_invalid_structure(self):
        """Test validating invalid structure raises validation error."""
        response_data = {"name": "Test"}  # Missing required fields
        response_text = json.dumps(response_data)
        
        with pytest.raises(LLMValidationError) as exc_info:
            await validate_llm_response(response_text)
        
        assert "validation failed" in str(exc_info.value)
        assert len(exc_info.value.validation_errors) > 0
    
    @pytest.mark.asyncio
    async def test_validate_invalid_trait_intensity(self):
        """Test validating invalid trait intensity."""
        response_data = self.create_valid_response_data()
        response_data["traits"][0]["intensity"] = 15  # Invalid intensity
        response_text = json.dumps(response_data)
        
        with pytest.raises(LLMValidationError):
            await validate_llm_response(response_text)
    
    @pytest.mark.asyncio
    async def test_validate_invalid_confidence(self):
        """Test validating invalid confidence score."""
        response_data = self.create_valid_response_data()
        response_data["confidence"] = 1.5  # Invalid confidence
        response_text = json.dumps(response_data)
        
        with pytest.raises(LLMValidationError):
            await validate_llm_response(response_text)


class TestLLMToProfileConversion:
    """Test conversion from LLM response to PersonalityProfile."""
    
    def create_llm_response(self):
        """Create a sample LLM response for testing."""
        return LLMPersonalityResponse(
            name="Sherlock Holmes",
            type="fictional",
            description="Brilliant detective with analytical mind",
            traits=[
                LLMTrait(trait="Analytical", intensity=9, description="Logical problem solver"),
                LLMTrait(trait="Observant", intensity=10, description="Notices small details")
            ],
            communication_style=LLMCommunicationStyle(
                tone="Direct and precise",
                formality="formal",
                verbosity="concise",
                technical_level="expert"
            ),
            mannerisms=["Uses deductive reasoning", "Speaks with authority"],
            confidence=0.95
        )
    
    @pytest.mark.asyncio
    async def test_convert_llm_to_profile(self):
        """Test converting LLM response to PersonalityProfile."""
        llm_response = self.create_llm_response()
        profile_id = "test-profile-123"
        
        profile = await convert_llm_to_profile(
            llm_response, 
            profile_id, 
            llm_provider="openai", 
            llm_model="gpt-4"
        )
        
        # Check basic profile properties
        assert profile.id == profile_id
        assert profile.name == "Sherlock Holmes"
        assert profile.type == PersonalityType.FICTIONAL
        
        # Check traits conversion
        assert len(profile.traits) == 2
        analytical_trait = next(t for t in profile.traits if t.trait == "Analytical")
        assert analytical_trait.intensity == 9
        assert "Logical problem solver" in analytical_trait.examples
        
        # Check communication style conversion
        assert profile.communication_style.tone == "Direct and precise"
        assert profile.communication_style.formality == FormalityLevel.FORMAL
        assert profile.communication_style.verbosity == VerbosityLevel.CONCISE
        assert profile.communication_style.technical_level == TechnicalLevel.EXPERT
        
        # Check mannerisms
        assert profile.mannerisms == ["Uses deductive reasoning", "Speaks with authority"]
        
        # Check research source
        assert len(profile.sources) == 1
        source = profile.sources[0]
        assert source.type == "llm_analysis"
        assert source.confidence == 0.95
        assert source.url is None
    
    @pytest.mark.asyncio
    async def test_convert_trait_categorization(self):
        """Test that traits are properly categorized."""
        llm_response = LLMPersonalityResponse(
            name="Test",
            type="custom",
            description="Test personality",
            traits=[
                LLMTrait(trait="Creative Problem Solver", intensity=8, description="Thinks outside the box"),
                LLMTrait(trait="Detail Oriented", intensity=7, description="Pays attention to specifics")
            ],
            communication_style=LLMCommunicationStyle(
                tone="Friendly", formality="casual", verbosity="moderate", technical_level="intermediate"
            ),
            confidence=0.8
        )
        
        profile = await convert_llm_to_profile(llm_response, "test-id")
        
        # Check that trait categories are derived from trait names
        creative_trait = next(t for t in profile.traits if t.trait == "Creative Problem Solver")
        assert creative_trait.category == "Creative"
        
        detail_trait = next(t for t in profile.traits if t.trait == "Detail Oriented")
        assert detail_trait.category == "Detail"


class TestLLMResponseRepair:
    """Test LLM response repair functionality."""
    
    @pytest.mark.asyncio
    async def test_repair_trailing_comma(self):
        """Test repairing JSON with trailing commas."""
        malformed_json = '{"name": "Test", "type": "custom",}'
        
        repaired = await repair_llm_response(malformed_json)
        assert repaired is not None
        
        # Should be valid JSON now
        parsed = json.loads(repaired)
        assert parsed["name"] == "Test"
        assert parsed["type"] == "custom"
    
    @pytest.mark.asyncio
    async def test_repair_missing_closing_brace(self):
        """Test repairing JSON with missing closing braces."""
        malformed_json = '{"name": "Test", "type": "custom"'
        
        repaired = await repair_llm_response(malformed_json)
        assert repaired is not None
        
        # Should be valid JSON now
        parsed = json.loads(repaired)
        assert parsed["name"] == "Test"
        assert parsed["type"] == "custom"
    
    @pytest.mark.asyncio
    async def test_repair_extra_closing_brace(self):
        """Test repairing JSON with extra closing braces."""
        malformed_json = '{"name": "Test", "type": "custom"}}'
        
        repaired = await repair_llm_response(malformed_json)
        assert repaired is not None
        
        # Should be valid JSON now
        parsed = json.loads(repaired)
        assert parsed["name"] == "Test"
        assert parsed["type"] == "custom"
    
    @pytest.mark.asyncio
    async def test_repair_unrepairable_json(self):
        """Test that severely malformed JSON returns None."""
        malformed_json = 'This is not JSON at all'
        
        repaired = await repair_llm_response(malformed_json)
        assert repaired is None
    
    @pytest.mark.asyncio
    async def test_repair_empty_response(self):
        """Test that empty response returns None."""
        repaired = await repair_llm_response("")
        assert repaired is None
        
        repaired = await repair_llm_response("   ")
        assert repaired is None


class TestValidateAndRepairLLMResponse:
    """Test combined validation and repair functionality."""
    
    def create_valid_response_data(self):
        """Create valid response data for testing."""
        return {
            "name": "Test Personality",
            "type": "custom",
            "description": "Test description",
            "traits": [
                {"trait": "Analytical", "intensity": 8, "description": "Logical thinker"}
            ],
            "communication_style": {
                "tone": "Professional",
                "formality": "formal",
                "verbosity": "moderate",
                "technical_level": "expert"
            },
            "mannerisms": ["Speaks clearly"],
            "confidence": 0.9
        }
    
    @pytest.mark.asyncio
    async def test_validate_and_repair_valid_response(self):
        """Test that valid response passes through without repair."""
        response_data = self.create_valid_response_data()
        response_text = json.dumps(response_data)
        
        result = await validate_and_repair_llm_response(response_text)
        
        assert isinstance(result, LLMPersonalityResponse)
        assert result.name == "Test Personality"
    
    @pytest.mark.asyncio
    async def test_validate_and_repair_repairable_response(self):
        """Test that repairable response is fixed and validated."""
        response_data = self.create_valid_response_data()
        # Add trailing comma to make it malformed but repairable
        malformed_text = json.dumps(response_data)[:-1] + ",}"
        
        result = await validate_and_repair_llm_response(malformed_text)
        
        assert isinstance(result, LLMPersonalityResponse)
        assert result.name == "Test Personality"
    
    @pytest.mark.asyncio
    async def test_validate_and_repair_unrepairable_response(self):
        """Test that unrepairable response raises original error."""
        malformed_text = "This is completely invalid"
        
        with pytest.raises(LLMParsingError):
            await validate_and_repair_llm_response(malformed_text)