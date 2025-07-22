"""LLM client protocol interface and base error classes."""

import asyncio
import json
from typing import Protocol, Dict, Any, Optional
from abc import abstractmethod

import httpx
import openai
import anthropic


class LLMError(Exception):
    """Base class for LLM-related errors."""
    pass


class LLMConnectionError(LLMError):
    """LLM service connection failed."""
    pass


class LLMRateLimitError(LLMError):
    """LLM service rate limit exceeded."""
    
    def __init__(self, message: str, retry_after: int = 60):
        super().__init__(message)
        self.retry_after = retry_after


class LLMValidationError(LLMError):
    """LLM response validation failed."""
    
    def __init__(self, message: str, raw_response: str, validation_errors: list[str]):
        super().__init__(message)
        self.raw_response = raw_response
        self.validation_errors = validation_errors


class LLMTimeoutError(LLMError):
    """LLM request timed out."""
    
    def __init__(self, message: str, timeout_duration: float):
        super().__init__(message)
        self.timeout_duration = timeout_duration


class LLMClient(Protocol):
    """Protocol for LLM client implementations."""
    
    @abstractmethod
    async def generate_response(
        self, 
        prompt: str, 
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> str:
        """Generate response from LLM.
        
        Args:
            prompt: The input prompt for the LLM
            max_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature (0.0 to 1.0)
            
        Returns:
            Generated response text
            
        Raises:
            LLMConnectionError: If connection to LLM service fails
            LLMRateLimitError: If rate limit is exceeded
            LLMTimeoutError: If request times out
        """
        
    @abstractmethod
    async def validate_connection(self) -> bool:
        """Validate LLM service connection.
        
        Returns:
            True if connection is valid, False otherwise
        """


class OpenAIClient:
    """OpenAI LLM client implementation."""
    
    def __init__(self, api_key: str, model: str):
        """Initialize OpenAI client.
        
        Args:
            api_key: OpenAI API key
            model: Model name (e.g., 'gpt-4', 'gpt-3.5-turbo')
        """
        self.client = openai.AsyncOpenAI(api_key=api_key)
        self.model = model
        self.provider = "openai"
    
    async def generate_response(
        self, 
        prompt: str, 
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> str:
        """Generate response from OpenAI LLM."""
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
                timeout=30.0
            )
            
            if not response.choices or not response.choices[0].message.content:
                raise LLMConnectionError("Empty response from OpenAI")
                
            return response.choices[0].message.content
            
        except openai.RateLimitError as e:
            retry_after = getattr(e, 'retry_after', 60)
            raise LLMRateLimitError(f"OpenAI rate limit exceeded: {e}", retry_after)
        except openai.APITimeoutError as e:
            raise LLMTimeoutError(f"OpenAI request timed out: {e}", 30.0)
        except openai.APIConnectionError as e:
            raise LLMConnectionError(f"OpenAI connection failed: {e}")
        except openai.APIError as e:
            raise LLMConnectionError(f"OpenAI API error: {e}")
        except Exception as e:
            raise LLMConnectionError(f"Unexpected OpenAI error: {e}")
    
    async def validate_connection(self) -> bool:
        """Validate OpenAI service connection."""
        try:
            # Make a minimal request to test connection
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=1,
                timeout=10.0
            )
            return response.choices is not None
        except Exception:
            return False


class AnthropicClient:
    """Anthropic LLM client implementation."""
    
    def __init__(self, api_key: str, model: str):
        """Initialize Anthropic client.
        
        Args:
            api_key: Anthropic API key
            model: Model name (e.g., 'claude-3-opus', 'claude-3-sonnet')
        """
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
        self.model = model
        self.provider = "anthropic"
    
    async def generate_response(
        self, 
        prompt: str, 
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> str:
        """Generate response from Anthropic LLM."""
        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}],
                timeout=30.0
            )
            
            if not response.content or not response.content[0].text:
                raise LLMConnectionError("Empty response from Anthropic")
                
            return response.content[0].text
            
        except anthropic.RateLimitError as e:
            retry_after = getattr(e, 'retry_after', 60)
            raise LLMRateLimitError(f"Anthropic rate limit exceeded: {e}", retry_after)
        except anthropic.APITimeoutError as e:
            raise LLMTimeoutError(f"Anthropic request timed out: {e}", 30.0)
        except anthropic.APIConnectionError as e:
            raise LLMConnectionError(f"Anthropic connection failed: {e}")
        except anthropic.APIError as e:
            raise LLMConnectionError(f"Anthropic API error: {e}")
        except Exception as e:
            raise LLMConnectionError(f"Unexpected Anthropic error: {e}")
    
    async def validate_connection(self) -> bool:
        """Validate Anthropic service connection."""
        try:
            # Make a minimal request to test connection
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=1,
                messages=[{"role": "user", "content": "test"}],
                timeout=10.0
            )
            return response.content is not None
        except Exception:
            return False


