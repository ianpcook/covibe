"""Unit tests for personality research functionality."""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, Mock
from datetime import datetime, timedelta
from src.covibe.services.research import (
    get_archetype_data,
    extract_traits_from_text,
    calculate_wikipedia_confidence,
    research_personality,
    research_personality_with_llm,
    fallback_research_personality
)
from src.covibe.models.core import PersonalityType
from src.covibe.models.llm import (
    LLMPersonalityResponse,
    LLMTrait,
    LLMCommunicationStyle
)
from src.covibe.services.prompt_manager import PromptConfig
from src.covibe.services.llm_cache import CachedLLMResponse
from src.covibe.utils.error_handling import NetworkError, RateLimitError


def test_get_archetype_data_cowboy():
    """Test getting cowboy archetype data."""
    result, confidence = get_archetype_data("cowboy personality")
    
    assert result is not None
    assert result["name"] == "Cowboy"
    assert "independent" in result["traits"]
    assert confidence > 0.8


def test_get_archetype_data_robot():
    """Test getting robot archetype data."""
    result, confidence = get_archetype_data("like a robot")
    
    assert result is not None
    assert result["name"] == "Robot/AI"
    assert "logical" in result["traits"]
    assert confidence > 0.8


def test_get_archetype_data_no_match():
    """Test getting archetype data with no match."""
    result, confidence = get_archetype_data("completely unknown archetype")
    
    assert result is None
    assert confidence == 0.0


def test_extract_traits_from_text():
    """Test extracting traits from descriptive text."""
    text = "A brilliant and creative genius who shows great leadership."
    
    traits = extract_traits_from_text(text)
    
    assert len(traits) > 0
    trait_names = [t.trait for t in traits]
    assert "intelligent" in trait_names  # Should match "brilliant"
    assert "creative" in trait_names


def test_calculate_wikipedia_confidence_full_data():
    """Test confidence calculation with complete data."""
    data = {
        "title": "Test Person",
        "description": "A description",
        "extract": "A long extract with lots of information about the person and their achievements and contributions to society which spans multiple sentences.",
        "url": "https://example.com"
    }
    
    confidence = calculate_wikipedia_confidence(data)
    assert confidence == 1.0


def test_calculate_wikipedia_confidence_empty_data():
    """Test confidence calculation with empty data."""
    data = {}
    
    confidence = calculate_wikipedia_confidence(data)
    assert confidence == 0.0


@pytest.mark.asyncio
async def test_research_personality_archetype():
    """Test personality research that finds archetype data."""
    # Disable LLM to test fallback behavior
    # Use "mentor" which should match archetype data
    result = await research_personality("mentor personality", use_llm=False)
    
    assert result.query == "mentor personality"
    assert len(result.profiles) > 0
    assert result.profiles[0].type == PersonalityType.ARCHETYPE
    assert result.confidence > 0.8


