"""
Metadata Manager for PDF Merger Pro

This module handles PDF metadata editing, validation, and management.
Supports editing title, author, subject, keywords, and other PDF properties.
"""

from typing import Dict, List, Any, Optional, Tuple
import logging
import re
from datetime import datetime

from ..utils.constants import (
    LOGGER_NAME, DEFAULT_METADATA, METADATA_MAX_LENGTH,
    STATUS_METADATA_SAVED, STATUS_METADATA_VALIDATION_ERROR
)


class MetadataValidator:
    """Validates PDF metadata fields."""

    # Patterns for validation
    EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    URL_PATTERN = r'^https?://(?:[-\w.])+(?:[:\d]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:#(?:\w*))*)?$'

    @staticmethod
    def validate_title(title: str) -> List[str]:
        """Validate title field."""
        errors = []

        if len(title) > METADATA_MAX_LENGTH['title']:
            errors.append(f"Title too long (max {METADATA_MAX_LENGTH['title']} characters)")

        # Check for excessive special characters
        special_chars = len(re.findall(r'[^\w\s]', title))
        if special_chars > len(title) * 0.5:  # More than 50% special characters
            errors.append("Title contains too many special characters")

        return errors

    @staticmethod
    def validate_author(author: str) -> List[str]:
        """Validate author field."""
        errors = []

        if len(author) > METADATA_MAX_LENGTH['author']:
            errors.append(f"Author too long (max {METADATA_MAX_LENGTH['author']} characters)")

        # Check for reasonable author name patterns
        if author and not re.match(r'^[\w\s.,\'"-]+$', author):
            errors.append("Author contains invalid characters")

        return errors

    @staticmethod
    def validate_subject(subject: str) -> List[str]:
        """Validate subject field."""
        errors = []

        if len(subject) > METADATA_MAX_LENGTH['subject']:
            errors.append(f"Subject too long (max {METADATA_MAX_LENGTH['subject']} characters)")

        # Check for reasonable content
        if not subject.strip():
            errors.append("Subject should not be empty")

        return errors

    @staticmethod
    def validate_keywords(keywords: str) -> List[str]:
        """Validate keywords field."""
        errors = []

        if len(keywords) > METADATA_MAX_LENGTH['keywords']:
            errors.append(f"Keywords too long (max {METADATA_MAX_LENGTH['keywords']} characters)")

        # Check for reasonable keyword format (comma-separated)
        if keywords:
            # Remove extra whitespace and check format
            cleaned = ' '.join(keywords.split())
            if len(cleaned) < len(keywords) * 0.8:  # Too much whitespace
                errors.append("Keywords contain excessive whitespace")

        return errors

    @staticmethod
    def validate_all(metadata: Dict[str, str]) -> Dict[str, List[str]]:
        """Validate all metadata fields."""
        return {
            'title': MetadataValidator.validate_title(metadata.get('title', '')),
            'author': MetadataValidator.validate_author(metadata.get('author', '')),
            'subject': MetadataValidator.validate_subject(metadata.get('subject', '')),
            'keywords': MetadataValidator.validate_keywords(metadata.get('keywords', ''))
        }

    @staticmethod
    def is_valid(metadata: Dict[str, str]) -> bool:
        """Check if all metadata is valid."""
        validation_results = MetadataValidator.validate_all(metadata)
        return all(len(errors) == 0 for errors in validation_results.values())


