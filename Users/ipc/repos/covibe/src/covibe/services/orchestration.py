"""Request orchestration system using functional programming and async composition."""

import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
from ..models.core import (
    PersonalityRequest,
    PersonalityConfig,
    PersonalityProfile,
    PersonalityType,
    CommunicationStyle,
    FormalityLevel,
    VerbosityLevel,
    TechnicalLevel,
    ErrorResponse,
    ErrorDetail
)
from .research import research_personality
from .context_generation import generate_personality_context
from ..integrations.ide_detection import detect_ides, get_primary_ide
from ..integrations.ide_writers import write_to_ide, write_to_multiple_ides, WriteResult


@dataclass
class OrchestrationResult:
    """Result of complete personality orchestration workflow."""
    success: bool
    config: Optional[PersonalityConfig]
    research_confidence: float
    context_generated: bool
    ide_integrations: List[WriteResult]
    errors: List[str]
    suggestions: List[str]
    processing_time: float


@dataclass
class OrchestrationOptions:
    """Options for orchestration workflow."""
    project_path: Optional[str] = None
    target_ide: Optional[str] = None
    auto_detect_ide: bool = True
    write_to_all_ides: bool = False
    skip_ide_integration: bool = False


async def orchestrate_personality_creation(
    request: PersonalityRequest,
    options: OrchestrationOptions = None
) -> OrchestrationResult:
    """
    Orchestrate the complete personality creation workflow.
    
    Args:
        request: PersonalityRequest with personality description
        options: OrchestrationOptions for workflow configuration
        
    Returns:
        OrchestrationResult with complete workflow results
    """
    start_time = datetime.now()
    options = options or OrchestrationOptions()
    
    errors = []
    suggestions = []
    config = None
    research_confidence = 0.0
    context_generated = False
    ide_integrations = []
    
    try:
        # Step 1: Research personality
        research_result = await research_personality(request.description)
        research_confidence = research_result.confidence
        
        if not research_result.profiles:
            errors.extend(research_result.errors)
            suggestions.extend(research_result.suggestions)
            return _create_failure_result(
                start_time, errors, suggestions, research_confidence
            )
        
        # Use the best profile from research
        profile = research_result.profiles[0]
        
        # Step 2: Generate context
        try:
            context = generate_personality_context(profile)
            context_generated = True
        except Exception as e:
            errors.append(f"Context generation failed: {str(e)}")
            context = f"Basic personality context for {profile.name}"
        
        # Step 3: Create personality configuration
        config = PersonalityConfig(
            id=request.id,
            profile=profile,
            context=context,
            ide_type="unknown",
            file_path="",
            active=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Step 4: IDE Integration (if not skipped)
        if not options.skip_ide_integration and options.project_path:
            ide_integrations = await handle_ide_integration(
                config, options, errors, suggestions
            )
        
        # Calculate processing time
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return OrchestrationResult(
            success=True,
            config=config,
            research_confidence=research_confidence,
            context_generated=context_generated,
            ide_integrations=ide_integrations,
            errors=errors,
            suggestions=suggestions,
            processing_time=processing_time
        )
        
    except Exception as e:
        errors.append(f"Orchestration failed: {str(e)}")
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return OrchestrationResult(
            success=False,
            config=config,
            research_confidence=research_confidence,
            context_generated=context_generated,
            ide_integrations=ide_integrations,
            errors=errors,
            suggestions=suggestions + ["Try again with a different personality description"],
            processing_time=processing_time
        )


async def handle_ide_integration(
    config: PersonalityConfig,
    options: OrchestrationOptions,
    errors: List[str],
    suggestions: List[str]
) -> List[WriteResult]:
    """Handle IDE integration workflow."""
    ide_integrations = []
    project_path = Path(options.project_path)
    
    try:
        if options.target_ide:
            # Write to specific IDE
            result = await write_to_ide(options.target_ide, config, project_path)
            ide_integrations.append(result)
            
            # Update config with IDE info
            if result.success:
                config.ide_type = options.target_ide
                config.file_path = result.file_path
            
        elif options.auto_detect_ide:
            # Auto-detect and write to IDEs
            detected_ides = detect_ides(str(project_path))
            
            if not detected_ides:
                suggestions.append("No IDEs detected. Consider specifying a target IDE or project path.")
                return ide_integrations
            
            if options.write_to_all_ides:
                # Write to all detected IDEs
                ide_types = [ide.type for ide in detected_ides]
                ide_integrations = await write_to_multiple_ides(ide_types, config, project_path)
            else:
                # Write to primary IDE only
                primary_ide = get_primary_ide(detected_ides)
                if primary_ide:
                    result = await write_to_ide(primary_ide.type, config, project_path)
                    ide_integrations.append(result)
                    
                    # Update config with IDE info
                    if result.success:
                        config.ide_type = primary_ide.type
                        config.file_path = result.file_path
        
        # Collect any integration errors
        for integration in ide_integrations:
            if not integration.success:
                errors.append(f"IDE integration failed: {integration.message}")
        
    except Exception as e:
        errors.append(f"IDE integration error: {str(e)}")
    
    return ide_integrations


def _create_failure_result(
    start_time: datetime,
    errors: List[str],
    suggestions: List[str],
    research_confidence: float
) -> OrchestrationResult:
    """Create a failure result for orchestration."""
    processing_time = (datetime.now() - start_time).total_seconds()
    
    return OrchestrationResult(
        success=False,
        config=None,
        research_confidence=research_confidence,
        context_generated=False,
        ide_integrations=[],
        errors=errors,
        suggestions=suggestions,
        processing_time=processing_time
    )


async def orchestrate_research_only(
    description: str
) -> Dict[str, Any]:
    """
    Orchestrate personality research only (no config creation).
    
    Args:
        description: Personality description to research
        
    Returns:
        Dictionary with research results
    """
    try:
        result = await research_personality(description)
        
        return {
            "success": True,
            "query": result.query,
            "profiles_found": len(result.profiles),
            "profiles": [
                {
                    "name": p.name,
                    "type": p.type.value,
                    "traits": [t.trait for t in p.traits],
                    "confidence": p.sources[0].confidence if p.sources else 0.0,
                    "communication_style": {
                        "tone": p.communication_style.tone,
                        "formality": p.communication_style.formality.value,
                        "verbosity": p.communication_style.verbosity.value,
                        "technical_level": p.communication_style.technical_level.value
                    }
                }
                for p in result.profiles
            ],
            "confidence": result.confidence,
            "suggestions": result.suggestions,
            "errors": result.errors
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "suggestions": ["Try a different personality description", "Check your input format"]
        }


async def orchestrate_context_generation(
    description: str,
    ide_type: str = "generic"
) -> Dict[str, Any]:
    """
    Orchestrate personality research and context generation.
    
    Args:
        description: Personality description to research
        ide_type: Target IDE type for context formatting
        
    Returns:
        Dictionary with context generation results
    """
    try:
        # Research personality
        result = await research_personality(description)
        
        if not result.profiles:
            return {
                "success": False,
                "error": "No personality profiles found",
                "suggestions": result.suggestions
            }
        
        profile = result.profiles[0]
        
        # Generate context
        from .context_generation import generate_context_for_ide
        context = generate_context_for_ide(profile, ide_type)
        
        return {
            "success": True,
            "personality_name": profile.name,
            "personality_type": profile.type.value,
            "ide_type": ide_type,
            "context": context,
            "confidence": result.confidence,
            "research_sources": len(profile.sources)
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "suggestions": ["Try a different personality description", "Check IDE type"]
        }


async def orchestrate_ide_detection(
    project_path: str
) -> Dict[str, Any]:
    """
    Orchestrate IDE detection for a project.
    
    Args:
        project_path: Path to the project directory
        
    Returns:
        Dictionary with IDE detection results
    """
    try:
        detected_ides = detect_ides(project_path)
        primary_ide = get_primary_ide(detected_ides)
        
        return {
            "success": True,
            "project_path": project_path,
            "total_detected": len(detected_ides),
            "primary_ide": {
                "name": primary_ide.name,
                "type": primary_ide.type,
                "confidence": primary_ide.confidence,
                "config_path": primary_ide.config_path,
                "markers": primary_ide.markers
            } if primary_ide else None,
            "all_detected": [
                {
                    "name": ide.name,
                    "type": ide.type,
                    "confidence": ide.confidence,
                    "config_path": ide.config_path,
                    "markers": ide.markers
                }
                for ide in detected_ides
            ]
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "suggestions": ["Check if the project path exists", "Ensure proper permissions"]
        }


class OrchestrationCache:
    """Simple in-memory cache for orchestration results."""
    
    def __init__(self, max_size: int = 100, ttl_seconds: int = 300):
        self._cache: Dict[str, Tuple[Any, datetime]] = {}
        self._max_size = max_size
        self._ttl_seconds = ttl_seconds
    
    def get(self, key: str) -> Optional[Any]:
        """Get cached result if not expired."""
        if key in self._cache:
            result, timestamp = self._cache[key]
            if (datetime.now() - timestamp).total_seconds() < self._ttl_seconds:
                return result
            else:
                del self._cache[key]
        return None
    
    def set(self, key: str, value: Any) -> None:
        """Set cached result with cleanup if needed."""
        # Clean up expired entries
        self._cleanup_expired()
        
        # Remove oldest if at capacity
        if len(self._cache) >= self._max_size:
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k][1])
            del self._cache[oldest_key]
        
        self._cache[key] = (value, datetime.now())
    
    def _cleanup_expired(self) -> None:
        """Remove expired cache entries."""
        now = datetime.now()
        expired_keys = [
            key for key, (_, timestamp) in self._cache.items()
            if (now - timestamp).total_seconds() >= self._ttl_seconds
        ]
        for key in expired_keys:
            del self._cache[key]


# Global cache instance
_orchestration_cache = OrchestrationCache()


async def cached_orchestrate_research(description: str) -> Dict[str, Any]:
    """Cached version of research orchestration."""
    cache_key = f"research:{hash(description)}"
    
    # Check cache first
    cached_result = _orchestration_cache.get(cache_key)
    if cached_result:
        return cached_result
    
    # Perform research and cache result
    result = await orchestrate_research_only(description)
    _orchestration_cache.set(cache_key, result)
    
    return result