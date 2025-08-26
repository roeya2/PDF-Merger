"""
Unit tests for the constants module.
"""

import os
from pathlib import Path
import pytest

from app.utils.constants import (
    # Application constants
    APP_NAME, APP_VERSION, LOGGER_NAME,

    # Configuration constants
    DEFAULT_CONFIG_FILENAME, DEFAULT_OUTPUT_FILENAME, MAX_RECENT_DIRS,
    DEFAULT_COMPRESSION, DEFAULT_PRESERVE_BOOKMARKS, DEFAULT_PASSWORD_PROTECT,
    DEFAULT_COLOR_MODE, DEFAULT_DPI, DEFAULT_LOG_OUTPUT, DEFAULT_LOG_LEVEL,
    DEFAULT_LOG_FILE_PATH, PROFILE_LIST_KEY, WINDOW_GEOMETRY_KEY, PANEDWINDOW_SASH_KEY,

    # UI/Preview constants
    THUMBNAIL_SIZE, MIN_ZOOM, MAX_ZOOM, ZOOM_STEP_FACTOR,
    CANVAS_RESIZE_DELAY, PREVIEW_LOAD_DELAY, PREVIEW_NO_DOC_MSG,
    PREVIEW_NO_FILES_MSG, PREVIEW_LOADING_MSG, PREVIEW_NO_PAGES_MSG,
    PREVIEW_ERROR_MSG, PREVIEW_IMAGE_ERROR_MSG, PREVIEW_NO_PREVIEW_MSG,

    # Zoom constants
    DEFAULT_ZOOM_STEP, MIN_ZOOM_FACTOR, MAX_ZOOM_FACTOR,

    # Window and dialog dimensions
    DEFAULT_WINDOW_WIDTH, DEFAULT_WINDOW_HEIGHT, MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT,
    DELETE_PROFILE_DIALOG_WIDTH, DELETE_PROFILE_DIALOG_HEIGHT,

    # Font specifications
    DEFAULT_FONT_FAMILY, HEADER_FONT_SIZE, TITLE_FONT_SIZE,
    ACTION_BUTTON_FONT_SIZE, FALLBACK_FONT_SIZE,

    # UI spacing and padding
    MAIN_FRAME_PADDING, HEADER_BOTTOM_PADDING, LOWER_FRAME_TOP_PADDING,
    PANEL_HORIZONTAL_PADDING, STATUS_BAR_TOP_PADDING, TOOLTIP_FRAME_PADDING,
    TOOLTIP_LABEL_PADDING, SEARCH_LABEL_RIGHT_PADDING, VERSION_LABEL_LEFT_PADDING,
    VERSION_LABEL_TOP_PADDING, FILE_LIST_RIGHT_PADDING, PREVIEW_LEFT_PADDING,
    OUTPUT_PANEL_RIGHT_PADDING, ACTION_PANEL_LEFT_PADDING, BUTTON_FRAME_PADDING,
    BUTTON_HORIZONTAL_PADDING, DIALOG_VERTICAL_PADDING, DIALOG_HORIZONTAL_PADDING,

    # Colors
    TOOLTIP_BACKGROUND, TOOLTIP_FOREGROUND, VERSION_LABEL_COLOR, ERROR_TEXT_COLOR,

    # Task queue and timing
    TASK_QUEUE_CHECK_INTERVAL,

    # Initial values
    DEFAULT_ZOOM_DISPLAY_FACTOR, DEFAULT_PROGRESS_VALUE, DEFAULT_CURRENT_PAGE,

    # Merge task constants
    MERGE_PROGRESS_FILE_WEIGHT, MERGE_PROGRESS_FINALIZE_WEIGHT, VALIDATION_REPORT_MAX_ISSUES,

    # File type constants
    PDF_FILETYPE, DOCX_FILETYPE, DOC_FILETYPE, WORD_FILETYPES,
    EPUB_FILETYPE, EBOOK_FILETYPES, JSON_FILETYPE, ZIP_FILETYPE,
    RAR_FILETYPE, ARCHIVE_FILETYPES, ALL_FILES_FILETYPE,

    # Paths
    DEFAULT_CONFIG_PATH, DEFAULT_LOG_PATH,

    # Status messages
    STATUS_PREVIEW_NO_DOC_SELECTED, STATUS_PREVIEW_NO_FILES, STATUS_PREVIEW_LOADING,
    STATUS_PREVIEW_GENERATING, STATUS_PREVIEW_NO_PAGE, STATUS_PREVIEW_READY,
    STATUS_PREVIEW_ERROR_LOADING, STATUS_PREVIEW_ERROR, STATUS_PREVIEW_IMAGE_ERROR,
    STATUS_PREVIEW_NO_PREVIEW, STATUS_READY, STATUS_NO_FILES, STATUS_FILES_LOADED,
    STATUS_ADDED_FILES, STATUS_NO_VALID_ADDED, STATUS_FILE_LIST_SAVED,
    STATUS_FILE_LIST_LOADED, STATUS_VALIDATING_FILE, STATUS_VALIDATION_COMPLETE,
    STATUS_VALIDATION_ISSUES, STATUS_REMOVED_FILES, STATUS_LIST_CLEARED,
    STATUS_PROFILE_SAVED, STATUS_PROFILE_LOADED, STATUS_PROFILE_DELETED,
    STATUS_MERGE_STARTING, STATUS_MERGE_APPENDING, STATUS_MERGE_APPENDING_PAGES,
    STATUS_MERGE_FINALIZING, STATUS_MERGE_WRITING, STATUS_MERGE_MOVING,
    STATUS_MERGE_SUCCESS, STATUS_OUTPUT_SET, STATUS_EXTRACTION_STARTING,
    STATUS_ARCHIVE_PROCESSED_NO_PDFS, STATUS_ARCHIVE_ERROR,

    # Word processing status
    STATUS_CONVERTING_WORD, STATUS_WORD_CONVERTED, STATUS_WORD_CONVERSION_ERROR,
    STATUS_WORD_SUPPORT_MISSING,

    # EPUB processing status
    STATUS_CONVERTING_EPUB, STATUS_EPUB_CONVERTED, STATUS_EPUB_CONVERSION_ERROR,
    STATUS_EPUB_SUPPORT_MISSING,

    # Additional status constants
    STATUS_MERGING, STATUS_VALIDATING, STATUS_VALIDATION_COMPLETE_ISSUES,
    STATUS_VALIDATION_COMPLETE_SUCCESS,

    # UI/Page range constants
    STATUS_PAGE_RANGE_SET_SINGLE, STATUS_PAGE_RANGE_SET_MULTIPLE,
    STATUS_PAGE_RANGE_INVALID, STATUS_NO_FILES_SELECTED_FOR_PAGES,
    PAGE_RANGE_DIALOG_WIDTH, PAGE_RANGE_DIALOG_HEIGHT
)


