"""Unit tests for LLM provider configuration management."""

import os
import tempfile
import yaml
from pathlib import Path
import pytest
from unittest.mock import patch, Mock, AsyncMock

from src.covibe.services.llm_provider_config import (
    ProviderConfig,
    ProviderHealth,
    ProvidersConfig,
    ProviderConfigError,
    ProviderManager,
    load_provider_config,
    get_default_provider_config,
    create_llm_client_from_config,
    create_llm_client_with_fallback
)


class TestProviderConfig:
    """Test ProviderConfig dataclass."""
    
    def test_provider_config_creation(self):
        """Test creating ProviderConfig."""
        config = ProviderConfig(
            name="openai",
            api_key_env="OPENAI_API_KEY",
            base_url="https://api.openai.com/v1",
            models=["gpt-4", "gpt-3.5-turbo"],
            default_model="gpt-4"
        )
        
        assert config.name == "openai"
        assert config.api_key_env == "OPENAI_API_KEY"
        assert config.base_url == "https://api.openai.com/v1"
        assert config.models == ["gpt-4", "gpt-3.5-turbo"]
        assert config.default_model == "gpt-4"
        assert config.requests_per_minute == 60  # Default value
    
    @patch.dict(os.environ, {"TEST_API_KEY": "test-key-123"})
    def test_get_api_key_exists(self):
        """Test getting API key when environment variable exists."""
        config = ProviderConfig(
            name="test",
            api_key_env="TEST_API_KEY",
            base_url="https://api.test.com",
            models=["test-model"],
            default_model="test-model"
        )
        
        assert config.get_api_key() == "test-key-123"
    
    def test_get_api_key_none(self):
        """Test getting API key when no env var is set."""
        config = ProviderConfig(
            name="test",
            api_key_env="NONEXISTENT_KEY",
            base_url="https://api.test.com",
            models=["test-model"],
            default_model="test-model"
        )
        
        assert config.get_api_key() is None
    
    def test_get_api_key_no_env_var(self):
        """Test getting API key when api_key_env is None."""
        config = ProviderConfig(
            name="local",
            api_key_env=None,
            base_url="http://localhost:11434",
            models=["llama2"],
            default_model="llama2"
        )
        
        assert config.get_api_key() is None
    
    @patch.dict(os.environ, {"TEST_API_KEY": "test-key-123"})
    def test_is_available_with_key(self):
        """Test availability check when API key is available."""
        config = ProviderConfig(
            name="test",
            api_key_env="TEST_API_KEY",
            base_url="https://api.test.com",
            models=["test-model"],
            default_model="test-model"
        )
        
        assert config.is_available() is True
    
    def test_is_available_without_key(self):
        """Test availability check when API key is missing."""
        config = ProviderConfig(
            name="test",
            api_key_env="NONEXISTENT_KEY",
            base_url="https://api.test.com",
            models=["test-model"],
            default_model="test-model"
        )
        
        assert config.is_available() is False
    
    def test_is_available_local(self):
        """Test availability check for local provider (no key needed)."""
        config = ProviderConfig(
            name="local",
            api_key_env=None,
            base_url="http://localhost:11434",
            models=["llama2"],
            default_model="llama2"
        )
        
        assert config.is_available() is True


class TestProvidersConfig:
    """Test ProvidersConfig dataclass."""
    
    @pytest.fixture
    def sample_providers_config(self):
        """Create sample providers configuration."""
        providers = {
            "openai": ProviderConfig(
                name="openai",
                api_key_env="OPENAI_API_KEY",
                base_url="https://api.openai.com/v1",
                models=["gpt-4"],
                default_model="gpt-4"
            ),
            "local": ProviderConfig(
                name="local",
                api_key_env=None,
                base_url="http://localhost:11434",
                models=["llama2"],
                default_model="llama2"
            )
        }
        
        return ProvidersConfig(
            providers=providers,
            default_provider="openai",
            fallback_providers=["local"],
            retry_config={"max_attempts": 3}
        )
    
    def test_get_provider_config(self, sample_providers_config):
        """Test getting specific provider configuration."""
        config = sample_providers_config.get_provider_config("openai")
        assert config is not None
        assert config.name == "openai"
        
        config = sample_providers_config.get_provider_config("nonexistent")
        assert config is None
    
    @patch.dict(os.environ, {}, clear=True)
    def test_get_available_providers_none(self, sample_providers_config):
        """Test getting available providers when no API keys are set."""
        available = sample_providers_config.get_available_providers()
        assert available == ["local"]  # Only local doesn't need API key
    
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    def test_get_available_providers_with_key(self, sample_providers_config):
        """Test getting available providers when API key is set."""
        available = sample_providers_config.get_available_providers()
        assert "openai" in available
        assert "local" in available


