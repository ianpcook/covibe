"""Unit tests for monitoring and metrics system."""

import time
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from src.covibe.utils.monitoring import (
    ErrorMonitor,
    HealthChecker,
    ComponentHealth,
    HealthStatus,
    ErrorMetric,
    PerformanceTimer,
    performance_monitor,
    get_error_monitor,
    get_health_checker,
    record_error,
    get_system_health,
    get_error_metrics
)
from src.covibe.utils.error_handling import (
    PersonalitySystemError,
    ResearchError,
    NetworkError,
    SystemError,
    ErrorCategory,
    ErrorSeverity
)


class TestErrorMetric:
    """Test error metric functionality."""
    
    def test_error_metric_creation(self):
        """Test creating error metric."""
        metric = ErrorMetric()
        
        assert metric.count == 0
        assert metric.last_occurrence is None
        assert len(metric.recent_occurrences) == 0
    
    def test_record_error(self):
        """Test recording error in metric."""
        metric = ErrorMetric()
        
        metric.record_error()
        
        assert metric.count == 1
        assert metric.last_occurrence is not None
        assert len(metric.recent_occurrences) == 1
        
        # Record another error
        metric.record_error()
        
        assert metric.count == 2
        assert len(metric.recent_occurrences) == 2
    
    def test_recent_occurrences_limit(self):
        """Test that recent occurrences are limited."""
        metric = ErrorMetric()
        
        # Record more than the limit (100)
        for _ in range(150):
            metric.record_error()
        
        assert metric.count == 150
        assert len(metric.recent_occurrences) == 100  # Limited to maxlen


class TestErrorMonitor:
    """Test error monitoring functionality."""
    
    def test_error_monitor_creation(self):
        """Test creating error monitor."""
        monitor = ErrorMonitor(window_minutes=30)
        
        assert monitor.window_minutes == 30
        assert len(monitor.error_metrics) == 0
        assert len(monitor.component_metrics) == 0
        assert isinstance(monitor.start_time, datetime)
    
    def test_record_error(self):
        """Test recording error in monitor."""
        monitor = ErrorMonitor()
        error = ResearchError("Test error")
        
        monitor.record_error(error)
        
        error_key = f"{error.category.value}:{error.code}"
        assert error_key in monitor.error_metrics
        assert monitor.error_metrics[error_key].count == 1
    
    def test_record_error_with_component(self):
        """Test recording error with component."""
        monitor = ErrorMonitor()
        error = ResearchError("Test error")
        
        monitor.record_error(error, "research")
        
        error_key = f"{error.category.value}:{error.code}"
        assert error_key in monitor.error_metrics
        assert error_key in monitor.component_metrics["research"]
        assert monitor.component_metrics["research"][error_key].count == 1
    
    def test_get_error_rate_all_errors(self):
        """Test getting error rate for all errors."""
        monitor = ErrorMonitor(window_minutes=60)
        
        # Record some errors
        for _ in range(5):
            error = ResearchError("Test error")
            monitor.record_error(error)
        
        error_rate = monitor.get_error_rate()
        assert error_rate == 5.0 / 60  # 5 errors in 60 minutes
    
    def test_get_error_rate_by_category(self):
        """Test getting error rate by category."""
        monitor = ErrorMonitor(window_minutes=60)
        
        # Record research errors
        for _ in range(3):
            error = ResearchError("Research error")
            monitor.record_error(error)
        
        # Record network errors
        for _ in range(2):
            error = NetworkError("Network error")
            monitor.record_error(error)
        
        research_rate = monitor.get_error_rate(category=ErrorCategory.RESEARCH)
        network_rate = monitor.get_error_rate(category=ErrorCategory.NETWORK)
        
        assert research_rate == 3.0 / 60
        assert network_rate == 2.0 / 60
    
    def test_get_error_rate_by_component(self):
        """Test getting error rate by component."""
        monitor = ErrorMonitor(window_minutes=60)
        
        # Record errors for different components
        for _ in range(4):
            error = ResearchError("Research error")
            monitor.record_error(error, "research")
        
        for _ in range(2):
            error = SystemError("System error")
            monitor.record_error(error, "orchestration")
        
        research_rate = monitor.get_error_rate(component="research")
        orchestration_rate = monitor.get_error_rate(component="orchestration")
        
        assert research_rate == 4.0 / 60
        assert orchestration_rate == 2.0 / 60
    
    def test_get_error_summary(self):
        """Test getting error summary."""
        monitor = ErrorMonitor()
        
        # Record various errors
        research_error = ResearchError("Research error")
        network_error = NetworkError("Network error")
        
        monitor.record_error(research_error, "research")
        monitor.record_error(network_error, "research")
        monitor.record_error(research_error, "orchestration")
        
        summary = monitor.get_error_summary()
        
        assert summary["total_errors"] == 3
        assert "research" in summary["categories"]
        assert "network" in summary["categories"]
        assert "research" in summary["components"]
        assert "orchestration" in summary["components"]
        
        # Check component breakdown
        assert summary["components"]["research"]["count"] == 2
        assert summary["components"]["orchestration"]["count"] == 1


