"""Personality API routes and handlers with database persistence."""

from fastapi import APIRouter, HTTPException, Request, status, Query, Depends
from fastapi.encoders import jsonable_encoder
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path
import uuid
from pydantic import BaseModel, Field

from ..models.core import (
    PersonalityRequest,
    PersonalityProfile,
    PersonalityConfig,
    ErrorResponse,
    ErrorDetail,
    SourceType,
    PersonalityType,
    CommunicationStyle,
    FormalityLevel,
    VerbosityLevel,
    TechnicalLevel
)
from ..services.orchestration import (
    orchestrate_personality_request,
    orchestrate_personality_request_enhanced,
    orchestrate_research_only,
    get_cache_stats,
    clear_cache
)
from ..services.input_processing import (
    analyze_personality_input,
    generate_personality_suggestions,
    generate_clarification_questions,
    InputType
)
from ..services.persistence import ConfigurationPersistenceService
from ..integrations.ide_detection import detect_ides, get_primary_ide
from ..utils.database import get_database_config


router = APIRouter(prefix="/api/personality", tags=["personality"])


# Dependency to get persistence service
async def get_persistence_service() -> ConfigurationPersistenceService:
    """Get persistence service instance."""
    db_config = await get_database_config()
    return ConfigurationPersistenceService(db_config)


# Request/Response models for API
class PersonalityRequestCreate(BaseModel):
    """Request model for creating personality configurations."""
    description: str = Field(..., min_length=1, max_length=500, description="Personality description")
    user_id: Optional[str] = Field(None, description="Optional user ID")
    project_path: Optional[str] = Field(None, description="Optional project path for IDE integration")
    source: SourceType = Field(default=SourceType.API, description="Request source")


class PersonalityUpdateRequest(BaseModel):
    """Request model for updating personality configurations."""
    description: Optional[str] = Field(None, min_length=1, max_length=500)
    project_path: Optional[str] = Field(None, description="Project path for IDE integration")


class ResearchOnlyRequest(BaseModel):
    """Request model for research-only operations."""
    description: str = Field(..., min_length=1, max_length=500, description="Personality description")
    use_cache: bool = Field(default=True, description="Whether to use cached results")


class PersonalityConfigResponse(BaseModel):
    """Response model for personality configurations."""
    id: str
    profile: PersonalityProfile
    context: str
    ide_type: str
    file_path: str
    active: bool
    created_at: datetime
    updated_at: datetime


class ResearchResponse(BaseModel):
    """Response model for research operations."""
    query: str
    profiles_found: int
    profiles: List[Dict[str, Any]]
    confidence: float
    suggestions: List[str]
    errors: List[str]
    # New fields for LLM enhancement (optional for backward compatibility)
    llm_used: Optional[bool] = Field(default=False, description="Whether LLM was used for research")
    llm_provider: Optional[str] = Field(default=None, description="LLM provider used")
    processing_time_ms: Optional[float] = Field(default=None, description="Processing time in milliseconds")


class ConfigurationHistoryResponse(BaseModel):
    """Response model for configuration history."""
    id: int
    version: int
    change_type: str
    change_description: str
    created_at: datetime
    created_by: Optional[str]


class BackupCreateRequest(BaseModel):
    """Request model for creating backups."""
    backup_name: str = Field(..., min_length=1, max_length=255, description="Name for the backup")
    config_ids: Optional[List[str]] = Field(None, description="Specific configuration IDs to backup (all if not provided)")


class BackupResponse(BaseModel):
    """Response model for backup operations."""
    id: int
    backup_name: str
    user_id: Optional[str]
    created_at: datetime
    file_size: int
    checksum: str


class InputAnalysisRequest(BaseModel):
    """Request model for input analysis."""
    description: str = Field(..., min_length=1, max_length=500, description="Personality description to analyze")


class InputAnalysisResponse(BaseModel):
    """Response model for input analysis."""
    input_type: str
    confidence: float
    primary_personality: Optional[str]
    modifiers: Optional[List[str]]
    combination_type: Optional[str]
    secondary_personality: Optional[str]
    suggestions: Optional[List[str]]
    clarification_questions: Optional[List[str]]


class PersonalitySuggestionResponse(BaseModel):
    """Response model for personality suggestions."""
    name: str
    confidence: float
    reason: str
    personality_type: str


