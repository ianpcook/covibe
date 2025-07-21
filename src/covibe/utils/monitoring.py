"""
Monitoring and metrics utilities for error tracking and system health.

This module provides error metrics collection, health checks, and monitoring
utilities for the Agent Personality System.
"""

import asyncio
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from threading import Lock
from enum import Enum

from .error_handling import PersonalitySystemError, ErrorCategory, ErrorSeverity


class HealthStatus(str, Enum):
    """Health status levels."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


@dataclass
class ErrorMetric:
    """Metrics for a specific error type."""
    count: int = 0
    last_occurrence: Optional[datetime] = None
    recent_occurrences: deque = field(default_factory=lambda: deque(maxlen=100))
    
    def record_error(self):
        """Record a new error occurrence."""
        now = datetime.now()
        self.count += 1
        self.last_occurrence = now
        self.recent_occurrences.append(now)


@dataclass
class ComponentHealth:
    """Health status for a system component."""
    name: str
    status: HealthStatus = HealthStatus.HEALTHY
    last_check: Optional[datetime] = None
    error_rate: float = 0.0
    response_time: float = 0.0
    uptime: float = 100.0
    details: Dict[str, Any] = field(default_factory=dict)


class ErrorMonitor:
    """Monitor and track errors across the system."""
    
    def __init__(self, window_minutes: int = 60):
        self.window_minutes = window_minutes
        self.error_metrics: Dict[str, ErrorMetric] = defaultdict(ErrorMetric)
        self.component_metrics: Dict[str, Dict[str, ErrorMetric]] = defaultdict(lambda: defaultdict(ErrorMetric))
        self.lock = Lock()
        self.start_time = datetime.now()
    
    def record_error(
        self,
        error: PersonalitySystemError,
        component: Optional[str] = None
    ):
        """Record an error occurrence."""
        with self.lock:
            # Record global error metrics
            error_key = f"{error.category.value}:{error.code}"
            self.error_metrics[error_key].record_error()
            
            # Record component-specific metrics
            if component:
                self.component_metrics[component][error_key].record_error()
    
    def get_error_rate(
        self,
        category: Optional[ErrorCategory] = None,
        component: Optional[str] = None,
        window_minutes: Optional[int] = None
    ) -> float:
        """Get error rate for a category/component within a time window."""
        window = window_minutes or self.window_minutes
        cutoff_time = datetime.now() - timedelta(minutes=window)
        
        with self.lock:
            if component and category:
                # Component-specific category error rate
                error_key = f"{category.value}:"
                relevant_metrics = [
                    metric for key, metric in self.component_metrics[component].items()
                    if key.startswith(error_key)
                ]
            elif component:
                # All errors for a component
                relevant_metrics = list(self.component_metrics[component].values())
            elif category:
                # Category errors across all components
                error_key = f"{category.value}:"
                relevant_metrics = [
                    metric for key, metric in self.error_metrics.items()
                    if key.startswith(error_key)
                ]
            else:
                # All errors
                relevant_metrics = list(self.error_metrics.values())
            
            total_errors = 0
            for metric in relevant_metrics:
                recent_errors = [
                    occurrence for occurrence in metric.recent_occurrences
                    if occurrence >= cutoff_time
                ]
                total_errors += len(recent_errors)
            
            # Calculate rate per minute
            return total_errors / window if window > 0 else 0.0
    
    def get_error_summary(self) -> Dict[str, Any]:
        """Get a summary of all error metrics."""
        with self.lock:
            # Calculate error rate without calling get_error_rate (to avoid deadlock)
            cutoff_time = datetime.now() - timedelta(minutes=self.window_minutes)
            total_recent_errors = 0
            for metric in self.error_metrics.values():
                recent_errors = [
                    occurrence for occurrence in metric.recent_occurrences
                    if occurrence >= cutoff_time
                ]
                total_recent_errors += len(recent_errors)
            
            error_rate_per_minute = total_recent_errors / self.window_minutes if self.window_minutes > 0 else 0.0
            
            summary = {
                "total_errors": sum(metric.count for metric in self.error_metrics.values()),
                "error_rate_per_minute": error_rate_per_minute,
                "uptime_minutes": (datetime.now() - self.start_time).total_seconds() / 60,
                "categories": {},
                "components": {}
            }
            
            # Summarize by category
            for error_key, metric in self.error_metrics.items():
                category = error_key.split(':')[0]
                if category not in summary["categories"]:
                    summary["categories"][category] = {
                        "count": 0,
                        "last_occurrence": None,
                        "recent_rate": 0.0
                    }
                
                summary["categories"][category]["count"] += metric.count
                if metric.last_occurrence:
                    if (not summary["categories"][category]["last_occurrence"] or
                        metric.last_occurrence > summary["categories"][category]["last_occurrence"]):
                        summary["categories"][category]["last_occurrence"] = metric.last_occurrence
            
            # Calculate recent rates for categories (without acquiring lock again)
            cutoff_time = datetime.now() - timedelta(minutes=self.window_minutes)
            for category in summary["categories"]:
                try:
                    cat_enum = ErrorCategory(category)
                    error_key = f"{cat_enum.value}:"
                    relevant_metrics = [
                        metric for key, metric in self.error_metrics.items()
                        if key.startswith(error_key)
                    ]
                    
                    total_errors = 0
                    for metric in relevant_metrics:
                        recent_errors = [
                            occurrence for occurrence in metric.recent_occurrences
                            if occurrence >= cutoff_time
                        ]
                        total_errors += len(recent_errors)
                    
                    summary["categories"][category]["recent_rate"] = total_errors / self.window_minutes if self.window_minutes > 0 else 0.0
                except ValueError:
                    pass
            
            # Summarize by component (calculate error rate without calling get_error_rate)
            for component, component_metrics in self.component_metrics.items():
                # Calculate component error rate without acquiring lock again
                component_total_errors = 0
                for metric in component_metrics.values():
                    recent_errors = [
                        occurrence for occurrence in metric.recent_occurrences
                        if occurrence >= cutoff_time
                    ]
                    component_total_errors += len(recent_errors)
                
                component_error_rate = component_total_errors / self.window_minutes if self.window_minutes > 0 else 0.0
                
                summary["components"][component] = {
                    "count": sum(metric.count for metric in component_metrics.values()),
                    "error_rate": component_error_rate,
                    "categories": {}
                }
                
                for error_key, metric in component_metrics.items():
                    category = error_key.split(':')[0]
                    if category not in summary["components"][component]["categories"]:
                        summary["components"][component]["categories"][category] = 0
                    summary["components"][component]["categories"][category] += metric.count
            
            return summary


class HealthChecker:
    """Check and monitor system component health."""
    
    def __init__(self, error_monitor: ErrorMonitor):
        self.error_monitor = error_monitor
        self.component_health: Dict[str, ComponentHealth] = {}
        self.lock = Lock()
    
    def check_component_health(
        self,
        component: str,
        error_threshold: float = 5.0,  # errors per minute
        response_time: Optional[float] = None
    ) -> ComponentHealth:
        """Check the health of a specific component."""
        
        error_rate = self.error_monitor.get_error_rate(component=component)
        
        # Determine health status based on error rate
        if error_rate > error_threshold:
            status = HealthStatus.UNHEALTHY
        elif error_rate > error_threshold * 0.5:
            status = HealthStatus.DEGRADED
        else:
            status = HealthStatus.HEALTHY
        
        health = ComponentHealth(
            name=component,
            status=status,
            last_check=datetime.now(),
            error_rate=error_rate,
            response_time=response_time or 0.0
        )
        
        # Add detailed error breakdown
        component_summary = self.error_monitor.get_error_summary()
        if component in component_summary["components"]:
            health.details = component_summary["components"][component]
        
        with self.lock:
            self.component_health[component] = health
        
        return health
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get overall system health status."""
        
        # Check health of all known components
        components = set(self.error_monitor.component_metrics.keys())
        components.update(["research", "context_generation", "ide_integration", "api"])
        
        component_statuses = {}
        overall_status = HealthStatus.HEALTHY
        
        for component in components:
            health = self.check_component_health(component)
            component_statuses[component] = {
                "status": health.status.value,
                "error_rate": health.error_rate,
                "response_time": health.response_time,
                "last_check": health.last_check.isoformat() if health.last_check else None
            }
            
            # Determine overall status (worst component status)
            if health.status == HealthStatus.UNHEALTHY:
                overall_status = HealthStatus.UNHEALTHY
            elif health.status == HealthStatus.DEGRADED and overall_status == HealthStatus.HEALTHY:
                overall_status = HealthStatus.DEGRADED
        
        error_summary = self.error_monitor.get_error_summary()
        
        return {
            "status": overall_status.value,
            "timestamp": datetime.now().isoformat(),
            "uptime_minutes": error_summary["uptime_minutes"],
            "total_errors": error_summary["total_errors"],
            "error_rate_per_minute": error_summary["error_rate_per_minute"],
            "components": component_statuses,
            "error_categories": error_summary["categories"]
        }


