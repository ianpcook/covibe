"""Unit tests for enhanced error handling and recovery mechanisms."""

import pytest
import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import patch, Mock, AsyncMock

from src.covibe.utils.error_handling import (
    ErrorCategory,
    ErrorSeverity,
    LLMError,
    LLMConnectionError,
    LLMRateLimitError,
    LLMValidationError,
    LLMTimeoutError,
    LLMQuotaExceededError,
    LLMErrorRecovery,
    recover_from_llm_error,
    log_llm_request,
    log_llm_response,
    log_llm_fallback,
    get_user_friendly_message,
    get_error_suggestions
)


class TestLLMErrorClasses:
    """Test LLM-specific error classes."""
    
    def test_llm_error_base(self):
        """Test base LLM error class."""
        error = LLMError(
            "Test LLM error",
            provider="openai",
            model="gpt-4"
        )
        
        assert error.message == "Test LLM error"
        assert error.category == ErrorCategory.LLM
        assert error.severity == ErrorSeverity.MEDIUM
        assert error.details["provider"] == "openai"
        assert error.details["model"] == "gpt-4"
    
    def test_llm_connection_error(self):
        """Test LLM connection error."""
        error = LLMConnectionError(
            "Connection failed",
            endpoint="https://api.openai.com/v1",
            provider="openai"
        )
        
        assert error.category == ErrorCategory.LLM
        assert error.severity == ErrorSeverity.HIGH
        assert error.details["endpoint"] == "https://api.openai.com/v1"
        assert error.details["provider"] == "openai"
    
    def test_llm_rate_limit_error(self):
        """Test LLM rate limit error."""
        error = LLMRateLimitError(
            "Rate limit exceeded",
            retry_after=120,
            provider="openai"
        )
        
        assert error.category == ErrorCategory.RATE_LIMIT
        assert error.details["retry_after"] == 120
        assert error.details["provider"] == "openai"
    
    def test_llm_validation_error(self):
        """Test LLM validation error."""
        raw_response = '{"name": "Tony Stark", invalid_json'
        validation_errors = ["Invalid JSON format", "Missing closing brace"]
        
        error = LLMValidationError(
            "Response validation failed",
            raw_response=raw_response,
            validation_errors=validation_errors,
            provider="openai"
        )
        
        assert error.category == ErrorCategory.VALIDATION
        assert error.details["raw_response"] == raw_response
        assert error.details["validation_errors"] == validation_errors
        assert error.details["provider"] == "openai"
    
    def test_llm_timeout_error(self):
        """Test LLM timeout error."""
        error = LLMTimeoutError(
            "Request timed out",
            timeout_duration=30.0,
            provider="anthropic"
        )
        
        assert error.category == ErrorCategory.TIMEOUT
        assert error.details["timeout_duration"] == 30.0
        assert error.details["provider"] == "anthropic"
    
    def test_llm_quota_exceeded_error(self):
        """Test LLM quota exceeded error."""
        error = LLMQuotaExceededError(
            "Monthly quota exceeded",
            quota_type="monthly",
            provider="openai"
        )
        
        assert error.category == ErrorCategory.LLM
        assert error.severity == ErrorSeverity.HIGH
        assert error.details["quota_type"] == "monthly"
        assert error.details["provider"] == "openai"


class TestLLMErrorMessages:
    """Test user-friendly messages and suggestions for LLM errors."""
    
    def test_llm_error_message(self):
        """Test user-friendly message for LLM errors."""
        error = LLMError("Test error")
        message = get_user_friendly_message(error)
        assert "AI service" in message
    
    def test_validation_error_message(self):
        """Test user-friendly message for validation errors."""
        error = LLMValidationError("Validation failed")
        message = get_user_friendly_message(error)
        assert "invalid response" in message
    
    def test_llm_error_suggestions(self):
        """Test suggestions for LLM errors."""
        error = LLMError("Test error")
        suggestions = get_error_suggestions(error)
        assert any("different AI provider" in s for s in suggestions)
        assert any("fallback" in s for s in suggestions)
    
    def test_validation_error_suggestions(self):
        """Test suggestions for validation errors."""
        error = LLMValidationError("Validation failed")
        suggestions = get_error_suggestions(error)
        assert any("malformed" in s for s in suggestions)
        assert any("rephrasing" in s for s in suggestions)


