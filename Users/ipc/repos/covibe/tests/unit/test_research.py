"""Unit tests for personality research functionality."""

import pytest
import httpx
from unittest.mock import AsyncMock, patch
from datetime import datetime
from covibe.services.research import (
    research_wikipedia,
    research_character_database,
    get_archetype_data,
    research_personality,
    create_profile_from_wikipedia,
    create_profile_from_character_data,
    create_profile_from_archetype,
    extract_traits_from_text,
    extract_mannerisms_from_text,
    generate_research_suggestions,
    calculate_wikipedia_confidence
)
from covibe.models.core import PersonalityType, FormalityLevel


class TestWikipediaResearch:
    """Tests for Wikipedia research functionality."""
    
    @pytest.mark.asyncio
    async def test_research_wikipedia_success(self):
        """Test successful Wikipedia research."""
        mock_response = {
            "title": "Albert Einstein",
            "description": "German-born theoretical physicist",
            "extract": "Albert Einstein was a German-born theoretical physicist who developed the theory of relativity.",
            "content_urls": {
                "desktop": {
                    "page": "https://en.wikipedia.org/wiki/Albert_Einstein"
                }
            }
        }
        
        mock_client = AsyncMock()
        mock_client.get.return_value.status_code = 200
        mock_client.get.return_value.json.return_value = mock_response
        
        result, confidence = await research_wikipedia("Albert Einstein", mock_client)
        
        assert result is not None
        assert result["title"] == "Albert Einstein"
        assert result["source_type"] == "wikipedia"
        assert confidence > 0.5
        mock_client.get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_research_wikipedia_not_found(self):
        """Test Wikipedia research when page not found."""
        mock_client = AsyncMock()
        mock_client.get.return_value.status_code = 404
        
        result, confidence = await research_wikipedia("NonexistentPerson", mock_client)
        
        assert result is None
        assert confidence == 0.0
    
    @pytest.mark.asyncio
    async def test_research_wikipedia_network_error(self):
        """Test Wikipedia research with network error."""
        mock_client = AsyncMock()
        mock_client.get.side_effect = httpx.RequestError("Network error")
        
        result, confidence = await research_wikipedia("Test Person", mock_client)
        
        assert result is None
        assert confidence == 0.0


class TestCharacterDatabaseResearch:
    """Tests for character database research."""
    
    @pytest.mark.asyncio
    async def test_research_character_database_known_character(self):
        """Test research for known fictional character."""
        mock_client = AsyncMock()
        
        result, confidence = await research_character_database("Tony Stark", mock_client)
        
        assert result is not None
        assert result["name"] == "Tony Stark"
        assert "intelligent" in result["traits"]
        assert confidence > 0.5
    
    @pytest.mark.asyncio
    async def test_research_character_database_unknown_character(self):
        """Test research for unknown character."""
        mock_client = AsyncMock()
        
        result, confidence = await research_character_database("Unknown Character", mock_client)
        
        assert result is None
        assert confidence == 0.0
    
    @pytest.mark.asyncio
    async def test_research_character_database_partial_match(self):
        """Test research with partial character name match."""
        mock_client = AsyncMock()
        
        result, confidence = await research_character_database("Sherlock", mock_client)
        
        assert result is not None
        assert result["name"] == "Sherlock Holmes"
        assert confidence > 0.5


