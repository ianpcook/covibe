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
    LLM = "llm"
    VALIDATION = "validation"


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


class LLMError(PersonalitySystemError):
    """Base class for LLM-related errors."""
    
    def __init__(self, message: str, provider: Optional[str] = None, model: Optional[str] = None, **kwargs):
        super().__init__(
            message=message,
            category=ErrorCategory.LLM,
            severity=ErrorSeverity.MEDIUM,
            **kwargs
        )
        if provider:
            self.details["provider"] = provider
        if model:
            self.details["model"] = model


class LLMConnectionError(LLMError):
    """LLM service connection failed."""
    
    def __init__(self, message: str, endpoint: Optional[str] = None, **kwargs):
        super().__init__(
            message=message,
            severity=ErrorSeverity.HIGH,
            **kwargs
        )
        if endpoint:
            self.details["endpoint"] = endpoint


class LLMRateLimitError(LLMError):
    """LLM service rate limit exceeded."""
    
    def __init__(self, message: str, retry_after: int = 60, **kwargs):
        super().__init__(
            message=message,
            category=ErrorCategory.RATE_LIMIT,
            severity=ErrorSeverity.MEDIUM,
            **kwargs
        )
        self.details["retry_after"] = retry_after


class LLMValidationError(LLMError):
    """LLM response validation failed."""
    
    def __init__(self, message: str, raw_response: Optional[str] = None, validation_errors: Optional[List[str]] = None, **kwargs):
        super().__init__(
            message=message,
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.MEDIUM,
            **kwargs
        )
        if raw_response:
            self.details["raw_response"] = raw_response[:500]  # Truncate to avoid huge logs
        if validation_errors:
            self.details["validation_errors"] = validation_errors


class LLMTimeoutError(LLMError):
    """LLM request timed out."""
    
    def __init__(self, message: str, timeout_duration: float, **kwargs):
        super().__init__(
            message=message,
            category=ErrorCategory.TIMEOUT,
            severity=ErrorSeverity.MEDIUM,
            **kwargs
        )
        self.details["timeout_duration"] = timeout_duration