class TestLLMLogging:
    """Test LLM-specific logging functions."""
    
    @patch('src.covibe.utils.error_handling.logger')
    def test_log_llm_request(self, mock_logger):
        """Test LLM request logging."""
        log_llm_request(
            provider="openai",
            model="gpt-4",
            prompt="Analyze this personality",
            request_id="req_123",
            max_tokens=1000,
            temperature=0.7
        )
        
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args
        assert "LLM request initiated" in call_args[0][0]
        
        extra_data = call_args[1]["extra"]
        assert extra_data["provider"] == "openai"
        assert extra_data["model"] == "gpt-4"
        assert extra_data["request_id"] == "req_123"
        assert extra_data["max_tokens"] == 1000
        assert extra_data["temperature"] == 0.7
    
    @patch('src.covibe.utils.error_handling.logger')
    def test_log_llm_response_success(self, mock_logger):
        """Test successful LLM response logging."""
        log_llm_response(
            provider="openai",
            model="gpt-4",
            response='{"name": "Tony Stark"}',
            request_id="req_123",
            duration=2.5,
            tokens_used=150,
            success=True
        )
        
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args
        assert "LLM response received" in call_args[0][0]
        
        extra_data = call_args[1]["extra"]
        assert extra_data["success"] is True
        assert extra_data["duration_seconds"] == 2.5
        assert extra_data["tokens_used"] == 150
    
    @patch('src.covibe.utils.error_handling.logger')
    def test_log_llm_response_failure(self, mock_logger):
        """Test failed LLM response logging."""
        log_llm_response(
            provider="openai",
            model="gpt-4",
            response="Error occurred",
            success=False
        )
        
        mock_logger.warning.assert_called_once()
        call_args = mock_logger.warning.call_args
        assert "LLM response failed" in call_args[0][0]
    
    @patch('src.covibe.utils.error_handling.logger')
    def test_log_llm_fallback(self, mock_logger):
        """Test LLM fallback logging."""
        log_llm_fallback(
            provider="openai",
            model="gpt-4",
            fallback_method="character_database",
            reason="Rate limit exceeded",
            request_id="req_123"
        )
        
        mock_logger.warning.assert_called_once()
        call_args = mock_logger.warning.call_args
        assert "LLM fallback triggered" in call_args[0][0]
        
        extra_data = call_args[1]["extra"]
        assert extra_data["failed_provider"] == "openai"
        assert extra_data["fallback_method"] == "character_database"
        assert extra_data["fallback_reason"] == "Rate limit exceeded"


