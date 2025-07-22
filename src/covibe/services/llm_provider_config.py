"""LLM provider configuration and management."""

import os
import yaml
import asyncio
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from .llm_client import (
    LLMClient, 
    create_openai_client, 
    create_anthropic_client, 
    create_local_client,
    LLMConnectionError,
    LLMRateLimitError,
    LLMTimeoutError
)
from ..utils.error_handling import ResearchError, NetworkError, RateLimitError
from ..utils.monitoring import performance_monitor, record_error


@dataclass
class ProviderHealth:
    """Health status for an LLM provider."""
    is_healthy: bool = True
    last_check: datetime = field(default_factory=datetime.now)
    consecutive_failures: int = 0
    last_failure_reason: Optional[str] = None
    rate_limit_reset: Optional[datetime] = None
    
    def is_rate_limited(self) -> bool:
        """Check if provider is currently rate limited."""
        if not self.rate_limit_reset:
            return False
        return datetime.now() < self.rate_limit_reset
    
    def mark_failure(self, reason: str, rate_limit_reset: Optional[datetime] = None):
        """Mark a failure for this provider."""
        self.is_healthy = False
        self.last_check = datetime.now()
        self.consecutive_failures += 1
        self.last_failure_reason = reason
        if rate_limit_reset:
            self.rate_limit_reset = rate_limit_reset
    
    def mark_success(self):
        """Mark a successful interaction with this provider."""
        self.is_healthy = True
        self.last_check = datetime.now()
        self.consecutive_failures = 0
        self.last_failure_reason = None
        self.rate_limit_reset = None


@dataclass
class ProviderConfig:
    """Configuration for an LLM provider."""
    name: str
    api_key_env: Optional[str]
    organization_env: Optional[str] = None
    base_url: str
    models: List[str]
    default_model: str
    requests_per_minute: int = 60
    tokens_per_minute: int = 90000
    health: ProviderHealth = field(default_factory=ProviderHealth)
    
    def get_api_key(self) -> Optional[str]:
        """Get API key from environment."""
        if self.api_key_env:
            return os.getenv(self.api_key_env)
        return None
    
    def get_organization(self) -> Optional[str]:
        """Get organization ID from environment."""
        if self.organization_env:
            return os.getenv(self.organization_env)
        return None
    
    def is_available(self) -> bool:
        """Check if provider is available (has API key if required)."""
        if self.name == "local":
            return True  # Local providers don't need API keys
        return bool(self.get_api_key())
    
    def is_usable(self) -> bool:
        """Check if provider is both available and healthy."""
        return self.is_available() and self.health.is_healthy and not self.health.is_rate_limited()


@dataclass
class ProvidersConfig:
    """Configuration for all LLM providers."""
    providers: Dict[str, ProviderConfig]
    default_provider: str
    fallback_providers: List[str]
    retry_config: Dict[str, Any]
    
    def get_available_providers(self) -> List[str]:
        """Get list of available providers."""
        return [
            name for name, config in self.providers.items()
            if config.is_available()
        ]
    
    def get_usable_providers(self) -> List[str]:
        """Get list of usable providers (available and healthy)."""
        return [
            name for name, config in self.providers.items()
            if config.is_usable()
        ]
    
    def get_provider_config(self, provider_name: str) -> Optional[ProviderConfig]:
        """Get configuration for specific provider."""
        return self.providers.get(provider_name)


class ProviderConfigError(Exception):
    """Error in provider configuration."""
    pass