class MetadataManager:
    """Manages PDF metadata editing and validation."""

    def __init__(self):
        """Initialize the metadata manager."""
        self.logger = logging.getLogger(LOGGER_NAME)
        self.current_metadata: Dict[str, str] = DEFAULT_METADATA.copy()
        self.validator = MetadataValidator()

    def set_metadata(self, metadata: Dict[str, str]) -> bool:
        """
        Set metadata values.

        Args:
            metadata: Dictionary of metadata fields

        Returns:
            True if metadata was set successfully
        """
        # Validate metadata first
        if not self.validator.is_valid(metadata):
            validation_errors = self.validator.validate_all(metadata)
            error_messages = []
            for field, errors in validation_errors.items():
                if errors:
                    error_messages.extend([f"{field}: {error}" for error in errors])

            self.logger.warning(f"Metadata validation failed: {', '.join(error_messages)}")
            return False

        # Set metadata
        self.current_metadata.update(metadata)
        self.logger.info("Metadata updated successfully")
        return True

    def get_metadata(self) -> Dict[str, str]:
        """Get current metadata values."""
        return self.current_metadata.copy()

    def get_field(self, field_name: str) -> str:
        """Get a specific metadata field value."""
        return self.current_metadata.get(field_name, '')

    def set_field(self, field_name: str, value: str) -> bool:
        """
        Set a specific metadata field.

        Args:
            field_name: Name of the field to set
            value: Value to set

        Returns:
            True if field was set successfully
        """
        if field_name not in DEFAULT_METADATA:
            self.logger.warning(f"Unknown metadata field: {field_name}")
            return False

        # Validate the specific field
        validator_method = getattr(self.validator, f'validate_{field_name}', None)
        if validator_method:
            errors = validator_method(value)
            if errors:
                self.logger.warning(f"Field validation failed for {field_name}: {', '.join(errors)}")
                return False

        self.current_metadata[field_name] = value
        self.logger.debug(f"Metadata field '{field_name}' set to: {value}")
        return True

    def reset_to_defaults(self):
        """Reset metadata to default values."""
        self.current_metadata = DEFAULT_METADATA.copy()
        self.logger.info("Metadata reset to defaults")

    def clear_field(self, field_name: str):
        """Clear a specific metadata field."""
        if field_name in self.current_metadata:
            self.current_metadata[field_name] = ''
            self.logger.debug(f"Metadata field '{field_name}' cleared")

    def clear_all(self):
        """Clear all metadata fields (except creator/producer)."""
        for field in list(self.current_metadata.keys()):
            if field not in ['creator', 'producer']:
                self.current_metadata[field] = ''
        self.logger.info("All metadata fields cleared")

    def load_from_pdf(self, pdf_path: str) -> bool:
        """
        Load metadata from an existing PDF file.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            True if metadata was loaded successfully
        """
        try:
            # Import here to avoid circular imports
            from ..utils.common_imports import PdfReader

            with open(pdf_path, 'rb') as file:
                pdf = PdfReader(file)
                pdf_metadata = pdf.metadata

                if pdf_metadata:
                    # Extract metadata fields
                    metadata = {}

                    if pdf_metadata.title:
                        metadata['title'] = pdf_metadata.title
                    if pdf_metadata.author:
                        metadata['author'] = pdf_metadata.author
                    if pdf_metadata.subject:
                        metadata['subject'] = pdf_metadata.subject
                    if hasattr(pdf_metadata, 'keywords') and pdf_metadata.keywords:
                        metadata['keywords'] = pdf_metadata.keywords

                    # Keep creator/producer from defaults
                    metadata['creator'] = self.current_metadata.get('creator', DEFAULT_METADATA['creator'])
                    metadata['producer'] = self.current_metadata.get('producer', DEFAULT_METADATA['producer'])

                    self.current_metadata.update(metadata)
                    self.logger.info(f"Loaded metadata from PDF: {pdf_path}")
                    return True
                else:
                    self.logger.info(f"No metadata found in PDF: {pdf_path}")
                    return False

        except Exception as e:
            self.logger.error(f"Failed to load metadata from PDF {pdf_path}: {e}")
            return False

    def save_to_config(self, config_manager) -> bool:
        """
        Save current metadata to configuration.

        Args:
            config_manager: ConfigManager instance

        Returns:
            True if saved successfully
        """
        try:
            config_manager.update_config({'default_metadata': self.current_metadata})
            self.logger.info("Metadata saved to configuration")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save metadata to config: {e}")
            return False

    def load_from_config(self, config_manager) -> bool:
        """
        Load metadata from configuration.

        Args:
            config_manager: ConfigManager instance

        Returns:
            True if loaded successfully
        """
        try:
            saved_metadata = config_manager.config.get('default_metadata', {})
            if saved_metadata:
                self.current_metadata.update(saved_metadata)
                self.logger.info("Metadata loaded from configuration")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to load metadata from config: {e}")
            return False

    def get_field_info(self, field_name: str) -> Dict[str, Any]:
        """Get information about a metadata field."""
        field_info = {
            'title': {
                'label': 'Title',
                'description': 'Document title',
                'placeholder': 'Enter document title',
                'multiline': False,
                'max_length': METADATA_MAX_LENGTH['title']
            },
            'author': {
                'label': 'Author',
                'description': 'Document author or creator',
                'placeholder': 'Enter author name',
                'multiline': False,
                'max_length': METADATA_MAX_LENGTH['author']
            },
            'subject': {
                'label': 'Subject',
                'description': 'Brief description of the document',
                'placeholder': 'Enter document subject',
                'multiline': True,
                'max_length': METADATA_MAX_LENGTH['subject']
            },
            'keywords': {
                'label': 'Keywords',
                'description': 'Comma-separated keywords',
                'placeholder': 'keyword1, keyword2, keyword3',
                'multiline': True,
                'max_length': METADATA_MAX_LENGTH['keywords']
            },
            'creator': {
                'label': 'Creator',
                'description': 'Application that created the document',
                'multiline': False,
                'readonly': True
            },
            'producer': {
                'label': 'Producer',
                'description': 'Application that produced the PDF',
                'multiline': False,
                'readonly': True
            }
        }

        return field_info.get(field_name, {})

    def get_all_field_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information for all metadata fields."""
        return {field: self.get_field_info(field) for field in DEFAULT_METADATA.keys()}

    def get_validation_errors(self) -> Dict[str, List[str]]:
        """Get validation errors for current metadata."""
        return self.validator.validate_all(self.current_metadata)

    def format_keywords_for_display(self, keywords: str) -> str:
        """Format keywords for better display."""
        if not keywords:
            return ""

        # Split by comma and clean up
        keyword_list = [k.strip() for k in keywords.split(',') if k.strip()]
        return ', '.join(keyword_list)

    def format_keywords_for_storage(self, keywords: str) -> str:
        """Format keywords for storage."""
        if not keywords:
            return ""

        # Clean up and join with commas
        keyword_list = [k.strip() for k in keywords.split(',') if k.strip()]
        return ', '.join(keyword_list)

    def get_metadata_summary(self) -> Dict[str, Any]:
        """Get a summary of current metadata."""
        validation_errors = self.get_validation_errors()
        has_errors = any(len(errors) > 0 for errors in validation_errors.values())

        return {
            'total_fields': len(self.current_metadata),
            'filled_fields': len([v for v in self.current_metadata.values() if v]),
            'has_errors': has_errors,
            'validation_errors': validation_errors,
            'is_valid': not has_errors
        }

    def export_metadata(self, format_type: str = 'dict') -> Any:
        """
        Export metadata in different formats.

        Args:
            format_type: Format to export ('dict', 'list', 'csv')

        Returns:
            Metadata in the requested format
        """
        if format_type == 'dict':
            return self.current_metadata.copy()
        elif format_type == 'list':
            return [(field, value) for field, value in self.current_metadata.items()]
        elif format_type == 'csv':
            return '\n'.join([f"{field},{value}" for field, value in self.current_metadata.items() if value])
        else:
            raise ValueError(f"Unsupported format: {format_type}")


# Global instance
_metadata_manager: Optional[MetadataManager] = None


def get_metadata_manager() -> MetadataManager:
    """Get the global metadata manager instance."""
    global _metadata_manager
    if _metadata_manager is None:
        _metadata_manager = MetadataManager()
    return _metadata_manager


def initialize_metadata_manager() -> MetadataManager:
    """Initialize the global metadata manager."""
    global _metadata_manager
    _metadata_manager = MetadataManager()
    return _metadata_manager