class LocalLLMClient:
    """Local LLM client implementation for self-hosted models."""
    
    def __init__(self, endpoint: str, model: str):
        """Initialize local LLM client.
        
        Args:
            endpoint: Local LLM service endpoint
            model: Model name
        """
        self.endpoint = endpoint.rstrip('/')
        self.model = model
        self.provider = "local"
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def generate_response(
        self, 
        prompt: str, 
        max_tokens: int = 1000,
        temperature: float = 0.7
    ) -> str:
        """Generate response from local LLM."""
        try:
            # Use OpenAI-compatible API format for local models
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": temperature,
                "stream": False
            }
            
            response = await self.client.post(
                f"{self.endpoint}/v1/chat/completions",
                json=payload,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 429:
                raise LLMRateLimitError("Local LLM rate limit exceeded", 60)
            elif response.status_code >= 400:
                raise LLMConnectionError(f"Local LLM HTTP error: {response.status_code}")
            
            data = response.json()
            
            if not data.get("choices") or not data["choices"][0].get("message", {}).get("content"):
                raise LLMConnectionError("Empty response from local LLM")
                
            return data["choices"][0]["message"]["content"]
            
        except LLMRateLimitError:
            # Re-raise our own rate limit errors
            raise
        except httpx.TimeoutException as e:
            raise LLMTimeoutError(f"Local LLM request timed out: {e}", 30.0)
        except httpx.ConnectError as e:
            raise LLMConnectionError(f"Local LLM connection failed: {e}")
        except json.JSONDecodeError as e:
            raise LLMConnectionError(f"Invalid JSON response from local LLM: {e}")
        except Exception as e:
            raise LLMConnectionError(f"Unexpected local LLM error: {e}")
    
    async def validate_connection(self) -> bool:
        """Validate local LLM service connection."""
        try:
            # Test connection with a minimal request
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": "test"}],
                "max_tokens": 1,
                "stream": False
            }
            
            response = await self.client.post(
                f"{self.endpoint}/v1/chat/completions",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=10.0
            )
            
            return response.status_code == 200
        except Exception:
            return False
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.client.aclose()


# Factory functions for creating LLM clients
async def create_openai_client(api_key: str, model: str) -> LLMClient:
    """Create OpenAI client implementation.
    
    Args:
        api_key: OpenAI API key
        model: Model name (e.g., 'gpt-4', 'gpt-3.5-turbo')
        
    Returns:
        LLMClient implementation for OpenAI
    """
    return OpenAIClient(api_key, model)


async def create_anthropic_client(api_key: str, model: str) -> LLMClient:
    """Create Anthropic client implementation.
    
    Args:
        api_key: Anthropic API key
        model: Model name (e.g., 'claude-3-opus', 'claude-3-sonnet')
        
    Returns:
        LLMClient implementation for Anthropic
    """
    return AnthropicClient(api_key, model)


async def create_local_client(endpoint: str, model: str) -> LLMClient:
    """Create local LLM client implementation.
    
    Args:
        endpoint: Local LLM service endpoint
        model: Model name
        
    Returns:
        LLMClient implementation for local models
    """
    return LocalLLMClient(endpoint, model)


def create_client_factory(provider: str, **kwargs) -> LLMClient:
    """Create LLM client based on provider configuration.
    
    Args:
        provider: Provider name ('openai', 'anthropic', 'local')
        **kwargs: Provider-specific configuration
        
    Returns:
        LLMClient implementation for the specified provider
        
    Raises:
        ValueError: If provider is not supported
    """
    if provider == "openai":
        api_key = kwargs.get("api_key")
        model = kwargs.get("model", "gpt-4")
        if not api_key:
            raise ValueError("OpenAI API key is required")
        return OpenAIClient(api_key, model)
    
    elif provider == "anthropic":
        api_key = kwargs.get("api_key")
        model = kwargs.get("model", "claude-3-sonnet-20240229")
        if not api_key:
            raise ValueError("Anthropic API key is required")
        return AnthropicClient(api_key, model)
    
    elif provider == "local":
        endpoint = kwargs.get("endpoint")
        model = kwargs.get("model", "llama2")
        if not endpoint:
            raise ValueError("Local LLM endpoint is required")
        return LocalLLMClient(endpoint, model)
    
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")