"""
Base class for PDF Merger Pro integration tests.

This module provides common setup, teardown, and utilities for integration tests
that test how different components work together.
"""

import os
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any
from unittest.mock import patch, MagicMock

import pytest

from app.managers.config_manager import ConfigManager
from app.managers.performance_monitor import get_performance_monitor


class BaseIntegrationTest:
    """Base class providing common setup and utilities for integration tests."""

    @pytest.fixture(autouse=True)
    def setup_integration_test(self):
        """Setup that runs before each integration test."""
        # Create temporary directory for the test
        self.temp_dir = Path(tempfile.mkdtemp(prefix="pdf_merger_integration_"))

        # Create test configuration path
        self.config_path = self.temp_dir / "test_config.json"

        # Store original working directory
        self.original_cwd = os.getcwd()

        # Setup test data directory
        self.test_data_dir = self.temp_dir / "test_data"
        self.test_data_dir.mkdir()

        # Create output directory
        self.output_dir = self.temp_dir / "output"
        self.output_dir.mkdir()

        # Initialize performance monitor
        self.perf_monitor = get_performance_monitor()

        yield

        # Cleanup after test
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def create_test_config_manager(self) -> ConfigManager:
        """Create a ConfigManager instance for testing."""
        return ConfigManager(self.config_path)

    def create_test_pdf(self, filename: str, content: str = "Test PDF content") -> Path:
        """Create a test PDF file for integration tests."""
        pdf_path = self.test_data_dir / filename

        # For integration tests, we'll create a mock PDF structure
        # In a real scenario, you might use libraries like reportlab to create actual PDFs
        pdf_path.write_text(f"Mock PDF: {content}")

        return pdf_path

    def create_test_word_doc(self, filename: str, content: str = "Test Word content") -> Path:
        """Create a test Word document for integration tests."""
        doc_path = self.test_data_dir / filename
        doc_path.write_text(f"Mock Word Document: {content}")
        return doc_path

    def create_test_epub(self, filename: str, content: str = "Test EPUB content") -> Path:
        """Create a test EPUB file for integration tests."""
        epub_path = self.test_data_dir / filename
        epub_path.write_text(f"Mock EPUB: {content}")
        return epub_path

    def create_test_archive(self, filename: str, files: List[Path]) -> Path:
        """Create a test archive containing the specified files."""
        import zipfile

        archive_path = self.test_data_dir / filename
        with zipfile.ZipFile(archive_path, 'w') as zf:
            for file_path in files:
                if file_path.exists():
                    zf.write(file_path, file_path.name)

        return archive_path

    def mock_file_operations(self):
        """Context manager to mock file operations for integration tests."""
        return patch.multiple(
            'app.file_operations',
            process_add_files_task=MagicMock(return_value=("success", [])),
            validate_file=MagicMock(return_value=True)
        )

    def mock_background_task(self):
        """Context manager to mock background task operations."""
        return patch('app.background_task.BackgroundTask.start')

    def mock_tkinter(self):
        """Context manager to mock Tkinter components."""
        class MockTkinterContext:
            def __init__(self):
                self.mock_tk = MagicMock()
                self.mock_tk_instance = MagicMock()
                self.mock_frame = MagicMock()
                self.mock_label = MagicMock()
                self.mock_string_var = MagicMock()

            def __enter__(self):
                # Configure basic mock behavior
                self.mock_tk.return_value = self.mock_tk_instance

                # Mock StringVar to return a mock with get/set methods
                def create_string_var(value=""):
                    mock_var = MagicMock()
                    current_value = [value]  # Use list to make it mutable

                    def get():
                        return current_value[0]

                    def set(new_value):
                        current_value[0] = new_value

                    def cget(key):
                        if key == 'text':
                            return current_value[0]
                        return current_value[0]

                    mock_var.get = get
                    mock_var.set = set
                    mock_var.cget = cget

                    return mock_var

                self.mock_string_var.side_effect = create_string_var

                # Mock Label to support configure and cget
                def create_label():
                    mock_label = MagicMock()
                    label_text = [""]  # Use list to make it mutable

                    def configure(**kwargs):
                        if 'text' in kwargs:
                            label_text[0] = kwargs['text']

                    def cget(key):
                        if key == 'text':
                            return label_text[0]
                        return ""

                    mock_label.configure = configure
                    mock_label.cget = cget

                    return mock_label

                self.mock_label.side_effect = create_label

                return {
                    'tk': self.mock_tk,
                    'tk_instance': self.mock_tk_instance,
                    'frame': self.mock_frame,
                    'label': self.mock_label,
                    'string_var': self.mock_string_var
                }

            def __exit__(self, exc_type, exc_val, exc_tb):
                pass

        return MockTkinterContext()

    def create_mock_app_core(self, config_manager):
        """Create a mock app_core for FileOperations testing."""
        mock_app_core = MagicMock()
        mock_app_core.app = MagicMock()
        mock_app_core.app.config_manager = config_manager
        mock_app_core.app.root = MagicMock()
        mock_app_core.app.root.title = MagicMock()
        return mock_app_core

    def create_mock_file_details(self, file_path: Path, pages: int = 5) -> Dict[str, Any]:
        """Create mock file details for testing."""
        return {
            'filepath': str(file_path),
            'filename': file_path.name,
            'selected_pages': list(range(pages)),
            'page_count': pages,
            'file_type': 'pdf',
            'file_size': 1024000  # 1MB mock size
        }

    def assert_config_persisted(self, manager: ConfigManager, expected_values: Dict[str, Any]):
        """Assert that configuration values were properly persisted."""
        # Save config
        manager.save_config()

        # Create new manager instance to load from file
        new_manager = ConfigManager(manager.config_path)

        # Verify values match
        for key, expected_value in expected_values.items():
            assert new_manager.config[key] == expected_value, f"Config value {key} not persisted correctly"

    def assert_performance_logged(self, operation_name: str):
        """Assert that performance was logged for an operation."""
        # This would check if performance monitoring logged the operation
        # In a real implementation, you might check log files or mock loggers
        pass

    def simulate_user_workflow(self, config_manager: ConfigManager, workflow_steps: List[Dict[str, Any]]):
        """Simulate a user workflow with the given steps."""
        results = []

        for step in workflow_steps:
            step_type = step.get('type')
            step_data = step.get('data', {})

            if step_type == 'add_recent_directory':
                with patch('os.path.isdir', return_value=True):
                    config_manager.add_recent_directory(step_data['path'])
                results.append(f"Added directory: {step_data['path']}")

            elif step_type == 'save_profile':
                config_manager.save_profile(
                    step_data['name'],
                    step_data.get('files', [])
                )
                results.append(f"Saved profile: {step_data['name']}")

            elif step_type == 'load_profile':
                profile = config_manager.get_profile(step_data['name'])
                results.append(f"Loaded profile: {profile}")

            elif step_type == 'delete_profile':
                success = config_manager.delete_profile(step_data['name'])
                results.append(f"Deleted profile: {step_data['name']} - {success}")

            elif step_type == 'save_window_state':
                config_manager.save_window_state(
                    step_data.get('geometry', '1200x800+100+100'),
                    step_data.get('sash_positions', {})
                )
                results.append("Saved window state")

        return results

    def verify_workflow_results(self, results: List[str], expected_count: int):
        """Verify that workflow produced expected results."""
        assert len(results) == expected_count, f"Expected {expected_count} results, got {len(results)}"
        return results
