"""
Enhanced Error Handling System for PDF Merger Pro

This module provides comprehensive error handling with specific error messages,
suggestions for resolution, and user-friendly error reporting.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime

from .constants import (
    # Error messages with suggestions
    ERROR_FILE_NOT_FOUND, ERROR_FILE_NOT_FOUND_SUGGESTION,
    ERROR_ENCRYPTED_PASSWORD_PROTECTED, ERROR_ENCRYPTED_SUGGESTION,
    ERROR_NO_PAGES_FOUND, ERROR_NO_PAGES_SUGGESTION,
    ERROR_CORRUPTED_FILE, ERROR_CORRUPTED_SUGGESTION,
    ERROR_PERMISSION_DENIED, ERROR_PERMISSION_SUGGESTION,
    ERROR_UNSUPPORTED_FILE_TYPE, ERROR_UNSUPPORTED_SUGGESTION,
    ERROR_WORD_CONVERSION_FAILED, ERROR_WORD_CONVERSION_SUGGESTION,
    ERROR_EPUB_CONVERSION_FAILED, ERROR_EPUB_CONVERSION_SUGGESTION,
    ERROR_ARCHIVE_EXTRACTION_FAILED, ERROR_ARCHIVE_EXTRACTION_SUGGESTION,
    ERROR_OUTPUT_PATH_INVALID, ERROR_OUTPUT_PATH_SUGGESTION,
    ERROR_MERGE_FAILED_GENERAL, ERROR_MERGE_FAILED_SUGGESTION,
    ERROR_MEMORY_INSUFFICIENT, ERROR_MEMORY_SUGGESTION,

    # Status messages
    STATUS_VALIDATION_ISSUES, STATUS_VALIDATION_COMPLETE,

    # Logger
    LOGGER_NAME,
)


class AppError(Exception):
    """Base exception class for application-specific errors."""

    def __init__(self, message: str, error_code: str = "unknown_error",
                 suggestion: str = "", details: Optional[Dict[str, Any]] = None):
        """
        Initialize application error.

        Args:
            message: Error message
            error_code: Error code for categorization
            suggestion: Suggested solution
            details: Additional error details
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.suggestion = suggestion
        self.details = details or {}
        self.timestamp = datetime.now()


class FileProcessingError(AppError):
    """Error related to file processing operations."""
    pass


class ValidationError(AppError):
    """Error related to file validation."""
    pass


class ConversionError(AppError):
    """Error related to file conversion operations."""
    pass


class MergeError(AppError):
    """Error related to PDF merging operations."""
    pass


class ConfigurationError(AppError):
    """Error related to configuration issues."""
    pass