class ClarificationQuestionResponse(BaseModel):
    """Response model for clarification questions."""
    question: str
    options: List[str]
    context: str


async def create_error_response(
    request: Request,
    code: str,
    message: str,
    suggestions: Optional[List[str]] = None
) -> ErrorResponse:
    """Create standardized error response."""
    return ErrorResponse(
        error=ErrorDetail(
            code=code,
            message=message,
            suggestions=suggestions or []
        ),
        request_id=getattr(request.state, 'request_id', 'unknown'),
        timestamp=datetime.now()
    )


@router.post("/", response_model=PersonalityConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_personality_config(
    request: Request,
    personality_request: PersonalityRequestCreate,
    use_llm: bool = Query(default=True, description="Whether to use LLM for research"),
    llm_provider: Optional[str] = Query(default=None, description="Specific LLM provider to use"),
    persistence_service: ConfigurationPersistenceService = Depends(get_persistence_service)
) -> PersonalityConfigResponse:
    """
    Create a new personality configuration using the orchestration system.
    Enhanced with LLM research capabilities.
    """
    try:
        # Create PersonalityRequest for orchestration
        request_obj = PersonalityRequest(
            id=str(uuid.uuid4()),
            description=personality_request.description,
            user_id=personality_request.user_id,
            timestamp=datetime.now(),
            source=personality_request.source
        )
        
        # Determine project path
        project_path = None
        if personality_request.project_path:
            project_path = Path(personality_request.project_path)
        
        # Log the LLM-enhanced personality creation request
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"LLM personality creation request: description='{personality_request.description}' use_llm={use_llm} provider={llm_provider} request_id={getattr(request.state, 'request_id', 'unknown')}")
        
        # Use orchestration system - for now, continue using existing orchestration
        # until we can enhance it with LLM parameters
        result = await orchestrate_personality_request(
            request_obj,
            project_path=project_path,
            use_cache=True
        )
        
        if not result.success:
            error_response = await create_error_response(
                request,
                result.error.code if result.error else "ORCHESTRATION_ERROR",
                result.error.message if result.error else "Failed to create personality configuration",
                result.error.suggestions if result.error else []
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=jsonable_encoder(error_response.dict())
            )
        
        # Store configuration in database
        config = result.config
        await persistence_service.create_configuration(
            config,
            user_id=personality_request.user_id,
            created_by=f"api_{request.state.request_id}"
        )
        
        return PersonalityConfigResponse(**config.model_dump())
        
    except HTTPException:
        raise
    except Exception as e:
        error_response = await create_error_response(
            request,
            "PROCESSING_ERROR",
            f"Failed to create personality configuration: {str(e)}",
            ["Try again with different input", "Contact support if the problem persists"]
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=jsonable_encoder(error_response.dict())
        )


@router.get("/configs")
async def list_personality_configs(
    request: Request,
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    active_only: bool = Query(True, description="Only return active configurations"),
    limit: int = Query(default=10, ge=1, le=100, description="Maximum number of configurations to return"),
    offset: int = Query(default=0, ge=0, description="Number of configurations to skip"),
    persistence_service: ConfigurationPersistenceService = Depends(get_persistence_service)
) -> Dict[str, Any]:
    """
    List all personality configurations with pagination.
    """
    try:
        # Get configurations from database
        configurations = await persistence_service.list_configurations(
            user_id=user_id,
            active_only=active_only,
            limit=limit,
            offset=offset
        )
        
        # Get total count for pagination (simplified - in production, you'd want a separate count query)
        all_configs = await persistence_service.list_configurations(
            user_id=user_id,
            active_only=active_only,
            limit=1000,  # Large limit to get approximate total
            offset=0
        )
        total = len(all_configs)
        
        return {
            "configurations": [
                jsonable_encoder(PersonalityConfigResponse(**config.model_dump()).model_dump())
                for config in configurations
            ],
            "pagination": {
                "total": total,
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < total
            }
        }
        
    except Exception as e:
        error_response = await create_error_response(
            request,
            "LIST_ERROR",
            f"Failed to list personality configurations: {str(e)}",
            ["Contact support if the problem persists"]
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=jsonable_encoder(error_response.dict())
        )


