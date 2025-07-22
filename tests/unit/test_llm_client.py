"""Unit tests for LLM client implementations."""

import json
import pytest
from unittest.mock import AsyncMock, Mock, patch
import httpx
import openai
import anthropic

from src.covibe.services.llm_client import (
    OpenAIClient,
    AnthropicClient,
    LocalLLMClient,
    create_openai_client,
    create_anthropic_client,
    create_local_client,
    create_client_factory,
    LLMConnectionError,
    LLMRateLimitError,
    LLMTimeoutError,
    LLMValidationError,
)


class TestOpenAIClient:
    """Test cases for OpenAI client implementation."""

    @pytest.fixture
    def openai_client(self):
        """Create OpenAI client for testing."""
        return OpenAIClient("test-api-key", "gpt-4")

    @pytest.mark.asyncio
    async def test_generate_response_success(self, openai_client):
        """Test successful response generation from OpenAI."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Test response from OpenAI"
        
        with patch.object(openai_client.client.chat.completions, 'create', new_callable=AsyncMock, return_value=mock_response):
            result = await openai_client.generate_response("Test prompt")
            
        assert result == "Test response from OpenAI"

    @pytest.mark.asyncio
    async def test_generate_response_empty_response(self, openai_client):
        """Test handling of empty response from OpenAI."""
        mock_response = Mock()
        mock_response.choices = []
        
        with patch.object(openai_client.client.chat.completions, 'create', new_callable=AsyncMock, return_value=mock_response):
            with pytest.raises(LLMConnectionError, match="Empty response from OpenAI"):
                await openai_client.generate_response("Test prompt")

    @pytest.mark.asyncio
    async def test_generate_response_rate_limit_error(self, openai_client):
        """Test handling of rate limit error from OpenAI."""
        rate_limit_error = openai.RateLimitError(
            message="Rate limit exceeded",
            response=Mock(),
            body={}
        )
        rate_limit_error.retry_after = 120
        
        with patch.object(openai_client.client.chat.completions, 'create', side_effect=rate_limit_error):
            with pytest.raises(LLMRateLimitError) as exc_info:
                await openai_client.generate_response("Test prompt")
            
            assert exc_info.value.retry_after == 120

    @pytest.mark.asyncio
    async def test_generate_response_timeout_error(self, openai_client):
        """Test handling of timeout error from OpenAI."""
        timeout_error = openai.APITimeoutError(request=Mock())
        
        with patch.object(openai_client.client.chat.completions, 'create', side_effect=timeout_error):
            with pytest.raises(LLMTimeoutError) as exc_info:
                await openai_client.generate_response("Test prompt")
            
            assert exc_info.value.timeout_duration == 30.0

    @pytest.mark.asyncio
    async def test_generate_response_connection_error(self, openai_client):
        """Test handling of connection error from OpenAI."""
        connection_error = openai.APIConnectionError(request=Mock())
        
        with patch.object(openai_client.client.chat.completions, 'create', side_effect=connection_error):
            with pytest.raises(LLMConnectionError, match="OpenAI connection failed"):
                await openai_client.generate_response("Test prompt")

    @pytest.mark.asyncio
    async def test_generate_response_api_error(self, openai_client):
        """Test handling of general API error from OpenAI."""
        api_error = openai.APIError(message="API Error", request=Mock(), body={})
        
        with patch.object(openai_client.client.chat.completions, 'create', side_effect=api_error):
            with pytest.raises(LLMConnectionError, match="OpenAI API error"):
                await openai_client.generate_response("Test prompt")

    @pytest.mark.asyncio
    async def test_validate_connection_success(self, openai_client):
        """Test successful connection validation for OpenAI."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        
        with patch.object(openai_client.client.chat.completions, 'create', new_callable=AsyncMock, return_value=mock_response):
            result = await openai_client.validate_connection()
            
        assert result is True

    @pytest.mark.asyncio
    async def test_validate_connection_failure(self, openai_client):
        """Test failed connection validation for OpenAI."""
        with patch.object(openai_client.client.chat.completions, 'create', side_effect=Exception("Connection failed")):
            result = await openai_client.validate_connection()
            
        assert result is False