class TestApplicationConstants:
    """Test application-level constants."""

    def test_app_constants(self):
        """Test basic application constants."""
        assert APP_NAME == "PDF Merger Pro"
        assert APP_VERSION == "2.4.0"
        assert LOGGER_NAME == "PDFMergerPro"

        # Ensure version follows semantic versioning format
        assert len(APP_VERSION.split('.')) >= 2
        assert all(part.isdigit() for part in APP_VERSION.split('.'))


class TestConfigurationConstants:
    """Test configuration-related constants."""

    def test_config_file_constants(self):
        """Test configuration file constants."""
        assert DEFAULT_CONFIG_FILENAME == "merge_config.json"
        assert DEFAULT_OUTPUT_FILENAME == "merged_output.pdf"
        assert MAX_RECENT_DIRS == 10
        assert MAX_RECENT_DIRS > 0

    def test_default_values(self):
        """Test default configuration values."""
        assert DEFAULT_COMPRESSION == "normal"
        assert DEFAULT_PRESERVE_BOOKMARKS is True
        assert DEFAULT_PASSWORD_PROTECT is False
        assert DEFAULT_COLOR_MODE == "Colorful (Original)"
        assert DEFAULT_DPI == "Original"

    def test_log_constants(self):
        """Test logging-related constants."""
        assert DEFAULT_LOG_OUTPUT == "both"
        assert DEFAULT_LOG_LEVEL == "INFO"
        assert DEFAULT_LOG_FILE_PATH == "pdf_merger.log"

    def test_profile_constants(self):
        """Test profile-related constants."""
        assert PROFILE_LIST_KEY == "pdf_merger_pro_list"
        assert WINDOW_GEOMETRY_KEY == "window_geometry"
        assert PANEDWINDOW_SASH_KEY == "panedwindow_sash_positions"