async def load_provider_config(config_path: Optional[Path] = None) -> ProvidersConfig:
    """Load LLM provider configuration from YAML file.
    
    Args:
        config_path: Path to configuration file (uses default if not provided)
        
    Returns:
        ProvidersConfig object with all provider configurations
        
    Raises:
        ProviderConfigError: If configuration is invalid
    """
    if not config_path:
        config_path = Path("config/llm/providers.yaml")
    
    if not config_path.exists():
        # Return default configuration if file doesn't exist
        return get_default_provider_config()
    
    try:
        with open(config_path, 'r') as f:
            data = yaml.safe_load(f)
        
        # Parse provider configurations
        providers = {}
        for name, provider_data in data.get("providers", {}).items():
            # Get rate limits for this provider
            rate_limits = data.get("rate_limits", {}).get(name, {})
            
            providers[name] = ProviderConfig(
                name=name,
                api_key_env=provider_data.get("api_key_env"),
                organization_env=provider_data.get("organization_env"),
                base_url=provider_data.get("base_url", ""),
                models=provider_data.get("models", []),
                default_model=provider_data.get("default_model", ""),
                requests_per_minute=rate_limits.get("requests_per_minute", 60),
                tokens_per_minute=rate_limits.get("tokens_per_minute", 90000)
            )
        
        return ProvidersConfig(
            providers=providers,
            default_provider=data.get("default_provider", "openai"),
            fallback_providers=data.get("fallback_providers", []),
            retry_config=data.get("retry_config", {})
        )
        
    except yaml.YAMLError as e:
        raise ProviderConfigError(f"Invalid YAML in provider config: {e}")
    except Exception as e:
        raise ProviderConfigError(f"Error loading provider config: {e}")


def get_default_provider_config() -> ProvidersConfig:
    """Get default provider configuration."""
    return ProvidersConfig(
        providers={
            "openai": ProviderConfig(
                name="openai",
                api_key_env="OPENAI_API_KEY",
                organization_env="OPENAI_ORG_ID",
                base_url="https://api.openai.com/v1",
                models=["gpt-4", "gpt-3.5-turbo"],
                default_model="gpt-4"
            ),
            "anthropic": ProviderConfig(
                name="anthropic",
                api_key_env="ANTHROPIC_API_KEY",
                base_url="https://api.anthropic.com",
                models=["claude-3-sonnet-20240229"],
                default_model="claude-3-sonnet-20240229"
            ),
            "local": ProviderConfig(
                name="local",
                api_key_env=None,
                base_url="http://localhost:11434",
                models=["llama2"],
                default_model="llama2"
            )
        },
        default_provider="openai",
        fallback_providers=["anthropic", "local"],
        retry_config={
            "max_attempts": 3,
            "base_delay": 2.0,
            "max_delay": 60.0
        }
    )


@performance_monitor("create_llm_client", "llm")
async def create_llm_client_from_config(
    provider_name: str,
    config: ProvidersConfig,
    model: Optional[str] = None
) -> LLMClient:
    """Create LLM client from provider configuration.
    
    Args:
        provider_name: Name of the provider
        config: Provider configuration
        model: Specific model to use (uses default if not provided)
        
    Returns:
        LLMClient instance
        
    Raises:
        ResearchError: If provider is not available or configuration is invalid
    """
    provider_config = config.get_provider_config(provider_name)
    if not provider_config:
        raise ResearchError(f"Unknown provider: {provider_name}")
    
    if not provider_config.is_available():
        raise ResearchError(
            f"Provider {provider_name} is not available",
            suggestions=[f"Set {provider_config.api_key_env} environment variable"]
        )
    
    # Use specified model or default
    if not model:
        model = provider_config.default_model
    
    # Create client based on provider type
    if provider_name == "openai":
        return await create_openai_client(
            api_key=provider_config.get_api_key(),
            model=model,
            organization=provider_config.get_organization()
        )
    elif provider_name == "anthropic":
        return await create_anthropic_client(
            api_key=provider_config.get_api_key(),
            model=model
        )
    elif provider_name == "local":
        return await create_local_client(
            endpoint=provider_config.base_url,
            model=model
        )
    else:
        raise ResearchError(f"Unsupported provider: {provider_name}")


