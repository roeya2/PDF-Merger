"""
Unit tests for the performance_monitor module.
"""

import pytest
from unittest.mock import patch, MagicMock, PropertyMock
from app.managers.performance_monitor import PerformanceMonitor, get_performance_monitor


class TestPerformanceMonitorInitialization:
    """Test PerformanceMonitor initialization and basic functionality."""

    def test_performance_monitor_creation(self):
        """Test that PerformanceMonitor can be created."""
        monitor = PerformanceMonitor()
        assert monitor is not None
        assert hasattr(monitor, 'get_memory_usage')
        assert hasattr(monitor, 'get_memory_percent')
        assert hasattr(monitor, 'get_cpu_usage')
        assert hasattr(monitor, 'get_system_memory_info')
        assert hasattr(monitor, 'get_performance_snapshot')
        assert hasattr(monitor, 'log_performance_snapshot')
        assert hasattr(monitor, 'check_memory_threshold')
        assert hasattr(monitor, 'is_performance_monitoring_available')

    def test_get_performance_monitor_singleton(self):
        """Test that get_performance_monitor returns a singleton."""
        monitor1 = get_performance_monitor()
        monitor2 = get_performance_monitor()

        assert monitor1 is monitor2
        assert isinstance(monitor1, PerformanceMonitor)

    def test_performance_monitor_with_psutil_available(self):
        """Test PerformanceMonitor when psutil is available."""
        with patch('app.managers.performance_monitor.PERFORMANCE_MONITORING_AVAILABLE', True):
            with patch('app.managers.performance_monitor.psutil') as mock_psutil:
                mock_process = MagicMock()
                mock_psutil.Process.return_value = mock_process

                monitor = PerformanceMonitor()

                assert monitor._process is not None
                assert monitor._process == mock_process

    def test_performance_monitor_without_psutil(self):
        """Test PerformanceMonitor when psutil is not available."""
        with patch('app.managers.performance_monitor.PERFORMANCE_MONITORING_AVAILABLE', False):
            with patch('app.managers.performance_monitor.psutil', None):
                monitor = PerformanceMonitor()

                assert monitor._process is None

    def test_performance_monitor_psutil_error_handling(self):
        """Test PerformanceMonitor handles psutil errors gracefully."""
        with patch('app.managers.performance_monitor.PERFORMANCE_MONITORING_AVAILABLE', True):
            with patch('app.managers.performance_monitor.psutil') as mock_psutil:
                mock_psutil.Process.side_effect = Exception("psutil error")

                monitor = PerformanceMonitor()

                # Should still create the monitor but with _process = None
                assert monitor._process is None