class TestArchetypeData:
    """Tests for archetype data functionality."""
    
    def test_get_archetype_data_direct_match(self):
        """Test getting archetype data with direct match."""
        result, confidence = get_archetype_data("cowboy personality")
        
        assert result is not None
        assert result["name"] == "Cowboy"
        assert "independent" in result["traits"]
        assert confidence > 0.8
    
    def test_get_archetype_data_keyword_match(self):
        """Test getting archetype data with keyword match."""
        result, confidence = get_archetype_data("like a military commander")
        
        assert result is not None
        assert result["name"] == "Drill Sergeant"
        assert confidence > 0.5
    
    def test_get_archetype_data_no_match(self):
        """Test getting archetype data with no match."""
        result, confidence = get_archetype_data("completely unknown archetype")
        
        assert result is None
        assert confidence == 0.0
    
    def test_get_archetype_data_robot_variations(self):
        """Test various robot/AI archetype keywords."""
        test_cases = ["robot", "android", "AI", "artificial intelligence"]
        
        for query in test_cases:
            result, confidence = get_archetype_data(f"like a {query}")
            assert result is not None
            assert result["name"] == "Robot/AI"
            assert confidence > 0.5


class TestProfileCreation:
    """Tests for profile creation functions."""
    
    def test_create_profile_from_wikipedia(self):
        """Test creating profile from Wikipedia data."""
        wiki_data = {
            "title": "Test Person",
            "description": "A brilliant and creative individual",
            "extract": "Known for being intelligent and innovative in their field.",
            "url": "https://en.wikipedia.org/wiki/Test_Person"
        }
        
        profile = create_profile_from_wikipedia(wiki_data, 0.8)
        
        assert profile is not None
        assert profile.name == "Test Person"
        assert profile.type == PersonalityType.CELEBRITY
        assert len(profile.traits) > 0
        assert profile.sources[0].confidence == 0.8
        assert profile.sources[0].type == "wikipedia"
    
    def test_create_profile_from_character_data(self):
        """Test creating profile from character data."""
        char_data = {
            "name": "Test Character",
            "traits": ["brave", "loyal", "determined"],
            "personality_notes": "A heroic character with strong moral values"
        }
        
        profile = create_profile_from_character_data(char_data, 0.9)
        
        assert profile is not None
        assert profile.name == "Test Character"
        assert profile.type == PersonalityType.FICTIONAL
        assert len(profile.traits) == 3
        assert profile.traits[0].trait == "brave"
        assert profile.sources[0].confidence == 0.9
    
    def test_create_profile_from_archetype(self):
        """Test creating profile from archetype data."""
        archetype_data = {
            "name": "Test Archetype",
            "traits": ["wise", "patient", "knowledgeable"],
            "communication_style": {
                "tone": "encouraging",
                "formality": "mixed",
                "verbosity": "moderate"
            },
            "mannerisms": ["asks guiding questions", "shares wisdom"]
        }
        
        profile = create_profile_from_archetype(archetype_data, 0.85)
        
        assert profile is not None
        assert profile.name == "Test Archetype"
        assert profile.type == PersonalityType.ARCHETYPE
        assert len(profile.traits) == 3
        assert profile.communication_style.tone == "encouraging"
        assert profile.communication_style.formality == FormalityLevel.MIXED
        assert len(profile.mannerisms) == 2


class TestTextExtraction:
    """Tests for text extraction functions."""
    
    def test_extract_traits_from_text(self):
        """Test extracting traits from descriptive text."""
        text = "A brilliant and creative genius who shows great leadership and is very funny."
        
        traits = extract_traits_from_text(text)
        
        assert len(traits) > 0
        trait_names = [t.trait for t in traits]
        assert "intelligent" in trait_names  # Should match "brilliant"
        assert "creative" in trait_names
        assert "leadership" in trait_names
        assert "humorous" in trait_names  # Should match "funny"
    
    def test_extract_traits_from_empty_text(self):
        """Test extracting traits from empty text."""
        traits = extract_traits_from_text("")
        assert len(traits) == 0
    
    def test_extract_mannerisms_from_text(self):
        """Test extracting mannerisms from text."""
        text = "He speaks in a distinctive way and is known for his unique approach to problems."
        
        mannerisms = extract_mannerisms_from_text(text)
        
        assert len(mannerisms) > 0
        assert any("speaking" in m.lower() for m in mannerisms)
    
    def test_extract_mannerisms_from_long_text(self):
        """Test extracting mannerisms from long text."""
        long_text = "A" * 300  # Long text should trigger complexity mannerism
        
        mannerisms = extract_mannerisms_from_text(long_text)
        
        assert len(mannerisms) > 0
        assert any("complex" in m.lower() for m in mannerisms)