class TestHealthChecker:
    """Test health checking functionality."""
    
    def test_health_checker_creation(self):
        """Test creating health checker."""
        monitor = ErrorMonitor()
        checker = HealthChecker(monitor)
        
        assert checker.error_monitor is monitor
        assert len(checker.component_health) == 0
    
    def test_check_component_health_healthy(self):
        """Test checking healthy component."""
        monitor = ErrorMonitor()
        checker = HealthChecker(monitor)
        
        # No errors recorded, should be healthy
        health = checker.check_component_health("research", error_threshold=5.0)
        
        assert health.name == "research"
        assert health.status == HealthStatus.HEALTHY
        assert health.error_rate == 0.0
        assert health.last_check is not None
    
    def test_check_component_health_degraded(self):
        """Test checking degraded component."""
        monitor = ErrorMonitor(window_minutes=1)  # Use 1-minute window for testing
        checker = HealthChecker(monitor)
        
        # Record some errors to make it degraded
        for _ in range(3):  # 3 errors per minute with 1-minute window
            error = ResearchError("Research error")
            monitor.record_error(error, "research")
        
        health = checker.check_component_health("research", error_threshold=5.0)
        
        assert health.status == HealthStatus.DEGRADED
        assert health.error_rate > 0
    
    def test_check_component_health_unhealthy(self):
        """Test checking unhealthy component."""
        monitor = ErrorMonitor(window_minutes=1)  # Use 1-minute window for testing
        checker = HealthChecker(monitor)
        
        # Record many errors to make it unhealthy
        for _ in range(10):  # 10 errors per minute with 1-minute window
            error = ResearchError("Research error")
            monitor.record_error(error, "research")
        
        health = checker.check_component_health("research", error_threshold=5.0)
        
        assert health.status == HealthStatus.UNHEALTHY
        assert health.error_rate > 5.0
    
    def test_get_system_health(self):
        """Test getting overall system health."""
        monitor = ErrorMonitor()
        checker = HealthChecker(monitor)
        
        # Record some errors
        error = ResearchError("Research error")
        monitor.record_error(error, "research")
        
        system_health = checker.get_system_health()
        
        assert "status" in system_health
        assert "timestamp" in system_health
        assert "uptime_minutes" in system_health
        assert "total_errors" in system_health
        assert "error_rate_per_minute" in system_health
        assert "components" in system_health
        assert "error_categories" in system_health
        
        # Check that research component is included
        assert "research" in system_health["components"]
        
        # Check overall status (should be healthy with just one error)
        assert system_health["status"] in [HealthStatus.HEALTHY.value, HealthStatus.DEGRADED.value]


class TestPerformanceTimer:
    """Test performance timing functionality."""
    
    def test_performance_timer_context_manager(self):
        """Test performance timer as context manager."""
        with PerformanceTimer("test_operation", "test_component") as timer:
            time.sleep(0.01)  # Small delay
        
        assert timer.start_time is not None
        assert timer.end_time is not None
        assert timer.end_time > timer.start_time
        assert timer.operation == "test_operation"
        assert timer.component == "test_component"
    
    @patch('src.covibe.utils.monitoring.record_error')
    @patch('logging.getLogger')
    def test_performance_timer_slow_operation(self, mock_logger, mock_record_error):
        """Test performance timer records error for slow operations."""
        mock_log = MagicMock()
        mock_logger.return_value = mock_log
        
        # Mock time to simulate slow operation
        with patch('time.time', side_effect=[0, 35]):  # 35 second operation
            with PerformanceTimer("slow_operation", "test_component"):
                pass
        
        # Should record error for slow operation
        mock_record_error.assert_called_once()
        error_arg = mock_record_error.call_args[0][0]
        assert "Slow operation" in str(error_arg)