class TestLLMErrorRecovery:
    """Test LLM error recovery mechanisms."""
    
    @pytest.mark.asyncio
    async def test_recover_from_rate_limit_short_wait(self):
        """Test recovery from short rate limit."""
        strategy = await LLMErrorRecovery.recover_from_rate_limit(
            provider="openai",
            retry_after=30,
            fallback_providers=["anthropic"]
        )
        
        assert strategy["strategy"] == "rate_limit_recovery"
        assert strategy["failed_provider"] == "openai"
        assert strategy["retry_after"] == 30
        assert strategy["recommended_action"] == "wait_and_retry"
    
    @pytest.mark.asyncio
    async def test_recover_from_rate_limit_long_wait_with_fallback(self):
        """Test recovery from long rate limit with fallback providers."""
        strategy = await LLMErrorRecovery.recover_from_rate_limit(
            provider="openai",
            retry_after=300,
            fallback_providers=["anthropic", "local"]
        )
        
        assert strategy["recommended_action"] == "switch_provider"
        assert strategy["fallback_providers"] == ["anthropic", "local"]
    
    @pytest.mark.asyncio
    async def test_recover_from_rate_limit_no_fallback(self):
        """Test recovery from rate limit with no fallback providers."""
        strategy = await LLMErrorRecovery.recover_from_rate_limit(
            provider="openai",
            retry_after=300,
            fallback_providers=None
        )
        
        assert strategy["recommended_action"] == "use_fallback_research"
        assert strategy["fallback_available"] is False
    
    @pytest.mark.asyncio
    async def test_recover_from_validation_error_valid_json(self):
        """Test recovery from validation error with extractable JSON."""
        raw_response = 'Some text before {"name": "Tony Stark", "type": "fictional"} some text after'
        
        strategy = await LLMErrorRecovery.recover_from_validation_error(
            raw_response, ["Invalid format"]
        )
        
        assert strategy["success"] is True
        assert strategy["recovered_data"]["name"] == "Tony Stark"
        assert strategy["recovered_data"]["type"] == "fictional"
        assert any(attempt["method"] == "partial_json_extraction" for attempt in strategy["recovery_attempts"])
    
    @pytest.mark.asyncio
    async def test_recover_from_validation_error_regex_extraction(self):
        """Test recovery using regex extraction."""
        raw_response = '''
        The personality analysis:
        "name": "Sherlock Holmes"
        "type": "fictional"
        "description": "Brilliant detective"
        Additional text here
        '''
        
        strategy = await LLMErrorRecovery.recover_from_validation_error(
            raw_response, ["No valid JSON"]
        )
        
        # Should attempt multiple recovery methods
        assert len(strategy["recovery_attempts"]) > 0
        
        # Check if regex extraction was attempted
        regex_attempt = next(
            (attempt for attempt in strategy["recovery_attempts"] 
             if attempt["method"] == "regex_extraction"), 
            None
        )
        
        if regex_attempt and regex_attempt["success"]:
            assert strategy["success"] is True
            assert "Sherlock Holmes" in str(strategy["recovered_data"])
    
    @pytest.mark.asyncio
    async def test_recover_from_validation_error_no_recovery(self):
        """Test validation error with no recoverable data."""
        raw_response = "Complete garbage with no useful information at all"
        
        strategy = await LLMErrorRecovery.recover_from_validation_error(
            raw_response, ["No valid data"]
        )
        
        assert strategy["success"] is False
        assert len(strategy["recovery_attempts"]) > 0
    
    @pytest.mark.asyncio
    async def test_recover_from_connection_error_timeout(self):
        """Test recovery from timeout connection error."""
        strategy = await LLMErrorRecovery.recover_from_connection_error(
            provider="openai",
            endpoint="https://api.openai.com/v1",
            error_details="Request timeout after 30 seconds"
        )
        
        assert strategy["strategy"] == "connection_recovery"
        assert strategy["failed_provider"] == "openai"
        assert "retry_with_longer_timeout" in strategy["recommended_actions"]
        assert "check_network_connectivity" in strategy["recommended_actions"]
    
    @pytest.mark.asyncio
    async def test_recover_from_connection_error_dns(self):
        """Test recovery from DNS connection error."""
        strategy = await LLMErrorRecovery.recover_from_connection_error(
            provider="local",
            endpoint="http://localhost:11434",
            error_details="Failed to resolve hostname"
        )
        
        assert "check_dns_settings" in strategy["recommended_actions"]
        assert "verify_endpoint_url" in strategy["recommended_actions"]
    
    @pytest.mark.asyncio
    async def test_recover_from_connection_error_ssl(self):
        """Test recovery from SSL connection error."""
        strategy = await LLMErrorRecovery.recover_from_connection_error(
            provider="openai",
            endpoint="https://api.openai.com/v1",
            error_details="SSL certificate verification failed"
        )
        
        assert "verify_ssl_certificates" in strategy["recommended_actions"]
        assert "check_system_time" in strategy["recommended_actions"]
    
    @pytest.mark.asyncio
    async def test_recover_from_connection_error_auth(self):
        """Test recovery from authentication connection error."""
        strategy = await LLMErrorRecovery.recover_from_connection_error(
            provider="openai",
            endpoint="https://api.openai.com/v1",
            error_details="401 Unauthorized: Invalid authentication"
        )
        
        assert "verify_api_key" in strategy["recommended_actions"]
        assert "check_api_key_permissions" in strategy["recommended_actions"]