class TestResearchSuggestions:
    """Tests for research suggestion generation."""
    
    def test_generate_suggestions_no_type_detected(self):
        """Test generating suggestions when no personality type detected."""
        suggestions = generate_research_suggestions("vague description", None)
        
        assert len(suggestions) > 0
        assert any("specific" in s.lower() for s in suggestions)
        assert any("full name" in s.lower() for s in suggestions)
    
    def test_generate_suggestions_short_description(self):
        """Test generating suggestions for short description."""
        suggestions = generate_research_suggestions("smart", "celebrity")
        
        assert len(suggestions) > 0
        assert any("more details" in s.lower() for s in suggestions)
    
    def test_generate_suggestions_good_description(self):
        """Test generating suggestions for adequate description."""
        suggestions = generate_research_suggestions("Tony Stark from Marvel", "fictional")
        
        assert len(suggestions) > 0  # Should still provide general suggestions
        assert any("alternative" in s.lower() for s in suggestions)


class TestConfidenceCalculation:
    """Tests for confidence calculation."""
    
    def test_calculate_wikipedia_confidence_full_data(self):
        """Test confidence calculation with complete data."""
        data = {
            "title": "Test Person",
            "description": "A description",
            "extract": "A long extract with lots of information about the person and their achievements.",
            "url": "https://example.com"
        }
        
        confidence = calculate_wikipedia_confidence(data)
        assert confidence == 1.0
    
    def test_calculate_wikipedia_confidence_partial_data(self):
        """Test confidence calculation with partial data."""
        data = {
            "title": "Test Person",
            "description": "A description"
        }
        
        confidence = calculate_wikipedia_confidence(data)
        assert 0.0 < confidence < 1.0
    
    def test_calculate_wikipedia_confidence_empty_data(self):
        """Test confidence calculation with empty data."""
        data = {}
        
        confidence = calculate_wikipedia_confidence(data)
        assert confidence == 0.0


@pytest.mark.asyncio
class TestResearchPersonality:
    """Integration tests for the main research function."""
    
    async def test_research_personality_with_mocked_responses(self):
        """Test complete personality research with mocked API responses."""
        with patch('covibe.services.research.research_wikipedia') as mock_wiki, \
             patch('covibe.services.research.research_character_database') as mock_char:
            
            # Mock Wikipedia response
            mock_wiki.return_value = ({
                "title": "Test Person",
                "description": "A brilliant individual",
                "extract": "Known for intelligence and creativity",
                "url": "https://example.com"
            }, 0.8)
            
            # Mock character database response
            mock_char.return_value = (None, 0.0)
            
            result = await research_personality("Test Person")
            
            assert result.query == "Test Person"
            assert len(result.profiles) > 0
            assert result.confidence > 0.0
            assert len(result.errors) == 0
    
    async def test_research_personality_archetype_only(self):
        """Test personality research that only finds archetype data."""
        result = await research_personality("cowboy personality")
        
        assert result.query == "cowboy personality"
        assert len(result.profiles) > 0
        assert result.profiles[0].type == PersonalityType.ARCHETYPE
        assert result.confidence > 0.8
    
    async def test_research_personality_no_results(self):
        """Test personality research with no results."""
        with patch('covibe.services.research.research_wikipedia') as mock_wiki, \
             patch('covibe.services.research.research_character_database') as mock_char:
            
            mock_wiki.return_value = (None, 0.0)
            mock_char.return_value = (None, 0.0)
            
            result = await research_personality("completely unknown person")
            
            assert result.query == "completely unknown person"
            assert len(result.profiles) == 0
            assert result.confidence == 0.0
            assert len(result.suggestions) > 0