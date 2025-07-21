"""Unit tests for comprehensive error handling system."""

import asyncio
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch, MagicMock

from src.covibe.utils.error_handling import (
    PersonalitySystemError,
    InputValidationError,
    ResearchError,
    IntegrationError,
    NetworkError,
    RateLimitError,
    SystemError,
    ErrorCategory,
    ErrorSeverity,
    ErrorContext,
    RetryConfig,
    get_user_friendly_message,
    get_error_suggestions,
    create_error_response,
    with_retry,
    with_fallback,
    log_error,
    error_handler
)


class TestPersonalitySystemError:
    """Test custom error classes."""
    
    def test_base_error_creation(self):
        """Test creating base PersonalitySystemError."""
        error = PersonalitySystemError(
            message="Test error",
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.HIGH,
            code="TEST_ERROR",
            suggestions=["Try again"],
            details={"key": "value"}
        )
        
        assert error.message == "Test error"
        assert error.category == ErrorCategory.SYSTEM
        assert error.severity == ErrorSeverity.HIGH
        assert error.code == "TEST_ERROR"
        assert error.suggestions == ["Try again"]
        assert error.details == {"key": "value"}
        assert isinstance(error.timestamp, datetime)
    
    def test_input_validation_error(self):
        """Test InputValidationError creation."""
        error = InputValidationError(
            message="Invalid field",
            field="username"
        )
        
        assert error.category == ErrorCategory.INPUT_VALIDATION
        assert error.severity == ErrorSeverity.LOW
        assert error.details["field"] == "username"
        assert error.code == "INPUT_VALIDATION_ERROR"
    
    def test_research_error(self):
        """Test ResearchError creation."""
        error = ResearchError(
            message="Research failed",
            source="wikipedia"
        )
        
        assert error.category == ErrorCategory.RESEARCH
        assert error.severity == ErrorSeverity.MEDIUM
        assert error.details["source"] == "wikipedia"
    
    def test_integration_error(self):
        """Test IntegrationError creation."""
        error = IntegrationError(
            message="IDE integration failed",
            ide_type="cursor"
        )
        
        assert error.category == ErrorCategory.INTEGRATION
        assert error.details["ide_type"] == "cursor"
    
    def test_network_error(self):
        """Test NetworkError creation."""
        error = NetworkError(
            message="Connection failed",
            url="https://example.com"
        )
        
        assert error.category == ErrorCategory.NETWORK
        assert error.details["url"] == "https://example.com"
    
    def test_rate_limit_error(self):
        """Test RateLimitError creation."""
        error = RateLimitError(
            message="Rate limited",
            retry_after=60
        )
        
        assert error.category == ErrorCategory.RATE_LIMIT
        assert error.details["retry_after"] == 60
    
    def test_system_error(self):
        """Test SystemError creation."""
        error = SystemError(message="System failure")
        
        assert error.category == ErrorCategory.SYSTEM
        assert error.severity == ErrorSeverity.HIGH


class TestErrorMessages:
    """Test error message generation."""
    
    def test_user_friendly_messages(self):
        """Test user-friendly message generation."""
        test_cases = [
            (InputValidationError("Invalid input", field="name"), 
             "There's an issue with the information you provided. Please check the 'name' field."),
            (ResearchError("Research failed", source="wikipedia"),
             "I had trouble researching that personality. The issue was with wikipedia."),
            (IntegrationError("IDE failed", ide_type="cursor"),
             "I couldn't integrate with your IDE. The issue was with cursor integration."),
            (NetworkError("Connection failed"),
             "I'm having trouble connecting to external services."),
            (RateLimitError("Rate limited"),
             "I'm being rate limited by external services."),
            (SystemError("System error"),
             "Something went wrong on our end.")
        ]
        
        for error, expected_message in test_cases:
            message = get_user_friendly_message(error)
            assert message == expected_message
    
    def test_error_suggestions(self):
        """Test error suggestion generation."""
        # Test with custom suggestions
        error = ResearchError("Failed", suggestions=["Custom suggestion"])
        suggestions = get_error_suggestions(error)
        assert suggestions == ["Custom suggestion"]
        
        # Test with category-based suggestions
        error = InputValidationError("Invalid input")
        suggestions = get_error_suggestions(error)
        assert "Please check your input and try again" in suggestions
        
        error = NetworkError("Connection failed")
        suggestions = get_error_suggestions(error)
        assert "Check your internet connection" in suggestions