class TestAnthropicClient:
    """Test cases for Anthropic client implementation."""

    @pytest.fixture
    def anthropic_client(self):
        """Create Anthropic client for testing."""
        return AnthropicClient("test-api-key", "claude-3-sonnet-20240229")

    @pytest.mark.asyncio
    async def test_generate_response_success(self, anthropic_client):
        """Test successful response generation from Anthropic."""
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = "Test response from Anthropic"
        
        with patch.object(anthropic_client.client.messages, 'create', new_callable=AsyncMock, return_value=mock_response):
            result = await anthropic_client.generate_response("Test prompt")
            
        assert result == "Test response from Anthropic"

    @pytest.mark.asyncio
    async def test_generate_response_empty_response(self, anthropic_client):
        """Test handling of empty response from Anthropic."""
        mock_response = Mock()
        mock_response.content = []
        
        with patch.object(anthropic_client.client.messages, 'create', new_callable=AsyncMock, return_value=mock_response):
            with pytest.raises(LLMConnectionError, match="Empty response from Anthropic"):
                await anthropic_client.generate_response("Test prompt")

    @pytest.mark.asyncio
    async def test_generate_response_rate_limit_error(self, anthropic_client):
        """Test handling of rate limit error from Anthropic."""
        rate_limit_error = anthropic.RateLimitError(
            message="Rate limit exceeded",
            response=Mock(),
            body={}
        )
        rate_limit_error.retry_after = 90
        
        with patch.object(anthropic_client.client.messages, 'create', side_effect=rate_limit_error):
            with pytest.raises(LLMRateLimitError) as exc_info:
                await anthropic_client.generate_response("Test prompt")
            
            assert exc_info.value.retry_after == 90

    @pytest.mark.asyncio
    async def test_generate_response_timeout_error(self, anthropic_client):
        """Test handling of timeout error from Anthropic."""
        timeout_error = anthropic.APITimeoutError(request=Mock())
        
        with patch.object(anthropic_client.client.messages, 'create', side_effect=timeout_error):
            with pytest.raises(LLMTimeoutError) as exc_info:
                await anthropic_client.generate_response("Test prompt")
            
            assert exc_info.value.timeout_duration == 30.0

    @pytest.mark.asyncio
    async def test_generate_response_connection_error(self, anthropic_client):
        """Test handling of connection error from Anthropic."""
        connection_error = anthropic.APIConnectionError(request=Mock())
        
        with patch.object(anthropic_client.client.messages, 'create', side_effect=connection_error):
            with pytest.raises(LLMConnectionError, match="Anthropic connection failed"):
                await anthropic_client.generate_response("Test prompt")

    @pytest.mark.asyncio
    async def test_validate_connection_success(self, anthropic_client):
        """Test successful connection validation for Anthropic."""
        mock_response = Mock()
        mock_response.content = [Mock()]
        
        with patch.object(anthropic_client.client.messages, 'create', new_callable=AsyncMock, return_value=mock_response):
            result = await anthropic_client.validate_connection()
            
        assert result is True

    @pytest.mark.asyncio
    async def test_validate_connection_failure(self, anthropic_client):
        """Test failed connection validation for Anthropic."""
        with patch.object(anthropic_client.client.messages, 'create', side_effect=Exception("Connection failed")):
            result = await anthropic_client.validate_connection()
            
        assert result is False