class ErrorHandler:
    """Comprehensive error handling and reporting system."""

    # Error code to message mapping
    ERROR_MESSAGES = {
        # File-related errors
        "file_not_found": (ERROR_FILE_NOT_FOUND, ERROR_FILE_NOT_FOUND_SUGGESTION),
        "file_encrypted": (ERROR_ENCRYPTED_PASSWORD_PROTECTED, ERROR_ENCRYPTED_SUGGESTION),
        "file_no_pages": (ERROR_NO_PAGES_FOUND, ERROR_NO_PAGES_SUGGESTION),
        "file_corrupted": (ERROR_CORRUPTED_FILE, ERROR_CORRUPTED_SUGGESTION),
        "permission_denied": (ERROR_PERMISSION_DENIED, ERROR_PERMISSION_SUGGESTION),
        "unsupported_file_type": (ERROR_UNSUPPORTED_FILE_TYPE, ERROR_UNSUPPORTED_SUGGESTION),

        # Conversion errors
        "word_conversion_failed": (ERROR_WORD_CONVERSION_FAILED, ERROR_WORD_CONVERSION_SUGGESTION),
        "epub_conversion_failed": (ERROR_EPUB_CONVERSION_FAILED, ERROR_EPUB_CONVERSION_SUGGESTION),

        # Archive errors
        "archive_extraction_failed": (ERROR_ARCHIVE_EXTRACTION_FAILED, ERROR_ARCHIVE_EXTRACTION_SUGGESTION),

        # Output errors
        "output_path_invalid": (ERROR_OUTPUT_PATH_INVALID, ERROR_OUTPUT_PATH_SUGGESTION),

        # Merge errors
        "merge_failed": (ERROR_MERGE_FAILED_GENERAL, ERROR_MERGE_FAILED_SUGGESTION),

        # System errors
        "memory_insufficient": (ERROR_MEMORY_INSUFFICIENT, ERROR_MEMORY_SUGGESTION),
        "disk_space_insufficient": ("Insufficient disk space", "Free up disk space or choose a different output location."),
        "network_error": ("Network error", "Check your internet connection and try again."),
    }

    def __init__(self):
        """Initialize the error handler."""
        self.logger = logging.getLogger(LOGGER_NAME)
        self.error_history: List[AppError] = []

    def handle_error(self, error: Exception, context: str = "",
                    show_dialog: bool = True, log_error: bool = True) -> AppError:
        """
        Handle an error with proper formatting and user feedback.

        Args:
            error: The exception that occurred
            context: Context where the error occurred
            show_dialog: Whether to show error dialog to user
            log_error: Whether to log the error

        Returns:
            Formatted AppError instance
        """
        # Convert to AppError if not already
        if isinstance(error, AppError):
            app_error = error
        else:
            app_error = self._classify_error(error, context)

        # Add to error history
        self.error_history.append(app_error)

        # Log the error
        if log_error:
            self._log_error(app_error, context)

        # Show user dialog if requested
        if show_dialog:
            self._show_error_dialog(app_error)

        return app_error

    def _classify_error(self, error: Exception, context: str) -> AppError:
        """
        Classify a generic exception into an appropriate AppError type.

        Args:
            error: The original exception
            context: Context where the error occurred

        Returns:
            Classified AppError instance
        """
        error_message = str(error)
        error_type = type(error).__name__

        # File-related errors
        if isinstance(error, FileNotFoundError) or "file not found" in error_message.lower() or "no such file" in error_message.lower():
            return FileProcessingError(
                ERROR_FILE_NOT_FOUND.format(filename="file"),
                "file_not_found",
                ERROR_FILE_NOT_FOUND_SUGGESTION
            )

        elif isinstance(error, PermissionError) or "permission denied" in error_message.lower() or "access denied" in error_message.lower():
            return FileProcessingError(
                ERROR_PERMISSION_DENIED.format(filename="file"),
                "permission_denied",
                ERROR_PERMISSION_SUGGESTION
            )

        elif "encrypted" in error_message.lower() or "password" in error_message.lower():
            return FileProcessingError(
                ERROR_ENCRYPTED_PASSWORD_PROTECTED.format(filename="file"),
                "file_encrypted",
                ERROR_ENCRYPTED_SUGGESTION
            )

        elif "no pages" in error_message.lower() or "empty" in error_message.lower():
            return FileProcessingError(
                ERROR_NO_PAGES_FOUND.format(filename="file"),
                "file_no_pages",
                ERROR_NO_PAGES_SUGGESTION
            )

        elif "corrupt" in error_message.lower() or "invalid" in error_message.lower():
            return FileProcessingError(
                ERROR_CORRUPTED_FILE.format(filename="file"),
                "file_corrupted",
                ERROR_CORRUPTED_SUGGESTION
            )

        elif "memory" in error_message.lower() or "out of memory" in error_message.lower():
            return AppError(
                ERROR_MEMORY_INSUFFICIENT,
                "memory_insufficient",
                ERROR_MEMORY_SUGGESTION
            )

        elif "disk" in error_message.lower() or "space" in error_message.lower():
            return AppError(
                "Insufficient disk space",
                "disk_space_insufficient",
                "Free up disk space or choose a different output location."
            )

        # Conversion-specific errors
        elif "docx2pdf" in error_message.lower() or "word" in context.lower():
            return ConversionError(
                ERROR_WORD_CONVERSION_FAILED.format(filename="file"),
                "word_conversion_failed",
                ERROR_WORD_CONVERSION_SUGGESTION
            )

        elif "ebooklib" in error_message.lower() or "weasyprint" in error_message.lower() or "epub" in context.lower():
            return ConversionError(
                ERROR_EPUB_CONVERSION_FAILED.format(filename="file"),
                "epub_conversion_failed",
                ERROR_EPUB_CONVERSION_SUGGESTION
            )

        # Archive errors
        elif "rar" in error_message.lower() or "zip" in error_message.lower():
            return FileProcessingError(
                ERROR_ARCHIVE_EXTRACTION_FAILED.format(filename="archive"),
                "archive_extraction_failed",
                ERROR_ARCHIVE_EXTRACTION_SUGGESTION
            )

        # Default error
        else:
            return AppError(
                f"An unexpected error occurred: {error_message}",
                "unknown_error",
                "Please check the log file for details or contact support if the problem persists."
            )

    def _log_error(self, error: AppError, context: str):
        """Log an error with appropriate level and details."""
        log_message = f"{context}: {error.message}" if context else error.message

        if error.error_code in ["file_not_found", "permission_denied", "unsupported_file_type"]:
            self.logger.warning(log_message)
        elif error.error_code in ["memory_insufficient", "disk_space_insufficient"]:
            self.logger.error(log_message)
        else:
            self.logger.error(log_message, exc_info=True)

        # Log additional details if available
        if error.details:
            self.logger.debug(f"Error details: {error.details}")

        if error.suggestion:
            self.logger.info(f"Suggestion: {error.suggestion}")

    def _show_error_dialog(self, error: AppError):
        """Show an error dialog to the user."""
        try:
            # Import here to avoid circular imports
            import tkinter.messagebox as messagebox
            from tkinter import Tk

            # Create a temporary root if needed
            root = Tk()
            root.withdraw()

            title = self._get_error_dialog_title(error.error_code)
            message = self._format_error_message(error)

            messagebox.showerror(title, message, parent=None)

            root.destroy()

        except Exception as e:
            # Fallback to console output if GUI fails
            print(f"ERROR: {error.message}")
            if error.suggestion:
                print(f"SUGGESTION: {error.suggestion}")

    def _get_error_dialog_title(self, error_code: str) -> str:
        """Get appropriate dialog title for error code."""
        title_map = {
            "file_not_found": "File Not Found",
            "file_encrypted": "File Protected",
            "file_no_pages": "Empty File",
            "file_corrupted": "File Error",
            "permission_denied": "Permission Error",
            "unsupported_file_type": "Unsupported File",
            "word_conversion_failed": "Conversion Error",
            "epub_conversion_failed": "Conversion Error",
            "archive_extraction_failed": "Archive Error",
            "output_path_invalid": "Output Error",
            "merge_failed": "Merge Error",
            "memory_insufficient": "Memory Error",
            "disk_space_insufficient": "Disk Space Error",
        }
        return title_map.get(error_code, "Error")

    def _format_error_message(self, error: AppError) -> str:
        """Format error message for display."""
        message_parts = [error.message]

        if error.suggestion:
            message_parts.extend(["", "Suggestion:", error.suggestion])

        if error.details:
            message_parts.extend(["", "Details:"])
            for key, value in error.details.items():
                message_parts.append(f"• {key}: {value}")

        return "\n".join(message_parts)

    def create_error_report(self, include_history: bool = True) -> str:
        """
        Create a comprehensive error report.

        Args:
            include_history: Whether to include error history

        Returns:
            Formatted error report
        """
        report_lines = [
            "PDF Merger Pro Error Report",
            "=" * 40,
            f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Python version: {sys.version}",
            f"Platform: {sys.platform}",
            "",
        ]

        if include_history and self.error_history:
            report_lines.extend([
                "Recent Errors:",
                "-" * 20,
            ])

            for i, error in enumerate(self.error_history[-10:], 1):  # Last 10 errors
                report_lines.extend([
                    f"{i}. {error.timestamp.strftime('%Y-%m-%d %H:%M:%S')}",
                    f"   Code: {error.error_code}",
                    f"   Message: {error.message}",
                    f"   Suggestion: {error.suggestion}",
                    "",
                ])

        return "\n".join(report_lines)

    def clear_error_history(self):
        """Clear the error history."""
        self.error_history.clear()

    def get_error_statistics(self) -> Dict[str, int]:
        """Get statistics about errors that have occurred."""
        stats = {}
        for error in self.error_history:
            stats[error.error_code] = stats.get(error.error_code, 0) + 1
        return stats

    def validate_file_operation(self, file_path: str, operation: str = "read") -> Optional[AppError]:
        """
        Validate a file operation before attempting it.

        Args:
            file_path: Path to the file
            operation: Type of operation ("read", "write")

        Returns:
            AppError if validation fails, None if successful
        """
        path = Path(file_path)

        # Check if path exists
        if operation == "read" and not path.exists():
            return FileProcessingError(
                ERROR_FILE_NOT_FOUND.format(filename=path.name),
                "file_not_found",
                ERROR_FILE_NOT_FOUND_SUGGESTION,
                {"file_path": str(path)}
            )

        # Check permissions
        if operation == "read" and not os.access(path, os.R_OK):
            return FileProcessingError(
                ERROR_PERMISSION_DENIED.format(filename=path.name),
                "permission_denied",
                ERROR_PERMISSION_SUGGESTION,
                {"file_path": str(path)}
            )

        if operation == "write":
            # Check if parent directory exists and is writable
            parent = path.parent
            if not parent.exists():
                try:
                    parent.mkdir(parents=True, exist_ok=True)
                except PermissionError:
                    return FileProcessingError(
                        ERROR_PERMISSION_DENIED.format(filename=str(parent)),
                        "permission_denied",
                        ERROR_PERMISSION_SUGGESTION,
                        {"file_path": str(parent)}
                    )

            # Check write permission more robustly
            try:
                # Try to create a temporary file to test write permission
                import tempfile
                with tempfile.NamedTemporaryFile(dir=str(parent), delete=True):
                    pass  # If we can create a temp file, we have write permission
            except (PermissionError, OSError):
                return FileProcessingError(
                    ERROR_PERMISSION_DENIED.format(filename=str(parent)),
                    "permission_denied",
                    ERROR_PERMISSION_SUGGESTION,
                    {"file_path": str(parent)}
                )

            # Also check with os.access as a fallback
            if not os.access(parent, os.W_OK):
                return FileProcessingError(
                    ERROR_PERMISSION_DENIED.format(filename=str(parent)),
                    "permission_denied",
                    ERROR_PERMISSION_SUGGESTION,
                    {"file_path": str(parent)}
                )

        return None


# Global error handler instance
_error_handler_instance: Optional[ErrorHandler] = None


def get_error_handler() -> ErrorHandler:
    """Get the global error handler instance."""
    global _error_handler_instance
    if _error_handler_instance is None:
        _error_handler_instance = ErrorHandler()
    return _error_handler_instance


def handle_error(error: Exception, context: str = "", **kwargs) -> AppError:
    """Convenience function to handle an error."""
    return get_error_handler().handle_error(error, context, **kwargs)


def validate_file_operation(file_path: str, operation: str = "read") -> Optional[AppError]:
    """Convenience function to validate file operations."""
    return get_error_handler().validate_file_operation(file_path, operation)
