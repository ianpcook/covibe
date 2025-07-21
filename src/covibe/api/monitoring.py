"""API endpoints for system monitoring and health checks."""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional
from datetime import datetime

from ..utils.monitoring import get_system_health, get_error_metrics, get_health_checker
from ..utils.error_handling import ErrorCategory, create_error_response
from ..models.core import ErrorResponse

router = APIRouter(prefix="/api/monitoring", tags=["monitoring"])


@router.get("/health")
async def get_health_status() -> Dict[str, Any]:
    """
    Get overall system health status.
    
    Returns comprehensive health information including:
    - Overall system status (healthy/degraded/unhealthy)
    - Component-specific health status
    - Error rates and metrics
    - System uptime
    """
    try:
        health_status = get_system_health()
        return health_status
    except Exception as e:
        error_response = create_error_response(e)
        raise HTTPException(
            status_code=500,
            detail=error_response.dict()
        )


@router.get("/metrics")
async def get_metrics() -> Dict[str, Any]:
    """
    Get detailed error metrics and statistics.
    
    Returns:
    - Total error counts
    - Error rates by category and component
    - Recent error trends
    - Component-specific breakdowns
    """
    try:
        metrics = get_error_metrics()
        return metrics
    except Exception as e:
        error_response = create_error_response(e)
        raise HTTPException(
            status_code=500,
            detail=error_response.dict()
        )


@router.get("/health/{component}")
async def get_component_health(
    component: str,
    error_threshold: Optional[float] = 5.0
) -> Dict[str, Any]:
    """
    Get health status for a specific component.
    
    Args:
        component: Name of the component to check
        error_threshold: Error rate threshold for health determination (errors per minute)
    
    Returns:
        Component health information including status, error rate, and details
    """
    try:
        health_checker = get_health_checker()
        component_health = health_checker.check_component_health(
            component, 
            error_threshold=error_threshold
        )
        
        return {
            "component": component_health.name,
            "status": component_health.status.value,
            "error_rate": component_health.error_rate,
            "response_time": component_health.response_time,
            "uptime": component_health.uptime,
            "last_check": component_health.last_check.isoformat() if component_health.last_check else None,
            "details": component_health.details
        }
        
    except Exception as e:
        error_response = create_error_response(e)
        raise HTTPException(
            status_code=500,
            detail=error_response.dict()
        )


@router.get("/errors/categories")
async def get_error_categories() -> Dict[str, Any]:
    """
    Get error breakdown by category.
    
    Returns error counts and rates for each error category:
    - Input validation errors
    - Research errors  
    - Integration errors
    - Network errors
    - System errors
    """
    try:
        metrics = get_error_metrics()
        categories = metrics.get("categories", {})
        
        # Add category descriptions
        category_info = {
            "input_validation": "Errors related to invalid user input or data validation",
            "research": "Errors during personality research operations",
            "integration": "Errors during IDE integration and file operations", 
            "network": "Network connectivity and external API errors",
            "system": "Internal system and unexpected errors",
            "rate_limit": "Rate limiting errors from external services",
            "authentication": "Authentication and authorization errors",
            "timeout": "Operation timeout errors"
        }
        
        result = {}
        for category, data in categories.items():
            result[category] = {
                **data,
                "description": category_info.get(category, "Unknown category")
            }
        
        return {
            "categories": result,
            "total_categories": len(result),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        error_response = create_error_response(e)
        raise HTTPException(
            status_code=500,
            detail=error_response.dict()
        )


@router.get("/errors/components")
async def get_error_components() -> Dict[str, Any]:
    """
    Get error breakdown by system component.
    
    Returns error counts and rates for each system component:
    - Research service
    - Context generation
    - IDE integration
    - API layer
    - Orchestration
    """
    try:
        metrics = get_error_metrics()
        components = metrics.get("components", {})
        
        # Add component descriptions
        component_info = {
            "research": "Personality research and data gathering",
            "context_generation": "Personality context and prompt generation",
            "ide_integration": "IDE detection and file writing operations",
            "orchestration": "Request coordination and workflow management",
            "api": "REST API and request handling",
            "chat": "Chat interface and WebSocket communication"
        }
        
        result = {}
        for component, data in components.items():
            result[component] = {
                **data,
                "description": component_info.get(component, "Unknown component")
            }
        
        return {
            "components": result,
            "total_components": len(result),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        error_response = create_error_response(e)
        raise HTTPException(
            status_code=500,
            detail=error_response.dict()
        )


@router.post("/health/check")
async def trigger_health_check() -> Dict[str, Any]:
    """
    Trigger a comprehensive health check of all system components.
    
    This endpoint forces a fresh health check of all components and returns
    the updated health status.
    """
    try:
        health_checker = get_health_checker()
        
        # Check health of all known components
        components = ["research", "context_generation", "ide_integration", "orchestration", "api", "chat"]
        
        component_results = {}
        for component in components:
            health = health_checker.check_component_health(component)
            component_results[component] = {
                "status": health.status.value,
                "error_rate": health.error_rate,
                "last_check": health.last_check.isoformat() if health.last_check else None
            }
        
        # Get overall system health
        system_health = get_system_health()
        
        return {
            "system_status": system_health["status"],
            "check_timestamp": datetime.now().isoformat(),
            "components": component_results,
            "summary": {
                "total_components": len(component_results),
                "healthy_components": sum(1 for c in component_results.values() if c["status"] == "healthy"),
                "degraded_components": sum(1 for c in component_results.values() if c["status"] == "degraded"),
                "unhealthy_components": sum(1 for c in component_results.values() if c["status"] == "unhealthy")
            }
        }
        
    except Exception as e:
        error_response = create_error_response(e)
        raise HTTPException(
            status_code=500,
            detail=error_response.dict()
        )