@router.post("/research", response_model=ResearchResponse, status_code=status.HTTP_200_OK)
async def research_personality_endpoint(
    request: Request,
    research_request: ResearchOnlyRequest,
    use_llm: bool = Query(default=True, description="Whether to use LLM for research"),
    llm_provider: Optional[str] = Query(default=None, description="Specific LLM provider to use")
) -> ResearchResponse:
    """
    Research a personality without creating a full configuration.
    Enhanced with LLM research capabilities.
    """
    import time
    start_time = time.time()
    
    try:
        # Import research function
        from ..services.research import research_personality
        
        # Log the LLM-enhanced request
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"LLM research request: query='{research_request.description}' use_llm={use_llm} provider={llm_provider} request_id={getattr(request.state, 'request_id', 'unknown')}")
        
        # Use enhanced research function with LLM support
        result = await research_personality(
            research_request.description,
            use_llm=use_llm,
            llm_provider=llm_provider,
            cache_enabled=research_request.use_cache
        )
        
        # Check if LLM was actually used based on source types
        llm_used = any(
            any(s.type.startswith("llm_") for s in p.sources) if p.sources else False
            for p in result.profiles
        )
        
        # Calculate processing time
        processing_time = (time.time() - start_time) * 1000  # Convert to milliseconds
        
        # Log the response
        logger.info(f"LLM research response: profiles_found={len(result.profiles)} llm_used={llm_used} provider={llm_provider} processing_time={processing_time:.2f}ms request_id={getattr(request.state, 'request_id', 'unknown')}")
        
        return ResearchResponse(
            query=result.query,
            profiles_found=len(result.profiles),
            profiles=[
                {
                    "id": p.id,
                    "name": p.name,
                    "type": p.type.value,
                    "traits": [{"trait": t.trait, "intensity": t.intensity} for t in p.traits],
                    "communication_style": {
                        "tone": p.communication_style.tone,
                        "formality": p.communication_style.formality.value,
                        "verbosity": p.communication_style.verbosity.value,
                        "technical_level": p.communication_style.technical_level.value
                    },
                    "mannerisms": p.mannerisms,
                    "confidence": p.sources[0].confidence if p.sources else 0.0,
                    "llm_enhanced": any(s.type.startswith("llm_") for s in p.sources) if p.sources else False
                }
                for p in result.profiles
            ],
            confidence=result.confidence,
            suggestions=result.suggestions,
            errors=result.errors,
            llm_used=llm_used,
            llm_provider=llm_provider if llm_used else None,
            processing_time_ms=processing_time
        )
        
    except Exception as e:
        error_response = await create_error_response(
            request,
            "RESEARCH_ERROR",
            f"Failed to research personality: {str(e)}",
            ["Try again with different input", "Contact support if the problem persists"]
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=jsonable_encoder(error_response.dict())
        )