class LLMQuotaExceededError(LLMError):
    """LLM service quota exceeded."""
    
    def __init__(self, message: str, quota_type: Optional[str] = None, **kwargs):
        super().__init__(
            message=message,
            severity=ErrorSeverity.HIGH,
            **kwargs
        )
        if quota_type:
            self.details["quota_type"] = quota_type


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
        ErrorCategory.TIMEOUT: "The operation took too long to complete.",
        ErrorCategory.LLM: "I encountered an issue with the AI service.",
        ErrorCategory.VALIDATION: "I received an invalid response from the AI service."
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
        ],
        ErrorCategory.LLM: [
            "Try again with a different AI provider",
            "Wait a moment and try again",
            "Use simpler language in your description",
            "Try using fallback research methods"
        ],
        ErrorCategory.VALIDATION: [
            "The AI response was malformed, trying again may help",
            "Consider rephrasing your personality description",
            "Try using a more specific character name or archetype"
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


def log_llm_request(
    provider: str,
    model: str,
    prompt: str,
    request_id: Optional[str] = None,
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None
):
    """
    Log LLM request details.
    
    Args:
        provider: LLM provider name
        model: Model name
        prompt: Request prompt (truncated for security)
        request_id: Request identifier
        max_tokens: Maximum tokens requested
        temperature: Temperature setting
    """
    
    log_data = {
        "event_type": "llm_request",
        "provider": provider,
        "model": model,
        "prompt_length": len(prompt),
        "prompt_preview": prompt[:200] + "..." if len(prompt) > 200 else prompt,
        "request_id": request_id,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "timestamp": datetime.now().isoformat()
    }
    
    logger.info("LLM request initiated", extra=log_data)


def log_llm_response(
    provider: str,
    model: str,
    response: str,
    request_id: Optional[str] = None,
    duration: Optional[float] = None,
    tokens_used: Optional[int] = None,
    success: bool = True
):
    """
    Log LLM response details.
    
    Args:
        provider: LLM provider name
        model: Model name
        response: Response text (truncated for security)
        request_id: Request identifier
        duration: Response time in seconds
        tokens_used: Number of tokens used
        success: Whether the response was successful
    """
    
    log_data = {
        "event_type": "llm_response",
        "provider": provider,
        "model": model,
        "response_length": len(response),
        "response_preview": response[:200] + "..." if len(response) > 200 else response,
        "request_id": request_id,
        "duration_seconds": duration,
        "tokens_used": tokens_used,
        "success": success,
        "timestamp": datetime.now().isoformat()
    }
    
    if success:
        logger.info("LLM response received", extra=log_data)
    else:
        logger.warning("LLM response failed", extra=log_data)


def log_llm_fallback(
    provider: str,
    model: str,
    fallback_method: str,
    reason: str,
    request_id: Optional[str] = None
):
    """
    Log when LLM fallback is triggered.
    
    Args:
        provider: Failed LLM provider
        model: Failed model
        fallback_method: Method used for fallback
        reason: Reason for fallback
        request_id: Request identifier
    """
    
    log_data = {
        "event_type": "llm_fallback",
        "failed_provider": provider,
        "failed_model": model,
        "fallback_method": fallback_method,
        "fallback_reason": reason,
        "request_id": request_id,
        "timestamp": datetime.now().isoformat()
    }
    
    logger.warning("LLM fallback triggered", extra=log_data)


class LLMErrorRecovery:
    """Error recovery mechanisms for common LLM failure scenarios."""
    
    @staticmethod
    async def recover_from_rate_limit(
        provider: str,
        retry_after: int,
        fallback_providers: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Recover from rate limit errors.
        
        Args:
            provider: Provider that hit rate limit
            retry_after: Seconds to wait before retry
            fallback_providers: Alternative providers to try
            
        Returns:
            Recovery strategy information
        """
        recovery_strategy = {
            "strategy": "rate_limit_recovery",
            "failed_provider": provider,
            "retry_after": retry_after,
            "recommended_action": None,
            "fallback_available": bool(fallback_providers)
        }
        
        if retry_after <= 60:  # Short wait
            recovery_strategy["recommended_action"] = "wait_and_retry"
        elif fallback_providers:  # Switch providers
            recovery_strategy["recommended_action"] = "switch_provider"
            recovery_strategy["fallback_providers"] = fallback_providers
        else:  # Use cache or alternative methods
            recovery_strategy["recommended_action"] = "use_fallback_research"
        
        return recovery_strategy
    
    @staticmethod
    async def recover_from_validation_error(
        raw_response: str,
        validation_errors: List[str]
    ) -> Dict[str, Any]:
        """
        Attempt to recover from response validation errors.
        
        Args:
            raw_response: Raw LLM response that failed validation
            validation_errors: List of validation errors
            
        Returns:
            Recovery attempt information
        """
        recovery_strategy = {
            "strategy": "validation_recovery",
            "recovery_attempts": [],
            "success": False,
            "recovered_data": None
        }
        
        # Attempt 1: Try to extract partial JSON
        try:
            import re
            json_match = re.search(r'\{.*\}', raw_response, re.DOTALL)
            if json_match:
                partial_json = json_match.group()
                import json
                parsed_data = json.loads(partial_json)
                recovery_strategy["recovery_attempts"].append({
                    "method": "partial_json_extraction",
                    "success": True,
                    "data": parsed_data
                })
                recovery_strategy["success"] = True
                recovery_strategy["recovered_data"] = parsed_data
                return recovery_strategy
        except Exception as e:
            recovery_strategy["recovery_attempts"].append({
                "method": "partial_json_extraction",
                "success": False,
                "error": str(e)
            })
        
        # Attempt 2: Try to fix common JSON issues
        try:
            # Fix common issues: missing quotes, trailing commas, etc.
            fixed_response = raw_response
            
            # Remove extra text before/after JSON
            import re
            json_pattern = r'\{(?:[^{}]|{[^{}]*})*\}'
            matches = re.findall(json_pattern, fixed_response, re.DOTALL)
            if matches:
                fixed_response = matches[0]
                
                # Try to parse fixed JSON
                import json
                parsed_data = json.loads(fixed_response)
                recovery_strategy["recovery_attempts"].append({
                    "method": "json_repair",
                    "success": True,
                    "data": parsed_data
                })
                recovery_strategy["success"] = True
                recovery_strategy["recovered_data"] = parsed_data
                return recovery_strategy
        except Exception as e:
            recovery_strategy["recovery_attempts"].append({
                "method": "json_repair",
                "success": False,
                "error": str(e)
            })
        
        # Attempt 3: Extract key information with regex
        try:
            extracted_data = {}
            
            # Extract name
            name_match = re.search(r'"name"\s*:\s*"([^"]+)"', raw_response)
            if name_match:
                extracted_data["name"] = name_match.group(1)
            
            # Extract type
            type_match = re.search(r'"type"\s*:\s*"([^"]+)"', raw_response)
            if type_match:
                extracted_data["type"] = type_match.group(1)
            
            # Extract description
            desc_match = re.search(r'"description"\s*:\s*"([^"]+)"', raw_response)
            if desc_match:
                extracted_data["description"] = desc_match.group(1)
            
            if extracted_data:
                recovery_strategy["recovery_attempts"].append({
                    "method": "regex_extraction",
                    "success": True,
                    "data": extracted_data
                })
                recovery_strategy["success"] = True
                recovery_strategy["recovered_data"] = extracted_data
                return recovery_strategy
        except Exception as e:
            recovery_strategy["recovery_attempts"].append({
                "method": "regex_extraction",
                "success": False,
                "error": str(e)
            })
        
        return recovery_strategy
    
    @staticmethod
    async def recover_from_connection_error(
        provider: str,
        endpoint: str,
        error_details: str
    ) -> Dict[str, Any]:
        """
        Attempt to recover from connection errors.
        
        Args:
            provider: Provider that failed
            endpoint: Failed endpoint
            error_details: Error details
            
        Returns:
            Recovery strategy information
        """
        recovery_strategy = {
            "strategy": "connection_recovery",
            "failed_provider": provider,
            "failed_endpoint": endpoint,
            "error_details": error_details,
            "recommended_actions": []
        }
        
        # Analyze error type
        error_lower = error_details.lower()
        
        if "timeout" in error_lower:
            recovery_strategy["recommended_actions"].extend([
                "retry_with_longer_timeout",
                "check_network_connectivity",
                "switch_to_fallback_provider"
            ])
        elif "dns" in error_lower or "resolve" in error_lower:
            recovery_strategy["recommended_actions"].extend([
                "check_dns_settings",
                "verify_endpoint_url",
                "switch_to_fallback_provider"
            ])
        elif "certificate" in error_lower or "ssl" in error_lower:
            recovery_strategy["recommended_actions"].extend([
                "verify_ssl_certificates",
                "check_system_time",
                "disable_ssl_verification_temporarily"
            ])
        elif "authentication" in error_lower or "401" in error_lower:
            recovery_strategy["recommended_actions"].extend([
                "verify_api_key",
                "check_api_key_permissions",
                "regenerate_api_key"
            ])
        else:
            recovery_strategy["recommended_actions"].extend([
                "retry_with_exponential_backoff",
                "check_service_status",
                "switch_to_fallback_provider"
            ])
        
        return recovery_strategy


async def recover_from_llm_error(error: LLMError, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Orchestrate recovery from LLM errors.
    
    Args:
        error: LLM error that occurred
        context: Additional context for recovery
        
    Returns:
        Recovery plan with recommended actions
    """
    recovery_plan = {
        "error_type": type(error).__name__,
        "recovery_strategy": None,
        "immediate_actions": [],
        "long_term_actions": [],
        "fallback_available": True
    }
    
    if isinstance(error, LLMRateLimitError):
        retry_after = error.details.get("retry_after", 60)
        provider = error.details.get("provider", "unknown")
        fallback_providers = context.get("fallback_providers", []) if context else []
        
        recovery_strategy = await LLMErrorRecovery.recover_from_rate_limit(
            provider, retry_after, fallback_providers
        )
        recovery_plan["recovery_strategy"] = recovery_strategy
        
        if recovery_strategy["recommended_action"] == "wait_and_retry":
            recovery_plan["immediate_actions"].append(f"Wait {retry_after} seconds and retry")
        elif recovery_strategy["recommended_action"] == "switch_provider":
            recovery_plan["immediate_actions"].append("Switch to alternative LLM provider")
        else:
            recovery_plan["immediate_actions"].append("Use fallback research methods")
    
    elif isinstance(error, LLMValidationError):
        raw_response = error.details.get("raw_response", "")
        validation_errors = error.details.get("validation_errors", [])
        
        recovery_strategy = await LLMErrorRecovery.recover_from_validation_error(
            raw_response, validation_errors
        )
        recovery_plan["recovery_strategy"] = recovery_strategy
        
        if recovery_strategy["success"]:
            recovery_plan["immediate_actions"].append("Use recovered data from response")
        else:
            recovery_plan["immediate_actions"].extend([
                "Retry request with refined prompt",
                "Use fallback research methods"
            ])
    
    elif isinstance(error, LLMConnectionError):
        provider = error.details.get("provider", "unknown")
        endpoint = error.details.get("endpoint", "unknown")
        
        recovery_strategy = await LLMErrorRecovery.recover_from_connection_error(
            provider, endpoint, str(error)
        )
        recovery_plan["recovery_strategy"] = recovery_strategy
        recovery_plan["immediate_actions"].extend(recovery_strategy["recommended_actions"][:2])
        recovery_plan["long_term_actions"].extend(recovery_strategy["recommended_actions"][2:])
    
    else:
        recovery_plan["immediate_actions"].extend([
            "Log error details for investigation",
            "Use fallback research methods",
            "Monitor for pattern of similar errors"
        ])
        recovery_plan["long_term_actions"].extend([
            "Review LLM provider configuration",
            "Consider alternative providers",
            "Update error handling logic"
        ])
    
    return recovery_plan


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