class TestLLMErrorRecoveryOrchestration:
    """Test orchestrated error recovery."""
    
    @pytest.mark.asyncio
    async def test_recover_from_rate_limit_error(self):
        """Test recovery orchestration for rate limit errors."""
        error = LLMRateLimitError(
            "Rate limited",
            retry_after=30,
            provider="openai"
        )
        
        context = {"fallback_providers": ["anthropic"]}
        
        recovery_plan = await recover_from_llm_error(error, context)
        
        assert recovery_plan["error_type"] == "LLMRateLimitError"
        assert recovery_plan["fallback_available"] is True
        assert len(recovery_plan["immediate_actions"]) > 0
        assert "Wait 30 seconds" in recovery_plan["immediate_actions"][0]
    
    @pytest.mark.asyncio
    async def test_recover_from_validation_error(self):
        """Test recovery orchestration for validation errors."""
        error = LLMValidationError(
            "Validation failed",
            raw_response='{"name": "Tony Stark"}',
            validation_errors=["Missing field"]
        )
        
        recovery_plan = await recover_from_llm_error(error)
        
        assert recovery_plan["error_type"] == "LLMValidationError"
        assert recovery_plan["recovery_strategy"] is not None
        assert len(recovery_plan["immediate_actions"]) > 0
    
    @pytest.mark.asyncio
    async def test_recover_from_connection_error(self):
        """Test recovery orchestration for connection errors."""
        error = LLMConnectionError(
            "Connection failed",
            endpoint="https://api.openai.com/v1",
            provider="openai"
        )
        
        recovery_plan = await recover_from_llm_error(error)
        
        assert recovery_plan["error_type"] == "LLMConnectionError"
        assert len(recovery_plan["immediate_actions"]) > 0
        assert len(recovery_plan["long_term_actions"]) > 0
    
    @pytest.mark.asyncio
    async def test_recover_from_unknown_llm_error(self):
        """Test recovery orchestration for unknown LLM errors."""
        error = LLMError("Unknown error")
        
        recovery_plan = await recover_from_llm_error(error)
        
        assert recovery_plan["error_type"] == "LLMError"
        assert "Log error details" in recovery_plan["immediate_actions"][0]
        assert "fallback research" in recovery_plan["immediate_actions"][1]
        assert len(recovery_plan["long_term_actions"]) > 0


class TestErrorRecoveryIntegration:
    """Test integration of error recovery with existing systems."""
    
    @pytest.mark.asyncio
    async def test_validation_error_recovery_with_partial_success(self):
        """Test that partial recovery from validation errors works."""
        # Simulate a response with extractable JSON
        raw_response = '''
        Here's the personality analysis you requested:
        {
            "name": "Albert Einstein",
            "type": "celebrity",
            "description": "Brilliant physicist and thinker"
        }
        Hope this helps!
        '''
        
        strategy = await LLMErrorRecovery.recover_from_validation_error(
            raw_response, ["Pydantic validation failed"]
        )
        
        assert strategy["success"] is True
        recovered = strategy["recovered_data"]
        assert recovered["name"] == "Albert Einstein"
        assert recovered["type"] == "celebrity"
        assert "physicist" in recovered["description"]
    
    @pytest.mark.asyncio
    async def test_error_recovery_logging_integration(self):
        """Test that error recovery integrates with logging."""
        with patch('src.covibe.utils.error_handling.logger') as mock_logger:
            error = LLMRateLimitError("Rate limited", retry_after=60)
            
            recovery_plan = await recover_from_llm_error(error)
            
            # Verify recovery plan is generated
            assert recovery_plan["error_type"] == "LLMRateLimitError"
            assert len(recovery_plan["immediate_actions"]) > 0
    
    def test_error_recovery_with_monitoring(self):
        """Test that error recovery can be monitored."""
        from src.covibe.utils.monitoring import record_error
        
        error = LLMConnectionError("Connection failed", provider="openai")
        
        # This should not raise an exception
        record_error(error, "llm_client")
        
        # Verify error categories are properly handled
        assert error.category == ErrorCategory.LLM
        assert error.severity == ErrorSeverity.HIGH