async def create_llm_client_with_fallback(
    config: ProvidersConfig,
    preferred_provider: Optional[str] = None
) -> Optional[LLMClient]:
    """Create LLM client with automatic fallback to available providers.
    
    Args:
        config: Provider configuration
        preferred_provider: Preferred provider to try first
        
    Returns:
        LLMClient instance or None if no providers available
    """
    # Determine provider order
    providers_to_try = []
    
    if preferred_provider and preferred_provider in config.providers:
        providers_to_try.append(preferred_provider)
    
    if config.default_provider not in providers_to_try:
        providers_to_try.append(config.default_provider)
    
    for fallback in config.fallback_providers:
        if fallback not in providers_to_try:
            providers_to_try.append(fallback)
    
    # Try each provider in order
    for provider_name in providers_to_try:
        try:
            provider_config = config.get_provider_config(provider_name)
            if provider_config and provider_config.is_usable():
                client = await create_llm_client_from_config(provider_name, config)
                
                # Validate connection
                if await client.validate_connection():
                    provider_config.health.mark_success()
                    return client
                else:
                    provider_config.health.mark_failure("Connection validation failed")
                    
        except Exception as e:
            # Mark provider as unhealthy
            provider_config = config.get_provider_config(provider_name)
            if provider_config:
                provider_config.health.mark_failure(str(e))
            continue
    
    return None