@router.get("/ide/detect")
async def detect_ide_environment(
    request: Request,
    project_path: str = Query(..., description="Project path to analyze for IDE detection")
):
    """
    Detect IDE environment in the specified project path.
    """
    try:
        path_obj = Path(project_path)
        if not path_obj.exists():
            error_response = await create_error_response(
                request,
                "PATH_NOT_FOUND",
                f"Project path does not exist: {project_path}",
                ["Check the project path", "Ensure the directory exists"]
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=jsonable_encoder(error_response.dict())
            )
        
        # Detect IDEs
        detected_ides = detect_ides(project_path)
        primary_ide = get_primary_ide(detected_ides)
        
        return {
            "project_path": project_path,
            "detected_ides": [
                {
                    "name": ide.name,
                    "type": ide.type,
                    "config_path": ide.config_path,
                    "confidence": ide.confidence,
                    "markers": ide.markers
                }
                for ide in detected_ides
            ],
            "primary_ide": {
                "name": primary_ide.name,
                "type": primary_ide.type,
                "config_path": primary_ide.config_path,
                "confidence": primary_ide.confidence,
                "markers": primary_ide.markers
            } if primary_ide else None,
            "total_detected": len(detected_ides)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        error_response = await create_error_response(
            request,
            "IDE_DETECTION_ERROR",
            f"Failed to detect IDE environment: {str(e)}",
            ["Check the project path", "Contact support if the problem persists"]
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=jsonable_encoder(error_response.dict())
        )


@router.get("/cache/stats")
async def get_cache_statistics(request: Request):
    """
    Get personality cache statistics.
    """
    try:
        stats = get_cache_stats()
        return {
            "cache_stats": stats,
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        error_response = await create_error_response(
            request,
            "CACHE_STATS_ERROR",
            f"Failed to get cache statistics: {str(e)}",
            ["Contact support if the problem persists"]
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=jsonable_encoder(error_response.dict())
        )


@router.delete("/cache")
async def clear_personality_cache(
    request: Request,
    clear_all: bool = Query(default=False, description="Whether to clear all entries or just expired ones")
):
    """
    Clear personality cache entries.
    """
    try:
        cleared_count = await clear_cache(clear_all=clear_all)
        
        return {
            "cleared_entries": cleared_count,
            "clear_type": "all" if clear_all else "expired_only",
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        error_response = await create_error_response(
            request,
            "CACHE_CLEAR_ERROR",
            f"Failed to clear cache: {str(e)}",
            ["Contact support if the problem persists"]
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=jsonable_encoder(error_response.dict())
        )


@router.get("/llm/status")
async def get_llm_provider_status(request: Request):
    """
    Get status and configuration information for LLM providers.
    """
    try:
        import os
        from ..services.llm_client import (
            create_openai_client,
            create_anthropic_client,
            create_local_client
        )
        
        providers = {}
        
        # Check OpenAI provider
        if os.getenv("OPENAI_API_KEY"):
            try:
                client = await create_openai_client(
                    api_key=os.getenv("OPENAI_API_KEY"),
                    model="gpt-4"
                )
                connection_status = await client.validate_connection()
                providers["openai"] = {
                    "available": True,
                    "connected": connection_status,
                    "models": ["gpt-4", "gpt-3.5-turbo"],
                    "default_model": "gpt-4"
                }
            except Exception as e:
                providers["openai"] = {
                    "available": True,
                    "connected": False,
                    "error": str(e),
                    "models": ["gpt-4", "gpt-3.5-turbo"],
                    "default_model": "gpt-4"
                }
        else:
            providers["openai"] = {
                "available": False,
                "connected": False,
                "error": "API key not configured",
                "models": ["gpt-4", "gpt-3.5-turbo"],
                "default_model": "gpt-4"
            }
        
        # Check Anthropic provider
        if os.getenv("ANTHROPIC_API_KEY"):
            try:
                client = await create_anthropic_client(
                    api_key=os.getenv("ANTHROPIC_API_KEY"),
                    model="claude-3-sonnet-20240229"
                )
                connection_status = await client.validate_connection()
                providers["anthropic"] = {
                    "available": True,
                    "connected": connection_status,
                    "models": ["claude-3-opus-20240229", "claude-3-sonnet-20240229"],
                    "default_model": "claude-3-sonnet-20240229"
                }
            except Exception as e:
                providers["anthropic"] = {
                    "available": True,
                    "connected": False,
                    "error": str(e),
                    "models": ["claude-3-opus-20240229", "claude-3-sonnet-20240229"],
                    "default_model": "claude-3-sonnet-20240229"
                }
        else:
            providers["anthropic"] = {
                "available": False,
                "connected": False,
                "error": "API key not configured",
                "models": ["claude-3-opus-20240229", "claude-3-sonnet-20240229"],
                "default_model": "claude-3-sonnet-20240229"
            }
        
        # Check local provider
        local_endpoint = os.getenv("LOCAL_LLM_ENDPOINT", "http://localhost:11434")
        try:
            client = await create_local_client(
                endpoint=local_endpoint,
                model="llama2"
            )
            connection_status = await client.validate_connection()
            providers["local"] = {
                "available": True,
                "connected": connection_status,
                "endpoint": local_endpoint,
                "models": ["llama2", "mistral"],
                "default_model": "llama2"
            }
        except Exception as e:
            providers["local"] = {
                "available": True,
                "connected": False,
                "error": str(e),
                "endpoint": local_endpoint,
                "models": ["llama2", "mistral"],
                "default_model": "llama2"
            }
        
        # Determine the preferred provider
        preferred_provider = None
        if providers["openai"]["connected"]:
            preferred_provider = "openai"
        elif providers["anthropic"]["connected"]:
            preferred_provider = "anthropic"
        elif providers["local"]["connected"]:
            preferred_provider = "local"
        
        return {
            "providers": providers,
            "preferred_provider": preferred_provider,
            "llm_research_enabled": preferred_provider is not None,
            "timestamp": datetime.now()
        }
        
    except Exception as e:
        error_response = await create_error_response(
            request,
            "LLM_STATUS_ERROR",
            f"Failed to get LLM provider status: {str(e)}",
            ["Contact support if the problem persists"]
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=jsonable_encoder(error_response.dict())
        )


@router.get("/{personality_id}", response_model=PersonalityConfigResponse)
async def get_personality_config(
    request: Request,
    personality_id: str,
    persistence_service: ConfigurationPersistenceService = Depends(get_persistence_service)
) -> PersonalityConfigResponse:
    """
    Retrieve a personality configuration by ID.
    """
    try:
        config = await persistence_service.get_configuration(personality_id)
        
        if not config:
            error_response = await create_error_response(
                request,
                "NOT_FOUND",
                f"Personality configuration with ID {personality_id} not found",
                ["Check the personality ID", "Create a new personality configuration"]
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=jsonable_encoder(error_response.model_dump())
            )
        
        return PersonalityConfigResponse(**config.model_dump())
        
    except HTTPException:
        raise
    except Exception as e:
        error_response = await create_error_response(
            request,
            "GET_ERROR",
            f"Failed to retrieve personality configuration: {str(e)}",
            ["Contact support if the problem persists"]
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=jsonable_encoder(error_response.model_dump())
        )


@router.put("/{personality_id}", response_model=PersonalityConfigResponse)
async def update_personality_config(
    request: Request,
    personality_id: str,
    update_request: PersonalityUpdateRequest,
    persistence_service: ConfigurationPersistenceService = Depends(get_persistence_service)
) -> PersonalityConfigResponse:
    """
    Update an existing personality configuration.
    """
    try:
        # Get existing configuration from database
        existing_config = await persistence_service.get_configuration(personality_id)
        
        if not existing_config:
            error_response = await create_error_response(
                request,
                "NOT_FOUND",
                f"Personality configuration with ID {personality_id} not found",
                ["Check the personality ID", "Create a new personality configuration"]
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=jsonable_encoder(error_response.model_dump())
            )
        
        # If description is provided, re-orchestrate with new personality
        if update_request.description:
            request_obj = PersonalityRequest(
                id=str(uuid.uuid4()),
                description=update_request.description,
                user_id=existing_config.profile.id,  # Use existing profile ID as user ID
                timestamp=datetime.now(),
                source=SourceType.API
            )
            
            # Determine project path
            project_path = None
            if update_request.project_path:
                project_path = Path(update_request.project_path)
            
            # Re-orchestrate with new description
            result = await orchestrate_personality_request(
                request_obj,
                project_path=project_path,
                use_cache=True
            )
            
            if not result.success:
                error_response = await create_error_response(
                    request,
                    result.error.code if result.error else "UPDATE_ERROR",
                    result.error.message if result.error else "Failed to update personality configuration",
                    result.error.suggestions if result.error else []
                )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=jsonable_encoder(error_response.model_dump())
                )
            
            # Update the configuration
            updated_config = result.config
            updated_config.id = personality_id  # Keep the same ID
            updated_config.created_at = existing_config.created_at  # Keep original creation time
            updated_config.updated_at = datetime.now()
            
        else:
            # Just update project path if provided
            updated_config = existing_config.model_copy()
            if update_request.project_path:
                project_path = Path(update_request.project_path)
                detected_ides = detect_ides(str(project_path))
                primary_ide = get_primary_ide(detected_ides)
                
                updated_config.ide_type = primary_ide.type if primary_ide else "unknown"
                updated_config.file_path = primary_ide.config_path if primary_ide else ""
                updated_config.active = bool(primary_ide)
            
            updated_config.updated_at = datetime.now()
        
        # Update configuration in database
        success = await persistence_service.update_configuration(
            personality_id,
            updated_config,
            updated_by=f"api_{request.state.request_id}"
        )
        
        if not success:
            error_response = await create_error_response(
                request,
                "UPDATE_FAILED",
                "Failed to update configuration in database",
                ["Try again", "Contact support if the problem persists"]
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=jsonable_encoder(error_response.model_dump())
            )
        
        return PersonalityConfigResponse(**updated_config.model_dump())
        
    except HTTPException:
        raise
    except Exception as e:
        error_response = await create_error_response(
            request,
            "UPDATE_ERROR",
            f"Failed to update personality configuration: {str(e)}",
            ["Try again with different input", "Contact support if the problem persists"]
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=jsonable_encoder(error_response.model_dump())
        )


@router.delete("/{personality_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_personality_config(
    request: Request,
    personality_id: str,
    persistence_service: ConfigurationPersistenceService = Depends(get_persistence_service)
):
    """
    Delete a personality configuration.
    """
    try:
        # Check if configuration exists and delete it
        success = await persistence_service.delete_configuration(
            personality_id,
            deleted_by=f"api_{request.state.request_id}"
        )
        
        if not success:
            error_response = await create_error_response(
                request,
                "NOT_FOUND",
                f"Personality configuration with ID {personality_id} not found",
                ["Check the personality ID"]
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=jsonable_encoder(error_response.model_dump())
            )
        
        # Return 204 No Content (no response body)
        
    except HTTPException:
        raise
    except Exception as e:
        error_response = await create_error_response(
            request,
            "DELETE_ERROR",
            f"Failed to delete personality configuration: {str(e)}",
            ["Contact support if the problem persists"]
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=jsonable_encoder(error_response.model_dump())
        )


# Configuration History and Versioning Endpoints

@router.get("/{personality_id}/history", response_model=List[ConfigurationHistoryResponse])
async def get_configuration_history(
    request: Request,
    personality_id: str,
    limit: int = Query(default=50, ge=1, le=100, description="Maximum number of history entries to return"),
    persistence_service: ConfigurationPersistenceService = Depends(get_persistence_service)
) -> List[ConfigurationHistoryResponse]:
    """
    Get configuration change history for a specific personality configuration.
    """
    try:
        # Check if configuration exists
        config = await persistence_service.get_configuration(personality_id)
        if not config:
            error_response = await create_error_response(
                request,
                "NOT_FOUND",
                f"Personality configuration with ID {personality_id} not found",
                ["Check the personality ID"]
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=jsonable_encoder(error_response.model_dump())
            )
        
        # Get history
        history = await persistence_service.get_configuration_history(personality_id, limit=limit)
        
        return [
            ConfigurationHistoryResponse(
                id=entry["id"],
                version=entry["version"],
                change_type=entry["change_type"],
                change_description=entry["change_description"],
                created_at=entry["created_at"],
                created_by=entry["created_by"]
            )
            for entry in history
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        error_response = await create_error_response(
            request,
            "HISTORY_ERROR",
            f"Failed to retrieve configuration history: {str(e)}",
            ["Contact support if the problem persists"]
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=jsonable_encoder(error_response.model_dump())
        )


@router.post("/{personality_id}/restore/{version}", response_model=PersonalityConfigResponse)
async def restore_configuration_version(
    request: Request,
    personality_id: str,
    version: int,
    persistence_service: ConfigurationPersistenceService = Depends(get_persistence_service)
) -> PersonalityConfigResponse:
    """
    Restore a personality configuration to a specific version.
    """
    try:
        # Restore to specified version
        success = await persistence_service.restore_configuration_version(
            personality_id,
            version,
            restored_by=f"api_{request.state.request_id}"
        )
        
        if not success:
            error_response = await create_error_response(
                request,
                "RESTORE_FAILED",
                f"Failed to restore configuration {personality_id} to version {version}",
                ["Check that the configuration and version exist", "Try a different version"]
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=jsonable_encoder(error_response.model_dump())
            )
        
        # Get the restored configuration
        restored_config = await persistence_service.get_configuration(personality_id)
        if not restored_config:
            error_response = await create_error_response(
                request,
                "RESTORE_ERROR",
                "Configuration was restored but could not be retrieved",
                ["Contact support"]
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=jsonable_encoder(error_response.model_dump())
            )
        
        return PersonalityConfigResponse(**restored_config.model_dump())
        
    except HTTPException:
        raise
    except Exception as e:
        error_response = await create_error_response(
            request,
            "RESTORE_ERROR",
            f"Failed to restore configuration version: {str(e)}",
            ["Contact support if the problem persists"]
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=jsonable_encoder(error_response.model_dump())
        )


# Backup and Restore Endpoints

@router.post("/backup", response_model=Dict[str, Any])
async def create_backup(
    request: Request,
    backup_request: BackupCreateRequest,
    user_id: Optional[str] = Query(None, description="User ID to filter configurations for backup"),
    persistence_service: ConfigurationPersistenceService = Depends(get_persistence_service)
) -> Dict[str, Any]:
    """
    Create a backup of personality configurations.
    """
    try:
        # Create backup
        checksum = await persistence_service.create_backup(
            backup_name=backup_request.backup_name,
            user_id=user_id,
            config_ids=backup_request.config_ids
        )
        
        return {
            "backup_name": backup_request.backup_name,
            "checksum": checksum,
            "created_at": datetime.now(),
            "message": "Backup created successfully"
        }
        
    except Exception as e:
        error_response = await create_error_response(
            request,
            "BACKUP_ERROR",
            f"Failed to create backup: {str(e)}",
            ["Try again with different parameters", "Contact support if the problem persists"]
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=jsonable_encoder(error_response.model_dump())
        )


@router.get("/backups", response_model=List[BackupResponse])
async def list_backups(
    request: Request,
    user_id: Optional[str] = Query(None, description="Filter backups by user ID"),
    limit: int = Query(default=50, ge=1, le=100, description="Maximum number of backups to return"),
    persistence_service: ConfigurationPersistenceService = Depends(get_persistence_service)
) -> List[BackupResponse]:
    """
    List available configuration backups.
    """
    try:
        backups = await persistence_service.list_backups(user_id=user_id, limit=limit)
        
        return [
            BackupResponse(
                id=backup["id"],
                backup_name=backup["backup_name"],
                user_id=backup["user_id"],
                created_at=backup["created_at"],
                file_size=backup["file_size"],
                checksum=backup["checksum"]
            )
            for backup in backups
        ]
        
    except Exception as e:
        error_response = await create_error_response(
            request,
            "LIST_BACKUPS_ERROR",
            f"Failed to list backups: {str(e)}",
            ["Contact support if the problem persists"]
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=jsonable_encoder(error_response.model_dump())
        )


@router.post("/backup/{backup_id}/restore", response_model=Dict[str, Any])
async def restore_backup(
    request: Request,
    backup_id: int,
    persistence_service: ConfigurationPersistenceService = Depends(get_persistence_service)
) -> Dict[str, Any]:
    """
    Restore configurations from a backup.
    """
    try:
        success, errors = await persistence_service.restore_backup(
            backup_id,
            restored_by=f"api_{request.state.request_id}"
        )
        
        if not success:
            error_response = await create_error_response(
                request,
                "RESTORE_BACKUP_FAILED",
                f"Failed to restore backup {backup_id}",
                ["Check that the backup exists and is valid"] + errors
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=jsonable_encoder(error_response.model_dump())
            )
        
        return {
            "backup_id": backup_id,
            "restored_at": datetime.now(),
            "success": success,
            "errors": errors,
            "message": "Backup restored successfully" if not errors else "Backup restored with some errors"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        error_response = await create_error_response(
            request,
            "RESTORE_BACKUP_ERROR",
            f"Failed to restore backup: {str(e)}",
            ["Contact support if the problem persists"]
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=jsonable_encoder(error_response.model_dump())
        )

# Advanced Input Processing Endpoints

@router.post("/analyze", response_model=InputAnalysisResponse)
async def analyze_personality_input_endpoint(
    request: Request,
    analysis_request: InputAnalysisRequest
) -> InputAnalysisResponse:
    """
    Analyze personality input to determine type and provide suggestions.
    """
    try:
        analysis = await analyze_personality_input(analysis_request.description)
        
        return InputAnalysisResponse(
            input_type=analysis.input_type.value,
            confidence=analysis.confidence,
            primary_personality=analysis.primary_personality,
            modifiers=analysis.modifiers,
            combination_type=analysis.combination_type.value if analysis.combination_type else None,
            secondary_personality=analysis.secondary_personality,
            suggestions=analysis.suggestions,
            clarification_questions=analysis.clarification_questions
        )
        
    except Exception as e:
        error_response = await create_error_response(
            request,
            "ANALYSIS_ERROR",
            f"Failed to analyze personality input: {str(e)}",
            ["Try again with different input", "Contact support if the problem persists"]
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=jsonable_encoder(error_response.model_dump())
        )


@router.post("/suggestions", response_model=List[PersonalitySuggestionResponse])
async def get_personality_suggestions_endpoint(
    request: Request,
    analysis_request: InputAnalysisRequest,
    max_suggestions: int = Query(default=5, ge=1, le=10, description="Maximum number of suggestions to return")
) -> List[PersonalitySuggestionResponse]:
    """
    Get personality suggestions for ambiguous or unclear input.
    """
    try:
        suggestions = await generate_personality_suggestions(
            analysis_request.description, 
            max_suggestions=max_suggestions
        )
        
        return [
            PersonalitySuggestionResponse(
                name=suggestion.name,
                confidence=suggestion.confidence,
                reason=suggestion.reason,
                personality_type=suggestion.personality_type.value
            )
            for suggestion in suggestions
        ]
        
    except Exception as e:
        error_response = await create_error_response(
            request,
            "SUGGESTIONS_ERROR",
            f"Failed to generate personality suggestions: {str(e)}",
            ["Try again with different input", "Contact support if the problem persists"]
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=jsonable_encoder(error_response.model_dump())
        )


@router.post("/clarify", response_model=List[ClarificationQuestionResponse])
async def get_clarification_questions_endpoint(
    request: Request,
    analysis_request: InputAnalysisRequest
) -> List[ClarificationQuestionResponse]:
    """
    Get clarification questions for unclear personality input.
    """
    try:
        # First analyze the input
        analysis = await analyze_personality_input(analysis_request.description)
        
        # Generate clarification questions
        questions = await generate_clarification_questions(analysis)
        
        return [
            ClarificationQuestionResponse(
                question=question.question,
                options=question.options,
                context=question.context
            )
            for question in questions
        ]
        
    except Exception as e:
        error_response = await create_error_response(
            request,
            "CLARIFICATION_ERROR",
            f"Failed to generate clarification questions: {str(e)}",
            ["Try again with different input", "Contact support if the problem persists"]
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=jsonable_encoder(error_response.model_dump())
        )


@router.post("/enhanced", response_model=PersonalityConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_personality_config_enhanced(
    request: Request,
    personality_request: PersonalityRequestCreate,
    persistence_service: ConfigurationPersistenceService = Depends(get_persistence_service)
) -> PersonalityConfigResponse:
    """
    Create a new personality configuration using enhanced orchestration with advanced input processing.
    """
    try:
        # Create PersonalityRequest for orchestration
        request_obj = PersonalityRequest(
            id=str(uuid.uuid4()),
            description=personality_request.description,
            user_id=personality_request.user_id,
            timestamp=datetime.now(),
            source=personality_request.source
        )
        
        # Determine project path
        project_path = None
        if personality_request.project_path:
            project_path = Path(personality_request.project_path)
        
        # Use enhanced orchestration system
        result = await orchestrate_personality_request_enhanced(
            request_obj,
            project_path=project_path,
            use_cache=True
        )
        
        if not result.success:
            error_response = await create_error_response(
                request,
                result.error.code if result.error else "ORCHESTRATION_ERROR",
                result.error.message if result.error else "Failed to create personality configuration",
                result.error.suggestions if result.error else []
            )
            
            # For ambiguous or unclear input, return 422 (Unprocessable Entity) instead of 400
            status_code = status.HTTP_422_UNPROCESSABLE_ENTITY if result.error and result.error.code in ["AMBIGUOUS_INPUT", "UNCLEAR_INPUT"] else status.HTTP_400_BAD_REQUEST
            
            raise HTTPException(
                status_code=status_code,
                detail=jsonable_encoder(error_response.model_dump())
            )
        
        # Store configuration in database
        config = result.config
        await persistence_service.create_configuration(
            config,
            user_id=personality_request.user_id,
            created_by=f"api_enhanced_{request.state.request_id}"
        )
        
        return PersonalityConfigResponse(**config.model_dump())
        
    except HTTPException:
        raise
    except Exception as e:
        error_response = await create_error_response(
            request,
            "PROCESSING_ERROR",
            f"Failed to create enhanced personality configuration: {str(e)}",
            ["Try again with different input", "Contact support if the problem persists"]
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=jsonable_encoder(error_response.model_dump())
        )