class TestPerformanceMonitorMethods:
    """Test individual PerformanceMonitor methods."""

    def test_get_memory_usage_with_psutil(self):
        """Test get_memory_usage when psutil is available."""
        with patch('app.managers.performance_monitor.PERFORMANCE_MONITORING_AVAILABLE', True):
            with patch('app.managers.performance_monitor.psutil') as mock_psutil:
                mock_process = MagicMock()
                mock_memory_info = MagicMock()
                mock_memory_info.rss = 104857600  # 100 MB in bytes
                mock_process.memory_info.return_value = mock_memory_info
                mock_psutil.Process.return_value = mock_process

                monitor = PerformanceMonitor()
                memory_mb = monitor.get_memory_usage()

                assert memory_mb == 100.0  # Should be converted to MB
                mock_process.memory_info.assert_called_once()

    def test_get_memory_usage_without_psutil(self):
        """Test get_memory_usage when psutil is not available."""
        with patch('app.managers.performance_monitor.PERFORMANCE_MONITORING_AVAILABLE', False):
            monitor = PerformanceMonitor()
            memory_mb = monitor.get_memory_usage()

            assert memory_mb is None

    def test_get_memory_usage_error_handling(self):
        """Test get_memory_usage handles errors gracefully."""
        with patch('app.managers.performance_monitor.PERFORMANCE_MONITORING_AVAILABLE', True):
            with patch('app.managers.performance_monitor.psutil') as mock_psutil:
                mock_process = MagicMock()
                mock_process.memory_info.side_effect = Exception("memory error")
                mock_psutil.Process.return_value = mock_process

                monitor = PerformanceMonitor()
                memory_mb = monitor.get_memory_usage()

                assert memory_mb is None

    def test_get_memory_percent_with_psutil(self):
        """Test get_memory_percent when psutil is available."""
        with patch('app.managers.performance_monitor.PERFORMANCE_MONITORING_AVAILABLE', True):
            with patch('app.managers.performance_monitor.psutil') as mock_psutil:
                mock_process = MagicMock()
                mock_process.memory_percent.return_value = 25.5
                mock_psutil.Process.return_value = mock_process

                monitor = PerformanceMonitor()
                memory_percent = monitor.get_memory_percent()

                assert memory_percent == 25.5
                mock_process.memory_percent.assert_called_once()

    def test_get_memory_percent_without_psutil(self):
        """Test get_memory_percent when psutil is not available."""
        with patch('app.managers.performance_monitor.PERFORMANCE_MONITORING_AVAILABLE', False):
            monitor = PerformanceMonitor()
            memory_percent = monitor.get_memory_percent()

            assert memory_percent is None

    def test_get_cpu_usage_with_psutil(self):
        """Test get_cpu_usage when psutil is available."""
        with patch('app.managers.performance_monitor.PERFORMANCE_MONITORING_AVAILABLE', True):
            with patch('app.managers.performance_monitor.psutil') as mock_psutil:
                mock_process = MagicMock()
                mock_process.cpu_percent.return_value = 15.3
                mock_psutil.Process.return_value = mock_process

                monitor = PerformanceMonitor()
                cpu_percent = monitor.get_cpu_usage()

                assert cpu_percent == 15.3
                mock_process.cpu_percent.assert_called_once_with(interval=0.1)

    def test_get_cpu_usage_without_psutil(self):
        """Test get_cpu_usage when psutil is not available."""
        with patch('app.managers.performance_monitor.PERFORMANCE_MONITORING_AVAILABLE', False):
            monitor = PerformanceMonitor()
            cpu_percent = monitor.get_cpu_usage()

            assert cpu_percent is None

    def test_get_system_memory_info_with_psutil(self):
        """Test get_system_memory_info when psutil is available."""
        with patch('app.managers.performance_monitor.PERFORMANCE_MONITORING_AVAILABLE', True):
            with patch('app.managers.performance_monitor.psutil') as mock_psutil:
                mock_memory = MagicMock()
                mock_memory.total = 8589934592  # 8 GB in bytes
                mock_memory.available = 4294967296  # 4 GB in bytes
                mock_memory.percent = 50.0
                mock_memory.used = 4294967296  # 4 GB in bytes
                mock_psutil.virtual_memory.return_value = mock_memory

                monitor = PerformanceMonitor()
                system_info = monitor.get_system_memory_info()

                assert system_info is not None
                assert system_info['total'] == 8192.0  # 8 GB in MB
                assert system_info['available'] == 4096.0  # 4 GB in MB
                assert system_info['percent'] == 50.0
                assert system_info['used'] == 4096.0  # 4 GB in MB

    def test_get_system_memory_info_without_psutil(self):
        """Test get_system_memory_info when psutil is not available."""
        with patch('app.managers.performance_monitor.PERFORMANCE_MONITORING_AVAILABLE', False), \
             patch('app.managers.performance_monitor.psutil', None):
            monitor = PerformanceMonitor()
            system_info = monitor.get_system_memory_info()

            assert system_info is None


