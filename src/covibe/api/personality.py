"""Personality API routes and handlers."""

from fastapi import APIRouter, HTTPException, Request, status
from typing import List, Optional
from datetime import datetime
import uuid
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


router = APIRouter(prefix="/api/personality", tags=["personality"])


# Request/Response models for API
class PersonalityRequestCreate(PersonalityRequest):
    """Request model for creating personality configurations."""
    id: Optional[str] = None
    timestamp: Optional[datetime] = None
    
    def __init__(self, **data):
        if 'id' not in data or data['id'] is None:
            data['id'] = str(uuid.uuid4())
        if 'timestamp' not in data or data['timestamp'] is None:
            data['timestamp'] = datetime.now()
        super().__init__(**data)


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


@router.post("/", response_model=PersonalityConfig, status_code=status.HTTP_201_CREATED)
async def create_personality_config(
    request: Request,
    personality_request: PersonalityRequestCreate
) -> PersonalityConfig:
    """
    Create a new personality configuration.
    """
    try:
        # Import research function
        from ..services.research import research_personality
        
        # Research the personality
        research_result = await research_personality(personality_request.description)
        
        # Use the first profile if available, otherwise create a basic one
        if research_result.profiles:
            profile = research_result.profiles[0]
        else:
            # Create a basic personality profile as fallback
            profile = PersonalityProfile(
                id=str(uuid.uuid4()),
                name="Custom Profile",
                type=PersonalityType.CUSTOM,
                traits=[],
                communication_style=CommunicationStyle(
                    tone="friendly",
                    formality=FormalityLevel.CASUAL,
                    verbosity=VerbosityLevel.MODERATE,
                    technical_level=TechnicalLevel.INTERMEDIATE
                ),
                mannerisms=[],
                sources=[]
            )
        
        # Create personality configuration
        config = PersonalityConfig(
            id=str(uuid.uuid4()),
            profile=profile,
            context=f"Generated context for {profile.name} personality - will be enhanced in future tasks",
            ide_type="unknown",
            file_path="",
            active=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        return config
        
    except ValueError as e:
        error_response = await create_error_response(
            request,
            "VALIDATION_ERROR",
            str(e),
            ["Check your input data", "Ensure all required fields are provided"]
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_response.dict()
        )
    except Exception as e:
        error_response = await create_error_response(
            request,
            "PROCESSING_ERROR",
            "Failed to create personality configuration",
            ["Try again with different input", "Contact support if the problem persists"]
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response.dict()
        )


@router.get("/{personality_id}", response_model=PersonalityConfig)
async def get_personality_config(
    request: Request,
    personality_id: str
) -> PersonalityConfig:
    """
    Retrieve a personality configuration by ID.
    """
    error_response = await create_error_response(
        request,
        "NOT_FOUND",
        f"Personality configuration with ID {personality_id} not found",
        ["Check the personality ID", "Create a new personality configuration"]
    )
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=error_response.dict()
    )


@router.post("/research", status_code=status.HTTP_200_OK)
async def research_personality_endpoint(
    request: Request,
    personality_request: PersonalityRequestCreate
):
    """
    Research a personality without creating a full configuration.
    """
    try:
        from ..services.research import research_personality
        
        # Research the personality
        result = await research_personality(personality_request.description)
        
        return {
            "query": result.query,
            "profiles_found": len(result.profiles),
            "profiles": [
                {
                    "name": p.name,
                    "type": p.type,
                    "traits": [t.trait for t in p.traits],
                    "confidence": p.sources[0].confidence if p.sources else 0.0
                }
                for p in result.profiles
            ],
            "confidence": result.confidence,
            "suggestions": result.suggestions,
            "errors": result.errors
        }
        
    except Exception as e:
        error_response = await create_error_response(
            request,
            "RESEARCH_ERROR",
            "Failed to research personality",
            ["Try again with different input", "Contact support if the problem persists"]
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response.dict()
        )