class TestLocalLLMClient:
    """Test cases for Local LLM client implementation."""

    @pytest.fixture
    def local_client(self):
        """Create Local LLM client for testing."""
        return LocalLLMClient("http://localhost:11434", "llama2")

    @pytest.mark.asyncio
    async def test_generate_response_success(self, local_client):
        """Test successful response generation from local LLM."""
        mock_response_data = {
            "choices": [
                {
                    "message": {
                        "content": "Test response from local LLM"
                    }
                }
            ]
        }
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_response_data
        
        with patch.object(local_client.client, 'post', return_value=mock_response):
            result = await local_client.generate_response("Test prompt")
            
        assert result == "Test response from local LLM"

    @pytest.mark.asyncio
    async def test_generate_response_empty_response(self, local_client):
        """Test handling of empty response from local LLM."""
        mock_response_data = {"choices": []}
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_response_data
        
        with patch.object(local_client.client, 'post', return_value=mock_response):
            with pytest.raises(LLMConnectionError, match="Empty response from local LLM"):
                await local_client.generate_response("Test prompt")

    @pytest.mark.asyncio
    async def test_generate_response_rate_limit_error(self, local_client):
        """Test handling of rate limit error from local LLM."""
        mock_response = Mock()
        mock_response.status_code = 429
        
        with patch.object(local_client.client, 'post', return_value=mock_response):
            with pytest.raises(LLMRateLimitError, match="Local LLM rate limit exceeded"):
                await local_client.generate_response("Test prompt")

    @pytest.mark.asyncio
    async def test_generate_response_http_error(self, local_client):
        """Test handling of HTTP error from local LLM."""
        mock_response = Mock()
        mock_response.status_code = 500
        
        with patch.object(local_client.client, 'post', return_value=mock_response):
            with pytest.raises(LLMConnectionError, match="Local LLM HTTP error: 500"):
                await local_client.generate_response("Test prompt")

    @pytest.mark.asyncio
    async def test_generate_response_timeout_error(self, local_client):
        """Test handling of timeout error from local LLM."""
        with patch.object(local_client.client, 'post', side_effect=httpx.TimeoutException("Request timed out")):
            with pytest.raises(LLMTimeoutError) as exc_info:
                await local_client.generate_response("Test prompt")
            
            assert exc_info.value.timeout_duration == 30.0

    @pytest.mark.asyncio
    async def test_generate_response_connection_error(self, local_client):
        """Test handling of connection error from local LLM."""
        with patch.object(local_client.client, 'post', side_effect=httpx.ConnectError("Connection failed")):
            with pytest.raises(LLMConnectionError, match="Local LLM connection failed"):
                await local_client.generate_response("Test prompt")

    @pytest.mark.asyncio
    async def test_generate_response_json_decode_error(self, local_client):
        """Test handling of JSON decode error from local LLM."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        
        with patch.object(local_client.client, 'post', return_value=mock_response):
            with pytest.raises(LLMConnectionError, match="Invalid JSON response from local LLM"):
                await local_client.generate_response("Test prompt")

    @pytest.mark.asyncio
    async def test_validate_connection_success(self, local_client):
        """Test successful connection validation for local LLM."""
        mock_response = Mock()
        mock_response.status_code = 200
        
        with patch.object(local_client.client, 'post', return_value=mock_response):
            result = await local_client.validate_connection()
            
        assert result is True

    @pytest.mark.asyncio
    async def test_validate_connection_failure(self, local_client):
        """Test failed connection validation for local LLM."""
        with patch.object(local_client.client, 'post', side_effect=Exception("Connection failed")):
            result = await local_client.validate_connection()
            
        assert result is False

    @pytest.mark.asyncio
    async def test_context_manager(self, local_client):
        """Test async context manager functionality."""
        with patch.object(local_client.client, 'aclose') as mock_close:
            async with local_client:
                pass
            mock_close.assert_called_once()


class TestFactoryFunctions:
    """Test cases for factory functions."""

    @pytest.mark.asyncio
    async def test_create_openai_client(self):
        """Test OpenAI client factory function."""
        client = await create_openai_client("test-key", "gpt-4")
        assert isinstance(client, OpenAIClient)
        assert client.model == "gpt-4"

    @pytest.mark.asyncio
    async def test_create_anthropic_client(self):
        """Test Anthropic client factory function."""
        client = await create_anthropic_client("test-key", "claude-3-sonnet-20240229")
        assert isinstance(client, AnthropicClient)
        assert client.model == "claude-3-sonnet-20240229"

    @pytest.mark.asyncio
    async def test_create_local_client(self):
        """Test local client factory function."""
        client = await create_local_client("http://localhost:11434", "llama2")
        assert isinstance(client, LocalLLMClient)
        assert client.model == "llama2"
        assert client.endpoint == "http://localhost:11434"

    def test_create_client_factory_openai(self):
        """Test client factory for OpenAI provider."""
        client = create_client_factory("openai", api_key="test-key", model="gpt-4")
        assert isinstance(client, OpenAIClient)
        assert client.model == "gpt-4"

    def test_create_client_factory_openai_default_model(self):
        """Test client factory for OpenAI provider with default model."""
        client = create_client_factory("openai", api_key="test-key")
        assert isinstance(client, OpenAIClient)
        assert client.model == "gpt-4"

    def test_create_client_factory_openai_missing_key(self):
        """Test client factory for OpenAI provider with missing API key."""
        with pytest.raises(ValueError, match="OpenAI API key is required"):
            create_client_factory("openai")

    def test_create_client_factory_anthropic(self):
        """Test client factory for Anthropic provider."""
        client = create_client_factory("anthropic", api_key="test-key", model="claude-3-opus-20240229")
        assert isinstance(client, AnthropicClient)
        assert client.model == "claude-3-opus-20240229"

    def test_create_client_factory_anthropic_default_model(self):
        """Test client factory for Anthropic provider with default model."""
        client = create_client_factory("anthropic", api_key="test-key")
        assert isinstance(client, AnthropicClient)
        assert client.model == "claude-3-sonnet-20240229"

    def test_create_client_factory_anthropic_missing_key(self):
        """Test client factory for Anthropic provider with missing API key."""
        with pytest.raises(ValueError, match="Anthropic API key is required"):
            create_client_factory("anthropic")

    def test_create_client_factory_local(self):
        """Test client factory for local provider."""
        client = create_client_factory("local", endpoint="http://localhost:11434", model="llama2")
        assert isinstance(client, LocalLLMClient)
        assert client.model == "llama2"
        assert client.endpoint == "http://localhost:11434"

    def test_create_client_factory_local_default_model(self):
        """Test client factory for local provider with default model."""
        client = create_client_factory("local", endpoint="http://localhost:11434")
        assert isinstance(client, LocalLLMClient)
        assert client.model == "llama2"

    def test_create_client_factory_local_missing_endpoint(self):
        """Test client factory for local provider with missing endpoint."""
        with pytest.raises(ValueError, match="Local LLM endpoint is required"):
            create_client_factory("local")

    def test_create_client_factory_unsupported_provider(self):
        """Test client factory with unsupported provider."""
        with pytest.raises(ValueError, match="Unsupported LLM provider: unsupported"):
            create_client_factory("unsupported")


class TestErrorClasses:
    """Test cases for error classes."""

    def test_llm_rate_limit_error(self):
        """Test LLMRateLimitError initialization."""
        error = LLMRateLimitError("Rate limit exceeded", 120)
        assert str(error) == "Rate limit exceeded"
        assert error.retry_after == 120

    def test_llm_rate_limit_error_default_retry(self):
        """Test LLMRateLimitError with default retry_after."""
        error = LLMRateLimitError("Rate limit exceeded")
        assert error.retry_after == 60

    def test_llm_validation_error(self):
        """Test LLMValidationError initialization."""
        error = LLMValidationError("Validation failed", "raw response", ["error1", "error2"])
        assert str(error) == "Validation failed"
        assert error.raw_response == "raw response"
        assert error.validation_errors == ["error1", "error2"]

    def test_llm_timeout_error(self):
        """Test LLMTimeoutError initialization."""
        error = LLMTimeoutError("Request timed out", 30.0)
        assert str(error) == "Request timed out"
        assert error.timeout_duration == 30.0