class ProviderManager:
    """Manages LLM providers with health checking and automatic switching."""
    
    def __init__(self, config: ProvidersConfig):
        """Initialize provider manager.
        
        Args:
            config: Provider configuration
        """
        self.config = config
        self.active_clients: Dict[str, LLMClient] = {}
        self.health_check_interval = 300  # 5 minutes
        self._health_check_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start background health checking."""
        if not self._health_check_task:
            self._health_check_task = asyncio.create_task(self._health_check_loop())
    
    async def stop(self):
        """Stop background health checking."""
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
            self._health_check_task = None
    
    async def _health_check_loop(self):
        """Background task to periodically check provider health."""
        while True:
            try:
                await asyncio.sleep(self.health_check_interval)
                await self.check_all_provider_health()
            except asyncio.CancelledError:
                break
            except Exception as e:
                record_error(e, "provider_health_check")
    
    async def check_all_provider_health(self):
        """Check health of all providers."""
        for provider_name, provider_config in self.config.providers.items():
            if provider_config.is_available():
                await self.check_provider_health(provider_name)
    
    async def check_provider_health(self, provider_name: str) -> bool:
        """Check health of a specific provider.
        
        Args:
            provider_name: Name of provider to check
            
        Returns:
            True if provider is healthy, False otherwise
        """
        provider_config = self.config.get_provider_config(provider_name)
        if not provider_config or not provider_config.is_available():
            return False
        
        try:
            # Create a test client
            client = await create_llm_client_from_config(provider_name, self.config)
            
            # Validate connection
            if await client.validate_connection():
                provider_config.health.mark_success()
                return True
            else:
                provider_config.health.mark_failure("Health check failed")
                return False
                
        except (LLMConnectionError, LLMTimeoutError) as e:
            provider_config.health.mark_failure(f"Connection error: {str(e)}")
            return False
        except LLMRateLimitError as e:
            # Calculate rate limit reset time
            reset_time = datetime.now() + timedelta(seconds=e.retry_after)
            provider_config.health.mark_failure(f"Rate limited: {str(e)}", reset_time)
            return False
        except Exception as e:
            provider_config.health.mark_failure(f"Unexpected error: {str(e)}")
            return False
    
    async def get_best_client(
        self,
        preferred_provider: Optional[str] = None,
        required_model: Optional[str] = None
    ) -> Tuple[Optional[LLMClient], Optional[str]]:
        """Get the best available LLM client.
        
        Args:
            preferred_provider: Preferred provider to try first
            required_model: Specific model requirement
            
        Returns:
            Tuple of (LLMClient, provider_name) or (None, None) if no providers available
        """
        # Get ordered list of providers to try
        providers_to_try = self._get_provider_order(preferred_provider)
        
        # Filter by model availability if required
        if required_model:
            providers_to_try = [
                p for p in providers_to_try
                if self.config.get_provider_config(p) and 
                required_model in self.config.get_provider_config(p).models
            ]
        
        # Try each provider
        for provider_name in providers_to_try:
            provider_config = self.config.get_provider_config(provider_name)
            if not provider_config or not provider_config.is_usable():
                continue
            
            try:
                # Use cached client if available and healthy
                if provider_name in self.active_clients:
                    client = self.active_clients[provider_name]
                    if await client.validate_connection():
                        provider_config.health.mark_success()
                        return client, provider_name
                    else:
                        # Remove invalid client
                        del self.active_clients[provider_name]
                
                # Create new client
                model = required_model or provider_config.default_model
                client = await create_llm_client_from_config(provider_name, self.config, model)
                
                if await client.validate_connection():
                    provider_config.health.mark_success()
                    self.active_clients[provider_name] = client
                    return client, provider_name
                else:
                    provider_config.health.mark_failure("Connection validation failed")
                
            except (LLMConnectionError, LLMTimeoutError) as e:
                provider_config.health.mark_failure(f"Connection error: {str(e)}")
            except LLMRateLimitError as e:
                reset_time = datetime.now() + timedelta(seconds=e.retry_after)
                provider_config.health.mark_failure(f"Rate limited: {str(e)}", reset_time)
            except Exception as e:
                provider_config.health.mark_failure(f"Unexpected error: {str(e)}")
        
        return None, None
    
    def _get_provider_order(self, preferred_provider: Optional[str] = None) -> List[str]:
        """Get ordered list of providers to try."""
        providers_to_try = []
        
        # Add preferred provider first
        if preferred_provider and preferred_provider in self.config.providers:
            providers_to_try.append(preferred_provider)
        
        # Add default provider
        if self.config.default_provider not in providers_to_try:
            providers_to_try.append(self.config.default_provider)
        
        # Add fallback providers
        for fallback in self.config.fallback_providers:
            if fallback not in providers_to_try:
                providers_to_try.append(fallback)
        
        # Sort by health status (healthy providers first)
        def sort_key(provider_name: str) -> Tuple[bool, bool, int]:
            config = self.config.get_provider_config(provider_name)
            if not config:
                return (False, False, 999)
            
            return (
                config.is_usable(),  # Usable providers first
                config.health.is_healthy,  # Healthy providers first
                config.health.consecutive_failures  # Fewer failures first
            )
        
        return sorted(providers_to_try, key=sort_key, reverse=True)
    
    async def handle_provider_error(
        self,
        provider_name: str,
        error: Exception
    ) -> Optional[Tuple[LLMClient, str]]:
        """Handle provider error and attempt fallback.
        
        Args:
            provider_name: Name of provider that failed
            error: Error that occurred
            
        Returns:
            Tuple of (fallback_client, fallback_provider) or None
        """
        provider_config = self.config.get_provider_config(provider_name)
        if provider_config:
            # Mark provider as unhealthy
            if isinstance(error, LLMRateLimitError):
                reset_time = datetime.now() + timedelta(seconds=error.retry_after)
                provider_config.health.mark_failure(f"Rate limited: {str(error)}", reset_time)
            else:
                provider_config.health.mark_failure(str(error))
            
            # Remove from active clients
            if provider_name in self.active_clients:
                del self.active_clients[provider_name]
        
        # Try to get a fallback client
        return await self.get_best_client()
    
    def get_provider_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all providers."""
        status = {}
        for name, config in self.config.providers.items():
            status[name] = {
                "available": config.is_available(),
                "healthy": config.health.is_healthy,
                "rate_limited": config.health.is_rate_limited(),
                "consecutive_failures": config.health.consecutive_failures,
                "last_check": config.health.last_check.isoformat() if config.health.last_check else None,
                "last_failure_reason": config.health.last_failure_reason,
                "rate_limit_reset": config.health.rate_limit_reset.isoformat() if config.health.rate_limit_reset else None
            }
        return status