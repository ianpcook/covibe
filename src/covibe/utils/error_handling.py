"""
Comprehensive error handling system for the Agent Personality System.

This module provides error classification, retry logic, fallback mechanisms,
and user-friendly error reporting.
"""

import asyncio
import logging
import time
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Type, Union, TypeVar, Awaitable
from dataclasses import dataclass
from functools import wraps

from ..models.core import ErrorResponse, ErrorDetail

logger = logging.getLogger(__name__)

T = TypeVar('T')


class ErrorCategory(str, Enum):
    """Categories of errors that can occur in the system."""
    INPUT_VALIDATION = "input_validation"
    RESEARCH = "research"
    INTEGRATION = "integration"
    SYSTEM = "system"
    NETWORK = "network"
    AUTHENTICATION = "authentication"
    RATE_LIMIT = "rate_limit"
    TIMEOUT = "timeout"


class ErrorSeverity(str, Enum):
    """Severity levels for errors."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RetryConfig:
    """Configuration for retry logic."""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True


@dataclass
class ErrorContext:
    """Context information for error handling."""
    operation: str
    component: str
    user_id: Optional[str] = None
    request_id: Optional[str] = None
    additional_data: Optional[Dict[str, Any]] = None


class PersonalitySystemError(Exception):
    """Base exception for all personality system errors."""
    
    def __init__(
        self,
        message: str,
        category: ErrorCategory,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        code: Optional[str] = None,
        suggestions: Optional[List[str]] = None,
        details: Optional[Dict[str, Any]] = None,
        context: Optional[ErrorContext] = None
    ):
        super().__init__(message)
        self.message = message
        self.category = category
        self.severity = severity
        self.code = code or f"{category.value.upper()}_ERROR"
        self.suggestions = suggestions or []
        self.details = details or {}
        self.context = context
        self.timestamp = datetime.now()


class InputValidationError(PersonalitySystemError):
    """Error for invalid input data."""
    
    def __init__(self, message: str, field: Optional[str] = None, **kwargs):
        super().__init__(
            message=message,
            category=ErrorCategory.INPUT_VALIDATION,
            severity=ErrorSeverity.LOW,
            **kwargs
        )
        if field:
            self.details["field"] = field


class ResearchError(PersonalitySystemError):
    """Error during personality research operations."""
    
    def __init__(self, message: str, source: Optional[str] = None, **kwargs):
        super().__init__(
            message=message,
            category=ErrorCategory.RESEARCH,
            severity=ErrorSeverity.MEDIUM,
            **kwargs
        )
        if source:
            self.details["source"] = source


class IntegrationError(PersonalitySystemError):
    """Error during IDE integration operations."""
    
    def __init__(self, message: str, ide_type: Optional[str] = None, **kwargs):
        super().__init__(
            message=message,
            category=ErrorCategory.INTEGRATION,
            severity=ErrorSeverity.MEDIUM,
            **kwargs
        )
        if ide_type:
            self.details["ide_type"] = ide_type


class NetworkError(PersonalitySystemError):
    """Error for network-related issues."""
    
    def __init__(self, message: str, url: Optional[str] = None, **kwargs):
        super().__init__(
            message=message,
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.MEDIUM,
            **kwargs
        )
        if url:
            self.details["url"] = url


class RateLimitError(PersonalitySystemError):
    """Error for rate limiting issues."""
    
    def __init__(self, message: str, retry_after: Optional[int] = None, **kwargs):
        super().__init__(
            message=message,
            category=ErrorCategory.RATE_LIMIT,
            severity=ErrorSeverity.MEDIUM,
            **kwargs
        )
        if retry_after:
            self.details["retry_after"] = retry_after


class SystemError(PersonalitySystemError):
    """Error for system-level issues."""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message=message,
            category=ErrorCategory.SYSTEM,
            severity=ErrorSeverity.HIGH,
            **kwargs
        )


def get_user_friendly_message(error: PersonalitySystemError) -> str:
    """Generate user-friendly error messages based on error type."""
    
    base_messages = {
        ErrorCategory.INPUT_VALIDATION: "There's an issue with the information you provided.",
        ErrorCategory.RESEARCH: "I had trouble researching that personality.",
        ErrorCategory.INTEGRATION: "I couldn't integrate with your IDE.",
        ErrorCategory.NETWORK: "I'm having trouble connecting to external services.",
        ErrorCategory.RATE_LIMIT: "I'm being rate limited by external services.",
        ErrorCategory.SYSTEM: "Something went wrong on our end.",
        ErrorCategory.AUTHENTICATION: "There's an authentication issue.",
        ErrorCategory.TIMEOUT: "The operation took too long to complete."
    }
    
    base_message = base_messages.get(error.category, "An unexpected error occurred.")
    
    # Add specific context if available
    if error.category == ErrorCategory.INPUT_VALIDATION and "field" in error.details:
        base_message += f" Please check the '{error.details['field']}' field."
    elif error.category == ErrorCategory.RESEARCH and "source" in error.details:
        base_message += f" The issue was with {error.details['source']}."
    elif error.category == ErrorCategory.INTEGRATION and "ide_type" in error.details:
        base_message += f" The issue was with {error.details['ide_type']} integration."
    
    return base_message


def get_error_suggestions(error: PersonalitySystemError) -> List[str]:
    """Generate helpful suggestions based on error type."""
    
    if error.suggestions:
        return error.suggestions
    
    suggestions_map = {
        ErrorCategory.INPUT_VALIDATION: [
            "Please check your input and try again",
            "Make sure all required fields are filled out",
            "Verify the format of your data"
        ],
        ErrorCategory.RESEARCH: [
            "Try a more specific personality description",
            "Check if the personality name is spelled correctly",
            "Try a different personality or archetype"
        ],
        ErrorCategory.INTEGRATION: [
            "Make sure your IDE is supported",
            "Check file permissions in your project directory",
            "Try manual configuration if automatic detection fails"
        ],
        ErrorCategory.NETWORK: [
            "Check your internet connection",
            "Try again in a few moments",
            "Contact support if the problem persists"
        ],
        ErrorCategory.RATE_LIMIT: [
            "Wait a few minutes before trying again",
            "Consider using cached results",
            "Try a different research source"
        ],
        ErrorCategory.SYSTEM: [
            "Try again in a few moments",
            "Contact support if the problem persists",
            "Check the system status page"
        ]
    }
    
    return suggestions_map.get(error.category, ["Please try again later"])


def create_error_response(
    error: Union[PersonalitySystemError, Exception],
    request_id: Optional[str] = None
) -> ErrorResponse:
    """Create a standardized error response."""
    
    if isinstance(error, PersonalitySystemError):
        user_message = get_user_friendly_message(error)
        suggestions = get_error_suggestions(error)
        
        error_detail = ErrorDetail(
            code=error.code,
            message=user_message,
            details=error.details,
            suggestions=suggestions
        )
    else:
        # Handle unexpected exceptions
        error_detail = ErrorDetail(
            code="UNEXPECTED_ERROR",
            message="An unexpected error occurred",
            suggestions=["Please try again later", "Contact support if the problem persists"]
        )
    
    return ErrorResponse(
        error=error_detail,
        request_id=request_id or f"req_{int(time.time())}",
        timestamp=datetime.now()
    )


async def with_retry(
    func: Callable[..., Awaitable[T]],
    *args,
    retry_config: Optional[RetryConfig] = None,
    retryable_exceptions: Optional[tuple] = None,
    context: Optional[ErrorContext] = None,
    **kwargs
) -> T:
    """
    Execute a function with retry logic and exponential backoff.
    
    Args:
        func: Async function to execute
        *args: Arguments for the function
        retry_config: Retry configuration
        retryable_exceptions: Tuple of exception types that should trigger retries
        context: Error context for logging
        **kwargs: Keyword arguments for the function
    
    Returns:
        Result of the function execution
    
    Raises:
        The last exception if all retries fail
    """
    
    config = retry_config or RetryConfig()
    retryable = retryable_exceptions or (NetworkError, RateLimitError, SystemError)
    
    last_exception = None
    
    for attempt in range(config.max_attempts):
        try:
            result = await func(*args, **kwargs)
            
            # Log successful retry if this wasn't the first attempt
            if attempt > 0 and context:
                logger.info(
                    f"Operation succeeded after {attempt + 1} attempts: "
                    f"{context.operation} in {context.component}"
                )
            
            return result
            
        except Exception as e:
            last_exception = e
            
            # Don't retry if this isn't a retryable exception
            if not isinstance(e, retryable):
                raise
            
            # Don't retry if this is the last attempt
            if attempt == config.max_attempts - 1:
                break
            
            # Calculate delay with exponential backoff
            delay = min(
                config.base_delay * (config.exponential_base ** attempt),
                config.max_delay
            )
            
            # Add jitter to prevent thundering herd
            if config.jitter:
                import random
                delay *= (0.5 + random.random() * 0.5)
            
            # Log retry attempt
            if context:
                logger.warning(
                    f"Attempt {attempt + 1} failed for {context.operation} "
                    f"in {context.component}: {str(e)}. "
                    f"Retrying in {delay:.2f} seconds..."
                )
            
            await asyncio.sleep(delay)
    
    # All retries failed
    if context:
        logger.error(
            f"All {config.max_attempts} attempts failed for {context.operation} "
            f"in {context.component}: {str(last_exception)}"
        )
    
    raise last_exception


def with_fallback(
    primary_func: Callable[..., Awaitable[T]],
    fallback_func: Callable[..., Awaitable[T]],
    fallback_exceptions: Optional[tuple] = None
) -> Callable[..., Awaitable[T]]:
    """
    Create a function that falls back to an alternative if the primary fails.
    
    Args:
        primary_func: Primary function to try first
        fallback_func: Fallback function to use if primary fails
        fallback_exceptions: Exceptions that should trigger fallback
    
    Returns:
        Wrapped function with fallback logic
    """
    
    fallback_on = fallback_exceptions or (NetworkError, RateLimitError, ResearchError)
    
    async def wrapper(*args, **kwargs) -> T:
        try:
            return await primary_func(*args, **kwargs)
        except Exception as e:
            if isinstance(e, fallback_on):
                logger.warning(f"Primary function failed: {str(e)}. Trying fallback...")
                return await fallback_func(*args, **kwargs)
            else:
                raise
    
    return wrapper


def log_error(
    error: Union[PersonalitySystemError, Exception],
    context: Optional[ErrorContext] = None,
    extra_data: Optional[Dict[str, Any]] = None
):
    """
    Log error with appropriate level and context.
    
    Args:
        error: The error to log
        context: Error context information
        extra_data: Additional data to include in log
    """
    
    log_data = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "timestamp": datetime.now().isoformat()
    }
    
    if isinstance(error, PersonalitySystemError):
        log_data.update({
            "category": error.category.value,
            "severity": error.severity.value,
            "code": error.code,
            "details": error.details
        })
    
    if context:
        log_data.update({
            "operation": context.operation,
            "component": context.component,
            "user_id": context.user_id,
            "request_id": context.request_id
        })
        if context.additional_data:
            log_data.update(context.additional_data)
    
    if extra_data:
        log_data.update(extra_data)
    
    # Choose log level based on severity
    if isinstance(error, PersonalitySystemError):
        if error.severity == ErrorSeverity.CRITICAL:
            logger.critical("Critical error occurred", extra=log_data)
        elif error.severity == ErrorSeverity.HIGH:
            logger.error("High severity error occurred", extra=log_data)
        elif error.severity == ErrorSeverity.MEDIUM:
            logger.warning("Medium severity error occurred", extra=log_data)
        else:
            logger.info("Low severity error occurred", extra=log_data)
    else:
        logger.error("Unexpected error occurred", extra=log_data)


def error_handler(
    category: ErrorCategory,
    operation: str,
    component: str,
    retry_config: Optional[RetryConfig] = None,
    fallback_func: Optional[Callable] = None
):
    """
    Decorator for comprehensive error handling.
    
    Args:
        category: Error category for this operation
        operation: Name of the operation being performed
        component: Component where the operation is happening
        retry_config: Retry configuration
        fallback_func: Optional fallback function
    """
    
    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            context = ErrorContext(
                operation=operation,
                component=component,
                request_id=kwargs.get('request_id')
            )
            
            try:
                # Apply retry logic if configured
                if retry_config:
                    return await with_retry(
                        func, *args,
                        retry_config=retry_config,
                        context=context,
                        **kwargs
                    )
                else:
                    return await func(*args, **kwargs)
                    
            except PersonalitySystemError as e:
                # Log the error with context
                log_error(e, context)
                
                # Try fallback if available
                if fallback_func and e.category in [ErrorCategory.RESEARCH, ErrorCategory.NETWORK]:
                    try:
                        logger.info(f"Trying fallback for {operation}")
                        return await fallback_func(*args, **kwargs)
                    except Exception as fallback_error:
                        log_error(fallback_error, context)
                        raise e  # Raise original error
                
                raise
                
            except Exception as e:
                # Convert unexpected exceptions to PersonalitySystemError
                system_error = SystemError(
                    message=f"Unexpected error in {operation}: {str(e)}",
                    context=context
                )
                log_error(system_error, context)
                raise system_error
        
        return wrapper
    return decorator