class TestUIConstants:
    """Test UI-related constants."""

    def test_preview_constants(self):
        """Test preview-related constants."""
        assert THUMBNAIL_SIZE == (100, 140)
        assert len(THUMBNAIL_SIZE) == 2
        assert all(dim > 0 for dim in THUMBNAIL_SIZE)

        assert 0 < MIN_ZOOM < MAX_ZOOM
        assert MAX_ZOOM > 1.0
        assert ZOOM_STEP_FACTOR > 1.0

        assert CANVAS_RESIZE_DELAY > 0
        assert PREVIEW_LOAD_DELAY > 0

    def test_preview_messages(self):
        """Test preview message constants."""
        assert PREVIEW_NO_DOC_MSG
        assert PREVIEW_NO_FILES_MSG
        assert "Loading page" in PREVIEW_LOADING_MSG
        assert PREVIEW_NO_PAGES_MSG
        assert PREVIEW_ERROR_MSG
        assert PREVIEW_IMAGE_ERROR_MSG
        assert PREVIEW_NO_PREVIEW_MSG

    def test_zoom_constants(self):
        """Test zoom-related constants."""
        assert DEFAULT_ZOOM_STEP > 0
        assert MIN_ZOOM_FACTOR == MIN_ZOOM
        assert MAX_ZOOM_FACTOR == MAX_ZOOM

    def test_window_dimensions(self):
        """Test window dimension constants."""
        assert DEFAULT_WINDOW_WIDTH > MIN_WINDOW_WIDTH
        assert DEFAULT_WINDOW_HEIGHT > MIN_WINDOW_HEIGHT
        assert MIN_WINDOW_WIDTH > 0
        assert MIN_WINDOW_HEIGHT > 0

        assert DELETE_PROFILE_DIALOG_WIDTH > 0
        assert DELETE_PROFILE_DIALOG_HEIGHT > 0

    def test_font_constants(self):
        """Test font-related constants."""
        assert DEFAULT_FONT_FAMILY
        assert HEADER_FONT_SIZE > 0
        assert TITLE_FONT_SIZE > HEADER_FONT_SIZE
        assert ACTION_BUTTON_FONT_SIZE > 0
        assert FALLBACK_FONT_SIZE > 0

    def test_spacing_constants(self):
        """Test UI spacing and padding constants."""
        assert MAIN_FRAME_PADDING >= 0
        assert HEADER_BOTTOM_PADDING >= 0
        assert LOWER_FRAME_TOP_PADDING >= 0
        assert PANEL_HORIZONTAL_PADDING >= 0
        assert STATUS_BAR_TOP_PADDING >= 0

        # Test tuple constants
        assert isinstance(TOOLTIP_FRAME_PADDING, tuple)
        assert isinstance(TOOLTIP_LABEL_PADDING, tuple)
        assert all(p >= 0 for p in TOOLTIP_FRAME_PADDING)
        assert all(p >= 0 for p in TOOLTIP_LABEL_PADDING)

    def test_color_constants(self):
        """Test color-related constants."""
        assert TOOLTIP_BACKGROUND.startswith('#')
        assert TOOLTIP_FOREGROUND
        assert VERSION_LABEL_COLOR
        assert ERROR_TEXT_COLOR

    def test_timing_constants(self):
        """Test timing-related constants."""
        assert TASK_QUEUE_CHECK_INTERVAL > 0
        assert TASK_QUEUE_CHECK_INTERVAL <= 1000  # Reasonable upper bound


