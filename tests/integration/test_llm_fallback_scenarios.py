"""Integration tests for LLM fallback scenarios when services are unavailable."""

import pytest
import asyncio
from unittest.mock import patch, AsyncMock, Mock
from typing import Dict, Any, List
import httpx

from src.covibe.services.research import research_personality
from src.covibe.services.orchestration import orchestrate_personality_request
from src.covibe.services.llm_client import OpenAIClient, AnthropicClient
from src.covibe.utils.error_handling import LLMError, LLMConnectionError, LLMRateLimitError, LLMTimeoutError
from src.covibe.models.core import ResearchResult, PersonalityProfile, PersonalityType, ResearchSource
from src.covibe.models.llm import LLMPersonalityResponse
from datetime import datetime


class TestLLMProviderFailureScenarios:
    """Test fallback behavior when LLM providers fail."""
    
    @pytest.fixture
    def mock_traditional_research_result(self):
        """Mock result from traditional research methods."""
        profile = PersonalityProfile(
            id="fallback-profile-123",
            name="Sherlock Holmes", 
            type=PersonalityType.FICTIONAL,
            traits=[],
            communication_style=None,
            mannerisms=["Deductive reasoning", "Pipe smoking"],
            sources=[ResearchSource(
                type="wikipedia",
                url="https://en.wikipedia.org/wiki/Sherlock_Holmes",
                confidence=0.8,
                last_updated=datetime.now()
            )]
        )
        
        return ResearchResult(
            query="brilliant detective",
            profiles=[profile], 
            confidence=0.8,
            suggestions=[],
            errors=[]
        )
    
    async def test_openai_service_unavailable_fallback_to_anthropic(self, mock_traditional_research_result):
        """Test fallback from OpenAI to Anthropic when OpenAI is unavailable."""
        
        async def mock_openai_failure(*args, **kwargs):
            raise LLMConnectionError("OpenAI service unavailable")
        
        async def mock_anthropic_success(*args, **kwargs):
            return """{
                "name": "Sherlock Holmes",
                "type": "fictional",
                "description": "Brilliant detective",
                "traits": [{"trait": "analytical", "intensity": 10, "description": "Exceptional analytical thinking"}],
                "communication_style": {"tone": "precise", "formality": "formal", "verbosity": "concise", "technical_level": "expert"},
                "mannerisms": ["Deductive reasoning", "Logical conclusions"],
                "confidence": 0.95
            }"""
        
        with patch('src.covibe.services.llm_client.OpenAIClient.generate_response', side_effect=mock_openai_failure), \
             patch('src.covibe.services.llm_client.AnthropicClient.generate_response', side_effect=mock_anthropic_success):
            
            result = await research_personality(
                "brilliant detective", 
                use_llm=True, 
                llm_provider="openai"  # Will fallback to anthropic
            )
            
            assert result is not None
            assert len(result.profiles) > 0
            assert result.profiles[0].name == "Sherlock Holmes"
            
            # Should indicate fallback occurred
            assert any("fallback" in error.lower() for error in result.errors) or \
                   any(source.type == "llm_anthropic" for source in result.profiles[0].sources)
    
    async def test_all_llm_providers_unavailable_fallback_to_traditional(self, mock_traditional_research_result):
        """Test fallback to traditional research when all LLM providers fail."""
        
        async def mock_llm_failure(*args, **kwargs):
            raise LLMConnectionError("LLM service unavailable")
        
        with patch('src.covibe.services.llm_client.OpenAIClient.generate_response', side_effect=mock_llm_failure), \
             patch('src.covibe.services.llm_client.AnthropicClient.generate_response', side_effect=mock_llm_failure), \
             patch('src.covibe.services.research.fallback_research_personality', return_value=mock_traditional_research_result):
            
            result = await research_personality(
                "brilliant detective",
                use_llm=True,
                llm_provider="openai"
            )
            
            assert result is not None
            assert len(result.profiles) > 0
            assert result.profiles[0].name == "Sherlock Holmes"
            
            # Should use traditional research source
            assert any(source.type == "wikipedia" for source in result.profiles[0].sources)
            assert "LLM service unavailable" in str(result.errors) or \
                   "fallback" in str(result.errors).lower()
    
    async def test_rate_limit_fallback_behavior(self, mock_traditional_research_result):
        """Test behavior when LLM provider hits rate limits."""
        
        call_count = 0
        
        async def mock_rate_limited_then_success(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            
            if call_count <= 2:
                raise LLMRateLimitError("Rate limit exceeded", retry_after=1)
            else:
                return """{
                    "name": "Einstein",
                    "type": "celebrity", 
                    "description": "Theoretical physicist",
                    "traits": [{"trait": "genius", "intensity": 10, "description": "Exceptional intelligence"}],
                    "communication_style": {"tone": "thoughtful", "formality": "academic", "verbosity": "detailed", "technical_level": "expert"},
                    "mannerisms": ["Complex theories", "Thought experiments"],
                    "confidence": 0.98
                }"""
        
        with patch('src.covibe.services.llm_client.OpenAIClient.generate_response', side_effect=mock_rate_limited_then_success), \
             patch('asyncio.sleep', new_callable=AsyncMock):  # Mock sleep to speed up test
            
            result = await research_personality(
                "theoretical physicist",
                use_llm=True,
                llm_provider="openai"
            )
            
            assert result is not None
            assert len(result.profiles) > 0
            assert result.profiles[0].name == "Einstein"
            
            # Should have retried and eventually succeeded
            assert call_count > 1, "Rate limit retry logic was not executed"
    
    async def test_rate_limit_exhaustion_fallback_to_different_provider(self, mock_traditional_research_result):
        """Test fallback to different provider when rate limits are exhausted."""
        
        async def mock_openai_rate_limit(*args, **kwargs):
            raise LLMRateLimitError("Rate limit exceeded", retry_after=3600)  # Long retry time
        
        async def mock_anthropic_success(*args, **kwargs):
            return """{
                "name": "Marie Curie",
                "type": "celebrity",
                "description": "Nobel Prize-winning scientist",
                "traits": [{"trait": "determined", "intensity": 10, "description": "Unwavering determination"}],
                "communication_style": {"tone": "scientific", "formality": "professional", "verbosity": "precise", "technical_level": "expert"},
                "mannerisms": ["Scientific rigor", "Methodical approach"],
                "confidence": 0.92
            }"""
        
        with patch('src.covibe.services.llm_client.OpenAIClient.generate_response', side_effect=mock_openai_rate_limit), \
             patch('src.covibe.services.llm_client.AnthropicClient.generate_response', side_effect=mock_anthropic_success):
            
            result = await research_personality(
                "Nobel Prize scientist",
                use_llm=True,
                llm_provider="openai"
            )
            
            assert result is not None
            assert len(result.profiles) > 0
            assert result.profiles[0].name == "Marie Curie"
            
            # Should have switched to anthropic due to rate limiting
            assert any(source.type == "llm_anthropic" for source in result.profiles[0].sources)
    
    async def test_timeout_fallback_behavior(self):
        """Test fallback behavior when LLM requests timeout."""
        
        async def mock_timeout(*args, **kwargs):
            raise LLMTimeoutError("Request timed out", timeout_duration=30.0)
        
        async def mock_anthropic_success(*args, **kwargs):
            return """{
                "name": "Leonardo da Vinci",
                "type": "celebrity",
                "description": "Renaissance polymath",
                "traits": [{"trait": "creative", "intensity": 10, "description": "Boundless creativity"}],
                "communication_style": {"tone": "artistic", "formality": "eloquent", "verbosity": "expressive", "technical_level": "expert"},
                "mannerisms": ["Artistic vision", "Innovative thinking"],
                "confidence": 0.90
            }"""
        
        with patch('src.covibe.services.llm_client.OpenAIClient.generate_response', side_effect=mock_timeout), \
             patch('src.covibe.services.llm_client.AnthropicClient.generate_response', side_effect=mock_anthropic_success):
            
            result = await research_personality(
                "Renaissance artist and inventor",
                use_llm=True,
                llm_provider="openai"
            )
            
            assert result is not None
            assert len(result.profiles) > 0
            assert result.profiles[0].name == "Leonardo da Vinci"
            
            # Should indicate timeout occurred and fallback was used
            assert "timed out" in str(result.errors).lower() or \
                   any(source.type == "llm_anthropic" for source in result.profiles[0].sources)


class TestNetworkFailureScenarios:
    """Test behavior during network and connectivity issues."""
    
    async def test_network_connectivity_failure(self):
        """Test behavior when network connectivity is lost."""
        
        async def mock_network_error(*args, **kwargs):
            raise httpx.ConnectError("Network connection failed")
        
        mock_fallback_result = ResearchResult(
            query="network test",
            profiles=[],
            confidence=0.0,
            suggestions=["Try again when network is available"],
            errors=["Network connectivity issue"]
        )
        
        with patch('httpx.AsyncClient.post', side_effect=mock_network_error), \
             patch('src.covibe.services.research.fallback_research_personality', return_value=mock_fallback_result):
            
            result = await research_personality(
                "test personality",
                use_llm=True,
                llm_provider="openai"
            )
            
            assert result is not None
            assert "network" in str(result.errors).lower() or \
                   "connectivity" in str(result.errors).lower()
            assert len(result.suggestions) > 0
    
    async def test_dns_resolution_failure(self):
        """Test behavior when DNS resolution fails."""
        
        async def mock_dns_error(*args, **kwargs):
            raise httpx.ConnectError("DNS resolution failed")
        
        with patch('httpx.AsyncClient.post', side_effect=mock_dns_error):
            result = await research_personality(
                "test personality",
                use_llm=True,
                llm_provider="openai"
            )
            
            # Should fallback gracefully
            assert result is not None
            # Either returned fallback result or handled DNS error gracefully
    
    async def test_ssl_certificate_error(self):
        """Test behavior when SSL certificate validation fails."""
        
        async def mock_ssl_error(*args, **kwargs):
            raise httpx.ConnectError("SSL certificate verification failed")
        
        with patch('httpx.AsyncClient.post', side_effect=mock_ssl_error):
            result = await research_personality(
                "test personality",
                use_llm=True,
                llm_provider="openai"
            )
            
            # Should handle SSL errors gracefully
            assert result is not None


class TestLLMServicePartialFailures:
    """Test scenarios where LLM services are partially functional."""
    
    async def test_malformed_response_fallback(self):
        """Test fallback when LLM returns malformed responses."""
        
        malformed_responses = [
            "This is not JSON at all",
            '{"incomplete": "json"',  # Invalid JSON
            '{"name": "Test"}',  # Missing required fields
            "",  # Empty response
            '{"name": "Test", "invalid_field": "should_not_exist"}',  # Invalid structure
        ]
        
        response_index = 0
        
        async def mock_malformed_response(*args, **kwargs):
            nonlocal response_index
            if response_index < len(malformed_responses):
                response = malformed_responses[response_index]
                response_index += 1
                return response
            else:
                # Eventually return valid response
                return """{
                    "name": "Valid Response",
                    "type": "custom",
                    "description": "Valid after retries",
                    "traits": [{"trait": "persistent", "intensity": 8, "description": "Keeps trying"}],
                    "communication_style": {"tone": "determined", "formality": "mixed", "verbosity": "moderate", "technical_level": "intermediate"},
                    "mannerisms": ["Never gives up"],
                    "confidence": 0.7
                }"""
        
        with patch('src.covibe.services.llm_client.OpenAIClient.generate_response', side_effect=mock_malformed_response):
            result = await research_personality(
                "persistent personality",
                use_llm=True,
                llm_provider="openai"
            )
            
            assert result is not None
            # Should either succeed after retries or fallback to traditional research
            if len(result.profiles) > 0:
                # If LLM eventually succeeded
                assert result.profiles[0].name in ["Valid Response", "Traditional Fallback"]
            else:
                # If fell back to traditional research
                assert len(result.errors) > 0 or len(result.suggestions) > 0
    
    async def test_inconsistent_response_quality(self):
        """Test handling of LLM responses with varying quality."""
        
        response_qualities = [
            # Low confidence response
            '{"name": "Low Quality", "type": "custom", "description": "Basic", "traits": [], "communication_style": {"tone": "neutral", "formality": "mixed", "verbosity": "moderate", "technical_level": "intermediate"}, "mannerisms": [], "confidence": 0.1}',
            # Medium confidence response  
            '{"name": "Medium Quality", "type": "custom", "description": "Better description", "traits": [{"trait": "average", "intensity": 5, "description": "Decent trait"}], "communication_style": {"tone": "neutral", "formality": "mixed", "verbosity": "moderate", "technical_level": "intermediate"}, "mannerisms": ["Some behavior"], "confidence": 0.6}',
            # High confidence response
            '{"name": "High Quality", "type": "custom", "description": "Excellent detailed description", "traits": [{"trait": "excellent", "intensity": 9, "description": "Outstanding trait analysis"}], "communication_style": {"tone": "engaging", "formality": "professional", "verbosity": "detailed", "technical_level": "expert"}, "mannerisms": ["Well-defined behavior", "Clear patterns"], "confidence": 0.95}'
        ]
        
        quality_index = 0
        
        async def mock_varying_quality(*args, **kwargs):
            nonlocal quality_index
            response = response_qualities[quality_index % len(response_qualities)]
            quality_index += 1
            return response
        
        results = []
        
        with patch('src.covibe.services.llm_client.OpenAIClient.generate_response', side_effect=mock_varying_quality):
            for i in range(3):
                result = await research_personality(
                    f"test personality {i}",
                    use_llm=True,
                    llm_provider="openai"
                )
                results.append(result)
        
        # All should succeed but with different quality levels
        assert len(results) == 3
        assert all(r is not None for r in results)
        
        # Should have varying confidence levels
        confidences = [r.confidence for r in results if r.profiles]
        assert len(set(confidences)) > 1, "All responses had same confidence level"
    
    async def test_partial_service_degradation(self):
        """Test behavior when LLM service is running but degraded."""
        
        degraded_response_count = 0
        
        async def mock_degraded_service(*args, **kwargs):
            nonlocal degraded_response_count
            degraded_response_count += 1
            
            # Simulate slower, lower-quality responses due to degradation
            await asyncio.sleep(0.5)  # Slower response
            
            if degraded_response_count % 3 == 0:
                # Occasional failure during degradation
                raise LLMError("Service temporarily degraded")
            else:
                # Lower quality response
                return '{"name": "Degraded Quality", "type": "custom", "description": "Limited analysis due to service issues", "traits": [{"trait": "basic", "intensity": 3, "description": "Basic analysis only"}], "communication_style": {"tone": "simple", "formality": "mixed", "verbosity": "concise", "technical_level": "basic"}, "mannerisms": ["Simple patterns"], "confidence": 0.4}'
        
        with patch('src.covibe.services.llm_client.OpenAIClient.generate_response', side_effect=mock_degraded_service):
            results = []
            
            for i in range(5):
                try:
                    result = await research_personality(
                        f"test personality {i}",
                        use_llm=True,
                        llm_provider="openai"
                    )
                    results.append(result)
                except Exception:
                    # Some requests may fail during degradation
                    pass
            
            # Should get some results despite degradation
            assert len(results) > 0
            
            # Results should indicate degraded quality
            for result in results:
                if result and result.profiles:
                    assert result.confidence < 0.8, "Confidence too high for degraded service"


class TestFallbackChainValidation:
    """Test the complete fallback chain from LLM to traditional research."""
    
    async def test_complete_fallback_chain_execution(self):
        """Test that the complete fallback chain executes properly."""
        
        fallback_steps = []
        
        async def mock_openai_failure(*args, **kwargs):
            fallback_steps.append("openai_failed")
            raise LLMConnectionError("OpenAI unavailable")
        
        async def mock_anthropic_failure(*args, **kwargs):
            fallback_steps.append("anthropic_failed")
            raise LLMConnectionError("Anthropic unavailable")
        
        def mock_traditional_success(*args, **kwargs):
            fallback_steps.append("traditional_research_used")
            return ResearchResult(
                query="fallback test",
                profiles=[],
                confidence=0.6,
                suggestions=["Traditional research completed"],
                errors=[]
            )
        
        with patch('src.covibe.services.llm_client.OpenAIClient.generate_response', side_effect=mock_openai_failure), \
             patch('src.covibe.services.llm_client.AnthropicClient.generate_response', side_effect=mock_anthropic_failure), \
             patch('src.covibe.services.research.fallback_research_personality', side_effect=mock_traditional_success):
            
            result = await research_personality(
                "fallback chain test",
                use_llm=True,
                llm_provider="openai"
            )
            
            assert result is not None
            
            # Verify the complete fallback chain was executed
            assert "openai_failed" in fallback_steps
            assert "anthropic_failed" in fallback_steps
            assert "traditional_research_used" in fallback_steps
            
            # Verify proper order
            openai_index = fallback_steps.index("openai_failed")
            anthropic_index = fallback_steps.index("anthropic_failed")
            traditional_index = fallback_steps.index("traditional_research_used")
            
            assert openai_index < anthropic_index < traditional_index, "Fallback chain executed in wrong order"
    
    async def test_fallback_chain_early_success(self):
        """Test that fallback chain stops when an earlier step succeeds."""
        
        fallback_steps = []
        
        async def mock_openai_failure(*args, **kwargs):
            fallback_steps.append("openai_failed")
            raise LLMConnectionError("OpenAI unavailable")
        
        async def mock_anthropic_success(*args, **kwargs):
            fallback_steps.append("anthropic_succeeded")
            return """{
                "name": "Anthropic Success",
                "type": "custom",
                "description": "Successfully handled by Anthropic",
                "traits": [{"trait": "reliable", "intensity": 8, "description": "Reliable fallback"}],
                "communication_style": {"tone": "helpful", "formality": "professional", "verbosity": "appropriate", "technical_level": "suitable"},
                "mannerisms": ["Fallback behavior"],
                "confidence": 0.85
            }"""
        
        def mock_traditional_should_not_run(*args, **kwargs):
            fallback_steps.append("traditional_research_should_not_run")
            return ResearchResult(query="should not reach", profiles=[], confidence=0.0, suggestions=[], errors=[])
        
        with patch('src.covibe.services.llm_client.OpenAIClient.generate_response', side_effect=mock_openai_failure), \
             patch('src.covibe.services.llm_client.AnthropicClient.generate_response', side_effect=mock_anthropic_success), \
             patch('src.covibe.services.research.fallback_research_personality', side_effect=mock_traditional_should_not_run):
            
            result = await research_personality(
                "early success test",
                use_llm=True,
                llm_provider="openai"
            )
            
            assert result is not None
            assert len(result.profiles) > 0
            assert result.profiles[0].name == "Anthropic Success"
            
            # Should have failed OpenAI and succeeded with Anthropic
            assert "openai_failed" in fallback_steps
            assert "anthropic_succeeded" in fallback_steps
            
            # Should NOT have reached traditional research
            assert "traditional_research_should_not_run" not in fallback_steps
    
    async def test_orchestration_level_fallback_handling(self):
        """Test that orchestration properly handles LLM fallbacks."""
        
        async def mock_llm_research_failure(*args, **kwargs):
            raise LLMError("All LLM providers failed")
        
        mock_request = Mock()
        mock_request.description = "orchestration fallback test"
        mock_request.user_id = "test_user"
        mock_request.source = "test"
        
        with patch('src.covibe.services.research.research_personality_with_llm', side_effect=mock_llm_research_failure), \
             patch('src.covibe.services.research.fallback_research_personality') as mock_fallback:
            
            mock_fallback.return_value = ResearchResult(
                query="orchestration fallback test",
                profiles=[],
                confidence=0.5,
                suggestions=["Fallback completed at orchestration level"],
                errors=["LLM services unavailable"]
            )
            
            result = await orchestrate_personality_request(mock_request, use_llm=True)
            
            assert result is not None
            
            # Should have called fallback research
            mock_fallback.assert_called_once()
            
            # Should indicate LLM failure and fallback usage
            assert result.success is True  # Orchestration should still succeed
            assert "fallback" in str(result).lower() or "unavailable" in str(result).lower()