class TestPerformanceMonitorDecorator:
    """Test performance monitor decorator."""
    
    @patch('src.covibe.utils.monitoring.PerformanceTimer')
    def test_performance_monitor_sync_function(self, mock_timer):
        """Test performance monitor with sync function."""
        mock_timer_instance = MagicMock()
        mock_timer.return_value.__enter__ = MagicMock(return_value=mock_timer_instance)
        mock_timer.return_value.__exit__ = MagicMock(return_value=None)
        
        @performance_monitor("test_operation", "test_component")
        def sync_function():
            return "result"
        
        result = sync_function()
        
        assert result == "result"
        mock_timer.assert_called_once_with("test_operation", "test_component")
    
    @patch('src.covibe.utils.monitoring.PerformanceTimer')
    @pytest.mark.asyncio
    async def test_performance_monitor_async_function(self, mock_timer):
        """Test performance monitor with async function."""
        mock_timer_instance = MagicMock()
        mock_timer.return_value.__enter__ = MagicMock(return_value=mock_timer_instance)
        mock_timer.return_value.__exit__ = MagicMock(return_value=None)
        
        @performance_monitor("test_operation", "test_component")
        async def async_function():
            return "async_result"
        
        result = await async_function()
        
        assert result == "async_result"
        mock_timer.assert_called_once_with("test_operation", "test_component")


class TestGlobalFunctions:
    """Test global monitoring functions."""
    
    def test_get_error_monitor(self):
        """Test getting global error monitor."""
        monitor = get_error_monitor()
        assert isinstance(monitor, ErrorMonitor)
    
    def test_get_health_checker(self):
        """Test getting global health checker."""
        checker = get_health_checker()
        assert isinstance(checker, HealthChecker)
    
    def test_record_error_global(self):
        """Test global record_error function."""
        error = ResearchError("Test error")
        
        # This should not raise an exception
        record_error(error, "test_component")
        
        # Verify it was recorded in global monitor
        monitor = get_error_monitor()
        error_key = f"{error.category.value}:{error.code}"
        assert error_key in monitor.error_metrics
    
    def test_get_system_health_global(self):
        """Test global get_system_health function."""
        health = get_system_health()
        
        assert isinstance(health, dict)
        assert "status" in health
        assert "timestamp" in health
    
    def test_get_error_metrics_global(self):
        """Test global get_error_metrics function."""
        metrics = get_error_metrics()
        
        assert isinstance(metrics, dict)
        assert "total_errors" in metrics
        assert "error_rate_per_minute" in metrics


class TestComponentHealth:
    """Test component health data structure."""
    
    def test_component_health_creation(self):
        """Test creating component health."""
        health = ComponentHealth(
            name="test_component",
            status=HealthStatus.HEALTHY,
            error_rate=1.5,
            response_time=0.25,
            uptime=99.9
        )
        
        assert health.name == "test_component"
        assert health.status == HealthStatus.HEALTHY
        assert health.error_rate == 1.5
        assert health.response_time == 0.25
        assert health.uptime == 99.9
        assert isinstance(health.details, dict)
    
    def test_component_health_defaults(self):
        """Test component health with defaults."""
        health = ComponentHealth(name="test_component")
        
        assert health.name == "test_component"
        assert health.status == HealthStatus.HEALTHY
        assert health.error_rate == 0.0
        assert health.response_time == 0.0
        assert health.uptime == 100.0
        assert health.last_check is None


class TestIntegration:
    """Test integration between monitoring components."""
    
    def test_error_monitor_health_checker_integration(self):
        """Test integration between error monitor and health checker."""
        monitor = ErrorMonitor()
        checker = HealthChecker(monitor)
        
        # Record errors in monitor
        for _ in range(3):
            error = ResearchError("Research error")
            monitor.record_error(error, "research")
        
        # Check health using checker
        health = checker.check_component_health("research")
        
        # Health should reflect the errors recorded in monitor
        assert health.error_rate > 0
        assert health.name == "research"
        
        # System health should include this component
        system_health = checker.get_system_health()
        assert "research" in system_health["components"]
        assert system_health["components"]["research"]["error_rate"] > 0


if __name__ == "__main__":
    pytest.main([__file__])