class TestInitialValues:
    """Test initial value constants."""

    def test_initial_values(self):
        """Test initial value constants."""
        assert 0.0 <= DEFAULT_ZOOM_DISPLAY_FACTOR <= 2.0
        assert DEFAULT_PROGRESS_VALUE == 0.0
        assert DEFAULT_CURRENT_PAGE == 0


class TestMergeTaskConstants:
    """Test merge task-related constants."""

    def test_merge_progress_constants(self):
        """Test merge progress weight constants."""
        assert MERGE_PROGRESS_FILE_WEIGHT > 0
        assert MERGE_PROGRESS_FINALIZE_WEIGHT > 0
        assert MERGE_PROGRESS_FILE_WEIGHT + MERGE_PROGRESS_FINALIZE_WEIGHT == 100

    def test_validation_constants(self):
        """Test validation-related constants."""
        assert VALIDATION_REPORT_MAX_ISSUES > 0
        assert VALIDATION_REPORT_MAX_ISSUES <= 50  # Reasonable upper bound


class TestFileTypeConstants:
    """Test file type constants."""

    def test_file_type_tuples(self):
        """Test file type tuple constants."""
        # Test PDF file type
        assert isinstance(PDF_FILETYPE, tuple)
        assert len(PDF_FILETYPE) == 2
        assert "PDF" in PDF_FILETYPE[0]
        assert "*.pdf" in PDF_FILETYPE[1]

        # Test Word file types
        assert isinstance(DOCX_FILETYPE, tuple)
        assert isinstance(DOC_FILETYPE, tuple)
        assert isinstance(WORD_FILETYPES, tuple)
        assert "*.docx" in DOCX_FILETYPE[1]
        assert "*.doc" in DOC_FILETYPE[1]
        assert "*.docx" in WORD_FILETYPES[1] and "*.doc" in WORD_FILETYPES[1]

        # Test EPUB file types
        assert isinstance(EPUB_FILETYPE, tuple)
        assert isinstance(EBOOK_FILETYPES, tuple)
        assert "*.epub" in EPUB_FILETYPE[1]
        assert "*.epub" in EBOOK_FILETYPES[1]

        # Test archive file types
        assert isinstance(ZIP_FILETYPE, tuple)
        assert isinstance(RAR_FILETYPE, tuple)
        assert isinstance(ARCHIVE_FILETYPES, tuple)
        assert "*.zip" in ZIP_FILETYPE[1]
        assert "*.rar" in RAR_FILETYPE[1]
        assert "*.zip" in ARCHIVE_FILETYPES[1] and "*.rar" in ARCHIVE_FILETYPES[1]

        # Test other file types
        assert isinstance(JSON_FILETYPE, tuple)
        assert isinstance(ALL_FILES_FILETYPE, tuple)
        assert "*.json" in JSON_FILETYPE[1]
        assert "*.*" in ALL_FILES_FILETYPE[1]


class TestPathConstants:
    """Test path-related constants."""

    def test_path_constants(self):
        """Test path constants."""
        assert isinstance(DEFAULT_CONFIG_PATH, Path)
        assert isinstance(DEFAULT_LOG_PATH, Path)
        assert str(DEFAULT_CONFIG_PATH) == DEFAULT_CONFIG_FILENAME
        assert str(DEFAULT_LOG_PATH) == DEFAULT_LOG_FILE_PATH