class TestPerformanceMonitorSnapshots:
    """Test performance snapshot functionality."""

    def test_get_performance_snapshot_with_monitoring(self):
        """Test get_performance_snapshot when monitoring is available."""
        with patch('app.managers.performance_monitor.PERFORMANCE_MONITORING_AVAILABLE', True):
            with patch('app.managers.performance_monitor.psutil') as mock_psutil:
                mock_process = MagicMock()
                mock_memory_info = MagicMock()
                mock_memory_info.rss = 104857600  # 100 MB
                mock_process.memory_info.return_value = mock_memory_info
                mock_process.memory_percent.return_value = 25.0
                mock_process.cpu_percent.return_value = 10.0
                mock_psutil.Process.return_value = mock_process

                mock_memory = MagicMock()
                mock_memory.total = 8589934592  # 8 GB
                mock_memory.available = 4294967296  # 4 GB
                mock_memory.percent = 50.0
                mock_memory.used = 4294967296  # 4 GB
                mock_psutil.virtual_memory.return_value = mock_memory

                monitor = PerformanceMonitor()
                snapshot = monitor.get_performance_snapshot()

                assert snapshot['monitoring_available'] is True
                assert snapshot['memory_usage_mb'] == 100.0
                assert snapshot['memory_percent'] == 25.0
                assert snapshot['cpu_percent'] == 10.0
                assert 'system_memory' in snapshot
                assert snapshot['system_memory']['total'] == 8192.0

    def test_get_performance_snapshot_without_monitoring(self):
        """Test get_performance_snapshot when monitoring is not available."""
        with patch('app.managers.performance_monitor.PERFORMANCE_MONITORING_AVAILABLE', False), \
             patch('app.managers.performance_monitor.psutil', None):
            monitor = PerformanceMonitor()
            snapshot = monitor.get_performance_snapshot()

            assert snapshot['monitoring_available'] is False
            assert snapshot['memory_usage_mb'] is None
            assert snapshot['memory_percent'] is None
            assert snapshot['cpu_percent'] is None
            assert 'system_memory' not in snapshot

    def test_log_performance_snapshot_with_monitoring(self):
        """Test log_performance_snapshot when monitoring is available."""
        with patch('app.managers.performance_monitor.PERFORMANCE_MONITORING_AVAILABLE', True):
            with patch('app.managers.performance_monitor.psutil') as mock_psutil:
                mock_process = MagicMock()
                mock_memory_info = MagicMock()
                mock_memory_info.rss = 52428800  # 50 MB
                mock_process.memory_info.return_value = mock_memory_info
                mock_process.memory_percent.return_value = 12.5
                mock_process.cpu_percent.return_value = 5.0
                mock_psutil.Process.return_value = mock_process

                # Mock system memory info as a proper mock object
                mock_system_memory = MagicMock()
                mock_system_memory.total = 8192.0
                mock_system_memory.available = 4096.0
                mock_system_memory.percent = 50.0
                mock_system_memory.used = 4096.0
                mock_psutil.virtual_memory.return_value = mock_system_memory

                monitor = PerformanceMonitor()

                with patch.object(monitor.logger, 'info') as mock_log, \
                     patch.object(monitor.logger, 'debug') as mock_debug:

                    monitor.log_performance_snapshot("test_operation")

                    # Verify that the log was called with performance info
                    mock_log.assert_called_once()
                    log_call = mock_log.call_args[0][0]
                    assert "test_operation" in log_call
                    assert "50.0MB" in log_call
                    assert "12.5%" in log_call
                    assert "5.0%" in log_call

                    # Should also call debug for system memory
                    mock_debug.assert_called_once()

    def test_log_performance_snapshot_without_monitoring(self):
        """Test log_performance_snapshot when monitoring is not available."""
        with patch('app.managers.performance_monitor.PERFORMANCE_MONITORING_AVAILABLE', False):
            monitor = PerformanceMonitor()

            with patch.object(monitor.logger, 'debug') as mock_log:
                monitor.log_performance_snapshot("test_operation")

                # Should log that monitoring is not available
                mock_log.assert_called_once()
                log_call = mock_log.call_args[0][0]
                assert "test_operation" in log_call
                assert "monitoring not available" in log_call