# Global instances
_error_monitor = ErrorMonitor()
_health_checker = HealthChecker(_error_monitor)


def get_error_monitor() -> ErrorMonitor:
    """Get the global error monitor instance."""
    return _error_monitor


def get_health_checker() -> HealthChecker:
    """Get the global health checker instance."""
    return _health_checker


def record_error(error: PersonalitySystemError, component: Optional[str] = None):
    """Record an error in the global monitor."""
    _error_monitor.record_error(error, component)


def get_system_health() -> Dict[str, Any]:
    """Get current system health status."""
    return _health_checker.get_system_health()


def get_error_metrics() -> Dict[str, Any]:
    """Get current error metrics."""
    return _error_monitor.get_error_summary()


class PerformanceTimer:
    """Context manager for measuring operation performance."""
    
    def __init__(self, operation: str, component: str):
        self.operation = operation
        self.component = component
        self.start_time = None
        self.end_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.end_time = time.time()
        duration = self.end_time - self.start_time
        
        # Log performance metrics
        import logging
        logger = logging.getLogger(__name__)
        logger.info(
            f"Performance: {self.operation} in {self.component} took {duration:.3f}s",
            extra={
                "operation": self.operation,
                "component": self.component,
                "duration_seconds": duration,
                "timestamp": datetime.now().isoformat()
            }
        )
        
        # Record error if operation was too slow (>30 seconds)
        if duration > 30.0:
            from .error_handling import SystemError, ErrorSeverity
            slow_error = SystemError(
                message=f"Slow operation: {self.operation} took {duration:.1f}s",
                details={"duration": duration, "threshold": 30.0}
            )
            record_error(slow_error, self.component)


def performance_monitor(operation: str, component: str):
    """Decorator for monitoring operation performance."""
    
    def decorator(func):
        if asyncio.iscoroutinefunction(func):
            async def async_wrapper(*args, **kwargs):
                with PerformanceTimer(operation, component):
                    return await func(*args, **kwargs)
            return async_wrapper
        else:
            def sync_wrapper(*args, **kwargs):
                with PerformanceTimer(operation, component):
                    return func(*args, **kwargs)
            return sync_wrapper
    
    return decorator