class TestStatusMessages:
    """Test status message constants."""

    def test_status_message_format(self):
        """Test that status messages are properly formatted strings."""
        status_messages = [
            STATUS_PREVIEW_NO_DOC_SELECTED, STATUS_PREVIEW_NO_FILES,
            STATUS_PREVIEW_LOADING, STATUS_PREVIEW_GENERATING,
            STATUS_PREVIEW_NO_PAGE, STATUS_PREVIEW_READY,
            STATUS_PREVIEW_ERROR_LOADING, STATUS_PREVIEW_ERROR,
            STATUS_PREVIEW_IMAGE_ERROR, STATUS_PREVIEW_NO_PREVIEW,
            STATUS_READY, STATUS_NO_FILES, STATUS_FILES_LOADED,
            STATUS_ADDED_FILES, STATUS_NO_VALID_ADDED,
            STATUS_FILE_LIST_SAVED, STATUS_FILE_LIST_LOADED,
            STATUS_VALIDATING_FILE, STATUS_VALIDATION_COMPLETE,
            STATUS_VALIDATION_ISSUES, STATUS_REMOVED_FILES,
            STATUS_LIST_CLEARED, STATUS_PROFILE_SAVED,
            STATUS_PROFILE_LOADED, STATUS_PROFILE_DELETED,
            STATUS_MERGE_STARTING, STATUS_MERGE_APPENDING,
            STATUS_MERGE_APPENDING_PAGES, STATUS_MERGE_FINALIZING,
            STATUS_MERGE_WRITING, STATUS_MERGE_MOVING,
            STATUS_MERGE_SUCCESS, STATUS_OUTPUT_SET,
            STATUS_EXTRACTION_STARTING, STATUS_ARCHIVE_PROCESSED_NO_PDFS,
            STATUS_ARCHIVE_ERROR, STATUS_CONVERTING_WORD,
            STATUS_WORD_CONVERTED, STATUS_WORD_CONVERSION_ERROR,
            STATUS_WORD_SUPPORT_MISSING, STATUS_CONVERTING_EPUB,
            STATUS_EPUB_CONVERTED, STATUS_EPUB_CONVERSION_ERROR,
            STATUS_EPUB_SUPPORT_MISSING, STATUS_MERGING,
            STATUS_VALIDATING, STATUS_VALIDATION_COMPLETE_ISSUES,
            STATUS_VALIDATION_COMPLETE_SUCCESS, STATUS_PAGE_RANGE_SET_SINGLE,
            STATUS_PAGE_RANGE_SET_MULTIPLE, STATUS_PAGE_RANGE_INVALID,
            STATUS_NO_FILES_SELECTED_FOR_PAGES
        ]

        for message in status_messages:
            assert isinstance(message, str)
            assert message.strip()  # Should not be empty
            assert not message.startswith(' ')
            assert not message.endswith(' ')

    def test_status_message_placeholders(self):
        """Test that status messages with placeholders are properly formatted."""
        # Messages with {} placeholders should be format strings
        formatted_messages = [
            STATUS_FILES_LOADED, STATUS_ADDED_FILES, STATUS_FILE_LIST_SAVED,
            STATUS_FILE_LIST_LOADED, STATUS_VALIDATING_FILE, STATUS_VALIDATION_ISSUES,
            STATUS_REMOVED_FILES, STATUS_PROFILE_SAVED, STATUS_PROFILE_LOADED,
            STATUS_PROFILE_DELETED, STATUS_MERGE_APPENDING, STATUS_MERGE_APPENDING_PAGES,
            STATUS_MERGE_SUCCESS, STATUS_OUTPUT_SET, STATUS_EXTRACTION_STARTING,
            STATUS_ARCHIVE_ERROR, STATUS_CONVERTING_WORD, STATUS_WORD_CONVERTED,
            STATUS_WORD_CONVERSION_ERROR, STATUS_CONVERTING_EPUB, STATUS_EPUB_CONVERTED,
            STATUS_EPUB_CONVERSION_ERROR, STATUS_MERGING, STATUS_VALIDATING,
            STATUS_VALIDATION_COMPLETE_ISSUES, STATUS_PAGE_RANGE_SET_MULTIPLE,
            STATUS_PREVIEW_LOADING, STATUS_PREVIEW_GENERATING, STATUS_PREVIEW_READY,
            STATUS_PREVIEW_ERROR_LOADING
        ]

        for message in formatted_messages:
            assert '{}' in message or '{:' in message, f"Message should have format placeholders: {message}"


