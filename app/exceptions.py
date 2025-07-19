"""
Custom exception classes for the PDF Merger Pro application.
"""

class PDFMergerError(Exception):
    """Base exception class for all application-specific errors."""
    pass

class FileHandlingError(PDFMergerError):
    """Exception raised for errors related to file operations."""
    pass

class MergeError(PDFMergerError):
    """Exception raised for errors during the PDF merging process."""
    pass

class ValidationError(PDFMergerError):
    """Exception raised for errors during file validation."""
    pass

class CorruptFileError(FileHandlingError):
    """Exception raised for errors related to corrupt files."""
    pass

class PasswordProtectedError(FileHandlingError):
    """Exception raised when a file is password protected and no password is provided."""
    pass