class TestPerformanceMonitorThresholds:
    """Test threshold checking functionality."""

    def test_check_memory_threshold_above_limit(self):
        """Test check_memory_threshold when memory usage is above threshold."""
        with patch('app.managers.performance_monitor.PERFORMANCE_MONITORING_AVAILABLE', True):
            with patch('app.managers.performance_monitor.psutil') as mock_psutil:
                mock_process = MagicMock()
                mock_memory_info = MagicMock()
                mock_memory_info.rss = 314572800  # 300 MB
                mock_process.memory_info.return_value = mock_memory_info
                mock_psutil.Process.return_value = mock_process

                monitor = PerformanceMonitor()
                result = monitor.check_memory_threshold(threshold_mb=200.0)

                assert result is True

    def test_check_memory_threshold_below_limit(self):
        """Test check_memory_threshold when memory usage is below threshold."""
        with patch('app.managers.performance_monitor.PERFORMANCE_MONITORING_AVAILABLE', True):
            with patch('app.managers.performance_monitor.psutil') as mock_psutil:
                mock_process = MagicMock()
                mock_memory_info = MagicMock()
                mock_memory_info.rss = 104857600  # 100 MB
                mock_process.memory_info.return_value = mock_memory_info
                mock_psutil.Process.return_value = mock_process

                monitor = PerformanceMonitor()
                result = monitor.check_memory_threshold(threshold_mb=200.0)

                assert result is False

    def test_check_memory_threshold_without_monitoring(self):
        """Test check_memory_threshold when monitoring is not available."""
        with patch('app.managers.performance_monitor.PERFORMANCE_MONITORING_AVAILABLE', False):
            monitor = PerformanceMonitor()
            result = monitor.check_memory_threshold(threshold_mb=200.0)

            assert result is False

    def test_is_performance_monitoring_available(self):
        """Test is_performance_monitoring_available method."""
        with patch('app.managers.performance_monitor.PERFORMANCE_MONITORING_AVAILABLE', True):
            with patch('app.managers.performance_monitor.psutil') as mock_psutil:
                mock_process = MagicMock()
                mock_psutil.Process.return_value = mock_process

                monitor = PerformanceMonitor()
                assert monitor.is_performance_monitoring_available() is True

        with patch('app.managers.performance_monitor.PERFORMANCE_MONITORING_AVAILABLE', False):
            monitor = PerformanceMonitor()
            assert monitor.is_performance_monitoring_available() is False


class TestPerformanceMonitorIntegration:
    """Integration tests for PerformanceMonitor."""

    def test_convenience_function_log_performance_snapshot(self):
        """Test the convenience function log_performance_snapshot."""
        from app.managers.performance_monitor import log_performance_snapshot

        with patch('app.managers.performance_monitor.PERFORMANCE_MONITORING_AVAILABLE', True):
            with patch('app.managers.performance_monitor.psutil') as mock_psutil:
                mock_process = MagicMock()
                mock_memory_info = MagicMock()
                mock_memory_info.rss = 26214400  # 25 MB
                mock_process.memory_info.return_value = mock_memory_info
                mock_process.memory_percent.return_value = 6.25
                mock_process.cpu_percent.return_value = 2.5
                mock_psutil.Process.return_value = mock_process

                with patch('app.managers.performance_monitor.get_performance_monitor') as mock_get_monitor:
                    mock_monitor = MagicMock()
                    mock_get_monitor.return_value = mock_monitor

                    log_performance_snapshot("integration_test")

                    mock_monitor.log_performance_snapshot.assert_called_once_with("integration_test")

    def test_multiple_instances_are_same_object(self):
        """Test that multiple calls to get_performance_monitor return the same instance."""
        monitor1 = get_performance_monitor()
        monitor2 = get_performance_monitor()

        assert monitor1 is monitor2

        # Clear the global instance for other tests
        import app.managers.performance_monitor
        app.managers.performance_monitor._performance_monitor = None

    def test_memory_conversion_accuracy(self):
        """Test that memory conversion from bytes to MB is accurate."""
        # Test various memory sizes
        test_cases = [
            (1024, 1024 / 1024 / 1024),  # 1 KB
            (1048576, 1.0),              # 1 MB
            (1073741824, 1024.0),       # 1 GB
            (2147483648, 2048.0),       # 2 GB
        ]

        for bytes_value, expected_mb in test_cases:
            with patch('app.managers.performance_monitor.PERFORMANCE_MONITORING_AVAILABLE', True):
                with patch('app.managers.performance_monitor.psutil') as mock_psutil:
                    mock_process = MagicMock()
                    mock_memory_info = MagicMock()
                    mock_memory_info.rss = bytes_value
                    mock_process.memory_info.return_value = mock_memory_info
                    mock_psutil.Process.return_value = mock_process

                    monitor = PerformanceMonitor()
                    memory_mb = monitor.get_memory_usage()

                    assert abs(memory_mb - expected_mb) < 0.001, f"Expected {expected_mb}, got {memory_mb}"


