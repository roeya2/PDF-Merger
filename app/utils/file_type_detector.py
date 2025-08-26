"""
File Type Detection System for PDF Merger Pro

This module provides intelligent file type detection and validation,
supporting content-based detection beyond simple extension checking.
"""

import os
import mimetypes
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union, Any
try:
    import magic  # python-magic library for content-based detection
    MAGIC_AVAILABLE = True
except ImportError:
    magic = None
    MAGIC_AVAILABLE = False

from .constants import (
    PDF_EXTENSION, DOCX_EXTENSION, DOC_EXTENSION, EPUB_EXTENSION,
    ZIP_EXTENSION, RAR_EXTENSION,
    PDF_FILETYPE, DOCX_FILETYPE, DOC_FILETYPE, WORD_FILETYPES,
    EPUB_FILETYPE, ZIP_FILETYPE, RAR_FILETYPE, ARCHIVE_FILETYPES,
    ALL_FILES_FILETYPE,
)


class FileTypeDetector:
    """Intelligent file type detection and validation system."""

    # MIME type mappings
    MIME_TYPE_MAPPING = {
        'application/pdf': 'pdf',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'docx',
        'application/msword': 'doc',
        'application/epub+zip': 'epub',
        'application/zip': 'zip',
        'application/x-rar': 'rar',
        'application/x-tar': 'tar',
        'application/gzip': 'gzip',
    }

    # File signatures (magic bytes) for content-based detection
    FILE_SIGNATURES = {
        'pdf': [b'%PDF-'],
        'docx': [b'PK\x03\x04', b'PK\x05\x06', b'PK\x07\x08'],  # ZIP-based
        'epub': [b'PK\x03\x04', b'PK\x05\x06', b'PK\x07\x08'],   # ZIP-based
        'zip': [b'PK\x03\x04', b'PK\x05\x06', b'PK\x07\x08'],
        'rar': [b'Rar!', b'RE~^'],
    }

    # Supported file types with their properties
    SUPPORTED_TYPES = {
        'pdf': {
            'extensions': [PDF_EXTENSION],
            'description': 'PDF Document',
            'category': 'document',
            'can_merge': True,
            'can_preview': True,
            'requires_conversion': False,
        },
        'docx': {
            'extensions': [DOCX_EXTENSION],
            'description': 'Word Document (DOCX)',
            'category': 'document',
            'can_merge': True,
            'can_preview': False,
            'requires_conversion': True,
            'converter': 'docx2pdf',
        },
        'doc': {
            'extensions': [DOC_EXTENSION],
            'description': 'Word Document (DOC)',
            'category': 'document',
            'can_merge': True,
            'can_preview': False,
            'requires_conversion': True,
            'converter': 'docx2pdf',
        },
        'epub': {
            'extensions': [EPUB_EXTENSION],
            'description': 'EPUB E-book',
            'category': 'ebook',
            'can_merge': True,
            'can_preview': False,
            'requires_conversion': True,
            'converter': 'ebooklib+weasyprint',
        },
        'zip': {
            'extensions': [ZIP_EXTENSION],
            'description': 'ZIP Archive',
            'category': 'archive',
            'can_merge': False,
            'can_preview': False,
            'requires_conversion': False,
            'extractor': 'zipfile',
        },
        'rar': {
            'extensions': [RAR_EXTENSION],
            'description': 'RAR Archive',
            'category': 'archive',
            'can_merge': False,
            'can_preview': False,
            'requires_conversion': False,
            'extractor': 'rarfile',
        },
    }

    def __init__(self):
        """Initialize the file type detector."""
        self._magic = None
        self._magic_available = self._initialize_magic()

    def _initialize_magic(self) -> bool:
        """Initialize the magic library for content-based detection."""
        if not MAGIC_AVAILABLE:
            return False

        try:
            self._magic = magic.Magic(mime=True)
            return True
        except (ImportError, AttributeError):
            try:
                self._magic = magic.open(magic.MAGIC_MIME)
                self._magic.load()
                return True
            except (ImportError, AttributeError):
                return False

    def detect_file_type(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Detect file type using multiple methods.

        Args:
            file_path: Path to the file

        Returns:
            Dictionary containing detection results
        """
        file_path = Path(file_path)

        if not file_path.exists():
            return {
                'detected_type': 'unknown',
                'confidence': 0,
                'error': 'file_not_found',
                'supported': False
            }

        result = {
            'file_path': str(file_path),
            'file_name': file_path.name,
            'file_size': file_path.stat().st_size,
            'extension': file_path.suffix.lower(),
            'detected_type': 'unknown',
            'confidence': 0,
            'method': 'unknown',
            'supported': False,
            'properties': {}
        }

        # Method 1: Extension-based detection
        extension_type = self._detect_by_extension(file_path)
        if extension_type:
            result.update({
                'detected_type': extension_type,
                'confidence': 0.5,
                'method': 'extension',
                'supported': extension_type in self.SUPPORTED_TYPES
            })

        # Method 2: MIME type detection (if available)
        mime_type = self._detect_by_mime(file_path)
        if mime_type:
            mime_detected_type = self.MIME_TYPE_MAPPING.get(mime_type, 'unknown')
            if mime_detected_type != 'unknown':
                result.update({
                    'detected_type': mime_detected_type,
                    'confidence': 0.8,
                    'method': 'mime_type',
                    'mime_type': mime_type,
                    'supported': mime_detected_type in self.SUPPORTED_TYPES
                })

        # Method 3: Content-based detection (highest priority)
        content_type = self._detect_by_content(file_path)
        if content_type:
            result.update({
                'detected_type': content_type,
                'confidence': 0.9,
                'method': 'content',
                'supported': content_type in self.SUPPORTED_TYPES
            })

        # Add type properties if supported
        if result['supported']:
            result['properties'] = self.SUPPORTED_TYPES[result['detected_type']]

        return result

    def _detect_by_extension(self, file_path: Path) -> Optional[str]:
        """Detect file type based on file extension."""
        extension = file_path.suffix.lower()

        for file_type, properties in self.SUPPORTED_TYPES.items():
            if extension in properties['extensions']:
                return file_type

        return None

    def _detect_by_mime(self, file_path: Path) -> Optional[str]:
        """Detect MIME type of file."""
        if not self._magic_available:
            return None

        try:
            return self._magic.from_file(str(file_path))
        except Exception:
            return None

    def _detect_by_content(self, file_path: Path) -> Optional[str]:
        """Detect file type based on content signatures."""
        try:
            with open(file_path, 'rb') as f:
                # Read first 512 bytes for signature detection
                header = f.read(512)

            # Special handling for EPUB first (before general ZIP detection)
            if self._is_epub(header):
                return 'epub'

            # Check file signatures in order of specificity
            # Start with most specific signatures first
            signature_order = ['pdf', 'rar', 'docx', 'epub', 'zip']

            for file_type in signature_order:
                if file_type in self.FILE_SIGNATURES:
                    signatures = self.FILE_SIGNATURES[file_type]
                    for signature in signatures:
                        if header.startswith(signature):
                            # For ZIP-based formats, we need to be more careful
                            if file_type == 'docx' and header.startswith(b'PK'):
                                # Check if this might be a different ZIP-based format
                                if self._is_epub(header):
                                    return 'epub'
                                # If extension suggests ZIP, return zip instead of docx
                                if file_path.suffix.lower() == '.zip':
                                    return 'zip'
                                # Otherwise, assume it's a DOCX file
                                return 'docx'
                            return file_type

        except (IOError, OSError):
            return None

        return None

    def _is_epub(self, header: bytes) -> bool:
        """Check if file is an EPUB based on content."""
        # EPUB files are ZIP files with specific content structure
        if not header.startswith(b'PK'):
            return False

        # Check for EPUB-specific files within the ZIP structure
        # This is a simplified check - in practice, you'd need to parse the ZIP
        return b'mimetype' in header or b'META-INF' in header

    def get_supported_files_in_directory(self, directory: Union[str, Path],
                                       recursive: bool = False) -> List[Dict[str, Any]]:
        """
        Get all supported files in a directory.

        Args:
            directory: Directory path
            recursive: Whether to search recursively

        Returns:
            List of file detection results
        """
        directory = Path(directory)
        supported_files = []

        if not directory.exists() or not directory.is_dir():
            return supported_files

        pattern = '**/*' if recursive else '*'

        for file_path in directory.glob(pattern):
            if file_path.is_file():
                detection_result = self.detect_file_type(file_path)
                if detection_result['supported']:
                    supported_files.append(detection_result)

        return supported_files

    def validate_file_for_merge(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Validate a file for merge operations.

        Args:
            file_path: Path to the file

        Returns:
            Validation result dictionary
        """
        detection = self.detect_file_type(file_path)

        result = {
            'valid': False,
            'reason': 'unknown_error',
            'file_info': detection
        }

        if not detection['supported']:
            result['reason'] = 'unsupported_file_type'
            return result

        file_type = detection['detected_type']
        properties = detection['properties']

        if not properties.get('can_merge', False):
            result['reason'] = 'cannot_merge'
            return result

        # Check file size (basic validation)
        if detection['file_size'] == 0:
            result['reason'] = 'empty_file'
            return result

        # Additional validation based on file type
        if file_type == 'pdf':
            if not self._validate_pdf(file_path):
                result['reason'] = 'invalid_pdf'
                return result

        result['valid'] = True
        result['reason'] = 'valid'
        return result

    def _validate_pdf(self, file_path: Path) -> bool:
        """Basic PDF validation."""
        try:
            # Try to read the file as a PDF
            with open(file_path, 'rb') as f:
                header = f.read(8)

            # Check PDF header
            if not header.startswith(b'%PDF-'):
                return False

            # Check for basic PDF structure
            with open(file_path, 'rb') as f:
                content = f.read()
                return b'%%EOF' in content

        except Exception:
            return False

    def get_file_type_display_info(self, file_path: Union[str, Path]) -> Dict[str, str]:
        """
        Get display information for a file type.

        Args:
            file_path: Path to the file

        Returns:
            Dictionary with display information
        """
        detection = self.detect_file_type(file_path)

        if not detection['supported']:
            return {
                'icon': '❓',
                'description': 'Unsupported file',
                'category': 'unknown'
            }

        file_type = detection['detected_type']
        properties = detection['properties']

        # Get appropriate icon
        from .icons import get_icon_manager
        icon_manager = get_icon_manager()

        icon_map = {
            'pdf': 'pdf',
            'docx': 'word',
            'doc': 'word',
            'epub': 'epub',
            'zip': 'archive',
            'rar': 'archive',
        }

        icon_name = icon_map.get(file_type, 'add_file')
        icon = icon_manager.get_icon(icon_name)

        return {
            'icon': icon,
            'description': properties.get('description', 'Unknown'),
            'category': properties.get('category', 'unknown'),
            'requires_conversion': properties.get('requires_conversion', False),
            'can_preview': properties.get('can_preview', False),
        }

    def batch_detect_files(self, file_paths: List[Union[str, Path]]) -> List[Dict[str, Any]]:
        """
        Detect file types for multiple files.

        Args:
            file_paths: List of file paths

        Returns:
            List of detection results
        """
        results = []
        for file_path in file_paths:
            results.append(self.detect_file_type(file_path))
        return results


# Global detector instance
_detector_instance: Optional[FileTypeDetector] = None


def get_file_type_detector() -> FileTypeDetector:
    """Get the global file type detector instance."""
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = FileTypeDetector()
    return _detector_instance


def detect_file_type(file_path: Union[str, Path]) -> Dict[str, Any]:
    """Convenience function to detect file type."""
    return get_file_type_detector().detect_file_type(file_path)


def validate_file_for_merge(file_path: Union[str, Path]) -> Dict[str, Any]:
    """Convenience function to validate file for merge."""
    return get_file_type_detector().validate_file_for_merge(file_path)