class TestDialogConstants:
    """Test dialog-related constants."""

    def test_dialog_dimensions(self):
        """Test dialog dimension constants."""
        assert PAGE_RANGE_DIALOG_WIDTH > 0
        assert PAGE_RANGE_DIALOG_HEIGHT > 0
        assert PAGE_RANGE_DIALOG_WIDTH >= 200  # Minimum reasonable width
        assert PAGE_RANGE_DIALOG_HEIGHT >= 150  # Minimum reasonable height


class TestConstantsConsistency:
    """Test consistency across related constants."""

    def test_zoom_range_consistency(self):
        """Test zoom range constants are consistent."""
        assert MIN_ZOOM == MIN_ZOOM_FACTOR
        assert MAX_ZOOM == MAX_ZOOM_FACTOR

    def test_file_type_consistency(self):
        """Test file type constants are consistent."""
        # Word file types should include both .docx and .doc
        assert "*.docx" in WORD_FILETYPES[1]
        assert "*.doc" in WORD_FILETYPES[1]

        # Archive file types should include both .zip and .rar
        assert "*.zip" in ARCHIVE_FILETYPES[1]
        assert "*.rar" in ARCHIVE_FILETYPES[1]

    def test_status_message_consistency(self):
        """Test status message constants are consistent."""
        # Preview status messages should be consistent
        assert STATUS_PREVIEW_LOADING == STATUS_PREVIEW_LOADING
        assert STATUS_VALIDATION_COMPLETE == STATUS_VALIDATION_COMPLETE_SUCCESS
        assert STATUS_VALIDATION_ISSUES == STATUS_VALIDATION_COMPLETE_ISSUES


# Integration test for constants module
class TestConstantsIntegration:
    """Integration tests for constants module."""

    def test_all_constants_defined(self):
        """Test that all expected constants are defined."""
        # This test ensures we don't accidentally remove constants
        expected_constants = [
            'APP_NAME', 'APP_VERSION', 'LOGGER_NAME',
            'DEFAULT_CONFIG_FILENAME', 'DEFAULT_OUTPUT_FILENAME',
            'THUMBNAIL_SIZE', 'MIN_ZOOM', 'MAX_ZOOM',
            'PDF_FILETYPE', 'ALL_FILES_FILETYPE',
            'STATUS_READY', 'STATUS_NO_FILES',
            'DEFAULT_CONFIG_PATH', 'DEFAULT_LOG_PATH'
        ]

        # Import all constants from the module
        import app.utils.constants as constants_module

        for const_name in expected_constants:
            assert hasattr(constants_module, const_name), f"Missing constant: {const_name}"

    def test_constants_types(self):
        """Test that constants have expected types."""
        # String constants
        assert isinstance(APP_NAME, str)
        assert isinstance(APP_VERSION, str)
        assert isinstance(DEFAULT_CONFIG_FILENAME, str)

        # Boolean constants
        assert isinstance(DEFAULT_PRESERVE_BOOKMARKS, bool)
        assert isinstance(DEFAULT_PASSWORD_PROTECT, bool)

        # Numeric constants
        assert isinstance(MAX_RECENT_DIRS, int)
        assert isinstance(MIN_ZOOM, (int, float))
        assert isinstance(MAX_ZOOM, (int, float))

        # Tuple constants
        assert isinstance(THUMBNAIL_SIZE, tuple)
        assert isinstance(PDF_FILETYPE, tuple)

        # Path constants
        assert isinstance(DEFAULT_CONFIG_PATH, Path)
        assert isinstance(DEFAULT_LOG_PATH, Path)
