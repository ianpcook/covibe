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
    SourceType
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


class PersonalityResponse(PersonalityConfig):
    """Response model for personality configurations."""
    pass


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


@router.post("/", response_model=PersonalityResponse, status_code=status.HTTP_201_CREATED)
async def create_personality_config(
    request: Request,
    personality_request: PersonalityRequestCreate
) -> PersonalityResponse:
    """
    Create a new personality configuration.
    
    This endpoint accepts a personality description and creates a complete
    personality configuration including research, context generation, and
    IDE integration setup.
    """
    try:
        # TODO: Implement personality research and context generation
        # For now, return a placeholder response
        
        # Create a basic personality profile (placeholder)
        from ..models.core import (
            PersonalityProfile,
            PersonalityType,
            CommunicationStyle,
            FormalityLevel,
            VerbosityLevel,
            TechnicalLevel
        )
        
        profile = PersonalityProfile(
            id=str(uuid.uuid4()),
            name="Placeholder Profile",
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
            context="Placeholder context - will be generated based on personality research",
            ide_type="unknown",
            file_path="",
            active=True,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        return PersonalityResponse(**config.dict())
        
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


@router.get("/{personality_id}", response_model=PersonalityResponse)
async def get_personality_config(
    request: Request,
    personality_id: str
) -> PersonalityResponse:
    """
    Retrieve a personality configuration by ID.
    """
    try:
        # TODO: Implement personality configuration retrieval from storage
        # For now, return a not found error
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
        
    except HTTPException:
        raise
    except Exception as e:
        error_response = await create_error_response(
            request,
            "RETRIEVAL_ERROR",
            "Failed to retrieve personality configuration",
            ["Try again later", "Contact support if the problem persists"]
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response.dict()
        )


@router.put("/{personality_id}", response_model=PersonalityResponse)
async def update_personality_config(
    request: Request,
    personality_id: str,
    personality_request: PersonalityRequestCreate
) -> PersonalityResponse:
    """
    Update an existing personality configuration.
    """
    try:
        # TODO: Implement personality configuration update
        error_response = await create_error_response(
            request,
            "NOT_IMPLEMENTED",
            "Personality configuration update not yet implemented",
            ["Use the create endpoint for now"]
        )
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=error_response.dict()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        error_response = await create_error_response(
            request,
            "UPDATE_ERROR",
            "Failed to update personality configuration",
            ["Try again later", "Contact support if the problem persists"]
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response.dict()
        )


@router.delete("/{personality_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_personality_config(
    request: Request,
    personality_id: str
):
    """
    Delete a personality configuration.
    """
    try:
        # TODO: Implement personality configuration deletion
        error_response = await create_error_response(
            request,
            "NOT_IMPLEMENTED",
            "Personality configuration deletion not yet implemented",
            ["Feature coming soon"]
        )
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=error_response.dict()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        error_response = await create_error_response(
            request,
            "DELETION_ERROR",
            "Failed to delete personality configuration",
            ["Try again later", "Contact support if the problem persists"]
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_response.dict()
        )


@router.post("/research", status_code=status.HTTP_200_OK)
async def research_personality(
    request: Request,
    personality_request: PersonalityRequestCreate
):
    """
    Research a personality without creating a full configuration.
    
    This endpoint is useful for testing personality descriptions
    and getting research results before committing to a full configuration.
    """
    try:
        # TODO: Implement personality research functionality
        error_response = await create_error_response(
            request,
            "NOT_IMPLEMENTED",
            "Personality research not yet implemented",
            ["Use the main personality endpoint for now"]
        )
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=error_response.dict()
        )
        
    except HTTPException:
        raise
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