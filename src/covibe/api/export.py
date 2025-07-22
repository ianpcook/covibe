"""Export API endpoints for IDE-specific configuration files."""

from fastapi import APIRouter, HTTPException, Request, status, Query, Depends, UploadFile, File
from fastapi.encoders import jsonable_encoder
from fastapi.responses import Response
from typing import Optional
from datetime import datetime
import zipfile
import io

from ..models.core import (
    ExportFormatOptions,
    BulkExportRequest,
    ErrorResponse,
    ErrorDetail
)
from ..services.export_generator import (
    generate_export_file,
    generate_preview_content,
    generate_bulk_export,
    get_supported_ide_types
)
from ..services.format_converter import (
    detect_ide_format,
    parse_imported_config
)
from ..services.persistence import ConfigurationPersistenceService
from ..utils.database import get_database_config


router = APIRouter(prefix="/api/personality", tags=["export"])


# Dependency to get persistence service
async def get_persistence_service() -> ConfigurationPersistenceService:
    """Get persistence service instance."""
    db_config = await get_database_config()
    return ConfigurationPersistenceService(db_config)


async def create_error_response(
    request: Request,
    code: str,
    message: str,
    suggestions: Optional[list] = None
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


@router.get("/{personality_id}/export/{ide_type}")
async def export_personality_config(
    request: Request,
    personality_id: str,
    ide_type: str,
    file_name: Optional[str] = Query(None, description="Custom file name for export"),
    include_metadata: bool = Query(True, description="Include export metadata"),
    include_instructions: bool = Query(True, description="Include placement instructions"),
    custom_header: Optional[str] = Query(None, description="Custom header text"),
    persistence_service: ConfigurationPersistenceService = Depends(get_persistence_service)
):
    """
    Export personality configuration as IDE-specific file for download.
    """
    try:
        # Get personality configuration
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
        
        # Check if IDE type is supported
        if ide_type.lower() not in get_supported_ide_types():
            error_response = await create_error_response(
                request,
                "UNSUPPORTED_IDE",
                f"IDE type '{ide_type}' is not supported",
                [f"Supported IDE types: {', '.join(get_supported_ide_types())}"]
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=jsonable_encoder(error_response.model_dump())
            )
        
        # Create export format options
        format_options = ExportFormatOptions(
            file_name=file_name,
            include_metadata=include_metadata,
            include_instructions=include_instructions,
            custom_header=custom_header
        )
        
        # Generate export file
        export_result = await generate_export_file(config, ide_type, format_options)
        
        if not export_result.success:
            error_response = await create_error_response(
                request,
                "EXPORT_FAILED",
                export_result.error or "Failed to generate export file",
                ["Try again with different parameters", "Contact support if the problem persists"]
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=jsonable_encoder(error_response.model_dump())
            )
        
        # Return file as download
        return Response(
            content=export_result.content,
            media_type=export_result.mime_type,
            headers={
                "Content-Disposition": f"attachment; filename={export_result.file_name}",
                "Content-Length": str(export_result.file_size)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        error_response = await create_error_response(
            request,
            "EXPORT_ERROR",
            f"Failed to export personality configuration: {str(e)}",
            ["Try again", "Contact support if the problem persists"]
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=jsonable_encoder(error_response.model_dump())
        )


@router.get("/{personality_id}/export/{ide_type}/preview")
async def preview_personality_export(
    request: Request,
    personality_id: str,
    ide_type: str,
    file_name: Optional[str] = Query(None, description="Custom file name for export"),
    include_metadata: bool = Query(True, description="Include export metadata"),
    include_instructions: bool = Query(True, description="Include placement instructions"),
    custom_header: Optional[str] = Query(None, description="Custom header text"),
    persistence_service: ConfigurationPersistenceService = Depends(get_persistence_service)
):
    """
    Preview personality configuration export without downloading.
    """
    try:
        # Get personality configuration
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
        
        # Check if IDE type is supported
        if ide_type.lower() not in get_supported_ide_types():
            error_response = await create_error_response(
                request,
                "UNSUPPORTED_IDE",
                f"IDE type '{ide_type}' is not supported",
                [f"Supported IDE types: {', '.join(get_supported_ide_types())}"]
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=jsonable_encoder(error_response.model_dump())
            )
        
        # Create export format options
        format_options = ExportFormatOptions(
            file_name=file_name,
            include_metadata=include_metadata,
            include_instructions=include_instructions,
            custom_header=custom_header
        )
        
        # Generate preview content
        preview_result = await generate_preview_content(config, ide_type, format_options)
        
        return {
            "content": preview_result.content,
            "file_name": preview_result.file_name,
            "file_size": preview_result.file_size,
            "syntax_language": preview_result.syntax_language,
            "placement_instructions": preview_result.placement_instructions,
            "metadata": preview_result.metadata
        }
        
    except HTTPException:
        raise
    except Exception as e:
        error_response = await create_error_response(
            request,
            "PREVIEW_ERROR",
            f"Failed to generate export preview: {str(e)}",
            ["Try again", "Contact support if the problem persists"]
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=jsonable_encoder(error_response.model_dump())
        )


@router.get("/export/supported-ides")
async def get_supported_ide_types_endpoint(request: Request):
    """
    Get list of supported IDE types for export.
    """
    try:
        return {
            "supported_ides": [
                {
                    "type": "cursor",
                    "name": "Cursor IDE", 
                    "description": "AI-powered code editor with personality rules",
                    "file_extension": "mdc",
                    "placement_path": ".cursor/rules/"
                },
                {
                    "type": "claude",
                    "name": "Claude",
                    "description": "Claude AI assistant with project context",
                    "file_extension": "md",
                    "placement_path": "project root"
                },
                {
                    "type": "windsurf",
                    "name": "Windsurf IDE",
                    "description": "Next-generation IDE with AI integration",
                    "file_extension": "windsurf",
                    "placement_path": "project root"
                },
                {
                    "type": "generic",
                    "name": "Generic",
                    "description": "Generic markdown format for any IDE",
                    "file_extension": "md",
                    "placement_path": "configurable"
                }
            ],
            "total_supported": len(get_supported_ide_types())
        }
    except Exception as e:
        error_response = await create_error_response(
            request,
            "SUPPORTED_IDES_ERROR",
            f"Failed to get supported IDE types: {str(e)}",
            ["Contact support if the problem persists"]
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=jsonable_encoder(error_response.model_dump())
        )


@router.post("/export/bulk")
async def bulk_export_personalities(
    request: Request,
    bulk_request: BulkExportRequest,
    persistence_service: ConfigurationPersistenceService = Depends(get_persistence_service)
):
    """
    Export multiple personality configurations as a ZIP archive.
    """
    try:
        # Validate that at least one personality is requested
        if not bulk_request.personality_ids:
            error_response = await create_error_response(
                request,
                "INVALID_REQUEST",
                "At least one personality ID must be provided",
                ["Provide one or more personality IDs to export"]
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=jsonable_encoder(error_response.model_dump())
            )
        
        # Validate that at least one IDE type is requested
        if not bulk_request.ide_types:
            error_response = await create_error_response(
                request,
                "INVALID_REQUEST", 
                "At least one IDE type must be provided",
                [f"Supported IDE types: {', '.join(get_supported_ide_types())}"]
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=jsonable_encoder(error_response.model_dump())
            )
        
        # Validate IDE types are supported
        supported_ides = get_supported_ide_types()
        invalid_ides = [ide for ide in bulk_request.ide_types if ide.lower() not in supported_ides]
        if invalid_ides:
            error_response = await create_error_response(
                request,
                "UNSUPPORTED_IDE",
                f"Unsupported IDE types: {', '.join(invalid_ides)}",
                [f"Supported IDE types: {', '.join(supported_ides)}"]
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=jsonable_encoder(error_response.model_dump())
            )
        
        # Get all requested personality configurations
        configs = []
        missing_configs = []
        
        for personality_id in bulk_request.personality_ids:
            config = await persistence_service.get_configuration(personality_id)
            if config:
                configs.append(config)
            else:
                missing_configs.append(personality_id)
        
        # Check if any configs were not found
        if missing_configs:
            error_response = await create_error_response(
                request,
                "NOT_FOUND",
                f"Personality configurations not found: {', '.join(missing_configs)}",
                ["Check the personality IDs", "Remove invalid IDs from the request"]
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=jsonable_encoder(error_response.model_dump())
            )
        
        # Generate bulk export
        bulk_result = await generate_bulk_export(
            configs,
            bulk_request.ide_types,
            bulk_request.format_options,
            bulk_request.include_readme
        )
        
        if not bulk_result.success:
            error_response = await create_error_response(
                request,
                "BULK_EXPORT_FAILED",
                bulk_result.error or "Failed to generate bulk export",
                ["Try again with fewer configurations", "Contact support if the problem persists"]
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=jsonable_encoder(error_response.model_dump())
            )
        
        # Return ZIP file as download
        return Response(
            content=bulk_result.zip_content,
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename={bulk_result.file_name}",
                "Content-Length": str(bulk_result.file_size)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        error_response = await create_error_response(
            request,
            "BULK_EXPORT_ERROR",
            f"Failed to perform bulk export: {str(e)}",
            ["Try again", "Contact support if the problem persists"]
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=jsonable_encoder(error_response.model_dump())
        )


@router.post("/import")
async def import_personality_config(
    request: Request,
    file: UploadFile = File(...),
    user_id: Optional[str] = None,
    persistence_service: ConfigurationPersistenceService = Depends(get_persistence_service)
):
    """
    Import personality configuration from uploaded file.
    """
    try:
        # Validate file size (max 5MB)
        if hasattr(file, 'size') and file.size and file.size > 5 * 1024 * 1024:
            error_response = await create_error_response(
                request,
                "FILE_TOO_LARGE",
                "File size must be less than 5MB",
                ["Upload a smaller file", "Compress the file before uploading"]
            )
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=jsonable_encoder(error_response.model_dump())
            )
        
        # Read file content
        try:
            content = await file.read()
            file_content = content.decode('utf-8')
        except UnicodeDecodeError:
            error_response = await create_error_response(
                request,
                "INVALID_FILE_ENCODING",
                "File must be UTF-8 encoded text",
                ["Ensure the file is a valid text file", "Check the file encoding"]
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=jsonable_encoder(error_response.model_dump())
            )
        
        # Detect IDE format
        format_detection = await detect_ide_format(file_content, file.filename or "unknown")
        
        if format_detection.confidence < 0.5:
            error_response = await create_error_response(
                request,
                "UNRECOGNIZED_FORMAT",
                f"Could not reliably detect file format (confidence: {format_detection.confidence:.2f})",
                [
                    "Ensure the file is a valid personality configuration",
                    f"Supported formats: {', '.join(get_supported_ide_types())}",
                    "Check the file content and structure"
                ]
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=jsonable_encoder(error_response.model_dump())
            )
        
        # Parse the configuration
        try:
            parsed_config = await parse_imported_config(file_content, format_detection.detected_format)
        except Exception as e:
            error_response = await create_error_response(
                request,
                "PARSING_FAILED",
                f"Failed to parse configuration file: {str(e)}",
                [
                    "Check the file format and structure",
                    "Ensure all required fields are present",
                    "Validate the file content"
                ]
            )
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=jsonable_encoder(error_response.model_dump())
            )
        
        # Store the configuration
        try:
            stored_config = await persistence_service.store_configuration(parsed_config)
            
            return {
                "id": stored_config.id,
                "profile": stored_config.profile,
                "context": stored_config.context,
                "ide_type": stored_config.ide_type,
                "file_path": stored_config.file_path,
                "active": stored_config.active,
                "created_at": stored_config.created_at,
                "updated_at": stored_config.updated_at,
                "import_metadata": {
                    "source_format": format_detection.detected_format,
                    "detection_confidence": format_detection.confidence,
                    "original_filename": file.filename
                }
            }
            
        except Exception as e:
            error_response = await create_error_response(
                request,
                "STORAGE_FAILED",
                f"Failed to store imported configuration: {str(e)}",
                ["Try importing again", "Contact support if the problem persists"]
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=jsonable_encoder(error_response.model_dump())
            )
        
    except HTTPException:
        raise
    except Exception as e:
        error_response = await create_error_response(
            request,
            "IMPORT_ERROR",
            f"Failed to import configuration: {str(e)}",
            ["Try again", "Contact support if the problem persists"]
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=jsonable_encoder(error_response.model_dump())
        )


@router.post("/import/validate")
async def validate_import_file(
    request: Request,
    file: UploadFile = File(...)
):
    """
    Validate import file format and content without importing.
    """
    try:
        # Validate file size
        if hasattr(file, 'size') and file.size and file.size > 5 * 1024 * 1024:
            return {
                "valid": False,
                "detected_format": "unknown",
                "ide_type": "unknown",
                "confidence": 0.0,
                "errors": ["File size must be less than 5MB"],
                "warnings": []
            }
        
        # Read file content
        try:
            content = await file.read()
            file_content = content.decode('utf-8')
        except UnicodeDecodeError:
            return {
                "valid": False,
                "detected_format": "unknown",
                "ide_type": "unknown", 
                "confidence": 0.0,
                "errors": ["File must be UTF-8 encoded text"],
                "warnings": []
            }
        
        # Detect format
        format_detection = await detect_ide_format(file_content, file.filename or "unknown")
        
        errors = []
        warnings = []
        
        # Check confidence
        if format_detection.confidence < 0.5:
            errors.append(f"Low format detection confidence ({format_detection.confidence:.2f})")
        elif format_detection.confidence < 0.8:
            warnings.append(f"Moderate format detection confidence ({format_detection.confidence:.2f})")
        
        # Try to parse (validation only)
        valid = True
        try:
            await parse_imported_config(file_content, format_detection.detected_format)
        except Exception as e:
            valid = False
            errors.append(f"Parsing failed: {str(e)}")
        
        return {
            "valid": valid and format_detection.confidence >= 0.5,
            "detected_format": format_detection.detected_format,
            "ide_type": format_detection.suggested_ide_type,
            "confidence": format_detection.confidence,
            "errors": errors,
            "warnings": warnings
        }
        
    except Exception as e:
        return {
            "valid": False,
            "detected_format": "unknown",
            "ide_type": "unknown",
            "confidence": 0.0,
            "errors": [f"Validation failed: {str(e)}"],
            "warnings": []
        }