class TestErrorResponse:
    """Test error response creation."""
    
    def test_create_error_response_from_custom_error(self):
        """Test creating error response from PersonalitySystemError."""
        error = ResearchError(
            "Research failed",
            suggestions=["Try again"]
        )
        
        response = create_error_response(error, "req_123")
        
        assert response.request_id == "req_123"
        assert response.error.code == "RESEARCH_ERROR"
        assert "I had trouble researching that personality" in response.error.message
        assert response.error.suggestions == ["Try again"]
        assert isinstance(response.timestamp, datetime)
    
    def test_create_error_response_from_generic_error(self):
        """Test creating error response from generic Exception."""
        error = ValueError("Generic error")
        
        response = create_error_response(error)
        
        assert response.error.code == "UNEXPECTED_ERROR"
        assert response.error.message == "An unexpected error occurred"
        assert "Please try again later" in response.error.suggestions


class TestRetryLogic:
    """Test retry logic functionality."""
    
    @pytest.mark.asyncio
    async def test_successful_retry(self):
        """Test successful operation with retry."""
        call_count = 0
        
        async def failing_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise NetworkError("Temporary failure")
            return "success"
        
        config = RetryConfig(max_attempts=3, base_delay=0.01)
        result = await with_retry(failing_func, retry_config=config)
        
        assert result == "success"
        assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_retry_exhaustion(self):
        """Test retry exhaustion."""
        async def always_failing_func():
            raise NetworkError("Always fails")
        
        config = RetryConfig(max_attempts=2, base_delay=0.01)
        
        with pytest.raises(NetworkError):
            await with_retry(always_failing_func, retry_config=config)
    
    @pytest.mark.asyncio
    async def test_non_retryable_error(self):
        """Test that non-retryable errors are not retried."""
        call_count = 0
        
        async def func_with_validation_error():
            nonlocal call_count
            call_count += 1
            raise InputValidationError("Invalid input")
        
        config = RetryConfig(max_attempts=3, base_delay=0.01)
        
        with pytest.raises(InputValidationError):
            await with_retry(func_with_validation_error, retry_config=config)
        
        assert call_count == 1  # Should not retry
    
    @pytest.mark.asyncio
    async def test_retry_with_context(self):
        """Test retry with error context."""
        async def failing_func():
            raise NetworkError("Network issue")
        
        context = ErrorContext(
            operation="test_operation",
            component="test_component"
        )
        
        config = RetryConfig(max_attempts=2, base_delay=0.01)
        
        with pytest.raises(NetworkError):
            await with_retry(
                failing_func,
                retry_config=config,
                context=context
            )


class TestFallbackLogic:
    """Test fallback functionality."""
    
    @pytest.mark.asyncio
    async def test_successful_primary(self):
        """Test successful primary function."""
        async def primary_func():
            return "primary_result"
        
        async def fallback_func():
            return "fallback_result"
        
        wrapped_func = with_fallback(primary_func, fallback_func)
        result = await wrapped_func()
        
        assert result == "primary_result"
    
    @pytest.mark.asyncio
    async def test_fallback_on_network_error(self):
        """Test fallback when primary fails with network error."""
        async def primary_func():
            raise NetworkError("Network failed")
        
        async def fallback_func():
            return "fallback_result"
        
        wrapped_func = with_fallback(primary_func, fallback_func)
        result = await wrapped_func()
        
        assert result == "fallback_result"
    
    @pytest.mark.asyncio
    async def test_no_fallback_on_validation_error(self):
        """Test that validation errors don't trigger fallback."""
        async def primary_func():
            raise InputValidationError("Invalid input")
        
        async def fallback_func():
            return "fallback_result"
        
        wrapped_func = with_fallback(primary_func, fallback_func)
        
        with pytest.raises(InputValidationError):
            await wrapped_func()


class TestErrorLogging:
    """Test error logging functionality."""
    
    @patch('src.covibe.utils.error_handling.logger')
    def test_log_personality_system_error(self, mock_logger):
        """Test logging PersonalitySystemError."""
        error = ResearchError("Research failed", source="wikipedia")
        context = ErrorContext(
            operation="test_operation",
            component="test_component",
            user_id="user123",
            request_id="req456"
        )
        
        log_error(error, context, {"extra": "data"})
        
        # Verify appropriate log level was called
        mock_logger.warning.assert_called_once()
        
        # Check log data structure
        call_args = mock_logger.warning.call_args
        log_data = call_args[1]['extra']
        
        assert log_data['error_type'] == 'ResearchError'
        assert log_data['category'] == 'research'
        assert log_data['severity'] == 'medium'
        assert log_data['operation'] == 'test_operation'
        assert log_data['component'] == 'test_component'
        assert log_data['user_id'] == 'user123'
        assert log_data['request_id'] == 'req456'
        assert log_data['extra'] == 'data'
    
    @patch('src.covibe.utils.error_handling.logger')
    def test_log_generic_error(self, mock_logger):
        """Test logging generic Exception."""
        error = ValueError("Generic error")
        
        log_error(error)
        
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args
        log_data = call_args[1]['extra']
        
        assert log_data['error_type'] == 'ValueError'
        assert log_data['error_message'] == 'Generic error'