class TestLLMResearchIntegration:
    """Integration tests for LLM research functionality."""
    
    @pytest.fixture
    def sample_llm_response(self):
        """Create sample LLM response for testing."""
        return LLMPersonalityResponse(
            name="Tony Stark",
            type="fictional",
            description="Genius inventor with wit and confidence",
            traits=[
                LLMTrait(trait="genius", intensity=10, description="Exceptionally intelligent"),
                LLMTrait(trait="witty", intensity=8, description="Sharp sense of humor"),
                LLMTrait(trait="confident", intensity=9, description="Self-assured")
            ],
            communication_style=LLMCommunicationStyle(
                tone="confident",
                formality="casual",
                verbosity="moderate",
                technical_level="expert"
            ),
            mannerisms=["Makes pop culture references", "Uses technical jargon"],
            confidence=0.95
        )
    
    @pytest.fixture
    def mock_llm_client(self, sample_llm_response):
        """Create mock LLM client."""
        client = AsyncMock()
        client.provider = "openai"
        client.model = "gpt-4"
        
        # Mock successful response
        client.generate_response.return_value = sample_llm_response.model_dump_json()
        
        return client
    
    @pytest.fixture
    def mock_prompt_config(self):
        """Create mock prompt configuration."""
        return PromptConfig(
            name="test_prompt",
            version="1.0",
            template="Analyze: {{description}}",
            variables={"description": "test"},
            max_tokens=1000,
            temperature=0.7,
            model="gpt-4"
        )
    
    @pytest.fixture
    def mock_cache_client(self):
        """Create mock cache client."""
        cache = AsyncMock()
        cache.get.return_value = None  # No cache hit by default
        cache.set.return_value = None
        cache.start.return_value = None
        cache.stop.return_value = None
        return cache
    
    @pytest.mark.asyncio
    async def test_llm_research_success(self, mock_llm_client, mock_prompt_config, mock_cache_client):
        """Test successful LLM research with response validation and conversion."""
        with patch('src.covibe.services.research.validate_and_repair_llm_response') as mock_validate, \
             patch('src.covibe.services.research.convert_llm_to_profile') as mock_convert, \
             patch('src.covibe.services.research.render_prompt') as mock_render:
            
            # Mock prompt rendering
            mock_render.return_value = "Analyze: Tony Stark personality"
            
            # Mock response validation
            sample_response = LLMPersonalityResponse(
                name="Tony Stark",
                type="fictional",
                description="Genius inventor",
                traits=[LLMTrait(trait="genius", intensity=10, description="Smart")],
                communication_style=LLMCommunicationStyle(
                    tone="confident", formality="casual", 
                    verbosity="moderate", technical_level="expert"
                ),
                confidence=0.95
            )
            mock_validate.return_value = sample_response
            
            # Mock profile conversion
            from src.covibe.models.core import PersonalityProfile, PersonalityTrait, CommunicationStyle
            mock_profile = Mock(spec=PersonalityProfile)
            mock_profile.name = "Tony Stark"
            mock_profile.type = PersonalityType.FICTIONAL
            mock_convert.return_value = mock_profile
            
            # Test LLM research
            result = await research_personality_with_llm(
                "Tony Stark personality",
                mock_llm_client,
                mock_prompt_config,
                mock_cache_client
            )
            
            # Verify calls
            mock_render.assert_called_once_with(mock_prompt_config, description="Tony Stark personality")
            mock_llm_client.generate_response.assert_called_once_with(
                "Analyze: Tony Stark personality",
                max_tokens=1000,
                temperature=0.7
            )
            mock_validate.assert_called_once()
            mock_convert.assert_called_once()
            
            # Verify result
            assert result.query == "Tony Stark personality"
            assert len(result.profiles) == 1
            assert result.profiles[0] == mock_profile
            assert result.confidence == 0.95
    
    @pytest.mark.asyncio
    async def test_llm_research_with_cache_hit(self, mock_llm_client, mock_prompt_config, sample_llm_response):
        """Test LLM research with cache hit."""
        # Create cached response
        cached_response = CachedLLMResponse(
            query_hash="test_hash",
            response=sample_llm_response,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(hours=1),
            llm_provider="openai",
            llm_model="gpt-4"
        )
        
        mock_cache_client = AsyncMock()
        mock_cache_client.get.return_value = cached_response
        
        with patch('src.covibe.services.research.convert_llm_to_profile') as mock_convert, \
             patch('src.covibe.services.research.generate_cache_key') as mock_gen_key:
            
            mock_gen_key.return_value = "test_hash"
            
            # Mock profile conversion
            mock_profile = Mock()
            mock_profile.name = "Tony Stark"
            mock_convert.return_value = mock_profile
            
            # Test LLM research with cache
            result = await research_personality_with_llm(
                "Tony Stark personality",
                mock_llm_client,
                mock_prompt_config,
                mock_cache_client
            )
            
            # Verify cache was checked and LLM was not called
            mock_cache_client.get.assert_called_once_with("test_hash")
            mock_llm_client.generate_response.assert_not_called()
            
            # Verify result uses cached data
            assert result.query == "Tony Stark personality"
            assert len(result.profiles) == 1
            assert result.confidence == 0.95
    
    @pytest.mark.asyncio
    async def test_llm_research_network_error(self, mock_prompt_config, mock_cache_client):
        """Test LLM research with network error handling."""
        # Mock LLM client that raises network error
        mock_llm_client = AsyncMock()
        mock_llm_client.provider = "openai"
        mock_llm_client.model = "gpt-4"
        mock_llm_client.generate_response.side_effect = NetworkError("Connection failed")
        
        with patch('src.covibe.services.research.render_prompt') as mock_render:
            mock_render.return_value = "Test prompt"
            
            # Test that network error is properly raised
            with pytest.raises(NetworkError):
                await research_personality_with_llm(
                    "test description",
                    mock_llm_client,
                    mock_prompt_config,
                    mock_cache_client
                )
    
    @pytest.mark.asyncio
    async def test_llm_research_validation_error(self, mock_llm_client, mock_prompt_config, mock_cache_client):
        """Test LLM research with response validation error."""
        from src.covibe.models.llm import LLMValidationError
        
        with patch('src.covibe.services.research.validate_and_repair_llm_response') as mock_validate, \
             patch('src.covibe.services.research.render_prompt') as mock_render:
            
            mock_render.return_value = "Test prompt"
            mock_validate.side_effect = LLMValidationError("Invalid response format")
            
            # Test that validation errors are handled gracefully
            result = await research_personality_with_llm(
                "test description",
                mock_llm_client,
                mock_prompt_config,
                mock_cache_client
            )
            
            # Should return empty result with error info
            assert result.query == "test description"
            assert len(result.profiles) == 0
            assert result.confidence == 0.0
            assert len(result.errors) > 0
            assert "validation failed" in result.errors[0]
    
    @pytest.mark.asyncio
    async def test_end_to_end_research_with_llm_success(self, sample_llm_response):
        """Test end-to-end research flow with successful LLM response."""
        with patch('src.covibe.services.research.load_prompt_config') as mock_load_prompt, \
             patch('src.covibe.services.research.create_openai_client') as mock_create_client, \
             patch('src.covibe.services.research.validate_and_repair_llm_response') as mock_validate, \
             patch('src.covibe.services.research.convert_llm_to_profile') as mock_convert, \
             patch('src.covibe.services.research.render_prompt') as mock_render, \
             patch('os.getenv') as mock_getenv:
            
            # Mock environment setup
            mock_getenv.side_effect = lambda key, default=None: {
                'OPENAI_API_KEY': 'test_key'
            }.get(key, default)
            
            # Mock prompt config
            mock_prompt_config = PromptConfig(
                name="test", version="1.0", template="{{description}}",
                variables={}, max_tokens=1000, temperature=0.7, model="gpt-4"
            )
            mock_load_prompt.return_value = mock_prompt_config
            mock_render.return_value = "Test prompt"
            
            # Mock LLM client
            mock_client = AsyncMock()
            mock_client.provider = "openai"
            mock_client.model = "gpt-4"
            mock_client.generate_response.return_value = sample_llm_response.model_dump_json()
            mock_create_client.return_value = mock_client
            
            # Mock response processing
            mock_validate.return_value = sample_llm_response
            mock_profile = Mock()
            mock_profile.name = "Tony Stark"
            mock_profile.type = PersonalityType.FICTIONAL
            mock_convert.return_value = mock_profile
            
            # Test end-to-end research
            result = await research_personality("Tony Stark personality", use_llm=True)
            
            # Verify the flow
            assert result.query == "Tony Stark personality"
            assert len(result.profiles) == 1
            assert result.profiles[0] == mock_profile
    
    @pytest.mark.asyncio
    async def test_end_to_end_research_with_llm_fallback(self):
        """Test end-to-end research flow with LLM failure and fallback."""
        with patch('src.covibe.services.research.load_prompt_config') as mock_load_prompt, \
             patch('src.covibe.services.research.create_openai_client') as mock_create_client, \
             patch('os.getenv') as mock_getenv:
            
            # Mock environment setup
            mock_getenv.side_effect = lambda key, default=None: {
                'OPENAI_API_KEY': 'test_key'
            }.get(key, default)
            
            # Mock prompt config
            mock_prompt_config = PromptConfig(
                name="test", version="1.0", template="{{description}}",
                variables={}, max_tokens=1000, temperature=0.7, model="gpt-4"
            )
            mock_load_prompt.return_value = mock_prompt_config
            
            # Mock LLM client that fails
            mock_client = AsyncMock()
            mock_client.generate_response.side_effect = NetworkError("Connection failed")
            mock_create_client.return_value = mock_client
            
            # Test research with LLM failure - should fall back to archetype
            result = await research_personality("mentor personality", use_llm=True)
            
            # Should find mentor archetype as fallback
            assert result.query == "mentor personality"
            assert len(result.profiles) > 0
            assert result.profiles[0].type == PersonalityType.ARCHETYPE
            assert "mentor" in result.profiles[0].name.lower()
    
    @pytest.mark.asyncio
    async def test_fallback_research_functionality(self):
        """Test fallback research methods work independently."""
        # Test character fallback
        result = await fallback_research_personality("Tony Stark")
        assert len(result.profiles) > 0
        assert "stark" in result.profiles[0].name.lower()
        
        # Test archetype fallback
        result = await fallback_research_personality("robot personality")
        assert len(result.profiles) > 0
        assert result.profiles[0].type == PersonalityType.ARCHETYPE
        
        # Test no matches
        result = await fallback_research_personality("completely unknown personality xyz123")
        # Should provide suggestions even if no matches
        assert len(result.suggestions) > 0
