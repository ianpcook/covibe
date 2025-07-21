"""Personality API routes and handlers."""

from fastapi import APIRouter, HTTPException, Request, status, Query
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
    orchestrate_research_only,
    get_cache_stats,
    clear_cache
)
from ..integrations.ide_detection import detect_ides, get_primary_ide


router = APIRouter(prefix="/api/personality", tags=["personality"])

# In-memory storage for configurations (will be replaced with database in Task 13)
_personality_configs: Dict[str, PersonalityConfig] = {}


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
    personality_request: PersonalityRequestCreate
) -> PersonalityConfigResponse:
    """
    Create a new personality configuration using the orchestration system.
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
        
        # Use orchestration system
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
        
        # Store configuration in memory
        config = result.config
        _personality_configs[config.id] = config
        
        return PersonalityConfigResponse(**config.dict())
        
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
    limit: int = Query(default=10, ge=1, le=100, description="Maximum number of configurations to return"),
    offset: int = Query(default=0, ge=0, description="Number of configurations to skip")
) -> Dict[str, Any]:
    """
    List all personality configurations with pagination.
    """
    try:
        # Get all configurations
        all_configs = list(_personality_configs.values())
        total = len(all_configs)
        
        # Apply pagination
        paginated_configs = all_configs[offset:offset + limit]
        
        return {
            "configurations": [
                jsonable_encoder(PersonalityConfigResponse(**config.dict()).dict())
                for config in paginated_configs
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


@router.get("/{personality_id}", response_model=PersonalityConfigResponse)
async def get_personality_config(
    request: Request,
    personality_id: str
) -> PersonalityConfigResponse:
    """
    Retrieve a personality configuration by ID.
    """
    if personality_id not in _personality_configs:
        error_response = await create_error_response(
            request,
            "NOT_FOUND",
            f"Personality configuration with ID {personality_id} not found",
            ["Check the personality ID", "Create a new personality configuration"]
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=jsonable_encoder(error_response.dict())
        )
    
    config = _personality_configs[personality_id]
    return PersonalityConfigResponse(**config.dict())


@router.put("/{personality_id}", response_model=PersonalityConfigResponse)
async def update_personality_config(
    request: Request,
    personality_id: str,
    update_request: PersonalityUpdateRequest
) -> PersonalityConfigResponse:
    """
    Update an existing personality configuration.
    """
    if personality_id not in _personality_configs:
        error_response = await create_error_response(
            request,
            "NOT_FOUND",
            f"Personality configuration with ID {personality_id} not found",
            ["Check the personality ID", "Create a new personality configuration"]
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=jsonable_encoder(error_response.dict())
        )
    
    try:
        existing_config = _personality_configs[personality_id]
        
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
                    detail=jsonable_encoder(error_response.dict())
                )
            
            # Update the configuration
            updated_config = result.config
            updated_config.id = personality_id  # Keep the same ID
            updated_config.created_at = existing_config.created_at  # Keep original creation time
            updated_config.updated_at = datetime.now()
            
        else:
            # Just update project path if provided
            updated_config = existing_config.copy()
            if update_request.project_path:
                project_path = Path(update_request.project_path)
                detected_ides = detect_ides(str(project_path))
                primary_ide = get_primary_ide(detected_ides)
                
                updated_config.ide_type = primary_ide.type if primary_ide else "unknown"
                updated_config.file_path = primary_ide.config_path if primary_ide else ""
                updated_config.active = bool(primary_ide)
            
            updated_config.updated_at = datetime.now()
        
        # Store updated configuration
        _personality_configs[personality_id] = updated_config
        
        return PersonalityConfigResponse(**updated_config.dict())
        
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
            detail=jsonable_encoder(error_response.dict())
        )


@router.delete("/{personality_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_personality_config(
    request: Request,
    personality_id: str
):
    """
    Delete a personality configuration.
    """
    if personality_id not in _personality_configs:
        error_response = await create_error_response(
            request,
            "NOT_FOUND",
            f"Personality configuration with ID {personality_id} not found",
            ["Check the personality ID"]
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=jsonable_encoder(error_response.dict())
        )
    
    # Remove from storage
    del _personality_configs[personality_id]
    
    # Return 204 No Content (no response body)


@router.post("/research", response_model=ResearchResponse, status_code=status.HTTP_200_OK)
async def research_personality_endpoint(
    request: Request,
    research_request: ResearchOnlyRequest
) -> ResearchResponse:
    """
    Research a personality without creating a full configuration.
    """
    try:
        # Use orchestration system for research-only
        result = await orchestrate_research_only(
            research_request.description,
            use_cache=research_request.use_cache
        )
        
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
                    "confidence": p.sources[0].confidence if p.sources else 0.0
                }
                for p in result.profiles
            ],
            confidence=result.confidence,
            suggestions=result.suggestions,
            errors=result.errors
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


# Additional API endpoints for IDE detection and cache management
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