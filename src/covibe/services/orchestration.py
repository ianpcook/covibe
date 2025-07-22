"""
Request orchestration system for coordinating personality configuration workflows.

This module provides the central orchestrator that manages the async workflow between
different components: research → context generation → IDE integration.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass
from pathlib import Path

from ..models.core import (
    PersonalityRequest, PersonalityProfile, PersonalityConfig,
    ResearchResult, ErrorResponse, ErrorDetail
)
from .research import research_personality
from .context_generation import generate_personality_context
from .input_processing import (
    analyze_personality_input, generate_personality_suggestions,
    process_combination_personality, generate_clarification_questions,
    InputType, InputAnalysis
)
from ..integrations.ide_detection import detect_ides, get_primary_ide
from ..utils.error_handling import (
    SystemError, IntegrationError, error_handler, ErrorCategory,
    RetryConfig, with_fallback, ErrorContext
)
from ..utils.monitoring import record_error, performance_monitor

logger = logging.getLogger(__name__)


@dataclass
class OrchestrationResult:
    """Result of orchestrated personality configuration process."""
    success: bool
    config: Optional[PersonalityConfig] = None
    error: Optional[ErrorDetail] = None
    partial_results: Optional[Dict[str, Any]] = None


@dataclass
class CacheEntry:
    """Cache entry for personality research results."""
    result: ResearchResult
    timestamp: datetime
    ttl_hours: int = 24
    
    @property
    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        return datetime.now() > self.timestamp + timedelta(hours=self.ttl_hours)


class PersonalityCache:
    """Simple in-memory cache for personality research results."""
    
    def __init__(self):
        self._cache: Dict[str, CacheEntry] = {}
    
    def get(self, query: str) -> Optional[ResearchResult]:
        """Get cached research result if available and not expired."""
        entry = self._cache.get(query.lower())
        if entry and not entry.is_expired:
            logger.info(f"Cache hit for personality query: {query}")
            return entry.result
        elif entry and entry.is_expired:
            # Clean up expired entry
            del self._cache[query.lower()]
        return None
    
    def set(self, query: str, result: ResearchResult, ttl_hours: int = 24) -> None:
        """Cache research result with TTL."""
        self._cache[query.lower()] = CacheEntry(
            result=result,
            timestamp=datetime.now(),
            ttl_hours=ttl_hours
        )
        logger.info(f"Cached personality research for: {query}")
    
    def clear_expired(self) -> int:
        """Remove expired cache entries and return count removed."""
        expired_keys = [
            key for key, entry in self._cache.items() 
            if entry.is_expired
        ]
        for key in expired_keys:
            del self._cache[key]
        
        if expired_keys:
            logger.info(f"Cleared {len(expired_keys)} expired cache entries")
        return len(expired_keys)


# Global cache instance
_personality_cache = PersonalityCache()


@error_handler(
    category=ErrorCategory.SYSTEM,
    operation="orchestrate_personality_request_enhanced",
    component="orchestration"
)
@performance_monitor("orchestrate_personality_request_enhanced", "orchestration")
async def orchestrate_personality_request_enhanced(
    request: PersonalityRequest,
    project_path: Optional[Path] = None,
    use_cache: bool = True
) -> OrchestrationResult:
    """
    Enhanced orchestration with advanced input processing.
    
    Pipeline: input analysis → research/combination processing → context generation → IDE integration
    """
    logger.info(f"Starting enhanced orchestration for request: {request.id}")
    
    context = ErrorContext(
        operation="orchestrate_personality_request_enhanced",
        component="orchestration",
        request_id=request.id,
        additional_data={"description": request.description}
    )
    
    try:
        # Stage 0: Advanced Input Analysis
        input_analysis = await analyze_personality_input(request.description)
        
        # Handle different input types
        if input_analysis.input_type == InputType.AMBIGUOUS:
            # Return suggestions for ambiguous input
            suggestions = await generate_personality_suggestions(request.description)
            clarification_questions = await generate_clarification_questions(input_analysis)
            
            error_detail = ErrorDetail(
                code="AMBIGUOUS_INPUT",
                message=f"Multiple personalities match '{request.description}'",
                suggestions=[s.name for s in suggestions[:3]] + [q.question for q in clarification_questions[:2]]
            )
            return OrchestrationResult(
                success=False,
                error=error_detail,
                partial_results={
                    "input_analysis": input_analysis,
                    "suggestions": suggestions,
                    "clarification_questions": clarification_questions
                }
            )
        
        elif input_analysis.input_type == InputType.UNCLEAR:
            # Return clarification questions for unclear input
            clarification_questions = await generate_clarification_questions(input_analysis)
            
            error_detail = ErrorDetail(
                code="UNCLEAR_INPUT",
                message=f"I need more information about '{request.description}'",
                suggestions=[q.question for q in clarification_questions]
            )
            return OrchestrationResult(
                success=False,
                error=error_detail,
                partial_results={
                    "input_analysis": input_analysis,
                    "clarification_questions": clarification_questions
                }
            )
        
        # Stage 1: Enhanced Research/Processing
        profile = None
        
        if input_analysis.input_type == InputType.COMBINATION:
            # Process combination personality
            profile = await process_combination_personality(input_analysis)
            if not profile:
                # Fallback to regular research
                research_result = await _execute_research_stage(
                    input_analysis.primary_personality, use_cache, context
                )
                if research_result.profiles:
                    profile = research_result.profiles[0]
        else:
            # Regular research for specific names and descriptive phrases
            research_query = input_analysis.primary_personality or request.description
            research_result = await _execute_research_stage(research_query, use_cache, context)
            if research_result.profiles:
                profile = research_result.profiles[0]
        
        if not profile:
            error_detail = ErrorDetail(
                code="RESEARCH_FAILED",
                message="I couldn't find or create that personality",
                suggestions=[
                    "Try a more specific personality description",
                    "Check the spelling of the name",
                    "Try a different personality or archetype"
                ]
            )
            return OrchestrationResult(
                success=False,
                error=error_detail,
                partial_results={"input_analysis": input_analysis}
            )
        
        # Stage 2: Context Generation
        context_result = await _execute_context_stage(profile, context)
        
        if not context_result:
            error_detail = ErrorDetail(
                code="CONTEXT_GENERATION_FAILED",
                message="I couldn't generate the personality context",
                suggestions=[
                    "Try again with the same personality",
                    "Contact support if the problem persists"
                ]
            )
            return OrchestrationResult(
                success=False,
                error=error_detail,
                partial_results={
                    "input_analysis": input_analysis,
                    "profile": profile
                }
            )
        
        # Stage 3: IDE Integration
        config = None
        if project_path:
            config = await _execute_ide_integration_stage(
                profile, context_result, project_path, request.id, context
            )
        
        # Create final configuration
        if not config:
            config = PersonalityConfig(
                id=request.id,
                profile=profile,
                context=context_result,
                ide_type="unknown",
                file_path="",
                active=True,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        
        logger.info(f"Successfully orchestrated enhanced request: {request.id}")
        return OrchestrationResult(
            success=True, 
            config=config,
            partial_results={"input_analysis": input_analysis}
        )
        
    except Exception as e:
        # Log the error with context
        record_error(e, "orchestration")
        
        error_detail = ErrorDetail(
            code="ORCHESTRATION_ERROR",
            message="An unexpected error occurred during personality configuration",
            suggestions=[
                "Try again in a few moments",
                "Contact support if the problem persists"
            ]
        )
        
        return OrchestrationResult(
            success=False,
            error=error_detail
        )


@error_handler(
    category=ErrorCategory.SYSTEM,
    operation="orchestrate_personality_request",
    component="orchestration"
)
@performance_monitor("orchestrate_personality_request", "orchestration")
async def orchestrate_personality_request(
    request: PersonalityRequest,
    project_path: Optional[Path] = None,
    use_cache: bool = True
) -> OrchestrationResult:
    """
    Orchestrate complete personality configuration workflow with comprehensive error handling.
    
    Pipeline: research → context generation → IDE integration
    
    Args:
        request: Personality configuration request
        project_path: Optional project path for IDE integration
        use_cache: Whether to use cached research results
    
    Returns:
        OrchestrationResult with success status and results/errors
    """
    logger.info(f"Starting orchestration for request: {request.id}")
    
    context = ErrorContext(
        operation="orchestrate_personality_request",
        component="orchestration",
        request_id=request.id,
        additional_data={"description": request.description}
    )
    
    try:
        # Stage 1: Personality Research (with fallback mechanisms)
        research_result = await _execute_research_stage(
            request.description, use_cache, context
        )
        
        if not research_result.profiles:
            error_detail = ErrorDetail(
                code="RESEARCH_FAILED",
                message="I couldn't find information about that personality",
                suggestions=research_result.suggestions or [
                    "Try a more specific personality description",
                    "Check the spelling of the name",
                    "Try a different personality or archetype"
                ]
            )
            return OrchestrationResult(
                success=False,
                error=error_detail,
                partial_results={"research": research_result}
            )
        
        # Use the first (best) profile found
        profile = research_result.profiles[0]
        
        # Stage 2: Context Generation (with error handling)
        context_result = await _execute_context_stage(profile, context)
        
        if not context_result:
            error_detail = ErrorDetail(
                code="CONTEXT_GENERATION_FAILED",
                message="I couldn't generate the personality context",
                suggestions=[
                    "Try again with the same personality",
                    "Contact support if the problem persists"
                ]
            )
            return OrchestrationResult(
                success=False,
                error=error_detail,
                partial_results={
                    "research": research_result,
                    "profile": profile
                }
            )
        
        # Stage 3: IDE Integration (if project path provided)
        config = None
        if project_path:
            config = await _execute_ide_integration_stage(
                profile, context_result, project_path, request.id, context
            )
        
        # Create final configuration
        if not config:
            config = PersonalityConfig(
                id=request.id,
                profile=profile,
                context=context_result,
                ide_type="unknown",
                file_path="",
                active=True,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        
        logger.info(f"Successfully orchestrated request: {request.id}")
        return OrchestrationResult(success=True, config=config)
        
    except Exception as e:
        # Log the error with context
        record_error(e, "orchestration")
        
        error_detail = ErrorDetail(
            code="ORCHESTRATION_ERROR",
            message="An unexpected error occurred during personality configuration",
            suggestions=[
                "Try again in a few moments",
                "Contact support if the problem persists"
            ]
        )
        
        return OrchestrationResult(
            success=False,
            error=error_detail
        )


async def _execute_research_stage(
    description: str, 
    use_cache: bool,
    context: ErrorContext
) -> ResearchResult:
    """Execute personality research stage with caching."""
    logger.info(f"Executing research stage for: {description}")
    
    # Check cache first
    if use_cache:
        cached_result = _personality_cache.get(description)
        if cached_result:
            return cached_result
    
    # Perform research
    try:
        result = await research_personality(description)
        
        # Cache successful results
        if use_cache and result.profiles:
            _personality_cache.set(description, result)
        
        return result
        
    except Exception as e:
        logger.error(f"Research stage failed: {str(e)}")
        return ResearchResult(
            query=description,
            profiles=[],
            confidence=0.0,
            suggestions=[],
            errors=[str(e)]
        )


async def _execute_context_stage(profile: PersonalityProfile, context: ErrorContext) -> Optional[str]:
    """Execute context generation stage."""
    logger.info(f"Executing context stage for profile: {profile.name}")
    
    try:
        context_result = generate_personality_context(profile)
        return context_result
        
    except Exception as e:
        logger.error(f"Context generation stage failed: {str(e)}")
        record_error(e, "orchestration")
        return None


async def _execute_ide_integration_stage(
    profile: PersonalityProfile,
    context: str,
    project_path: Path,
    request_id: str,
    error_context: ErrorContext
) -> Optional[PersonalityConfig]:
    """Execute IDE integration stage."""
    logger.info(f"Executing IDE integration stage for: {project_path}")
    
    try:
        # Detect IDE types
        detected_ides = detect_ides(str(project_path))
        primary_ide = get_primary_ide(detected_ides)
        
        ide_type = primary_ide.type if primary_ide else "unknown"
        file_path = primary_ide.config_path if primary_ide else ""
        
        # Create configuration
        config = PersonalityConfig(
            id=request_id,
            profile=profile,
            context=context,
            ide_type=ide_type,
            file_path=file_path,
            active=True,  # Configuration is active regardless of IDE detection
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # For now, we'll just create the config without writing files
        # The actual file writing will be implemented in the IDE writers module
        if primary_ide:
            logger.info(f"Detected IDE: {primary_ide.name} (confidence: {primary_ide.confidence})")
            logger.info(f"Config would be written to: {primary_ide.config_path}")
        else:
            logger.info("No IDE detected, configuration created without file integration")
        
        return config
        
    except Exception as e:
        logger.error(f"IDE integration stage failed: {str(e)}")
        return None


async def orchestrate_research_only(
    description: str,
    use_cache: bool = True
) -> ResearchResult:
    """
    Orchestrate personality research only (no context generation or IDE integration).
    
    Args:
        description: Personality description to research
        use_cache: Whether to use cached results
    
    Returns:
        ResearchResult with personality profiles found
    """
    logger.info(f"Starting research-only orchestration for: {description}")
    
    context = ErrorContext(
        operation="research_only",
        component="orchestration",
        additional_data={"description": description}
    )
    
    return await _execute_research_stage(description, use_cache, context)


async def orchestrate_batch_requests(
    requests: List[PersonalityRequest],
    project_path: Optional[Path] = None,
    max_concurrent: int = 3
) -> List[OrchestrationResult]:
    """
    Orchestrate multiple personality requests concurrently.
    
    Args:
        requests: List of personality requests to process
        project_path: Optional project path for IDE integration
        max_concurrent: Maximum number of concurrent requests
    
    Returns:
        List of orchestration results in same order as requests
    """
    logger.info(f"Starting batch orchestration for {len(requests)} requests")
    
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def process_request(request: PersonalityRequest) -> OrchestrationResult:
        async with semaphore:
            return await orchestrate_personality_request(request, project_path)
    
    # Process requests concurrently
    tasks = [process_request(req) for req in requests]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Handle any exceptions
    final_results = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error(f"Batch request {i} failed: {str(result)}")
            final_results.append(OrchestrationResult(
                success=False,
                error=ErrorDetail(
                    code="BATCH_REQUEST_ERROR",
                    message=f"Request failed: {str(result)}"
                )
            ))
        else:
            final_results.append(result)
    
    logger.info(f"Completed batch orchestration: {len(final_results)} results")
    return final_results


def get_cache_stats() -> Dict[str, Any]:
    """Get personality cache statistics."""
    cache_size = len(_personality_cache._cache)
    expired_count = sum(
        1 for entry in _personality_cache._cache.values() 
        if entry.is_expired
    )
    
    return {
        "total_entries": cache_size,
        "expired_entries": expired_count,
        "active_entries": cache_size - expired_count
    }


async def clear_cache(clear_all: bool = False) -> int:
    """
    Clear personality cache.
    
    Args:
        clear_all: If True, clear all entries. If False, only clear expired.
    
    Returns:
        Number of entries cleared
    """
    if clear_all:
        count = len(_personality_cache._cache)
        _personality_cache._cache.clear()
        logger.info(f"Cleared all {count} cache entries")
        return count
    else:
        return _personality_cache.clear_expired()