class TestLoadProviderConfig:
    """Test loading provider configuration from YAML."""
    
    @pytest.mark.asyncio
    async def test_load_valid_config(self):
        """Test loading valid provider configuration."""
        config_data = {
            "providers": {
                "openai": {
                    "api_key_env": "OPENAI_API_KEY",
                    "base_url": "https://api.openai.com/v1",
                    "models": ["gpt-4", "gpt-3.5-turbo"],
                    "default_model": "gpt-4"
                },
                "local": {
                    "base_url": "http://localhost:11434",
                    "models": ["llama2"],
                    "default_model": "llama2"
                }
            },
            "default_provider": "openai",
            "fallback_providers": ["local"],
            "rate_limits": {
                "openai": {
                    "requests_per_minute": 60,
                    "tokens_per_minute": 90000
                }
            },
            "retry_config": {
                "max_attempts": 3,
                "base_delay": 2.0
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            config_path = Path(f.name)
        
        try:
            config = await load_provider_config(config_path)
            
            assert config.default_provider == "openai"
            assert config.fallback_providers == ["local"]
            assert "openai" in config.providers
            assert "local" in config.providers
            
            openai_config = config.providers["openai"]
            assert openai_config.api_key_env == "OPENAI_API_KEY"
            assert openai_config.requests_per_minute == 60
            
        finally:
            config_path.unlink()
    
    @pytest.mark.asyncio
    async def test_load_nonexistent_file(self):
        """Test loading non-existent configuration file returns default."""
        config = await load_provider_config(Path("/nonexistent/config.yaml"))
        
        # Should return default configuration
        assert isinstance(config, ProvidersConfig)
        assert config.default_provider == "openai"
    
    @pytest.mark.asyncio
    async def test_load_invalid_yaml(self):
        """Test loading invalid YAML raises error."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("invalid: yaml: content: [")
            config_path = Path(f.name)
        
        try:
            with pytest.raises(ProviderConfigError, match="Invalid YAML"):
                await load_provider_config(config_path)
        finally:
            config_path.unlink()


class TestDefaultProviderConfig:
    """Test default provider configuration."""
    
    def test_get_default_config(self):
        """Test getting default provider configuration."""
        config = get_default_provider_config()
        
        assert isinstance(config, ProvidersConfig)
        assert config.default_provider == "openai"
        assert "openai" in config.providers
        assert "anthropic" in config.providers
        assert "local" in config.providers
        
        openai_config = config.providers["openai"]
        assert openai_config.api_key_env == "OPENAI_API_KEY"
        assert openai_config.default_model == "gpt-4"


class TestCreateLLMClient:
    """Test creating LLM clients from configuration."""
    
    @pytest.fixture
    def sample_config(self):
        """Create sample configuration for testing."""
        return get_default_provider_config()
    
    @pytest.mark.asyncio
    async def test_create_client_unknown_provider(self, sample_config):
        """Test creating client for unknown provider."""
        from src.covibe.utils.error_handling import ResearchError
        
        with pytest.raises(ResearchError, match="Unknown provider"):
            await create_llm_client_from_config("unknown", sample_config)
    
    @pytest.mark.asyncio
    @patch.dict(os.environ, {}, clear=True)
    async def test_create_client_unavailable_provider(self, sample_config):
        """Test creating client for unavailable provider."""
        from src.covibe.utils.error_handling import ResearchError
        
        with pytest.raises(ResearchError, match="not available"):
            await create_llm_client_from_config("openai", sample_config)
    
    @pytest.mark.asyncio
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch("src.covibe.services.llm_provider_config.create_openai_client")
    async def test_create_openai_client(self, mock_create_openai, sample_config):
        """Test creating OpenAI client."""
        mock_client = Mock()
        mock_create_openai.return_value = mock_client
        
        client = await create_llm_client_from_config("openai", sample_config)
        
        mock_create_openai.assert_called_once_with(
            api_key="test-key",
            model="gpt-4"
        )
        assert client == mock_client
    
    @pytest.mark.asyncio
    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"})
    @patch("src.covibe.services.llm_provider_config.create_anthropic_client")
    async def test_create_anthropic_client(self, mock_create_anthropic, sample_config):
        """Test creating Anthropic client."""
        mock_client = Mock()
        mock_create_anthropic.return_value = mock_client
        
        client = await create_llm_client_from_config("anthropic", sample_config)
        
        mock_create_anthropic.assert_called_once_with(
            api_key="test-key",
            model="claude-3-sonnet-20240229"
        )
        assert client == mock_client
    
    @pytest.mark.asyncio
    @patch("src.covibe.services.llm_provider_config.create_local_client")
    async def test_create_local_client(self, mock_create_local, sample_config):
        """Test creating local client."""
        mock_client = Mock()
        mock_create_local.return_value = mock_client
        
        client = await create_llm_client_from_config("local", sample_config)
        
        mock_create_local.assert_called_once_with(
            endpoint="http://localhost:11434",
            model="llama2"
        )
        assert client == mock_client


class TestCreateClientWithFallback:
    """Test creating LLM client with automatic fallback."""
    
    @pytest.fixture
    def sample_config(self):
        """Create sample configuration for testing."""
        return get_default_provider_config()
    
    @pytest.mark.asyncio
    @patch("src.covibe.services.llm_provider_config.create_llm_client_from_config")
    async def test_fallback_success_first_try(self, mock_create_client, sample_config):
        """Test successful client creation on first try."""
        mock_client = AsyncMock()
        mock_client.validate_connection.return_value = True
        mock_create_client.return_value = mock_client
        
        client = await create_llm_client_with_fallback(sample_config)
        
        assert client == mock_client
        mock_create_client.assert_called_once()
    
    @pytest.mark.asyncio
    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key-1", "ANTHROPIC_API_KEY": "test-key-2"})
    @patch("src.covibe.services.llm_provider_config.create_llm_client_from_config")
    async def test_fallback_success_second_try(self, mock_create_client, sample_config):
        """Test successful client creation on fallback."""
        # First call fails, second succeeds
        mock_client = AsyncMock()
        mock_client.validate_connection.return_value = True
        
        mock_create_client.side_effect = [Exception("First failed"), mock_client]
        
        client = await create_llm_client_with_fallback(sample_config)
        
        assert client == mock_client
        assert mock_create_client.call_count == 2
    
    @pytest.mark.asyncio
    @patch("src.covibe.services.llm_provider_config.create_llm_client_from_config")
    async def test_fallback_all_fail(self, mock_create_client, sample_config):
        """Test when all providers fail."""
        mock_create_client.side_effect = Exception("All failed")
        
        client = await create_llm_client_with_fallback(sample_config)
        
        assert client is None


class TestProviderHealth:
    """Test ProviderHealth functionality."""
    
    def test_provider_health_creation(self):
        """Test creating ProviderHealth with defaults."""
        health = ProviderHealth()
        
        assert health.is_healthy is True
        assert health.consecutive_failures == 0
        assert health.last_failure_reason is None
        assert health.rate_limit_reset is None
    
    def test_mark_failure(self):
        """Test marking provider failure."""
        health = ProviderHealth()
        
        health.mark_failure("Connection failed")
        
        assert health.is_healthy is False
        assert health.consecutive_failures == 1
        assert health.last_failure_reason == "Connection failed"
        
        # Mark another failure
        health.mark_failure("Rate limited")
        assert health.consecutive_failures == 2
    
    def test_mark_success(self):
        """Test marking provider success."""
        health = ProviderHealth()
        
        # First mark failure
        health.mark_failure("Test failure")
        assert health.is_healthy is False
        assert health.consecutive_failures == 1
        
        # Then mark success
        health.mark_success()
        assert health.is_healthy is True
        assert health.consecutive_failures == 0
        assert health.last_failure_reason is None
    
    def test_is_rate_limited(self):
        """Test rate limit checking."""
        from datetime import datetime, timedelta
        
        health = ProviderHealth()
        
        # Not rate limited initially
        assert health.is_rate_limited() is False
        
        # Mark as rate limited with future reset time
        future_time = datetime.now() + timedelta(minutes=5)
        health.mark_failure("Rate limited", future_time)
        
        assert health.is_rate_limited() is True
        
        # Mark with past reset time
        past_time = datetime.now() - timedelta(minutes=5)
        health.rate_limit_reset = past_time
        
        assert health.is_rate_limited() is False


class TestProviderConfigEnhanced:
    """Test enhanced ProviderConfig functionality."""
    
    def test_is_usable_healthy(self):
        """Test is_usable when provider is healthy."""
        config = ProviderConfig(
            name="local",
            api_key_env=None,
            base_url="http://localhost:11434",
            models=["llama2"],
            default_model="llama2"
        )
        
        assert config.is_usable() is True
    
    def test_is_usable_unhealthy(self):
        """Test is_usable when provider is unhealthy."""
        config = ProviderConfig(
            name="local",
            api_key_env=None,
            base_url="http://localhost:11434",
            models=["llama2"],
            default_model="llama2"
        )
        
        config.health.mark_failure("Test failure")
        assert config.is_usable() is False
    
    def test_is_usable_rate_limited(self):
        """Test is_usable when provider is rate limited."""
        from datetime import datetime, timedelta
        
        config = ProviderConfig(
            name="local",
            api_key_env=None,
            base_url="http://localhost:11434",
            models=["llama2"],
            default_model="llama2"
        )
        
        future_time = datetime.now() + timedelta(minutes=5)
        config.health.mark_failure("Rate limited", future_time)
        
        assert config.is_usable() is False


class TestProvidersConfigEnhanced:
    """Test enhanced ProvidersConfig functionality."""
    
    @pytest.fixture
    def providers_config_with_health(self):
        """Create providers config with different health states."""
        healthy_provider = ProviderConfig(
            name="healthy",
            api_key_env=None,
            base_url="http://localhost:11434",
            models=["model1"],
            default_model="model1"
        )
        
        unhealthy_provider = ProviderConfig(
            name="unhealthy", 
            api_key_env="UNHEALTHY_KEY",
            base_url="http://unhealthy.com",
            models=["model2"],
            default_model="model2"
        )
        unhealthy_provider.health.mark_failure("Connection failed")
        
        return ProvidersConfig(
            providers={
                "healthy": healthy_provider,
                "unhealthy": unhealthy_provider
            },
            default_provider="healthy",
            fallback_providers=["unhealthy"],
            retry_config={}
        )
    
    def test_get_usable_providers(self, providers_config_with_health):
        """Test getting only usable providers."""
        usable = providers_config_with_health.get_usable_providers()
        assert usable == ["healthy"]
    
    @patch.dict(os.environ, {"UNHEALTHY_KEY": "test-key"})
    def test_get_available_vs_usable(self, providers_config_with_health):
        """Test difference between available and usable providers."""
        available = providers_config_with_health.get_available_providers()
        usable = providers_config_with_health.get_usable_providers()
        
        # Both should be available (have API keys)
        assert "healthy" in available
        assert "unhealthy" in available
        
        # Only healthy should be usable
        assert usable == ["healthy"]


class TestProviderManager:
    """Test ProviderManager functionality."""
    
    @pytest.fixture
    def sample_config(self):
        """Create sample configuration for testing."""
        return get_default_provider_config()
    
    @pytest.fixture
    def provider_manager(self, sample_config):
        """Create ProviderManager instance."""
        return ProviderManager(sample_config)
    
    @pytest.mark.asyncio
    async def test_manager_start_stop(self, provider_manager):
        """Test starting and stopping provider manager."""
        await provider_manager.start()
        assert provider_manager._health_check_task is not None
        
        await provider_manager.stop()
        assert provider_manager._health_check_task is None
    
    @pytest.mark.asyncio
    @patch("src.covibe.services.llm_provider_config.create_llm_client_from_config")
    async def test_check_provider_health_success(self, mock_create_client, provider_manager):
        """Test successful provider health check."""
        mock_client = AsyncMock()
        mock_client.validate_connection.return_value = True
        mock_create_client.return_value = mock_client
        
        result = await provider_manager.check_provider_health("local")
        
        assert result is True
        local_config = provider_manager.config.get_provider_config("local")
        assert local_config.health.is_healthy is True
    
    @pytest.mark.asyncio
    @patch("src.covibe.services.llm_provider_config.create_llm_client_from_config")
    async def test_check_provider_health_failure(self, mock_create_client, provider_manager):
        """Test failed provider health check."""
        mock_create_client.side_effect = Exception("Connection failed")
        
        result = await provider_manager.check_provider_health("local")
        
        assert result is False
        local_config = provider_manager.config.get_provider_config("local")
        assert local_config.health.is_healthy is False
        assert "Connection failed" in local_config.health.last_failure_reason
    
    @pytest.mark.asyncio
    @patch("src.covibe.services.llm_provider_config.create_llm_client_from_config")
    async def test_get_best_client_success(self, mock_create_client, provider_manager):
        """Test getting best client successfully."""
        mock_client = AsyncMock()
        mock_client.validate_connection.return_value = True
        mock_create_client.return_value = mock_client
        
        client, provider_name = await provider_manager.get_best_client()
        
        assert client == mock_client
        assert provider_name in provider_manager.config.providers
    
    @pytest.mark.asyncio
    @patch("src.covibe.services.llm_provider_config.create_llm_client_from_config")
    async def test_get_best_client_preferred_provider(self, mock_create_client, provider_manager):
        """Test getting best client with preferred provider."""
        mock_client = AsyncMock()
        mock_client.validate_connection.return_value = True
        mock_create_client.return_value = mock_client
        
        client, provider_name = await provider_manager.get_best_client(preferred_provider="local")
        
        assert client == mock_client
        assert provider_name == "local"
    
    @pytest.mark.asyncio
    @patch("src.covibe.services.llm_provider_config.create_llm_client_from_config")
    async def test_get_best_client_model_filtering(self, mock_create_client, provider_manager):
        """Test getting best client with model requirement."""
        mock_client = AsyncMock()
        mock_client.validate_connection.return_value = True
        mock_create_client.return_value = mock_client
        
        # Request specific model that only certain providers have
        client, provider_name = await provider_manager.get_best_client(required_model="llama2")
        
        if client:  # If any provider has llama2
            assert provider_name == "local"  # Should pick local provider
    
    @pytest.mark.asyncio
    async def test_handle_provider_error(self, provider_manager):
        """Test handling provider errors."""
        from src.covibe.services.llm_client import LLMRateLimitError
        
        # Simulate rate limit error
        error = LLMRateLimitError("Rate limited", retry_after=60)
        
        with patch.object(provider_manager, 'get_best_client') as mock_get_best:
            mock_get_best.return_value = (None, None)
            
            result = await provider_manager.handle_provider_error("openai", error)
            
            assert result == (None, None)
            
            # Check that provider was marked as unhealthy
            openai_config = provider_manager.config.get_provider_config("openai")
            if openai_config:
                assert openai_config.health.is_healthy is False
                assert openai_config.health.is_rate_limited() is True
    
    def test_get_provider_status(self, provider_manager):
        """Test getting provider status."""
        status = provider_manager.get_provider_status()
        
        assert isinstance(status, dict)
        assert "openai" in status
        assert "anthropic" in status
        assert "local" in status
        
        for provider_status in status.values():
            assert "available" in provider_status
            assert "healthy" in provider_status
            assert "rate_limited" in provider_status
            assert "consecutive_failures" in provider_status
    
    def test_provider_order_health_based(self, provider_manager):
        """Test that provider ordering considers health."""
        # Mark openai as unhealthy
        openai_config = provider_manager.config.get_provider_config("openai")
        if openai_config:
            openai_config.health.mark_failure("Test failure")
        
        # Get provider order
        order = provider_manager._get_provider_order()
        
        # Healthy providers should come first
        healthy_providers = [
            p for p in order 
            if provider_manager.config.get_provider_config(p) and 
            provider_manager.config.get_provider_config(p).health.is_healthy
        ]
        unhealthy_providers = [
            p for p in order
            if provider_manager.config.get_provider_config(p) and 
            not provider_manager.config.get_provider_config(p).health.is_healthy
        ]
        
        # All healthy providers should come before unhealthy ones
        if healthy_providers and unhealthy_providers:
            healthy_indices = [order.index(p) for p in healthy_providers]
            unhealthy_indices = [order.index(p) for p in unhealthy_providers]
            assert max(healthy_indices) < min(unhealthy_indices)