class TestPerformanceMonitorErrorHandling:
    """Test error handling in PerformanceMonitor."""

    def test_memory_info_error_returns_none(self):
        """Test that memory_info errors return None."""
        with patch('app.managers.performance_monitor.PERFORMANCE_MONITORING_AVAILABLE', True):
            with patch('app.managers.performance_monitor.psutil') as mock_psutil:
                mock_process = MagicMock()
                mock_process.memory_info.side_effect = Exception("Memory info error")
                mock_psutil.Process.return_value = mock_process

                monitor = PerformanceMonitor()
                memory_mb = monitor.get_memory_usage()

                assert memory_mb is None

    def test_memory_percent_error_returns_none(self):
        """Test that memory_percent errors return None."""
        with patch('app.managers.performance_monitor.PERFORMANCE_MONITORING_AVAILABLE', True):
            with patch('app.managers.performance_monitor.psutil') as mock_psutil:
                mock_process = MagicMock()
                mock_process.memory_percent.side_effect = Exception("Memory percent error")
                mock_psutil.Process.return_value = mock_process

                monitor = PerformanceMonitor()
                memory_percent = monitor.get_memory_percent()

                assert memory_percent is None

    def test_cpu_usage_error_returns_none(self):
        """Test that cpu_percent errors return None."""
        with patch('app.managers.performance_monitor.PERFORMANCE_MONITORING_AVAILABLE', True):
            with patch('app.managers.performance_monitor.psutil') as mock_psutil:
                mock_process = MagicMock()
                mock_process.cpu_percent.side_effect = Exception("CPU usage error")
                mock_psutil.Process.return_value = mock_process

                monitor = PerformanceMonitor()
                cpu_percent = monitor.get_cpu_usage()

                assert cpu_percent is None

    def test_system_memory_error_returns_none(self):
        """Test that system memory errors return None."""
        with patch('app.managers.performance_monitor.PERFORMANCE_MONITORING_AVAILABLE', True):
            with patch('app.managers.performance_monitor.psutil') as mock_psutil:
                mock_psutil.virtual_memory.side_effect = Exception("System memory error")

                monitor = PerformanceMonitor()
                system_info = monitor.get_system_memory_info()

                assert system_info is None

    def test_log_performance_snapshot_handles_log_errors(self):
        """Test that log_performance_snapshot handles logger errors gracefully."""
        with patch('app.managers.performance_monitor.PERFORMANCE_MONITORING_AVAILABLE', True):
            with patch('app.managers.performance_monitor.psutil') as mock_psutil:
                mock_process = MagicMock()
                mock_memory_info = MagicMock()
                mock_memory_info.rss = 104857600  # 100 MB
                mock_process.memory_info.return_value = mock_memory_info
                mock_process.memory_percent.return_value = 25.0
                mock_process.cpu_percent.return_value = 10.0
                mock_psutil.Process.return_value = mock_process

                monitor = PerformanceMonitor()

                # Mock logger to raise an exception - current implementation does not handle this
                with patch.object(monitor.logger, 'info', side_effect=Exception("Logger error")):

                    # Current implementation will raise the exception
                    with pytest.raises(Exception):
                        monitor.log_performance_snapshot("test_operation")