class TestErrorHandlerDecorator:
    """Test error handler decorator."""
    
    @pytest.mark.asyncio
    async def test_successful_operation(self):
        """Test decorator with successful operation."""
        @error_handler(
            category=ErrorCategory.RESEARCH,
            operation="test_operation",
            component="test_component"
        )
        async def successful_func():
            return "success"
        
        result = await successful_func()
        assert result == "success"
    
    @pytest.mark.asyncio
    async def test_error_conversion(self):
        """Test decorator converts generic errors to PersonalitySystemError."""
        @error_handler(
            category=ErrorCategory.RESEARCH,
            operation="test_operation",
            component="test_component"
        )
        async def failing_func():
            raise ValueError("Generic error")
        
        with pytest.raises(SystemError) as exc_info:
            await failing_func()
        
        assert "Unexpected error in test_operation" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_personality_system_error_passthrough(self):
        """Test decorator passes through PersonalitySystemError."""
        @error_handler(
            category=ErrorCategory.RESEARCH,
            operation="test_operation",
            component="test_component"
        )
        async def failing_func():
            raise ResearchError("Research failed")
        
        with pytest.raises(ResearchError):
            await failing_func()
    
    @pytest.mark.asyncio
    async def test_decorator_with_retry(self):
        """Test decorator with retry configuration."""
        call_count = 0
        
        @error_handler(
            category=ErrorCategory.RESEARCH,
            operation="test_operation",
            component="test_component",
            retry_config=RetryConfig(max_attempts=3, base_delay=0.01)
        )
        async def intermittent_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise NetworkError("Temporary failure")
            return "success"
        
        result = await intermittent_func()
        assert result == "success"
        assert call_count == 3
    
    @pytest.mark.asyncio
    async def test_decorator_with_fallback(self):
        """Test decorator with fallback function."""
        async def fallback_func(*args, **kwargs):
            return "fallback_result"
        
        @error_handler(
            category=ErrorCategory.RESEARCH,
            operation="test_operation",
            component="test_component",
            fallback_func=fallback_func
        )
        async def failing_func():
            raise ResearchError("Research failed")
        
        result = await failing_func()
        assert result == "fallback_result"


class TestRetryConfig:
    """Test retry configuration."""
    
    def test_default_config(self):
        """Test default retry configuration."""
        config = RetryConfig()
        
        assert config.max_attempts == 3
        assert config.base_delay == 1.0
        assert config.max_delay == 60.0
        assert config.exponential_base == 2.0
        assert config.jitter is True
    
    def test_custom_config(self):
        """Test custom retry configuration."""
        config = RetryConfig(
            max_attempts=5,
            base_delay=0.5,
            max_delay=30.0,
            exponential_base=1.5,
            jitter=False
        )
        
        assert config.max_attempts == 5
        assert config.base_delay == 0.5
        assert config.max_delay == 30.0
        assert config.exponential_base == 1.5
        assert config.jitter is False


class TestErrorContext:
    """Test error context functionality."""
    
    def test_error_context_creation(self):
        """Test creating error context."""
        context = ErrorContext(
            operation="test_operation",
            component="test_component",
            user_id="user123",
            request_id="req456",
            additional_data={"key": "value"}
        )
        
        assert context.operation == "test_operation"
        assert context.component == "test_component"
        assert context.user_id == "user123"
        assert context.request_id == "req456"
        assert context.additional_data == {"key": "value"}
    
    def test_minimal_error_context(self):
        """Test creating minimal error context."""
        context = ErrorContext(
            operation="test_operation",
            component="test_component"
        )
        
        assert context.operation == "test_operation"
        assert context.component == "test_component"
        assert context.user_id is None
        assert context.request_id is None
        assert context.additional_data is None


if __name__ == "__main__":
    pytest.main([__file__])