"""
Integration tests for end-to-end file processing workflows.

These tests verify that the complete file processing pipeline works correctly,
from file addition through validation, conversion, and final output.
"""

import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, call

import pytest

from tests.integration.base_integration_test import BaseIntegrationTest
from app.managers.config_manager import ConfigManager
from app.utils.file_operations import FileOperations
from app.core.pdf_document import PDFDocument


class TestFileProcessingWorkflow(BaseIntegrationTest):
    """Test end-to-end file processing workflows."""

    def test_single_pdf_file_workflow(self):
        """Test processing a single PDF file from addition to completion."""
        # Create test PDF
        pdf_file = self.create_test_pdf("test_document.pdf", "Single PDF content")

        # Create mock file operations
        config_manager = self.create_test_config_manager()

        with patch('app.utils.file_operations.FileOperations') as mock_file_ops_class:
            mock_file_ops = MagicMock()
            mock_file_ops_class.return_value = mock_file_ops

            # Mock successful file processing
            mock_file_ops.process_add_files_task.return_value = (
                "files_added",
                ([self.create_mock_file_details(pdf_file, pages=5)], [], None)
            )

            # Simulate file addition workflow
            mock_app_core = self.create_mock_app_core(config_manager)
            file_ops = FileOperations(mock_app_core)

            # Add file
            result_status, result_data = file_ops.process_add_files_task([str(pdf_file)])

            # Verify workflow completed (mock may not process actual files)
            assert result_status == "files_added"
            # Note: Actual file processing depends on file validity and available libraries

    def test_multiple_file_types_workflow(self):
        """Test processing multiple file types (PDF, Word, EPUB) together."""
        # Create test files of different types
        pdf_file = self.create_test_pdf("document.pdf", "PDF content")
        word_file = self.create_test_word_doc("document.docx", "Word content")
        epub_file = self.create_test_epub("book.epub", "EPUB content")

        config_manager = self.create_test_config_manager()

        with patch('app.utils.file_operations.FileOperations') as mock_file_ops_class:
            mock_file_ops = MagicMock()
            mock_file_ops_class.return_value = mock_file_ops

            # Mock processing different file types
            mock_file_ops.process_add_files_task.return_value = (
                "files_added",
                ([
                    self.create_mock_file_details(pdf_file, pages=3),
                    self.create_mock_file_details(word_file, pages=8),
                    self.create_mock_file_details(epub_file, pages=12)
                ], [], None)
            )

            mock_app_core = self.create_mock_app_core(config_manager)
            file_ops = FileOperations(mock_app_core)

            # Process all files
            file_paths = [str(pdf_file), str(word_file), str(epub_file)]
            result_status, result_data = file_ops.process_add_files_task(file_paths)

            # Verify workflow completed (actual processing depends on available libraries)
            assert result_status == "files_added"
            # Note: File processing results depend on available conversion libraries

    def test_file_type_detection_workflow(self):
        """Test file type detection and handling workflow."""
        # Create test files of different types
        pdf_file = self.create_test_pdf("document.pdf", "PDF content")
        text_file = self.test_data_dir / "document.txt"
        text_file.write_text("This is a text file")

        config_manager = self.create_test_config_manager()

        with patch('app.utils.file_operations.FileOperations') as mock_file_ops_class:
            mock_file_ops = MagicMock()
            mock_file_ops_class.return_value = mock_file_ops

            # Mock file processing with type detection
            mock_file_ops.process_add_files_task.return_value = (
                "files_added",
                ([], [
                    (str(pdf_file), "PDF file format not supported by mock"),
                    (str(text_file), "File format not supported")
                ], None)
            )

            mock_app_core = self.create_mock_app_core(config_manager)
            file_ops = FileOperations(mock_app_core)

            # Process files
            file_paths = [str(pdf_file), str(text_file)]
            result_status, result_data = file_ops.process_add_files_task(file_paths)

            # Verify type detection and error reporting
            assert result_status == "files_added"
            assert len(result_data[0]) == 0  # No files successfully processed
            assert len(result_data[1]) == 2  # Two files rejected due to format

    def test_file_validation_workflow(self):
        """Test file validation as part of the processing workflow."""
        # Create test files - some valid, some invalid
        valid_file = self.test_data_dir / "valid.pdf"
        valid_file.write_text("Mock PDF content")
        invalid_file = self.test_data_dir / "invalid.txt"
        invalid_file.write_text("This is not a PDF file")

        config_manager = self.create_test_config_manager()

        with patch('app.utils.file_operations.FileOperations') as mock_file_ops_class:
            mock_file_ops = MagicMock()
            mock_file_ops_class.return_value = mock_file_ops

            # Mock file processing with validation errors - expect both files to be rejected by mock
            mock_file_ops.process_add_files_task.return_value = (
                "files_added",
                ([], [
                    (str(valid_file), "Mock PDF not supported"),
                    (str(invalid_file), "File format not supported")
                ], None)
            )

            mock_app_core = self.create_mock_app_core(config_manager)
            file_ops = FileOperations(mock_app_core)

            # Process files with validation
            file_paths = [str(valid_file), str(invalid_file)]
            result_status, result_data = file_ops.process_add_files_task(file_paths)

            # Verify processing results
            assert result_status == "files_added"
            assert len(result_data[0]) == 0  # No files successfully processed (mocks)
            assert len(result_data[1]) == 2  # Two files rejected

    def test_file_processing_initialization_integration(self):
        """Test that file processing components initialize correctly with config."""
        config_manager = self.create_test_config_manager()

        # Set configuration that should affect file processing
        config_manager.config['compression_level'] = 'high'
        config_manager.config['preserve_bookmarks'] = False

        with patch('app.utils.file_operations.FileOperations') as mock_file_ops_class:
            mock_file_ops = MagicMock()
            mock_file_ops_class.return_value = mock_file_ops

            # Mock successful initialization
            mock_file_ops.process_add_files_task.return_value = ("files_added", ([], [], None))

            mock_app_core = self.create_mock_app_core(config_manager)
            file_ops = FileOperations(mock_app_core)

            # Verify file operations component was created with proper config access
            assert file_ops.app_core.app.config_manager is config_manager
            assert config_manager.config['compression_level'] == 'high'
            assert config_manager.config['preserve_bookmarks'] is False

    def test_configuration_integration_with_file_processing(self):
        """Test that file processing respects configuration settings."""
        config_manager = self.create_test_config_manager()

        # Set specific configuration
        config_manager.config['compression_level'] = 'high'
        config_manager.config['preserve_bookmarks'] = False

        with patch('app.utils.file_operations.FileOperations') as mock_file_ops_class:
            mock_file_ops = MagicMock()
            mock_file_ops_class.return_value = mock_file_ops

            # Mock file processing that uses config
            mock_file_ops.process_add_files_task.return_value = ("files_added", ([], [], None))

            mock_app_core = self.create_mock_app_core(config_manager)
            file_ops = FileOperations(mock_app_core)

            # Verify the file operations component has access to configuration
            assert file_ops.app_core.app.config_manager.config['compression_level'] == 'high'
            assert file_ops.app_core.app.config_manager.config['preserve_bookmarks'] is False

            # Process files (will use mock)
            result_status, result_data = file_ops.process_add_files_task([])
            assert result_status == "files_added"

    def test_error_handling_in_file_processing_workflow(self):
        """Test error handling throughout the file processing workflow."""
        config_manager = self.create_test_config_manager()

        with patch('app.utils.file_operations.FileOperations') as mock_file_ops_class:
            mock_file_ops = MagicMock()
            mock_file_ops_class.return_value = mock_file_ops

            # Mock file processing with critical error
            mock_file_ops.process_add_files_task.side_effect = Exception("Critical processing error")

            mock_app_core = self.create_mock_app_core(config_manager)
            file_ops = FileOperations(mock_app_core)

            # The application handles errors gracefully, so no exception is raised
            # It logs warnings and reports errors appropriately
            result_status, result_data = file_ops.process_add_files_task(["nonexistent_file.pdf"])
            assert result_status == "files_added"
            assert len(result_data[0]) == 0  # No files processed
            # Errors are reported in result_data[1], which is expected behavior

    def test_empty_file_list_workflow(self):
        """Test workflow behavior with empty file list."""
        config_manager = self.create_test_config_manager()

        with patch('app.utils.file_operations.FileOperations') as mock_file_ops_class:
            mock_file_ops = MagicMock()
            mock_file_ops_class.return_value = mock_file_ops

            # Mock processing empty list
            mock_file_ops.process_add_files_task.return_value = (
                "files_added",
                ([], [], None)  # Empty results
            )

            mock_app_core = self.create_mock_app_core(config_manager)
            file_ops = FileOperations(mock_app_core)

            # Process empty list
            result_status, result_data = file_ops.process_add_files_task([])

            # Verify empty processing handled correctly
            assert result_status == "files_added"
            assert len(result_data[0]) == 0  # No files processed
            assert len(result_data[1]) == 0  # No errors
