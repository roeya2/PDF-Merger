"""
Performance monitoring utilities for PDF Merger Pro.

This module provides functionality to monitor system resources and application
performance, particularly useful when processing large files.
"""

import os
import logging
from typing import Dict, Any, Optional
from ..utils.common_imports import PERFORMANCE_MONITORING_AVAILABLE
from ..utils.constants import MEMORY_BYTES_TO_MB, MEMORY_THRESHOLD_MB

if PERFORMANCE_MONITORING_AVAILABLE:
    from ..utils.common_imports import psutil
else:
    psutil = None

logger = logging.getLogger(__name__)


class PerformanceMonitor:
    """Monitors application performance and system resources."""

    def __init__(self):
        """Initialize the performance monitor."""
        self.logger = logging.getLogger(__name__)
        self._process = None

        if PERFORMANCE_MONITORING_AVAILABLE and psutil:
            try:
                self._process = psutil.Process(os.getpid())
                self.logger.info("Performance monitoring initialized with psutil")
            except Exception as e:
                self.logger.warning(f"Failed to initialize performance monitoring: {e}")
                self._process = None
        else:
            self.logger.info("Performance monitoring not available (psutil not installed)")

    def get_memory_usage(self) -> Optional[float]:
        """
        Get current memory usage in MB.

        Returns:
            Current memory usage in MB, or None if monitoring is not available.
        """
        if not self._process:
            return None

        try:
            memory_info = self._process.memory_info()
            return memory_info.rss / MEMORY_BYTES_TO_MB  # Convert to MB
        except Exception as e:
            self.logger.warning(f"Failed to get memory usage: {e}")
            return None

    def get_memory_percent(self) -> Optional[float]:
        """
        Get current memory usage as a percentage.

        Returns:
            Current memory usage percentage, or None if monitoring is not available.
        """
        if not self._process:
            return None

        try:
            return self._process.memory_percent()
        except Exception as e:
            self.logger.warning(f"Failed to get memory percentage: {e}")
            return None

    def get_cpu_usage(self) -> Optional[float]:
        """
        Get current CPU usage percentage.

        Returns:
            Current CPU usage percentage, or None if monitoring is not available.
        """
        if not self._process:
            return None

        try:
            return self._process.cpu_percent(interval=0.1)
        except Exception as e:
            self.logger.warning(f"Failed to get CPU usage: {e}")
            return None

    def get_system_memory_info(self) -> Optional[Dict[str, Any]]:
        """
        Get system-wide memory information.

        Returns:
            Dictionary with system memory information, or None if monitoring is not available.
        """
        if not psutil:
            return None

        try:
            memory = psutil.virtual_memory()
            return {
                'total': memory.total / MEMORY_BYTES_TO_MB,  # MB
                'available': memory.available / MEMORY_BYTES_TO_MB,  # MB
                'percent': memory.percent,
                'used': memory.used / MEMORY_BYTES_TO_MB,  # MB
            }
        except Exception as e:
            self.logger.warning(f"Failed to get system memory info: {e}")
            return None

    def get_performance_snapshot(self) -> Dict[str, Any]:
        """
        Get a comprehensive performance snapshot.

        Returns:
            Dictionary containing current performance metrics.
        """
        snapshot = {
            'monitoring_available': bool(self._process),
            'memory_usage_mb': self.get_memory_usage(),
            'memory_percent': self.get_memory_percent(),
            'cpu_percent': self.get_cpu_usage(),
        }

        system_memory = self.get_system_memory_info()
        if system_memory:
            snapshot['system_memory'] = system_memory

        return snapshot

    def log_performance_snapshot(self, operation: str = "operation"):
        """
        Log a performance snapshot with context.

        Args:
            operation: Description of the current operation for context.
        """
        snapshot = self.get_performance_snapshot()

        if snapshot['monitoring_available']:
            memory_mb = snapshot.get('memory_usage_mb', 'N/A')
            memory_percent = snapshot.get('memory_percent', 'N/A')
            cpu_percent = snapshot.get('cpu_percent', 'N/A')

            self.logger.info(
                f"Performance snapshot for '{operation}': "
                f"Memory: {memory_mb:.1f}MB ({memory_percent:.1f}%), "
                f"CPU: {cpu_percent:.1f}%"
            )

            if 'system_memory' in snapshot:
                sys_mem = snapshot['system_memory']
                self.logger.debug(
                    f"System memory: {sys_mem['used']:.0f}MB used / "
                    f"{sys_mem['total']:.0f}MB total ({sys_mem['percent']:.1f}%)"
                )
        else:
            self.logger.debug(f"Performance snapshot requested for '{operation}' but monitoring not available")

    def check_memory_threshold(self, threshold_mb: float = MEMORY_THRESHOLD_MB) -> bool:
        """
        Check if memory usage exceeds a threshold.

        Args:
            threshold_mb: Memory threshold in MB.

        Returns:
            True if memory usage exceeds threshold, False otherwise.
        """
        memory_usage = self.get_memory_usage()
        if memory_usage is None:
            return False

        return memory_usage > threshold_mb

    def is_performance_monitoring_available(self) -> bool:
        """
        Check if performance monitoring is available.

        Returns:
            True if performance monitoring is available, False otherwise.
        """
        return bool(self._process)


# Global performance monitor instance
_performance_monitor = None


def get_performance_monitor() -> PerformanceMonitor:
    """
    Get the global performance monitor instance.

    Returns:
        The global PerformanceMonitor instance.
    """
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor


def log_performance_snapshot(operation: str = "operation"):
    """
    Convenience function to log a performance snapshot.

    Args:
        operation: Description of the current operation.
    """
    monitor = get_performance_monitor()
    monitor.log_performance_snapshot(operation)
